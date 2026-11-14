# Feature Specification: Tetris Stage 3 Option A - Persistent High Scores, Dockerization, Playwright Benchmarking, and CI

**Feature Branch**: `003-tetris-stage3-option-a`

**Created**: Thursday, October 29, 2026

**Status**: Draft

**Input**: User description: "Extend this tool's own final Stage 2 option A Tetris source and native specifications to Stage 3 option A as a brownfield change. Work only in this tool's Stage 3 directory. Preserve Python FastAPI, React/TypeScript, the 10-by-20 React DOM board, seven unrotated tetrominoes, authoritative in-memory backend games, existing API compatibility, left/right/soft-drop, collision, locking, line clearing, game over, restart by creating a new game, score rules, lines, levels, progressive gravity, Hold and next preview. Preserve existing tests and add meaningful tests. Use English for tool interactions, native specs, application text, comments and tests. Create or revise native specifications before implementation; all corrections to generated code must first be reflected in native specs and then applied through the tool's normal workflow.

Add persistent high scores using SQLite and Python's standard sqlite3 module. The configurable environment variable TETRIS_DB_PATH defaults to ./data/high-scores.sqlite3. Initialize the parent directory and schema safely on service startup. A game is eligible only when its authoritative backend state reaches game over. Persist every completed game including zero scores, once per game ID, using a database uniqueness constraint and atomic parameterized writes. Record game_id, score, total_lines, level, and completed_at (UTC ISO-8601). A game ended through gravity, soft drop or obstructed Hold must follow the same finalization rules. A restart or abandoned live game must not create a high score. Repeated terminal actions and concurrent finalization attempts must not duplicate or replace the original result or completion timestamp. GET game state and leaderboard reads must not mutate game state or create records. Protect state mutation and finalization from races within the supported single-process backend. Active games remain in memory and are not resumed after process restart; high scores survive backend and container restart. Do not claim multiple-worker support for in-memory games.

GET /api/high-scores returns an object with a scores array of at most ten entries, ordered by score descending, then completed_at ascending, then game_id ascending. Each entry has exactly the recorded fields above. No public endpoint accepts a client-supplied score, lines, level, completion time or arbitrary game ID to insert a score. Reject extra fields in game creation and move request bodies rather than silently trusting submitted score metadata; preserve valid bodyless game creation and existing valid movement bodies. Invalid direction returns a documented 4xx, unknown game remains 404. Storage failures on leaderboard or finalization produce a controlled 503 JSON response without leaking file paths, SQL or stack traces. If finalization fails after game over, a subsequent mutating request on that terminal game retries persistence safely while preserving its state; a GET never performs that retry. Tests must explicitly cover failure and recovery, ties, concurrency, idempotency, injection-like inputs, and persistence after a new app/store instance opens the same DB file.

Show a High Scores panel in the frontend, with score, lines and level; handle loading, empty and error states. Fetch on initial load and after game over, without polling on every gravity tick. Preserve keyboard controls, Hold restrictions, restart and stale-response protection. The frontend must use a configurable API base with a same-origin /api default, so development and Docker deployment work without a hardcoded localhost URL. Define and document a restrictive, configurable CORS policy; no wildcard origin with credentials. No authentication or player-name collection is required.

Provide reproducible Docker packaging: separate backend and frontend images using multi-stage Dockerfiles where useful, a .dockerignore, and Docker Compose as the local runner. The frontend serves the production build and proxies /api to the backend. Both application containers run as non-root, publish only the frontend on host 5183, and keep the backend internal. Use a named volume with write permissions for the backend SQLite directory, configurable backend DB path, health checks, and one backend worker. Do not bake credentials or development dependencies into runtime images. Document exact build, start, stop and persistence-verification commands. Measure actual image sizes and build time when Docker is available, report those values without inventing an optimization percentage or imposing an arbitrary size limit.

Add an executable browser performance benchmark using Playwright Chromium against the production frontend. Separate browser frame scheduling, actual game DOM updates and API timing: requestAnimationFrame frequency alone is not proof of rendering throughput. Retain raw frame intervals, DOM mutation/update counts and action-to-visible-update samples, plus a browser performance trace with screenshot frames or equivalent evidence. The controlled scenario uses a visible foreground browser at 1280x900, device scale factor 1, a recorded 60 Hz target, five seconds of warm-up and three independent measured 30-second runs. Exercise actual left/right/soft-drop changes and restart as needed to maintain gameplay. Record browser/runtime/OS/hardware, display and headless/foreground mode, scenario, frame interval median/p95/p99, approximate FPS, intervals above 33.34 ms and action latency. The operational target is mean frame scheduling rate >=55 FPS and p95 interval <=25 ms in every run; explain that this is a tolerance around a 60 Hz target, not a guarantee of physical display presentation. Report unsupported environment or failed targets honestly. Benchmarking must not change game gravity, add a permanent animation loop solely to inflate the metric, rotate pieces, migrate DOM to Canvas/WebGL, or issue 60 API requests per second. Run timing-sensitive checks separately from ordinary unit CI, with an explicit performance job or documented manual command.

Include a GitHub Actions continuous-integration workflow for backend tests and coverage, frontend tests and production build, and Docker image builds. Pin the Python and Node major versions used by the workflow and document reproducible dependency installation; preserve or update dependency lockfiles coherently. The workflow must not require private secrets for these checks. Add basic dependency audit commands and report their actual findings. The researcher will run independent Stage 1/2 regression, Stage 3 acceptance and SonarQube checks; do not fabricate their results, tokens, costs, screenshots, CI runs, performance, or Docker success. A local workflow file is not evidence of a hosted Actions run.

Exclude rotation, wall kicks, ghost piece, T-Spins, time attack, achievements, saved/resumable games, PostgreSQL, authentication, multiplayer, global real-time leaderboards and cloud deployment. Preserve previous stage outputs in their original directories. Do not create commits, push, publish images or deploy externally."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - SQLite-Backed Persistent High Scores & Database Isolation (Priority: P1)

As a Tetris player, I want my finished games (including zero scores) to be permanently and reliably persisted on the backend server using an SQLite database, so that my achievements survive backend, container, or server restarts.

**Why this priority**: Permanent and robust persistence is the foundational backend database change that powers the entire Stage 3 feature set.

**Independent Test**: Can be fully tested by starting a game, letting it reach game over (either via falling pieces reaching the top-center spawn origin, or using a soft drop, or hitting an obstructed Hold spawning block), and verifying that:
1. The backend SQLite database is written to immediately under the location specified by the `TETRIS_DB_PATH` environment variable.
2. The database contains exactly one row for this game's UUID (`game_id`), the final `score`, `total_lines` cleared, final `level`, and a correct UTC ISO-8601 timestamp (`completed_at`).
3. If the backend process is killed and restarted, the high score remains in the database and is readable via the leaderboard endpoint.

**Acceptance Scenarios**:

1. **Given** the backend server is starting up, **When** checking the directory path configured in `TETRIS_DB_PATH` (defaulting to `./data/high-scores.sqlite3`), **Then** the server must safely create the parent directory if it does not exist, initialize the SQLite file, and construct the `high_scores` table schema with appropriate constraints if it is not already present, without crashing.
2. **Given** an active, authoritative in-memory game session, **When** its status transitions to `"game_over"` (whether by progressive gravity tick, soft drop move, or Hold piece obstruction), **Then** the backend must perform an atomic, parameterized database insert of the game's final metrics once, using the game's UUID as the `game_id` primary/unique key.
3. **Given** a game is already in `"game_over"` status, **When** repeated terminal requests (such as additional tick or move commands) or concurrent requests attempt to finalize the game again, **Then** the database uniqueness constraint on `game_id` must prevent any duplicate records or overwrites, preserving the original record and its completion timestamp exactly.
4. **Given** a game in progress is abandoned or restarted (a new game session is created by the player), **When** the in-memory game is discarded, **Then** no database row must be generated for that discarded game ID, and its incomplete metrics must not appear on the high scores table.
5. **Given** a GET request is issued to inspect the game state or the leaderboard, **When** the server handles the request, **Then** the server must never write any records to the database or modify any game session states.

---

### User Story 2 - Secure High-Scores REST API with Rigorous Body Validation (Priority: P2)

As a security-conscious game developer, I want the backend REST API to expose a read-only leaderboard endpoint and rigorously validate all input requests, rejecting extra metadata or client-supplied scores, so that the leaderboard is protected from cheating, SQL injection, or data corruption.

**Why this priority**: API validation and read-only constraints prevent players from forging high score submissions or injecting arbitrary records.

**Independent Test**: Can be tested by sending malformed payloads, headers, or SQL-injection-like patterns to `/api/games` and `/api/games/{id}/move` endpoints and verifying they are rejected with a 4xx error. Confirm that sending a manual payload to `/api/high-scores` is not supported (no POST method on that path) and that GET requests return clean, validated data.

**Acceptance Scenarios**:

1. **Given** a client requests `GET /api/high-scores`, **When** the database contains several scores, **Then** the response must be a JSON object containing a `scores` array of at most 10 entries, sorted in descending order of `score`, then ascending order of `completed_at` (to favor earlier achievements), and finally ascending order of `game_id` (for absolute determinism in ties), with each entry containing exactly the five fields: `game_id`, `score`, `total_lines`, `level`, and `completed_at`.
2. **Given** a client makes a `POST /api/games` or `POST /api/games/{id}/move` request, **When** the request body contains extra keys (e.g. attempting to submit score metadata or client-computed levels), **Then** the backend must reject the request with a documented `4xx` error rather than silently ignoring or trusting the submitted metadata, while still accepting valid bodyless game creations and existing valid movement bodies.
3. **Given** a move request contains an invalid movement direction, **When** processed by the API, **Then** the API must return a documented 4xx response, whereas a request for an unknown game ID must return a `404 Not Found` response.
4. **Given** a database query or connection failure occurs during leaderboard fetching or game finalization, **When** the API handles the request, **Then** the API must return a clean, controlled `503 Service Unavailable` JSON response that explicitly hides database paths, raw SQL strings, or Python stack traces.
5. **Given** a database persistence error occurs during the initial finalization of a terminal game, **When** a subsequent mutating action (such as soft drop on the dead game) is issued, **Then** the backend must attempt to retry the database persistence safely without altering the existing terminal game state.

---

### User Story 3 - High Scores UI Panel and Stale-Response Protection (Priority: P2)

As a Tetris player, I want to see the top 10 persistent high scores on a "High Scores" panel in the frontend dashboard, showing the score, line count, and level, with smooth transitions, error handling, and robust stale-response filtering, so that I have immediate visual feedback on my ranking.

**Why this priority**: The frontend presentation completes the persistent high scores feature, enabling the player to instantly see the results of their gameplay.

**Independent Test**: Can be tested by opening the frontend, verifying that the High Scores panel loads its content on startup, handles empty state (displays "No high scores yet") or error state (displays an elegant warning message) gracefully, updates immediately after a game ends, and ignores slow/out-of-order API responses.

**Acceptance Scenarios**:

1. **Given** the Tetris application starts up in the browser, **When** the main page loads, **Then** the frontend must immediately request `/api/high-scores` and render the panel showing the rank, score, lines, and level for each of the top 10 scores, showing a loading indicator during the request.
2. **Given** a game is currently active, **When** the player is playing, **Then** the frontend must never poll or fetch the high scores list during active gameplay ticks, preventing unnecessary API overhead, and only trigger a new fetch once the game transitions to `"game_over"`.
3. **Given** the frontend receives an error from the leaderboard API (e.g., a 503 error), **When** displaying the High Scores panel, **Then** the panel must show a user-friendly error state indicating that the leaderboard is temporarily unavailable, without breaking the rest of the game UI.
4. **Given** a player is rapidly restarting the game or issuing moves, **When** multiple backend HTTP responses arrive out of order, **Then** the frontend must discard any stale responses and only apply the state corresponding to the most recent request sequence or timestamp.
5. **Given** the application is deployed in a Docker or custom production environment, **When** making API calls, **Then** the frontend must use a configurable API base that defaults to the same-origin `/api` (avoiding a hardcoded `localhost:8000` string) so that proxying and custom routing function seamlessly.

---

### User Story 4 - High-Performance Containerized Packaging (Priority: P3)

As a system operator, I want to build and execute the entire Tetris application with a single command using Docker Compose, running under non-root permissions and using a persistent named volume for the SQLite database, so that deployment is clean, reproducible, and secure.

**Why this priority**: Containerization guarantees that local development matches the production target precisely and runs with high security standards.

**Independent Test**: Can be tested by running `docker compose up --build`, confirming that host port 5183 is mapped to the frontend production build which proxies `/api` to the backend internal network, verifying that both containers execute as non-root users, and verifying that database writes persist after a complete docker-compose down and up cycle.

**Acceptance Scenarios**:

1. **Given** separate backend and frontend multi-stage Dockerfiles and a `.dockerignore` file, **When** running Docker Compose, **Then** the frontend production build must be served by a non-root lightweight server, and the backend must run a single-worker Uvicorn process under a non-root user.
2. **Given** the Docker containers are running, **When** accessing host port 5183, **Then** the player must be able to load the frontend and play the game successfully, while host port 8000 (backend) remains completely closed to the public host interface.
3. **Given** a Docker environment, **When** the backend container writes to SQLite, **Then** it must store the database inside a persistent named volume mapped to the backend SQLite directory, utilizing the `TETRIS_DB_PATH` environment variable.
4. **Given** the containers are running, **When** running docker health checks, **Then** both containers must report healthy status using lightweight, non-intrusive health checks.
5. **Given** the production images are built, **When** inspecting their layers, **Then** neither development dependencies nor hardcoded credentials must be baked into the runtime images.

---

### User Story 5 - Automated Browser Performance Benchmarking & CI Pipeline (Priority: P4)

As a QA engineer, I want to execute an automated performance benchmark using Playwright Chromium to measure the exact frame-scheduling intervals and latency of the production frontend, and to have a GitHub Actions workflow that automatically validates all tests and builds on every commit, so that code quality and visual smoothness are guaranteed.

**Why this priority**: Verifies rendering performance and workflow health continuously without relying on manual checks or physical display capabilities.

**Independent Test**: Execute the Playwright script manually or via CI, confirming that it spawns a foreground browser at 1280x900, runs for the specified duration (5s warmup, 3x30s runs) while triggering keyboard inputs, collects frame times and action latencies, and produces a summary report with screenshot/trace proofs.

**Acceptance Scenarios**:

1. **Given** the Playwright performance test script is executed against the production frontend, **When** the benchmark runs in a 1280x900 foreground browser window, **Then** it must record actual frame scheduling intervals via `requestAnimationFrame` timing, actual DOM update counts, action-to-visible-update latency, and generate a standard performance trace with screenshots, without altering game gravity or adding fake loops.
2. **Given** the benchmark runs complete, **When** reporting metrics, **Then** it must output the median, p95, and p99 frame intervals, approximate FPS, and the count of slow frames (intervals > 33.34 ms), targeting a mean scheduling rate >=55 FPS and a p95 interval <=25 ms.
3. **Given** the GitHub Actions workflow file is executed on a push or pull request, **When** running on the host, **Then** it must successfully install pinned Python and Node major versions, run backend tests and coverage, run frontend tests and production builds, execute a basic security dependency audit, and test-build the Docker images, without requiring any repository-wide private secrets.

---

### Edge Cases

1. **Obstructed Hold Game Over**: If a player swaps the active piece with a held piece that immediately overlaps with settled blocks at the top-center spawn coordinates, the game state must transition to `"game_over"`. This terminal state must immediately trigger game finalization and persist the score (even if 0 or low) to the SQLite database.
2. **Database Write Failure Handling**: If the database file is locked or the disk is full when a game ends, the API must respond with a controlled 503. If the user subsequent triggers a mutating action (e.g. soft drop down) on that already dead game, the API must attempt to re-save the score, resolving temporary lock situations.
3. **SQL-Injection attempts in Game ID**: If a client calls `GET /api/games/1; DROP TABLE high_scores;--` or similar SQL injection strings, the server must reject it cleanly (as an invalid UUID / 404 or a validated 4xx path parameter pattern) rather than executing or interpolating the string into raw SQLite commands.
4. **Ties in High Scores**: If multiple games end with the exact same score, they must be ordered in the leaderboard by `completed_at` ascending (favoring the game that was achieved earlier), then by `game_id` lexicographically ascending.

## Requirements *(mandatory)*

### Functional Requirements

#### SQLite Storage & Database Schema Requirements
- **FR-001**: The backend MUST utilize a local SQLite database using Python's standard `sqlite3` module.
- **FR-002**: The backend MUST read the database file path from the environment variable `TETRIS_DB_PATH`, falling back to `./data/high-scores.sqlite3` if not defined.
- **FR-003**: During service startup, the backend MUST ensure the parent directory of the database file exists, creating it safely if missing.
- **FR-004**: The backend MUST initialize the database schema safely on service startup with a table named `high_scores` if it does not exist, containing the following columns:
  - `game_id` TEXT (Primary Key, Unique, UUID string)
  - `score` INTEGER (Not Null, >= 0)
  - `total_lines` INTEGER (Not Null, >= 0)
  - `level` INTEGER (Not Null, >= 1)
  - `completed_at` TEXT (Not Null, ISO-8601 UTC string format)
- **FR-005**: Game finalization MUST write to the database using atomic parameterized queries (e.g., `INSERT INTO high_scores ... VALUES (?, ?, ?, ?, ?)`) to prevent SQL injection.
- **FR-006**: A game score MUST be finalized and persisted immediately when the authoritative in-memory game state reaches `"game_over"`. This includes games ended through:
  - Progressive gravity (standard game ticks resulting in block placement overlap at the spawn origin),
  - Soft drops (natural-play progressive gravity ticks occurring on pieces positioned at the bottom, resulting in block placement overlap at the spawn origin), or
  - Obstructed Hold operations, covering both empty-slot first hold (firstHold) and occupied-slot piece swap (swap) where the newly spawned tetromino overlaps with settled blocks on the board.
  *Design Note on Manual Down Collision*: In accordance with Stage 1 FR016, manual collision actions (including manual downward movement requests) MUST leave the state completely unchanged and do NOT lock pieces or trigger game over. Only gravity ticks (or obstructed hold) can lock pieces and transition the game to `"game_over"`. Therefore, a manual down move request at the bottom will not lock the piece or finalize the game. This is a deliberate design preservation of the Stage 1 & 2 core mechanics. While automated common checkers expecting manual down to lock immediately will report a mismatch (such as S3-API08), this is a documented and verified compatibility constraint.
  All finalizations must use legal tetromino states. A restart, abandoned live game, or a read-only GET request MUST NOT create a high score or mutate game state.
- **FR-007**: Every completed game, including those with a score of 0, MUST be persisted exactly once per unique `game_id`.
- **FR-008**: An active game session that is restarted, abandoned, or closed before reaching `"game_over"` MUST NOT generate any records in the database.
- **FR-009**: The backend MUST protect both the authoritative in-memory game state and finalization from races using explicit thread-safe synchronization (e.g., a mutex or threading lock) in the single-process, one-worker backend. Serializing SQLite database writes or relying solely on SQLite's database-level unique constraints is insufficient. All mutating game operations (tick, move, hold) and finalization must be fully serialized. GET requests remain strictly read-only and MUST NOT write records, perform persistence, or retry failed persistence.
- **FR-010**: Active games MUST reside purely in-memory and MUST NOT be persisted or resume after a backend process restart; however, completed high scores MUST survive backend and container restarts.
- **FR-011**: The backend MUST NOT claim multiple-worker support for active, in-memory games.

#### Leaderboard and API Requirements
- **FR-012**: The API MUST expose `GET /api/high-scores` returning a JSON object with a `scores` array containing at most 10 entries.
- **FR-013**: The leaderboard entries returned by `GET /api/high-scores` MUST be ordered by `score` descending, then `completed_at` ascending (UTC time), then `game_id` ascending.
- **FR-014**: There MUST be no public API endpoint that accepts client-supplied scores, line counts, levels, or timestamps to insert arbitrary high score records.
- **FR-015**: The backend MUST rigorously validate incoming JSON request bodies for `POST /api/games` and `POST /api/games/{id}/move` and reject any request containing extra fields (preventing clients from submitting forged metadata). Valid bodyless game creations and existing valid movement bodies MUST be accepted.
- **FR-016**: An invalid movement direction string in `/api/games/{id}/move` MUST return a documented 4xx error response.
- **FR-017**: A request querying a non-existent or unknown game ID MUST return a `404 Not Found` response.
- **FR-018**: In the event of a database storage failure (e.g., database locked, disk full), the API MUST return a controlled `503 Service Unavailable` JSON response and MUST NOT leak any file system paths, SQL queries, or Python stack traces.
- **FR-019**: If database finalization fails after game over (e.g. database locked), subsequent mutating requests on that terminal game must safely retry persistence while preserving its terminal state exactly. GET requests must remain read-only and never trigger retries. Repeated terminal actions or concurrent finalization attempts must be idempotent, never duplicating the record or replacing the original score or completion timestamp.

#### Frontend Panel and Integration Requirements
- **FR-020**: The frontend MUST display a visually appealing High Scores panel listing the rank, score, total lines, and level for the top 10 entries.
- **FR-021**: The frontend MUST show explicit loading, empty (no records present), and error states (if the API fails or returns 503) on the High Scores panel.
- **FR-022**: The frontend MUST fetch the leaderboard on initial application load and immediately after a game transitions to `"game_over"`, and MUST NOT poll the leaderboard during active gameplay or gravity ticks.
- **FR-023**: The frontend MUST use a configurable API base URL with a default of the same-origin `/api` path, allowing development and Docker Compose routing to function without hardcoded hostnames.
- **FR-024**: The frontend and backend MUST preserve all Stage 2 controls, Hold mechanics, keyboard key binds (`C` for Hold, left/right/soft-drop), score accumulation rules, progressive gravity, and next-piece previews.
- **FR-025**: The frontend MUST maintain stale-response protection, discarding out-of-order or late API responses to prevent visual jumping.
- **FR-026**: The application MUST configure and document a restrictive CORS policy that prohibits wildcard origins (`*`) when credentials are used. No user registration, player-name inputs, or authentication are required.

#### Containerization & Docker Compose Requirements
- **FR-027**: The project MUST provide a reproducible Docker Compose environment as the local runner.
- **FR-028**: The backend and frontend MUST have separate images, leveraging multi-stage Dockerfiles to minimize final image sizes.
- **FR-029**: The frontend image MUST serve the production build and proxy `/api` requests to the backend service.
- **FR-030**: Both application containers MUST execute under non-root user accounts.
- **FR-031**: The host environment MUST only expose port 5183 for the frontend container. The backend container MUST remain completely internal to the Docker network.
- **FR-032**: The backend container MUST mount a named Docker volume with write permissions mapped to the SQLite database directory.
- **FR-033**: The Docker compose configuration MUST configure the SQLite path via the `TETRIS_DB_PATH` environment variable.
- **FR-034**: Both containers MUST include lightweight, non-root health checks.
- **FR-035**: The production images MUST NOT bake in credentials or development dependencies.
- **FR-036**: A `.dockerignore` file MUST be supplied to exclude development node_modules, Python virtual environments, and database files from build context.

#### Playwright Performance Benchmark Requirements
- **FR-037**: The project MUST include an executable performance benchmark script using Playwright Chromium targeting the production frontend.
- **FR-037B**: The browser launch MUST set `chromiumSandbox: true` explicitly in EVERY browser launch branch, including the installed Chrome channel and the bundled fallback browser. It MUST NEVER add `--no-sandbox` or a fallback that silently disables the sandbox. It MUST record the actual launch configuration (including headless=false/chromiumSandbox=true/channel/version) in raw environment metadata so the sandbox choice is auditable, together with headless, channel, version, viewport, DPR, and focus.
- **FR-038**: The benchmark MUST measure actual frame-rendering throughput, making separate and independent observations of browser frame scheduling (cadence of `requestAnimationFrame` events), actual game DOM updates, and API transaction timing. It must explicitly note that `requestAnimationFrame` scheduling rate alone does not prove rendering throughput, physical display presentation, or causal input redraw.
- **FR-039**: The benchmark MUST capture and report: median, p95, and p99 frame intervals; approximate FPS; the count of slow frames (intervals > 33.34 ms); and input action-to-visible-update latency.
- **FR-040**: The benchmark MUST record system details (OS, hardware, browser, headless/foreground mode, and scenario details) and export raw frame intervals, DOM mutation/update counts, action-latency samples, and a Chromium performance trace with screenshots.
- **FR-041**: The benchmark scenario MUST use a visible foreground browser sized at 1280x900 with a device scale factor of 1, targeting 60 Hz scheduling. It MUST feature a 5-second warm-up and a fixed 30-second measurement window for *each* of the three independent runs (each run has its own independent 5-second warm-up and 30-second measurement).
- **FR-041B**: The benchmark MUST utilize an independent in-page `requestAnimationFrame` sampler owned by the external benchmark harness. It MUST NOT depend on the application calling `requestAnimationFrame` to obtain frame samples or inject a permanent app-side loop.
- **FR-041C**: The benchmark MUST continuously monitor and record page visibility and focus throughout each run's warmup and measurement windows. After EACH collector reset, the benchmark MUST retain a current visibility/focus snapshot, plus start/end snapshots and all visibility/focus events for the trial, proving the page was visible and focused at the start and end, with no loss of focus or visibility during the entire measured window. Faking hasFocus, visibility, or browser globals is strictly prohibited.
- **FR-041D**: The benchmark MUST reset collectors after each run's warmup and freeze buffers precisely at the declared 30-second window end before any serialization, tracing, or screenshot I/O. It must distinguish start/end timestamps and categorize boundary intervals or out-of-window events.
- **FR-041D1**: The benchmark MUST use a single declared in-page monotonic timeline for every independent trial:
  1. Warmup start: `warmupStart = now`. Warmup end: `warmupEnd = warmupStart + 5000`. Measurement start: `measurementStart = warmupEnd`. Declared measurement end: `declaredEnd = measurementStart + 30000`. Classify all samples by these exact clock bounds independently of any Node/Playwright delay.
  2. Retain `performance.timeOrigin`, `warmupStart`, `warmupEnd` and their clock units. Each trial has its own 5-second warmup, with a declared warmup deadline; warmup frames do not enter the measured metrics.
  3. At measurement start set `start = warmupEnd` and `declaredEnd = start + 30000`. That `declaredEnd` defines the metric window regardless of Node event-loop, Playwright transport, actions, screenshots, or serialization delays.
  4. Every rAF record contains its interval start and interval end. It enters summary statistics only when `intervalStart >= start` AND `intervalEnd <= declaredEnd`. Retain crossing/before/after intervals separately with explicit reasons, rather than deleting them or counting them as within-window. Preserve timestamps needed to reproduce this classification. Zero/nonpositive intervals remain raw and are explicitly ineligible; summary counts only eligible positive intervals.
  5. All DOM/action/API/focus events carry timestamps and window classification. Retain actions that timeout or remain pending; do not invent completion. Request IDs, endpoint/method/game identity and timing allow correlation where supported. Mark next-DOM-change action latency as heuristic/causality unknown unless there is stronger evidence; never present an unrelated mutation as proven visual completion.
  6. Stop collecting measured buffers at `declaredEnd` using the in-page clock/deadline. A timer may fire late: record `observedWarmupStop` and `observedStop` separately, retain/classify late observations, and keep reported `end = declaredEnd`. Freeze before any trace/screenshot/JSON I/O. The parent may await an in-page completion signal; its own wall-clock wait does not define the metric duration.
  7. Calculate FPS over exactly 30 seconds from eligible scheduling intervals and derive percentiles only from those eligible positive intervals. Empty arrays produce `null`/N-D and a failed/inconclusive trial, never `p95 = 0` pass. Summary and raw data must agree exactly. Retain visibility/focus state over the whole measured period; keep unknown or unsupported conditions honest. Bring the actual page to foreground normally if needed, and retain any unsupported trial.
- **FR-041E**: Raw data arrays for rAF intervals, action dispatches, API timing/failures, and board-DOM observations are mandatory. Missing measurements must be represented as `null`/N-D with a reason, never zero samples interpreted as zero FPS or passing p95.
- **FR-041F**: Each attempt MUST create a unique run directory under `frontend/tests/evidence/` with a UTC timestamp and random ID (e.g., `run_YYYYMMDD_HHMMSS_XXXXXX`). The script MUST fail or allocate a new directory if the destination already exists. It MUST NEVER overwrite old runs or delete failed evidence.
- **FR-041G**: The benchmark MUST use the actual application at its live URL with valid control selectors, ordinary left/right/down keyboard controls, and real restart after game over. Action timeouts and API failures (including trials with no activity) must be retained. It must not attribute arbitrary DOM changes to actions without an explicit matching rule; unknown causality must be labeled honestly. It must record request URL, method, game identity, and common clock mapping.
- **FR-041H**: The benchmark MUST preserve actual inherited manual-down collision behavior and the recorded strict common S3API08 mismatch. It must not force down-collision locking, relax thresholds, modify the common seed, or replace failed strict acceptance data.
- **FR-042**: The operational targets for the benchmark are a mean frame scheduling rate of >=55 FPS and a p95 frame interval of <=25 ms in every run, functioning as tolerance targets around a 60 Hz baseline. This is a tolerance window, not a physical display presentation guarantee. Failed targets or unsupported environments must be reported honestly. No new performance thresholds, gravity changes, or permanent application animation loops may be added to inflate the metrics.
- **FR-043**: The benchmark MUST NOT alter game gravity, inject permanent animation loops solely to inflate metrics, rotate pieces, migrate the DOM to Canvas/WebGL, or issue high-frequency API polling (e.g. 60 requests per second).
- **FR-044**: Benchmarking tests MUST run separately from standard unit CI, using a distinct manual command or dedicated test task.

#### Continuous Integration Requirements
- **FR-045**: The project MUST provide a GitHub Actions workflow file that validates backend tests (with coverage), frontend unit tests, production building, and Docker image builds.
- **FR-046**: The workflow MUST pin Python and Node major versions, and execute reproducible dependency installation using lockfiles.
- **FR-047**: The CI workflow MUST NOT require any repository-wide private secrets.
- **FR-048**: The workflow MUST include automated basic dependency security audits (e.g., audit commands) and report their findings.
- **FR-048B (S3-CI-01)**: The CI workflow MUST run `pip-audit` cleanly without suppressing GHSA-vv3r-rc64-8847 or any other vulnerabilities, keeping the real failure behavior and unweakened security policies.
- **FR-048C (S3-CI-02)**: The project MUST define reproducible, fully-pinned Python runtime and development/audit installation requirements suitable for Python 3.11, using exact verified installed versions from the existing production container as a runtime reference to guarantee a minimal, non-root production image.

### Key Entities

#### 1. HighScore Record
Represents a completed game's final performance state recorded in the SQLite database.
- `game_id` (TEXT, UUID string): The primary key. Uniquely identifies the authoritative game.
- `score` (INTEGER): The final accumulated score (>= 0).
- `total_lines` (INTEGER): The total horizontal lines cleared (>= 0).
- `level` (INTEGER): The final level reached (>= 1).
- `completed_at` (TEXT, ISO-8601 UTC format): The date and time when the game reached game over (e.g. `2026-10-29T14:30:22Z`).

#### 2. Leaderboard
A calculated collection of up to 10 HighScore records, returned as a read-only list.
- `scores`: Array of HighScore records sorted descending by `score`, then ascending by `completed_at`, then lexicographically ascending by `game_id`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: **Persistence Integrity**: 100% of games reaching game over are successfully written to SQLite, surviving complete backend, process, and container restarts.
- **SC-002**: **No Cheat Vulnerability**: 100% of API requests containing extra fields or manual client-supplied score parameters are rejected with a 4xx error.
- **SC-003**: **Controlled Error States**: Database locks, missing files, or query exceptions trigger a controlled 503 response, hiding internal file system paths, SQL queries, or stack traces from the JSON response.
- **SC-004**: **UI Frame Scheduling Rate**: In a local foreground Playwright performance test, the mean frame scheduling rate is >=55 FPS and the p95 frame interval is <=25 ms in every run.
- **SC-005**: **Isolated Port Exposed**: Only port 5183 is mapped and open on the host machine. Port 8000 (backend API) is completely closed to the host interfaces and only accessible via internal Docker networking.
- **SC-006**: **Zero-Secret CI**: The GitHub Actions workflow file defines a secret-free, locally reproducible pipeline for dependency audits, unit testing, production building, and Docker image builds. Since no commit or repository push is authorized during this phase, any hosted run is reported as not executed.

## Assumptions

- **Single-Process Backend**: The backend operates as a single-process service. Multi-worker synchronization or clustered database locking is out of scope since the game session is stored in memory.
- **Local SQLite DB**: The SQLite database runs in-process as a file, and no external DB engine (e.g. PostgreSQL) is needed.
- **CORS Config**: The CORS policy can be configured via an environment variable `TETRIS_CORS_ALLOWED_ORIGINS` which contains a list of authorized origin strings, defaulting to safe origins and disabling credentials when wildcard is configured.
- **No Player Authentication**: No user registration, authentication, login sessions, or player name entry is required. High scores are recorded purely by game UUIDs.
- **Environment**: Playwright benchmarking requires a local environment with a physical or virtual display (Xvfb) and Chromium to run in foreground mode. If run in a headless Docker CI runner, it may report unsupported features gracefully.
