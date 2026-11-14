# Spec Delta

## Purpose
Provides secure, persistent storage of completed Tetris game results using SQLite, offering high-score tracking, a RESTful leaderboard API, strict schema validation, responsive frontend visualization, and production-ready containerized packaging with continuous integration.

## ADDED Requirements

### Requirement: REQ-045 SQLite Schema Initialization and Reload Persistence
The system MUST initialize the SQLite database schema automatically on startup, safely creating its parent directory if it does not already exist. The database path MUST be configurable via the `TETRIS_DB_PATH` environment variable, defaulting to `./data/high-scores.sqlite3`. High scores MUST survive backend restarts, reload actions, and container recreation, meaning that subsequent connections or new store instances opening the same database file MUST load and preserve previously recorded results without overwriting them.

Additionally, to satisfy the `TEST-ISOLATION-01` QA criteria, all unit and integration tests MUST utilize isolated temporary test databases (e.g., using pytest's `tmp_path` fixture or equivalent unique temporary directories) so that test execution never deletes, modifies, or overwrites the configured application data directory (`./data`) or real high scores. Destructive recursive directory deletion (such as `shutil.rmtree`) of non-temporary directories is strictly forbidden in test fixtures.

#### Scenario: Verify database schema initialization and persistence across reloads
- **GIVEN** the database file and its parent directory do not exist
- **WHEN** the backend service starts up
- **THEN** the parent directory is created and the database file is initialized with the required table schema and unique constraints
- **AND GIVEN** high scores have been successfully written to the database file
- **WHEN** the backend is restarted or a new database store instance opens the same DB file path
- **THEN** the previously written scores remain fully intact and readable from GET `/api/high-scores`

### Requirement: REQ-046 Persistent High Score Recording on Game Over
Upon game over, the backend MUST persist the final game outcome to the SQLite database. A game is eligible only when its authoritative backend state transitions to `game_over` via gravity ticks, soft drops, or obstructed Hold (both first-Hold empty-slot collision and occupied-Hold swap-collision paths). Active, restarted, or abandoned live games MUST NOT create a high-score record.
The database record MUST include:
1. `game_id` (string, UUID, primary key)
2. `score` (integer, non-negative)
3. `total_lines` (integer, non-negative)
4. `level` (integer, >= 1)
5. `completed_at` (string, ISO-8601 UTC timestamp format e.g., `YYYY-MM-DDTHH:MM:SS.mmmmmmZ` or similar)

Every completed game (including 0 scores) MUST be written exactly once per game ID, enforced by atomic parameterized writes and a database uniqueness constraint. Once finalized, the original stored result and `completed_at` timestamp MUST remain immutable, even if late concurrent or duplicate requests arrive with different score metadata.

#### Scenario: Persistent recording of game over state and immutability
- **GIVEN** a live game session with ID "test-session-1" reaches game over naturally via gravity tick
- **WHEN** the game over state is finalized on the backend
- **THEN** a row is inserted in the high scores database containing game_id="test-session-1" and the correct final scores
- **AND WHEN** a late duplicate request or a subsequent movement request is made with different score metrics for "test-session-1"
- **THEN** the database unique constraint and backend guard reject the write, leaving the original stored scores and `completed_at` immutable

#### Scenario: Verify first-Hold and occupied-Hold obstruction finalizations
- **GIVEN** a game where the spawn area is obstructed such that putting a piece in Hold (first-time, empty hold slot) or swapping a held piece (occupied hold slot) triggers a collision at the spawn origin `[0, 3]`
- **AND GIVEN** the active piece has a legal, canonical four-cell geometry (such as `"O"` at origin `[17, 0]` with cells `[[18,1], [18,2], [19,1], [19,2]]`)
- **AND GIVEN** the next piece to spawn is `"S"`, which spawns at coordinates `[1, 4]`, `[1, 5]`, `[2, 3]`, `[2, 4]` (not overlapping active cells), and the board has a settled block at `[1, 4]` (obstructing `"S"`)
- **WHEN** the Hold operation is executed (first-time, empty hold slot)
- **THEN** the game status transitions to `game_over` and the score is persisted exactly once in the database
- **AND GIVEN** the active piece has a legal, canonical four-cell geometry (such as `"O"` at origin `[17, 0]`), the held piece is `"T"`, which spawns at cells `[1, 4]`, `[2, 3]`, `[2, 4]`, `[2, 5]` (not overlapping active cells), and the board has a settled block at `[1, 4]` (obstructing `"T"`)
- **WHEN** the Swap operation is executed (occupied hold slot)
- **THEN** the game status transitions to `game_over` and the score is persisted exactly once in the database

#### Scenario: Exclude restarted and abandoned games from persistence
- **GIVEN** a live game session is active with score 1200
- **WHEN** the user starts a new game (generating a restart) or the process is stopped before game over
- **THEN** no high score entry is written to the SQLite database for that game session

### Requirement: REQ-047 Leaderboard Retrieval, Truncation, and Tie-Breakers
The backend MUST expose GET `/api/high-scores` to retrieve the top high scores. It MUST return an object containing a `scores` array of at most ten entries (top 10 truncation). The entries MUST be ordered by:
1. `score` descending
2. `completed_at` ascending (ISO-8601 UTC chronological sequence)
3. `game_id` ascending (lexicographical sequence for identical score and timestamp)

Each entry MUST expose exactly the five fields: `game_id`, `score`, `total_lines`, `level`, and `completed_at`. GET requests MUST be fully idempotent and MUST NOT mutate game state or write any database records.

#### Scenario: Retrieve top scores with strict truncation and tie-breaking
- **GIVEN** twelve high-score records exist in the database with ties in score and completion timestamp:
  - Record A: game_id="g1", score=1000, completed_at="2026-10-28T12:00:00Z"
  - Record B: game_id="g2", score=1000, completed_at="2026-10-28T12:00:00Z"
  - Record C: game_id="g3", score=1000, completed_at="2026-10-28T11:59:00Z"
  - Record D: game_id="g4", score=1200, completed_at="2026-10-28T12:05:00Z"
  - ... and 8 other lower scores
- **WHEN** GET `/api/high-scores` is requested
- **THEN** the response contains at most 10 entries
- **AND** the ordering starts with Record D (score 1200)
- **AND** the score 1000 tie is broken chronologically by completed_at, putting Record C (11:59:00) before Records A and B
- **AND** the tie between Record A and Record B (same score and same timestamp) is broken lexicographically, putting Record A ("g1") before Record B ("g2")
- **AND** the fields in each score element contain exactly `game_id`, `score`, `total_lines`, `level`, and `completed_at`

### Requirement: REQ-048 Storage Failure Error Handling and Controlled 503
Database connection, lock, or query errors encountered during leaderboard retrieval (read) or game finalization (write) MUST return a controlled HTTP 503 Service Unavailable JSON response. This error response MUST NOT leak server file paths, SQL queries, database schema details, or programming stack traces.

#### Scenario: Handle database write/read failure gracefully
- **GIVEN** the SQLite database file is locked or its directory is un-writable
- **WHEN** GET `/api/high-scores` or a game finalization write is triggered
- **THEN** the server returns an HTTP 503 status code and a sanitized JSON payload: `{ "detail": "Storage service unavailable" }`

### Requirement: REQ-049 Finalization Retry Behavior on Terminal Mutation
If high-score persistence fails at the moment of game over (producing a 503 error), any subsequent state-mutating request (move, tick, or hold) on that terminal game session MUST retry the persistence operation. A read-only request (GET `/api/games/{id}`) MUST NOT trigger a retry. The underlying game session state MUST NOT be altered by this retry attempt.

#### Scenario: Retry persistence on subsequent move request of a terminal game
- **GIVEN** a game is at status `game_over` but database write initially failed (database locked)
- **WHEN** a client POSTs to `/api/games/{id}/move` for that game session
- **THEN** the backend retries persisting the score, returning success once the database becomes available again, while the game state remains identical and GET `/api/games/{id}` does not trigger a retry

### Requirement: REQ-050 Frontend High Scores Display and UX States
The frontend MUST render a High Scores panel displaying the leaderboard. It MUST fetch high scores on initial page load and immediately after game over, without polling on every gravity tick. It MUST handle and display the following UX states gracefully:
1. **Loading state**: Visible spinner or text indicator while the leaderboard fetch is in-flight.
2. **Empty state**: A friendly, styled message indicating no scores exist yet when the database is empty.
3. **Error state**: A graceful message indicating high scores could not be loaded when the backend returns a 503 error, keeping other UI components working.
4. **Stale-response protection**: Out-of-order API responses must be discarded to prevent older score reads from overwriting newer ones.

#### Scenario: Leaderboard refreshed on game over without tick-polling
- **GIVEN** the game session transitions to game over
- **WHEN** the frontend receives the game over status
- **THEN** the frontend immediately fetches high scores from GET `/api/high-scores` and updates the leaderboard panel
- **AND** no automatic network request is emitted on gravity tick events

### Requirement: REQ-051 CORS Policy Configuration
The backend MUST implement a secure and restrictive CORS policy. Wildcard origins (`*`) are strictly forbidden when credentials are enabled. Configured origins MUST be specified explicitly through the `ALLOWED_ORIGINS` environment variable.

#### Scenario: CORS preflight request check with credentials
- **GIVEN** a client from a configured frontend origin initiates a request with credentials
- **WHEN** the request arrives at the backend
- **THEN** the backend includes the matching `Access-Control-Allow-Origin` and `Access-Control-Allow-Credentials: true` headers rather than wildcard values

#### Scenario: Reject wildcard origin configuration with credentials on startup
- **GIVEN** the environment variable `ALLOWED_ORIGINS` is set to `*` or contains `*`
- **WHEN** the backend service starts up
- **THEN** the backend raises an explicit ValueError or configuration exception to prevent insecure wildcard credentials configuration, ensuring arbitrary origins cannot receive credentialed access

### Requirement: REQ-052 Configurable Same-Origin API Base and Proxy Setup
The frontend MUST use a configurable API base URL, defaulting to the same-origin `/api` path. In development, the Vite development proxy MUST proxy `/api` paths to the backend service. In production containerized deployments, the proxy MUST handle same-origin proxying transparently.

#### Scenario: Verify same-origin API base path structure
- **GIVEN** the frontend application is running in Vite development mode
- **WHEN** network requests to `/api/games` are made
- **THEN** Vite's development proxy routes the request to the backend container or local server, operating seamlessly under same-origin rules

### Requirement: REQ-053 Reproducible Containerized Environment and Operational Isolation
The project MUST include reproducible and isolated Docker packaging. It MUST define separate multi-stage Dockerfiles for backend and frontend, set up a local runner using Docker Compose, run containers as non-root users, publish only the frontend on host port 5183 with the backend remaining internal, and map the backend SQLite database directory through a named writeable volume.

Operational and policy constraints include:
1. **PACKAGING-ISOLATION-01**: The Compose project, backend/frontend container names, and named SQLite database volume MUST be fully isolated and namespaced specifically to this tool/stage, utilizing the name `tetris-stage3-openspec` (e.g. `tetris-stage3-openspec-backend`, `tetris-stage3-openspec-frontend`, and `tetris_stage3_openspec_data`). The documented compose command must run within this isolated project scope. Unrelated volumes (such as `tetris_sqlite_data` from prior initial06 drafts) must remain untouched.
2. **PACKAGING-CONTEXT-01**: The `.dockerignore` file MUST explicitly exclude `docs/`, `.gemini/`, `.git/`, all local venvs, `node_modules/`, `caches/`, `build/`, `coverage/`, `runtimeDB`, and `credentials` to keep the context size minimized and prevent leaking of secrets/test-runs.
3. **RUNTIME-POLICY-01**: Node 24 (LTS) MUST be used consistently for frontend Docker builds and CI instead of EOL Node 20. The production frontend Nginx base image MUST use an official, maintained, stable Nginx Alpine image (e.g., `nginx:stable-alpine` representing current 1.30.x stable branch or 1.26.x depending on release cycles as checked on 2026-10-28) rather than the EOL 1.25 branch, and its digest/version must be captured in evidence. Python 3.11 remains unchanged.
4. **Non-Root Runtime**: Both backend and frontend containers MUST run as non-root users (e.g. `appuser` with UID 10001 in backend, and standard system user `nginx` in frontend).
5. **Single Backend Worker**: The backend ASGI runner MUST be configured with exactly one worker thread/process to support the authoritative in-memory state.
6. **Health Checks**: Containers MUST feature health checks to verify service availability.
7. **Named Volume Verification**: The named volume must be mounted with write permissions, and persistence must survive container destruction and recreation (`docker compose down && docker compose up -d`) as long as the volume is not explicitly deleted.

#### Scenario: Validate isolated container health, non-root run, and persistence
- **GIVEN** the isolated containers are started via Docker Compose in the `tetris-stage3-openspec` project namespace
- **WHEN** the frontend is accessed on host port 5183 and high scores are created on the namespaced database volume `tetris_stage3_openspec_data`
- **THEN** backend and frontend containers run as non-root users, the frontend proxies `/api` to the backend, and high scores survive container recreation without deleting the named volume

### Requirement: REQ-054 Executable Performance Benchmarking and Evidence
The system MUST include an executable performance benchmark using Playwright Chromium to verify rendering and frame throughput against the production frontend. The benchmark scenario MUST use a visible foreground browser at 1280x900, device scale factor 1, a 60 Hz target, 5 seconds of warm-up, and three independent 30-second runs while simulating user actions to maintain active gameplay.

Detailed evidence constraints (PERF-EVIDENCE-01) include:
1. **Raw Arrays & Outcomes**: The benchmark script MUST save per-run raw JSON arrays of `frameIntervals` and `actionLatencies`, and record every single action outcome (success, timeout, blocked, or no-change), `browser.version()`, exact timestamps, foreground/visibility state, execution metadata, trace file path, and trace hashes.
2. **Fresh Contexts**: The benchmark MUST use a completely fresh context and page per independent run, executing its own warmup phase prior to the 30-second measurement.
3. **Deterministic Actions**: User key-strokes (left, right, soft-drop, and hold) MUST be simulated using a deterministic and replayable action sequence, rather than a completely random selection.
4. **Active Board Observer**: A MutationObserver MUST be attached directly to the active current board DOM container, and MUST be re-attached/re-initialized to the current board element after any game restart or reset.
5. **Attribution and Limits**: The benchmark must correlate action, API, and DOM observations as closely as possible and explicitly label any attribution limitations (e.g., distinguishing action latency from gravity-induced ticks, and identifying that the first DOM mutation after dispatch may be due to gravity rather than user action).
6. **Execution Mode and Environment Controls**: Explicit headful/foreground run is required for full acceptance. Running in a headless environment must be labeled unsupported/not accepted for that specific criterion. Chromium's sandbox MUST NOT be disabled unless explicitly required by environment limits, and never disabled globally. To support HOST headed capability where bundled Playwright Chromium fails with spawnUNKNOWN, an explicit `BROWSER_CHANNEL=chrome` override (or equivalent flag/config) MUST be supported to launch the installed official Chrome via `Playwright.chromium` with `chromiumSandbox: true`, disclosing the brand/version/channel as a controlled Chromium-family variation without modifying any personal browser profiles or tabs. Headless fallback data may be retained but MUST NOT earn headed acceptance or successful overall exit; headless and headed are separate outcomes.
7. **Timing Window Precision**: The benchmark MUST capture frame intervals and DOM update counts only inside the precise active 30000ms measurement window (defined by `measurementActive` and browser-monotonic start/end timestamps, which begins AFTER restart settles and warmup completes). Raw frame interval and action data collection MUST be frozen and copied/serialized BEFORE screenshots are taken, tracing is stopped, or zip ZIP I/O operations occur, to prevent I/O lag from contaminating the performance measurements.
8. **Action Evidence Integrity**: Retain every key dispatch attempt with unique IDs, key name, timestamp, expected/blocked/rejected/nochange/timeout classification, and raw latency observations. Add actual API request, response status, and round-trip timing correlated to each backend dispatch where possible. Never drop 200ms timeouts from the evidence or silently conflate no-ops as slow success.
9. **Failed Targets**: The benchmark must enforce a non-zero exit code if the mean frame scheduling rate drops below 55 FPS or the p95 interval exceeds 25 ms, while still ensuring that all collected raw data, JSON outputs, and zip traces are preserved.
10. **Isolated Evidence**: The benchmark must preserve prior run results (e.g., initial06/07 traces) and save its outputs in a unique evidence directory per invocation (refusing to overwrite existing folders). It must also capture and save application screenshot PNGs/JPGs at meaningful game states for visual QA.

The operational targets are: mean frame scheduling rate >=55 FPS and p95 interval <=25 ms in every run (as a tolerance around a 60 Hz target, not a guarantee of physical display presentation). Timing-sensitive benchmarks MUST be separate from ordinary CI unit testing.

#### Scenario: Run Playwright performance benchmark and output raw metrics
- **GIVEN** the production frontend and backend containers are active
- **WHEN** the performance benchmark script is executed with `BROWSER_CHANNEL=chrome`
- **THEN** it performs three 30-second runs under the configured conditions, collects and writes raw metrics and browser traces to disk, and reports statistical aggregates honestly without altering game gravity

### Requirement: REQ-055 GitHub Actions Continuous Integration and Quality Gate Checks
The repository MUST include a GitHub Actions continuous-integration workflow. It MUST pin Python and Node major versions, run backend tests and coverage, run frontend tests and production builds, run dependency audits, and verify Docker image builds. The workflow MUST NOT require any private secrets.

It MUST output real file paths for fresh coverage LCOV or XML, run basic security dependency audits, and record their findings without fabricating remote hosted execution results.

It MUST resolve Sonar QA issues from the analysis qa07 (analysis `24b87da3-2e58-4087-a9aa-17dae3c27c05` which resulted in an ERROR gate) without weakening assertions, changing gate thresholds, hiding files, or adding suppressions:
1. **python:S1192** (String literals duplication): Extract duplicated string literals in `backend/main.py` (such as the Hold rejection message `"Hold disabled: piece already swapped this turn"`) into a named constant.
2. **python:S9100** (Unnecessary yield fixture): Correct any backend test fixtures in `backend/test_stage3.py` that utilize a `yield` statement without performing any post-yield teardown/cleanup, refactoring them to use simple `return` values if teardown is not needed.
3. **typescript:S6582 and S7741** (Optional chaining / direct comparison with undefined): Refactor typescript checks in `frontend/src/api.ts` to use explicit direct comparison against `undefined` or robust checks instead of improper optional chain usages.

#### Scenario: Verify continuous integration workflow and QA Quality Gate compliance
- **GIVEN** a pull request is created or code is pushed
- **WHEN** the GitHub Actions CI trigger fires and Sonar scans are performed
- **THEN** it runs all lint, build, test (saving LCOV and XML coverage outputs), and container checks, outputting findings with 0 Quality Gate violations on Sonar metrics.

### Requirement: REQ-057 State Mutation Synchronization Boundary
The backend MUST protect authoritative in-memory game state mutations (ticks, moves, hold swaps) and finalization from concurrent/duplicate requests within the single-process backend. A synchronization boundary (such as an asynchronous lock per game ID) MUST guard state changes. If multiple concurrent requests arrive for the same game session, they MUST be serialized. When a duplicate finalization request is processed, the original stored score and `completed_at` MUST remain immutable, and subsequent writes for that game ID MUST be safely rejected.

#### Scenario: Serialized concurrent mutations on active game
- **GIVEN** a single-process backend handling active game session "game-concurrent-1"
- **WHEN** two concurrent POST requests to move or tick game "game-concurrent-1" arrive simultaneously
- **THEN** they are serialized by the backend synchronization lock, preventing race conditions or corrupt board matrix states
