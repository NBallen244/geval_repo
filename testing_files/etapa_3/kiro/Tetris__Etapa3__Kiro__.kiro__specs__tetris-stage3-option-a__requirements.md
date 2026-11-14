# Requirements Document

## Introduction

This document defines the functional scope for Stage 3, Option A, of a browser-based Tetris study. It is a brownfield extension of this tool's own final Stage 2, Option A implementation (the `backend/` FastAPI service and `frontend/` React + TypeScript client in this workspace), whose native specification lives under `.kiro/specs/tetris-stage2-option-a/`, which in turn extended Stage 1 under `.kiro/specs/tetris-stage1-option-a/`. All Stage 1 and Stage 2 behavior and contracts are the baseline and must be preserved; Stage 3 only adds the features described below.

Stage 3 adds **persistent high scores** backed by SQLite (Python standard-library `sqlite3`), a **leaderboard endpoint** and a **frontend High Scores panel**, **Docker packaging** for local deployment, a **browser performance benchmark** harness, and **continuous-integration** workflows. The backend remains the single authoritative owner of all game state and rules; the frontend renders backend state and forwards controls.

Stage 3 intentionally **supersedes two specific Stage 2 exclusions** rather than rewriting Stage 2 history: Stage 2 excluded "no persistence / no database" and deployment. Stage 3 deliberately **adds SQLite persistence of completed-game high scores** and **Docker-based local deployment**. The Stage 2 specification documents remain accurate as a record of Stage 2 scope; they are not edited. Every other Stage 2 exclusion is retained (see Exclusions below).

Live game state continues to exist in memory only for the lifetime of the backend process. Stage 3 does **not** make games saved or resumable: only the summary record of a completed game is persisted. High scores survive a backend process restart and a container restart; active in-memory games do not survive a restart and are not resumed.

The inherited specifications under `.kiro/specs/tetris-stage1-option-a/` and `.kiro/specs/tetris-stage2-option-a/` must be preserved byte-for-byte and must not be edited by this stage. This document describes WHAT must hold; it does not claim that any build, test, audit, container run, CI run, or performance measurement has been executed, and it does not assert any approval, metric, screenshot, token, cost, or result.

### Relationship to Stage 2 (preserved baseline)

The following Stage 1 and Stage 2 facts are inputs and must not be changed by Stage 3. They are reproduced here so Stage 3 acceptance criteria can reference them precisely.

- **Backend / frontend stack:** a Python FastAPI backend and a React + TypeScript frontend. The backend holds authoritative in-memory game state; the frontend renders backend state and forwards controls.
- **Board:** 20 rows by 10 columns, rendered as a React DOM grid. Row `0` is the top, row `19` is the bottom; column `0` is leftmost, column `9` is rightmost.
- **Pieces:** the seven standard tetrominoes `I`, `O`, `T`, `S`, `Z`, `J`, `L` in their initial (unrotated) orientation only.
- **Spawn origin:** `(row 0, column 3)` in the initial orientation.
- **Piece generator:** a seeded deterministic shuffled 7-bag; the same seed produces the same type sequence; exactly one preview piece is exposed.
- **Board serialization:** JSON board is a 20x10 array of integer codes, `0` = empty and `1..7` = settled block type codes (`I=1, O=2, T=3, S=4, Z=5, J=6, L=7`).
- **Active piece key:** the active piece is exposed under the key `active_piece` with `type`, `origin`, and `cells`.
- **Endpoints:** `POST /api/games`, `GET /api/games/{id}`, `POST /api/games/{id}/tick`, `POST /api/games/{id}/move`, and `POST /api/games/{id}/hold` keep their existing request/response compatibility. `POST /api/games` returns HTTP 200 (not 201).
- **Status values:** `playing` and `game_over`.
- **Lock / clear / spawn ordering:** on a lock, the active piece settles into the board, completed lines are cleared, scoring/leveling/gravity are applied using the pre-lock level, and only then is the next piece spawned.
- **Stage 2 state fields:** every state response includes `score`, `total_lines`, `level`, `gravity_interval_ms`, `next_piece`, `hold_piece`, and `can_hold` in addition to `id`, `status`, `board`, and `active_piece`. Scoring (`100/300/500/800 * pre_lock_level`), cumulative line count, level (`1 + floor(total_lines / 10)`), progressive gravity (`max(100, 500 - 50 * (level - 1))`), one-piece Hold with once-per-active-piece availability, and the one-piece next preview are all preserved.
- **Controls and restart:** left, right, and soft drop; collision; locking; line clearing; game over; Hold via button and `C`/`c` key; and restart by creating a new game are preserved. Soft drop grants no points.
- **Frontend lifecycle safety:** the Stage 2 frontend request-ordering and lifecycle guarantees are preserved, including generation tokens, per-generation FIFO serialization of mutating requests, the coalesced per-generation automatic-tick scheduler, dynamic gravity scheduling from `gravity_interval_ms`, stale-response discarding after both `fetch` and `response.json()` resolve, exact timeout cancellation and rescheduling, React StrictMode safety, and the R1 through R5 request-ordering / timeout-reconciliation protections.
- **Regression tests:** all inherited Stage 1 and Stage 2 backend and frontend regression tests must continue to pass unchanged, including the detailed Stage 2 frontend request-ordering / lifecycle tests.
- **Dependency pinning:** backend dependencies are pinned in `backend/requirements.txt` (and dev tooling in `backend/requirements-dev.txt`); frontend dependencies are pinned in `frontend/package.json`. Note that the inherited `backend/requirements.txt` currently mixes runtime packages (`fastapi`, `uvicorn`, `pydantic`) with test/dev packages (`pytest`, `httpx`), and `backend/requirements-dev.txt` adds `pytest-cov`. Stage 3 will distinguish a production RUNTIME dependency set (`fastapi`, `uvicorn`, `pydantic` plus their resolved transitive locks) from a DEV/AUDIT set (`pytest`, `httpx`, `pytest-cov`, `pip-audit` plus their transitive locks), so runtime images contain no development or test dependencies. The inherited pinned versions and the inherited test assertions and behaviors are preserved by default; however, compatible, supported security updates ARE permitted and ARE REQUIRED where an actual audit finding justifies them, provided the inherited behaviors and the inherited test assertions remain satisfied after the upgrade. Audit findings MUST be remediated by upgrading to a compatible, supported version, NOT by ignore lists, suppression, floating or unpinned runtime transitives, or arbitrary version overrides. Existing frontend pins passed baseline npm audit and are preserved unless an actual compatibility or security finding justifies a change. Dependencies remain reproducible and security-fixed with explicit major versions; audit findings are not suppressed and production files are not excluded from coverage.

## Glossary

- **Backend / System:** the authoritative FastAPI service that owns all game state and rules and now owns high-score persistence.
- **Frontend:** the React + TypeScript client that renders backend state and forwards controls.
- **High_Score_Store:** the Stage 3 persistence component that reads and writes completed-game records in a SQLite database using the Python standard-library `sqlite3` module.
- **High_Score_Record:** a persisted summary of one completed game, with exactly the fields `game_id`, `score`, `total_lines`, `level`, and `completed_at`.
- **Completed game:** a game whose authoritative backend status has reached `game_over`.
- **Finalization:** the act of persisting the already-captured `High_Score_Record` for a completed game, performed at most once per `game_id`; finalization writes the previously captured record and does not create the `completed_at` timestamp at write or success time.
- **completed_at:** the UTC completion timestamp in ISO-8601 format, assigned once at the first terminal transition (terminal time) and captured into an immutable finalization record before the storage write, never changed by any later retry or action.
- **Leaderboard:** the ordered set of up to ten `High_Score_Record` entries returned by the `GET /api/high-scores` endpoint.
- **TETRIS_DB_PATH:** the environment variable that configures the SQLite database file path, defaulting to `./data/high-scores.sqlite3`.
- **Mutating request:** a request that may change authoritative game state: `POST /api/games`, `POST /api/games/{id}/tick`, `POST /api/games/{id}/move`, or `POST /api/games/{id}/hold`.
- **Read request:** a request that must not change authoritative game state or create records: `GET /api/games/{id}` and `GET /api/high-scores`.
- **Benchmark_Harness:** the Playwright-driven performance measurement tool that drives the production frontend in a real Chromium browser.
- **Frame interval:** the elapsed wall-clock time between two consecutive browser animation frames, in milliseconds.
- **Single in-memory game worker:** the Stage 3 constraint that exactly one backend process (one worker) owns in-memory games; multiple-worker support for in-memory games is not claimed.

## Requirements

### Requirement 1: SQLite high-score store initialization

**User Story:** As an operator, I want the high-score database initialized safely on startup, so that persistence works without manual setup.

#### Acceptance Criteria

1. WHEN the backend starts THEN the High_Score_Store SHALL resolve its database file path from the `TETRIS_DB_PATH` environment variable.
2. IF `TETRIS_DB_PATH` is not set THEN the High_Score_Store SHALL use the default path `./data/high-scores.sqlite3`.
3. WHEN the backend starts AND the parent directory of the resolved database path does not exist THEN the High_Score_Store SHALL create that parent directory before opening the database.
4. WHEN the backend starts THEN the High_Score_Store SHALL create the high-score schema if it does not already exist, using the Python standard-library `sqlite3` module.
5. WHEN the backend starts AND the schema already exists THEN the High_Score_Store SHALL leave existing `High_Score_Record` rows unchanged.
6. WHEN the High_Score_Store defines the schema THEN it SHALL enforce a UNIQUE constraint on `game_id` so that at most one `High_Score_Record` exists per game.
7. WHEN the High_Score_Store defines a `High_Score_Record` THEN the record SHALL contain the fields `game_id`, `score`, `total_lines`, `level`, and `completed_at`.

### Requirement 2: Persist every completed game exactly once

**User Story:** As a researcher, I want every completed game recorded exactly once, so that the leaderboard is accurate and tamper-resistant.

#### Acceptance Criteria

1. WHEN a game's authoritative backend status makes its first transition to `game_over` THEN the System SHALL finalize that game by writing exactly one `High_Score_Record` using a parameterized write that is all-or-nothing, so that no partial `High_Score_Record` persists if the write fails.
2. WHEN a game reaches `game_over` with a `score` of `0` THEN the System SHALL still finalize that game as a `High_Score_Record`.
3. WHEN finalization writes a `High_Score_Record` THEN the record SHALL store the game's `game_id`, a `score` that is a non-negative integer, a `total_lines` that is a non-negative integer, a `level` that is a positive integer greater than or equal to `1`, and a `completed_at` that is a UTC ISO-8601 timestamp string.
4. WHEN a game reaches `game_over` because of a gravity tick, a soft drop, or an obstructed Hold at the spawn origin THEN the System SHALL apply the same finalization rules as any other game-over cause.
5. IF a `High_Score_Record` already exists for a `game_id` THEN the System SHALL NOT create a second record for that `game_id` and SHALL NOT overwrite the existing record's `score`, `total_lines`, `level`, or `completed_at`.
6. WHEN a game makes its first transition to `game_over` THEN the System SHALL set the `completed_at` timestamp once at that first terminal transition (terminal time), capture it into an immutable finalization record before the storage write, and SHALL NOT change it on any later retry or action.
7. WHILE a game is still `playing` THEN the System SHALL NOT create a `High_Score_Record` for that game.
8. WHEN a client restarts by creating a new game while a previous game is still `playing` THEN the System SHALL NOT create a `High_Score_Record` for the abandoned previous game.
9. IF a finalization write fails for a reason other than the `game_id` UNIQUE-constraint duplicate THEN the System SHALL NOT persist a partial `High_Score_Record`, SHALL retain the game's `game_over` state so that a later mutating request can retry finalization, and SHALL surface the failure as defined in Requirement 7.

### Requirement 3: Finalization idempotency and read purity

**User Story:** As a researcher, I want repeated or concurrent terminal actions and reads to never duplicate or mutate records, so that results stay trustworthy.

#### Acceptance Criteria

1. WHEN repeated mutating requests are sent to a game that is already `game_over` THEN the System SHALL keep exactly one `High_Score_Record` for that `game_id` with its original `score`, `total_lines`, `level`, and `completed_at`.
2. WHEN two finalization attempts for the same `game_id` occur within the supported single-process backend THEN the System SHALL persist exactly one `High_Score_Record` and SHALL rely on the UNIQUE constraint to reject the duplicate.
3. WHEN a `GET /api/games/{id}` read is served THEN the System SHALL NOT change any authoritative game state and SHALL NOT create or modify a `High_Score_Record`.
4. WHEN a `GET /api/high-scores` read is served THEN the System SHALL NOT change any authoritative game state and SHALL NOT create or modify a `High_Score_Record`.
5. WHILE the backend runs as a single in-memory game worker THEN the System SHALL protect game-state mutation and finalization from races between concurrent requests to the same game.

### Requirement 4: Persistence durability and process model

**User Story:** As an operator, I want high scores to survive restarts while live games do not resume, so that the persistence boundary is explicit.

#### Acceptance Criteria

1. WHEN the backend process restarts THEN the System SHALL retain all previously persisted `High_Score_Record` rows readable from the same database file.
2. WHEN the backend container restarts AND the database file is on a persistent volume THEN the System SHALL retain all previously persisted `High_Score_Record` rows.
3. WHEN the backend process restarts THEN the System SHALL NOT resume or restore any previously active in-memory game.
4. WHEN a new backend process or store instance opens an existing database file THEN the System SHALL read the previously persisted `High_Score_Record` rows without reinitializing or clearing them.
5. WHEN documenting the process model THEN the System SHALL describe exactly one in-memory game worker and SHALL NOT claim multiple-worker support for in-memory games.

### Requirement 5: Leaderboard endpoint

**User Story:** As a player, I want to see the top ten high scores, so that I can compare results.

#### Acceptance Criteria

1. WHEN a client sends `GET /api/high-scores` THEN the System SHALL respond with an object containing a `scores` array.
2. WHEN the System returns the `scores` array THEN the array SHALL contain at most ten `High_Score_Record` entries.
3. WHEN the System orders the `scores` array THEN it SHALL order entries by `score` descending, then by `completed_at` ascending, then by `game_id` ascending.
4. WHEN the System returns a `High_Score_Record` entry THEN the entry SHALL contain exactly the fields `game_id`, `score`, `total_lines`, `level`, and `completed_at`.
5. WHEN no `High_Score_Record` rows exist THEN the System SHALL respond with an object whose `scores` array is empty.

### Requirement 6: No client-supplied score injection

**User Story:** As a researcher, I want scores to be server-authoritative, so that the leaderboard cannot be forged.

#### Acceptance Criteria

1. WHEN any public endpoint is defined THEN the System SHALL NOT accept a client-supplied `score`, `total_lines`, `level`, `completed_at`, or arbitrary `game_id` as input used to insert or modify a `High_Score_Record`.
2. WHEN `POST /api/games` receives a request body containing fields beyond the documented contract THEN the System SHALL reject the request with a documented 4xx response rather than trusting the extra fields.
3. WHEN `POST /api/games/{id}/move` receives a request body containing fields beyond the documented `direction` field THEN the System SHALL reject the request with a documented 4xx response.
4. WHEN `POST /api/games` receives a valid bodyless request THEN the System SHALL continue to create a game and respond with HTTP 200.
5. WHEN `POST /api/games/{id}/move` receives a valid body with `direction` equal to `left`, `right`, or `down` THEN the System SHALL behave exactly as in Stage 2.
6. WHEN `POST /api/games/{id}/move` receives a missing or invalid `direction` THEN the System SHALL respond with a documented 4xx response (HTTP 422).
7. WHEN any game-scoped endpoint receives an unknown game id THEN the System SHALL respond with HTTP 404.

### Requirement 7: Storage error handling and safe retry

**User Story:** As a player, I want storage failures handled cleanly, so that the app degrades gracefully and never leaks internals.

#### Acceptance Criteria

1. IF a storage failure occurs while serving `GET /api/high-scores` THEN the System SHALL respond with HTTP 503.
2. IF a storage failure occurs during finalization triggered by a mutating request THEN the System SHALL respond with HTTP 503.
3. WHEN the System returns a 503 storage-failure response THEN the response SHALL use a JSON content type (`application/json`) and SHALL contain a valid JSON body.
4. WHEN the System returns a 503 storage-failure response THEN the JSON body SHALL contain a human-readable message that indicates a storage failure.
5. WHEN the System returns a 503 storage-failure response THEN the body SHALL NOT include a filesystem path, SQL text, an exception or class name, or a stack trace.
6. IF finalization fails after a game reaches `game_over` THEN the System SHALL mark that game as pending finalization while preserving the terminal `game_over` state, keeping the game's `board`, `score`, `level`, `total_lines`, and active piece unchanged.
7. WHEN a subsequent mutating request is sent to a terminal game that is pending finalization THEN the System SHALL retry the finalization write.
8. WHEN a retry of finalization succeeds THEN the System SHALL persist exactly one `High_Score_Record` for that `game_id` with the single `completed_at` timestamp captured once at the first terminal transition (terminal time) and unchanged by later retries, regardless of how many retries preceded the success, and SHALL clear the pending-finalization marker.
9. WHEN a `GET` request is served for a terminal game that is pending finalization THEN the System SHALL return the current terminal game state, SHALL NOT perform the finalization retry, and SHALL NOT change the pending-finalization status.

### Requirement 8: Frontend High Scores panel

**User Story:** As a player, I want a High Scores panel in the UI, so that I can view the leaderboard.

#### Acceptance Criteria

1. WHEN the Frontend renders THEN it SHALL display a High Scores panel showing each entry's `score`, `total_lines`, and `level`.
2. WHILE the leaderboard request is in flight THEN the Frontend SHALL display a loading state.
3. WHEN the leaderboard response contains an empty `scores` array THEN the Frontend SHALL display an empty state.
4. IF the leaderboard request fails THEN the Frontend SHALL display an error state without crashing the page.
5. WHEN the Frontend performs the initial load THEN it SHALL fetch the leaderboard once.
6. WHEN a game transitions to `game_over` THEN the Frontend SHALL fetch the leaderboard.
7. WHEN automatic gravity ticks occur THEN the Frontend SHALL NOT fetch the leaderboard on every tick.
8. WHEN a restart is requested (creating a new game) THEN the Frontend SHALL synchronously invalidate the current leaderboard request generation so that a delayed `fetch` AND a delayed `response.json()` from before the restart, whether they resolve as success, error, or in a `finally` block, SHALL NOT commit to the panel after the restart.
9. WHEN a restart is requested THEN the Frontend SHALL refresh or retain the appropriate current leaderboard state without mutating the game FIFO queue, timers, or the per-generation automatic-tick scheduler.
10. WHEN a game-over refresh is fired WHILE the initial leaderboard read is still pending THEN the Frontend SHALL NOT drop the game-over refresh; the newer request SHALL be the one allowed to commit.
11. WHEN the Frontend renders any High Scores label, status, or message THEN the visible text SHALL be in English.

### Requirement 9: Preserved frontend controls and lifecycle safety

**User Story:** As a player, I want Stage 2 controls and safety to keep working, so that adding the panel does not regress gameplay.

#### Acceptance Criteria

1. WHEN the Stage 2 keyboard controls (left, right, soft drop, Hold via `C`/`c`, restart) are used THEN the Frontend SHALL behave exactly as in Stage 2.
2. WHEN `can_hold` is `false` or the game is not `playing` THEN the Frontend SHALL keep the Stage 2 Hold restrictions.
3. WHEN overlapping, out-of-order, or previous-generation responses arrive THEN the Frontend SHALL preserve the Stage 2 stale-response and generation protections, including for leaderboard fetches.
4. WHEN the leaderboard fetch is added THEN it SHALL NOT clear, block, or reschedule the per-generation automatic-tick scheduler or the manual FIFO queue of the current game generation.

### Requirement 10: Configurable API base and CORS policy

**User Story:** As an operator, I want configurable API wiring and restrictive CORS, so that dev and Docker both work securely.

#### Acceptance Criteria

1. WHEN the Frontend issues API requests THEN it SHALL use a configurable API base whose default is the same-origin path prefix `/api`.
2. WHEN the Frontend is built for production THEN it SHALL NOT use a hardcoded `localhost` API base.
3. WHEN the backend defines its CORS policy THEN the policy SHALL be restrictive and configurable.
4. WHEN the backend CORS policy allows credentials THEN it SHALL NOT also use a wildcard (`*`) allowed origin.
5. WHEN the resolved CORS allow-list contains a wildcard (`*`) entry, including a mixed list that combines `*` with concrete origins, AND credentials are enabled THEN the System SHALL reject that configuration at resolution time with a configuration error (fail closed) rather than returning `*` to the CORS middleware, so no credentialed response is ever granted to an arbitrary origin.
6. WHEN the resolved CORS allow-list contains only concrete explicit origins THEN the System SHALL use that explicit allow-list with credentials enabled, preserving valid configurations.
7. WHEN `TETRIS_ALLOWED_ORIGINS` is unset or empty THEN the System SHALL use the restrictive local-development default allow-list and SHALL NOT grant a wildcard origin.
8. WHEN Stage 3 is implemented THEN the System SHALL NOT add authentication and SHALL NOT collect player names.

### Requirement 11: Docker images and compose

**User Story:** As an operator, I want containerized backend and frontend, so that I can run the app locally in a reproducible way.

#### Acceptance Criteria

1. WHEN Stage 3 provides container images THEN it SHALL provide separate backend and frontend images, using multi-stage Dockerfiles where a build stage differs from the runtime stage.
2. WHEN Stage 3 provides container build context THEN it SHALL include a `.dockerignore` that excludes files not needed in the images.
3. WHEN Stage 3 provides a local runner THEN it SHALL provide a Docker Compose configuration that starts the backend and frontend together.
4. WHEN the frontend container runs THEN it SHALL serve the production frontend build and proxy requests under `/api` to the backend container.
5. WHEN the containers run THEN the backend and frontend SHALL each run as a non-root user, and the two containers SHALL use distinct non-root users.
6. WHEN the Compose stack publishes ports THEN it SHALL publish only the frontend on host port `5183` and SHALL keep the backend reachable only inside the internal container network.

### Requirement 12: Container persistence, health, and hygiene

**User Story:** As an operator, I want durable storage and clean runtime images, so that data survives and images stay minimal.

#### Acceptance Criteria

1. WHEN the Compose stack runs THEN it SHALL mount a named volume with write permissions for the backend SQLite directory.
2. WHEN the backend container runs THEN its SQLite database path SHALL be configurable via `TETRIS_DB_PATH`.
3. WHEN the Compose stack runs THEN the backend and frontend services SHALL each define a health check.
4. WHEN the backend container runs THEN it SHALL run exactly one backend worker.
5. WHEN runtime images are built THEN they SHALL NOT contain baked-in credentials and SHALL NOT include development-only dependencies.
6. WHEN Stage 3 documents containers THEN it SHALL document the exact commands to build the images, start the stack, stop the stack, and verify persistence across a container restart.
7. WHERE Docker is available THEN Stage 3 SHALL measure actual image sizes and build time and report the measured values, without inventing an optimization percentage or an arbitrary size limit.
8. WHERE Docker is not available THEN Stage 3 SHALL report that the image-size and build-time measurement could not be executed, without fabricating values.

### Requirement 13: Performance benchmark scenario and controls

**User Story:** As a researcher, I want a rigorous browser benchmark, so that rendering performance claims are evidence-based.

#### Acceptance Criteria

1. WHEN the Benchmark_Harness runs THEN it SHALL drive the production Frontend in a real Chromium browser via Playwright.
2. WHEN the Benchmark_Harness measures performance THEN it SHALL separately record browser frame scheduling, actual game DOM updates, and API timing, and SHALL NOT treat `requestAnimationFrame` frequency alone as proof of rendering throughput.
3. WHEN the Benchmark_Harness records evidence THEN it SHALL retain raw frame intervals, DOM mutation / update counts, action-to-visible-update samples, and a browser performance trace that includes real screenshot frames (PNG images or screenshot-bearing traces).
4. WHEN the Benchmark_Harness runs the scenario THEN it SHALL use a visible foreground Chromium window at 1280x900 with device scale factor 1, a recorded 60 Hz target, a 5-second warm-up, and exactly three independent measured runs of 30 seconds each.
5. WHEN the Benchmark_Harness runs THEN it SHALL capture geometry evidence proving the full 10x20 board stays visible and evidence that the page has input focus.
6. WHEN the Benchmark_Harness runs THEN it SHALL exercise actual left, right, and soft-drop movements and restart as needed to keep gameplay active.
7. WHEN the Benchmark_Harness computes a board signature THEN the signature SHALL encode the complete, unambiguous state of all 200 cells including the actual displayed active and settled state, and SHALL NOT truncate per-cell style in a way that collapses distinct colors or states to a constant value.
8. WHEN the Benchmark_Harness installs its board observer THEN it SHALL wait for document readiness and for the full 10x20 board to exist before observing it and before warm-up, and SHALL NOT observe a not-yet-existing body; this readiness wait SHALL NOT change gameplay.
9. WHEN the Benchmark_Harness launches the browser THEN it SHALL explicitly enable the Chromium sandbox (`chromiumSandbox: true`) and SHALL support a documented `PERF_BROWSER_CHANNEL` (for example `chrome`) so a host-installed stable Chrome can be used; it SHALL record the actual browser, browser version, channel, and the Playwright version, and SHALL NOT claim sandbox or foreground state from a hard-coded constant.

### Requirement 14: Performance benchmark reporting and targets

**User Story:** As a researcher, I want honest, well-scoped performance metrics, so that targets are interpreted correctly.

#### Acceptance Criteria

1. WHEN the Benchmark_Harness reports results THEN it SHALL record the browser, runtime, operating system, hardware, display configuration, headless-versus-foreground mode, and the scenario parameters.
2. WHEN the Benchmark_Harness reports frame metrics THEN it SHALL record the frame-interval median, p95, and p99, an approximate FPS, the count of intervals above `33.34` ms, and action latency.
3. WHEN all three measured runs complete THEN the operational target SHALL be a mean frame-scheduling rate of at least `55` FPS and a p95 frame interval of at most `25` ms in every run.
4. WHEN the Benchmark_Harness states the target THEN it SHALL explain that the target is a tolerance around a 60 Hz target and not a guarantee of physical display presentation.
5. WHEN the Benchmark_Harness records results THEN it SHALL record browser frame scheduling separately from game DOM throughput and separately from physical display presentation.
6. IF the environment is unsupported or a target is not met THEN the Benchmark_Harness SHALL report that outcome honestly rather than fabricating a passing result.
7. WHEN the Benchmark_Harness defines a measured run THEN it SHALL use a fixed page-clock window of exactly `end = start + 30000` ms measured on the page performance clock, SHALL retain raw and previous-frame timestamps, and SHALL select a frame interval only when BOTH of its endpoints fall inside that fixed window, with boundary and warm-up samples explicitly excluded; the action, focus, geometry, DOM, and API summaries SHALL use that same measured window and SHALL NOT aggregate warm-up activity.
8. WHEN the Benchmark_Harness associates an action with a visible update THEN it SHALL await the relevant authoritative response and an actual visible board-signature transition before completing the action, SHALL retain action identifiers, before/after game state and signatures, action/request/response association, and page-clock dispatch/update timestamps, and SHALL NOT treat the first arbitrary later mutation as causal proof; ambiguous, unchanged, censored, or out-of-window samples SHALL be excluded from latency statistics AND reported with a reason, and delayed or overlapping gravity updates SHALL be guarded.
9. WHEN the Benchmark_Harness records API timing THEN it SHALL treat Resource Timing as the same page performance clock (not an independent clock) and label it honestly as a separate measurement stream on that clock, OR add a separately identified Node request-to-response timing stream without subtracting timestamps across clock domains.
10. WHEN the Benchmark_Harness evaluates a run THEN it SHALL separate numerical scheduling targets (mean FPS, p95 interval) from measurement-validity qualification, and a run with no DOM evidence, lost input focus, a clipped or incomplete 20x10 board, empty samples, or an absent screenshot-bearing trace SHALL fail qualification honestly rather than passing on numeric targets alone.
11. WHEN the Benchmark_Harness records the environment THEN it SHALL record the actual browser, Playwright version, Node version, OS, CPU, and RAM, plus available GPU and display configuration, and SHALL leave unobservable physical display presentation as unknown rather than claimed.

### Requirement 15: Performance benchmark integrity and isolation

**User Story:** As a researcher, I want the benchmark to measure the real game without distorting it, so that results are valid.

#### Acceptance Criteria

1. WHEN the Benchmark_Harness runs THEN it SHALL NOT change game gravity to influence the metric.
2. WHEN the Benchmark_Harness runs THEN it SHALL NOT add a permanent animation loop whose sole purpose is to inflate the frame-rate metric.
3. WHEN the Benchmark_Harness runs THEN it SHALL NOT rotate pieces and SHALL NOT migrate the board rendering from React DOM to Canvas or WebGL.
4. WHEN the Benchmark_Harness runs THEN it SHALL NOT issue sixty API requests per second.
5. WHEN timing-sensitive performance checks are run THEN they SHALL be run separately from ordinary unit CI, as an explicit performance job or a documented manual command.
6. WHEN a benchmark run fails or raises THEN the Benchmark_Harness SHALL preserve partial raw datasets, failure metadata, and exception details in a `finally` block rather than exiting with console output only, SHALL close only the browser and context it owns, SHALL stop the sampler after capture, and SHALL leave no orphaned child processes.

### Requirement 16: Continuous integration

**User Story:** As a maintainer, I want CI to build and test the project, so that regressions are caught reproducibly.

#### Acceptance Criteria

1. WHEN the CI workflow runs THEN it SHALL run the backend tests with coverage, the frontend tests, the frontend production build, and the Docker image builds.
2. WHEN the CI workflow defines runtimes THEN it SHALL pin the Python major version and the Node major version.
3. WHEN the CI workflow installs dependencies THEN it SHALL document reproducible installation and SHALL preserve or update the dependency lockfiles coherently, installing from complete resolved locks that pin every transitive dependency (not only the four direct runtime packages and four direct dev tools), with clean runtime-versus-dev separation and valid platform markers where needed; the production RUNTIME lock SHALL be the set installed in the runtime Docker image, and the DEV lock SHALL be the set installed for local and CI tests and audits.
4. WHEN the CI workflow runs THEN it SHALL NOT require private secrets to perform the backend, frontend, build, and image checks.
5. WHEN the CI workflow runs THEN it SHALL include basic dependency audit commands and SHALL report the actual findings without suppression.
6. WHEN CI is described THEN the System SHALL treat a local workflow file as a configuration artifact only and SHALL NOT claim it is evidence of a hosted Actions run.
7. WHEN CI is organized THEN it SHALL separate ordinary unit, build, and image checks from the manual timing-sensitive performance checks.

### Requirement 17: Testing coverage for persistence and contracts

**User Story:** As a researcher, I want tests that cover the hard cases, so that persistence and contracts are trustworthy.

#### Acceptance Criteria

1. WHEN Stage 3 tests are authored THEN they SHALL cover storage failure and recovery, including the 503 contract and the safe finalization retry on a later mutating request.
2. WHEN Stage 3 tests are authored THEN they SHALL cover leaderboard tie-breaking across equal `score` values using `completed_at` ascending then `game_id` ascending.
3. WHEN Stage 3 tests are authored THEN they SHALL cover concurrent finalization attempts for the same `game_id` resolving to exactly one `High_Score_Record`.
4. WHEN Stage 3 tests are authored THEN they SHALL cover idempotency of repeated terminal mutating actions producing no duplicate record and no changed `completed_at`.
5. WHEN Stage 3 tests are authored THEN they SHALL cover injection-like inputs (for example extra body fields and arbitrary `game_id` or score metadata) being rejected or ignored for persistence.
6. WHEN Stage 3 tests are authored THEN they SHALL cover persistence surviving a new application or store instance opening the same database file.
7. WHEN Stage 3 tests verify three-row and four-row clears THEN they SHALL use explicitly synthetic fixtures that drive the real production clear-and-score path and SHALL NOT rotate pieces or invent gameplay pieces.
8. WHEN Stage 3 tests are authored THEN they SHALL assert the exact public JSON contract of `GET /api/high-scores`, the body-validation contracts of Requirement 6, and the 503 contract of Requirement 7.
9. WHEN Stage 3 tests are authored THEN they SHALL include lifecycle-safe leaderboard tests confirming reads do not mutate game state or create records and that the leaderboard fetch does not disturb the Stage 2 scheduling and FIFO guarantees.

### Requirement 18: Preserved boundaries and retained exclusions

**User Story:** As a researcher, I want scope controlled, so that Stage 3 adds only the intended features.

#### Acceptance Criteria

1. WHEN Stage 3 is implemented THEN all inherited Stage 1 and Stage 2 backend and frontend regression tests SHALL continue to pass, including the Stage 2 frontend request-ordering / lifecycle tests.
2. WHEN Stage 3 is implemented THEN rotation, wall kicks, ghost piece, T-Spins, time attack, achievements, saved or resumable games, PostgreSQL, authentication, multiplayer, global real-time leaderboards, and cloud deployment SHALL NOT be added.
3. WHEN Stage 3 is implemented THEN the inherited specifications under `.kiro/specs/tetris-stage1-option-a/` and `.kiro/specs/tetris-stage2-option-a/` SHALL remain unchanged and SHALL be preserved in their original directories.
4. WHEN Stage 3 is implemented THEN the only persisted data SHALL be completed-game `High_Score_Record` rows; live game state SHALL remain in memory only.
5. WHEN Stage 3 is implemented THEN the System SHALL NOT perform commits, pushes, container image publishing, or external deployment.
6. WHEN Stage 3 documentation reports status THEN it SHALL NOT fabricate completed approvals, checks, metrics, CI runs, tokens, costs, screenshots, Docker successes, or performance results.

### Requirement 19: Dependency security remediation and reproducible locks

**User Story:** As a maintainer, I want audit-justified dependency security fixes applied through compatible, documented, pinned upgrades, so that known advisories are remediated without regressing inherited behavior or inherited test assertions.

#### Acceptance Criteria

1. WHERE an independent pip-audit `2.10.1` run of the inherited `backend/requirements.txt` resolved `18` packages and reported `16` raw advisory entries representing `8` UNIQUE package/version/advisory findings THEN the System SHALL treat exactly the following enumerated findings as the preserved, non-invented audit baseline: (a) `pytest` `8.3.4` — `PYSEC-2026-1845` (alias `CVE-2025-71176`), fixed in `9.0.3`; (b) `starlette` `0.41.3` — `PYSEC-2026-1941`, fixed in `0.47.2`; (c) `starlette` `0.41.3` — `PYSEC-2026-1942`, fixed in `0.49.1`; (d) `starlette` `0.41.3` — `PYSEC-2026-161`, fixed in `1.0.1`; (e) `starlette` `0.41.3` — `PYSEC-2026-2280/2281` (a single finding with two aliases), fixed in `1.1.0`; (f) `starlette` `0.41.3` — `PYSEC-2026-248`, fixed in `1.3.0`; (g) `starlette` `0.41.3` — `PYSEC-2026-249`, fixed in `1.3.1`.
2. WHEN the System records the audit baseline THEN it SHALL note that `starlette` is a transitive dependency of `fastapi` and is not pinned directly in `backend/requirements.txt`, and that `pytest-cov` is added to the dev set via `-r requirements.txt` in `backend/requirements-dev.txt`.
3. WHEN the System records the audit baseline THEN it SHALL preserve the exact finding identifiers and aliases listed in acceptance criterion `1`, SHALL NOT invent additional advisories, and SHALL NOT treat duplicate raw advisory entries as distinct defects.
4. WHEN Stage 3 remediates the audit findings THEN the System SHALL select a compatible, supported production RUNTIME set covering FastAPI, Starlette, Pydantic, and Uvicorn, and a compatible, supported DEV/TEST/AUDIT set covering pytest, httpx, pytest-cov, and pip-audit.
5. WHEN Stage 3 selects the remediation versions THEN the System SHALL document the EXACT selected versions and the resolved lock strategy in the Stage 3 design document BEFORE changing any dependency manifest or lockfile and BEFORE installing the selected set.
6. WHEN Stage 3 remediates the audit findings THEN the System SHALL NOT use ignore lists, SHALL NOT use suppression, SHALL NOT use floating or unpinned runtime transitives, and SHALL NOT use arbitrary version overrides, and SHALL remediate each finding by upgrading to a compatible, supported version.
7. WHEN the remediation upgrade is applied THEN the inherited Stage 1 and Stage 2 behaviors and the inherited test assertions SHALL remain satisfied.
8. WHERE the existing frontend pins passed the baseline npm audit THEN the System SHALL preserve those frontend pins unless an actual compatibility or security finding justifies a change.
9. WHEN this document states the remediation scope THEN it SHALL NOT assert that any install, audit, or test has actually been executed, because this document describes WHAT must hold.
10. WHEN Stage 3 produces dependency locks THEN it SHALL produce complete resolved RUNTIME and DEV locks for Python 3.12 that pin every transitive dependency with valid platform markers where needed, SHALL retain the human-authored input manifests as inputs distinct from the resolved locks, SHALL document which files are inputs and which are resolved locks, and SHALL NOT copy another tool's lockfile or source.
11. WHEN Stage 3 reports dependency reproducibility THEN it SHALL report the actual resolved packages produced in the owned Python 3.12 environment and validated by fresh installation, `pip check`, the native tests, and BOTH runtime and dev dependency audits, rather than a blanket reproducibility claim; the frontend pins SHALL be preserved unless an actual audit or compatibility finding requires a change, and the performance harness dependency set SHALL also be audited.

### Requirement 20: Corrected benchmark measurement contract (round-06 defects)

**User Story:** As a researcher, I want the benchmark's action-association, windowing, sampler-lifecycle, failure-telemetry, and timestamp semantics corrected, so that any future measured run produces trustworthy, non-fabricated evidence.

#### Acceptance Criteria

1. WHEN the Benchmark_Harness assigns action identifiers THEN the identifiers SHALL be run-wide monotonically unique across the entire measured run and SHALL NOT reset per driving sub-call.
2. WHEN the Benchmark_Harness records an action THEN it SHALL retain the dispatch-to-update association per unique action identifier.
3. WHEN a completed action-latency sample exists for a unique action identifier THEN the Benchmark_Harness SHALL NOT overwrite that sample with a later record that reuses the same identifier.
4. WHEN the Benchmark_Harness completes an action-latency sample THEN it SHALL complete the sample only after the corresponding real successful API response AND the displayed board-state DOM transition are associated with that action.
5. WHEN a visible board change is caused by ordinary gravity rather than the dispatched action THEN the Benchmark_Harness SHALL NOT use that change to complete an action-latency sample.
6. WHEN the Benchmark_Harness records an action-latency sample THEN it SHALL preserve the raw request and response identifiers, the HTTP method, the route, the action payload, the status, the dispatch and update timestamps, the response state identity, and the DOM-signature evidence.
7. IF an action-latency sample is ambiguous, overlapping, a no-op, or timed-out THEN the Benchmark_Harness SHALL exclude that sample from latency statistics and SHALL report the exclusion with a reason rather than attributing the sample to arbitrary gravity.
8. WHERE the eligible-action subset is explicitly limited THEN the Benchmark_Harness SHALL report that limited subset with the stated reasons.
9. WHEN the Benchmark_Harness drives input THEN it SHALL issue at most four actions per second, SHALL use ordinary gravity and real keyboard controls, and SHALL NOT inject fake game responses.
10. WHEN the Benchmark_Harness records Node API round-trip time THEN it SHALL record that time on its own monotonic clock separate from the page-clock dispatch-to-DOM measurement, and SHALL NOT subtract timestamps across clocks.
11. WHEN the Benchmark_Harness drives the Frontend THEN it SHALL NOT interfere with the application's request bodies or request queues.
12. WHEN the Benchmark_Harness marks a latency sample eligible THEN it SHALL require that BOTH the dispatch timestamp AND the matched update timestamp fall inside the same fixed page-clock window `[start, start + 30000]` ms.
13. WHEN a latency sample is excluded as a boundary sample THEN the Benchmark_Harness SHALL retain that excluded sample with a reason.
14. WHEN the measured capture ends THEN the Benchmark_Harness SHALL stop and release the passive samplers for frame scheduling and for focus and geometry.
15. WHEN the measured capture ends THEN the Benchmark_Harness SHALL record the actual capture-end time separately.
16. IF the full fixed window was not observed THEN the Benchmark_Harness SHALL mark the capture as unqualified.
17. WHEN the Benchmark_Harness evaluates qualification THEN it SHALL require exactly `200` visible board cells and an adequate count of valid samples for every claimed measured stream.
18. WHEN the Benchmark_Harness computes the DOM batch count THEN the count SHALL be the number of changed-signature observer batches and SHALL NOT be a count of individual cell mutations.
19. WHEN the Benchmark_Harness records capture evidence THEN it SHALL preserve all raw timestamps and the full `200`-cell signatures.
20. IF any failure occurs during a benchmark run THEN the Benchmark_Harness SHALL fetch best-effort partial telemetry from the surviving page BEFORE closing that page.
21. IF any failure occurs during a benchmark run THEN the Benchmark_Harness SHALL always save the raw data, the exception, and the real success flags for the PNG and for the trace.
22. IF a trace-stop failure was swallowed THEN the Benchmark_Harness SHALL NOT set the trace-taken flag to true.
23. WHEN the Benchmark_Harness claims that an artifact exists THEN it SHALL verify the artifact's existence and non-zero size before making that claim.
24. WHEN the Benchmark_Harness records batch-level and per-run `startedAt` and `finishedAt` timestamps THEN it SHALL capture `startedAt` at the real start and `finishedAt` at the real finish, and SHALL NOT capture both after completion.
25. WHEN the corrected Benchmark_Harness runs THEN it SHALL preserve three independent fresh headed sandboxed Chrome or Chromium sessions at `1280x900` with device scale factor `1`, a recorded `60` Hz target, at least `5` seconds of active warm-up excluded from action latency, and fixed `30`-second measured windows.
26. WHEN the corrected Benchmark_Harness runs THEN it SHALL preserve raw `requestAnimationFrame` both-endpoint filtering, full `200`-cell changed signatures, focus and geometry samples throughout, traces WITH screenshot frames, and an actual final PNG per trial.
27. WHEN the corrected Benchmark_Harness runs THEN it SHALL support a documented `PERF_BROWSER_CHANNEL=chrome` option.
28. WHEN the corrected Benchmark_Harness evaluates a run THEN it SHALL keep the numeric targets of a mean of at least `55` FPS and a p95 frame interval of at most `25` ms separate from qualification.
29. IF a capture is invalid OR the numeric targets are not met THEN the corrected Benchmark_Harness SHALL exit with a failing status.
30. WHEN the corrected Benchmark_Harness reports physical-display presentation THEN it SHALL report that presentation as unknown rather than claimed.
31. WHEN this round reports status THEN it SHALL NOT mark final performance execution complete before real evidence exists.
32. WHEN this document states the round-06 benchmark scope THEN it SHALL NOT assert that any benchmark timing run has been executed.

### Requirement 21: Auditable action-to-visible-update association and nonempty valid-sample qualification (round-07 defects)

**User Story:** As a researcher, I want each action-latency sample bound to its own matched request and its own expected displayed board state, and qualification to require real directional samples, so that no unrelated gravity transition can masquerade as an action's visible update.

#### Acceptance Criteria

1. WHEN the Benchmark_Harness observes API requests and responses THEN it SHALL observe them PASSIVELY via Playwright network events, and SHALL NOT consume, clone, or alter the application's fetch response body, request bodies, or request queues.
2. WHEN the Benchmark_Harness dispatches an action THEN it SHALL assign a unique per-run request identifier and SHALL retain that request's HTTP method, URL, direction payload, response status, and the successful response JSON state identity.
3. WHEN the Benchmark_Harness observes an API request THEN it SHALL record Node-side monotonic request-to-body-end timestamps for that request on the Node clock only.
4. WHEN the Benchmark_Harness matches a dispatched action to a request THEN it SHALL select the single NEW `/move` request whose direction matches the dispatched key and whose lifecycle begins after the action is dispatched.
5. IF no candidate request, more than one candidate request, an overlapping candidate, or a failed, no-op, or timed-out response is found THEN the Benchmark_Harness SHALL exclude that action, SHALL report the exclusion reason, and SHALL NOT attribute the action to an arbitrary later gravity update.
6. WHEN the Benchmark_Harness computes the expected displayed board signature for a matched action THEN it SHALL compute the full 200-cell signature from the matched response's `board` plus `active_piece`, using the same overlay and per-cell color mapping the production Board component applies, so the expected signature matches the DOM signature format exactly.
7. WHEN the Benchmark_Harness completes an action THEN it SHALL complete the action only when the observed DOM board signature equals that specific expected 200-cell signature, and SHALL NOT complete the action merely because the signature differs from the pre-dispatch signature.
8. IF a displayed board state is coalesced and never actually observed in the DOM THEN the Benchmark_Harness SHALL exclude that state and SHALL NOT assign it an arbitrary later gravity transition.
9. WHEN the Benchmark_Harness completes an action THEN it SHALL retain the matched request identifier, the expected signature, the observed signature, and the page-clock dispatch and observed-update timestamps.
10. WHEN the Benchmark_Harness records timing THEN it SHALL keep API round-trip time entirely on the Node monotonic clock and the dispatch-to-observed-DOM latency entirely on the page clock, and SHALL NOT subtract timestamps across the two clocks.
11. WHEN the Benchmark_Harness reports latency THEN it SHALL document observer and polling overhead and SHALL state that the measured latency is not input-to-photon or physical display presentation latency.
12. WHEN a run is evaluated as qualified THEN the Benchmark_Harness SHALL require a nonempty set of valid action-latency samples for that run.
13. WHEN a run is evaluated as qualified THEN the Benchmark_Harness SHALL require that the valid action-latency samples cover actual left, right, and soft-drop actions.
14. WHEN the Benchmark_Harness reports action samples THEN it SHALL report every excluded action sample together with its exclusion reason.
15. WHEN the Benchmark_Harness evaluates whether the fixed 30-second window was observed THEN it SHALL require `captureEndAt` to be greater than or equal to `windowEnd` strictly with no earlier-stop tolerance, and SHALL retain any actual late stop separately.
16. WHEN the Benchmark_Harness runs THEN it SHALL preserve every already-correct round-04 and round-06 control: three fresh headed sandboxed sessions, `1280x900` at device scale factor `1`, a recorded `60` Hz target, at least `5` seconds of warm-up excluded from latency, fixed `30`-second windows, `requestAnimationFrame` both-endpoint filtering, full `200`-cell signatures and changed-batch counts, focus and full-board geometry throughout, a screenshot-bearing trace plus a final PNG, truthful failure partials and timestamps, Chrome channel support, at most four keyboard actions per second, unchanged gravity, real application responses, and numeric targets kept separate from qualification.
17. IF a specific edge case is genuinely ambiguous THEN the Benchmark_Harness SHALL exclude it, SHALL explain it, and SHALL NOT overclaim causality.
18. WHERE only a subset of action samples is well-associated THEN the Benchmark_Harness SHALL be permitted to report only that well-associated subset of action samples.
19. WHEN this round reports status THEN it SHALL NOT mark final performance execution complete, and SHALL NOT assert that any benchmark timing run was executed this round, because manual measured execution remains pending.

## Material Ambiguities and Assumptions

These are recorded for transparency.

1. **Superseded exclusions are additive, not retroactive.** Stage 3 adds SQLite persistence and Docker deployment. It does not edit or invalidate the Stage 2 specification documents, which remain an accurate record of Stage 2 scope.
2. **Persistence boundary.** Only completed-game summaries are persisted. Games are never saved or resumed; an active in-memory game is lost on restart by design.
3. **Single-process concurrency.** Race protection and idempotency are scoped to the supported single in-memory game worker. The UNIQUE constraint on `game_id` is the final backstop against duplicate records.
4. **Performance target semantics.** The `>= 55` FPS mean and `<= 25` ms p95 targets are a tolerance around a 60 Hz scheduling target and are not a claim about physical display presentation; frame scheduling, game DOM throughput, and display presentation are reported separately.
5. **Measurement honesty.** Any image-size, build-time, audit, CI, or benchmark value is produced only by an actual execution in the implementation phase. This specification does not assert any such value.
6. **Dependency remediation versions.** The specific chosen remediation versions for the runtime and dev/test/audit sets are selected and recorded in the Stage 3 design during implementation, constrained by the audit baseline in Requirement 19 and the preservation of inherited behaviors and test assertions. This document does not assert that any audit, install, or test was executed.
7. **Round-06 benchmark corrections are narrowly scoped.** The round-06 corrections captured in Requirement 20 change only `perf/benchmark.mjs`, `perf/README.md`, and a native evidence note. The accepted application code, tests, dependencies, Docker artifacts, and CI workflows, as well as the earlier-stage specifications, are unchanged. Final performance execution remains unexecuted: no real timing run was performed this round.
8. **Round-07 benchmark corrections are narrowly scoped.** The round-07 corrections captured in Requirement 21 change only `perf/benchmark.mjs` and `perf/README.md`, plus an optional native evidence note under `docs/native-checks/07`. The accepted application code, tests, dependencies, Docker artifacts, and CI workflows, as well as the earlier-stage specifications, are unchanged. Final performance execution remains pending: no real timing run was executed this round.
9. **Round-08 benchmark corrections are narrowly scoped and verified.** The round-08 corrections captured in Requirement 22 record two actually reproduced defects in `perf/benchmark.mjs`: a template-literal regex escape loss that makes the cooked injected instrumentation fail to compile in the browser, and an observation body-readiness race that can falsely reject a still-parsing successful response. They change only `perf/benchmark.mjs` and `perf/README.md`, plus an optional native evidence note under `docs/native-checks/08`. The accepted application code, tests, dependency locks, Docker artifacts, and CI workflows, as well as the earlier-stage specifications, are unchanged. Round-08's own narrow change executed no real timing-sensitive benchmark run, and real performance evidence did not exist at the time of that change. The controlled performance measurement that validates these corrections has since been executed and passed, as recorded in item 10.
10. **Round-08 corrections are now backed by an actual controlled benchmark measurement (closure).** The round-08 corrections in Requirement 22 are now supported by an actual controlled benchmark measurement produced by the unchanged manual command. The run executed three fresh headed sandboxed Chrome sessions at `1280x900` with device scale factor `1`, a `5`-second active warm-up, and exact `30000` ms measured page-clock windows per run.
    - **Scheduling results.** All three runs reported an approximate frame-scheduling rate of about `165` FPS (`165.0068`, `164.9724`, and `165.0063`) on a configured physical display of `165` Hz against a recorded `60` Hz target, which is NOT a proof of physical display presentation; the p95 frame interval was `6.2` ms in each run; and the numeric operational targets of a mean of at least `55` FPS and a p95 frame interval of at most `25` ms were met in every run.
    - **Independent audit and samples.** The raw frames, the changed-signature DOM batches, the API actions, the focus evidence, the geometry evidence, the traces, and the PNGs independently passed `52` checks; the full board was visible in all three PNGs; the valid action samples were `100`, `99`, and `98` with excluded action samples of `0`, `0`, and `1`, where the single exclusion was a dispatch and/or observed update outside the fixed window and was retained with its reason rather than discarded.
    - **Honest limits carried from the researcher facts.** The `requestAnimationFrame` scheduling stream, the changed-signature DOM batches, and the Node API observations are separate streams, and none of these streams is physical display presentation. The dispatch-to-observed-DOM latency includes observer, automation, and polling overhead and is NOT input-to-photon latency. Additional game creates or restarts were `0` in every run, so the conditional restart path was NOT exercised by these timing trials; restart and persistence behavior are separately verified by the API tests and synthetic fixtures. The late capture stops of `220`, `246`, and `310.3` ms are retained while the statistics use only the exact `30000` ms window bounds. The `5000` ms warm-up boundary timestamps are not separately persisted by the harness and SHALL NOT be invented.
    - **CI and review scope.** Ordinary hosted GitHub Actions execution remains NOT performed; the authored workflow file plus the local clean-equivalent checks are what passed. Native checkboxes and prose are not independent acceptance, and no human review is claimed.
    - **Scope exception for the validation utility.** Round-08 added a permanent non-timing validation utility at `perf/validate-instrument.mjs` and an `npm` command `validate:instrument` beyond the originally narrow requested file list; the researcher accepted an exact script-only metadata and support-file exception AFTER full review, with the original strict-binding failure retained. This closure SHALL NOT be read as a retrospective claim of exact file-list compliance.
### Requirement 22: Corrected injected-instrumentation integrity and observation body-readiness (round-08 defects)

**User Story:** As a researcher, I want the benchmark's injected instrumentation to survive template cooking and its request observer to wait for a fully parsed response body, so that telemetry actually installs in the browser and successful responses are never falsely rejected.

#### Acceptance Criteria

1. WHEN the Benchmark_Harness builds the injected instrumentation string that `perf/benchmark.mjs` passes to Playwright `addInitScript` THEN the cooked injected script SHALL preserve every regex backslash so that no regex literal in the cooked script is malformed.
2. WHEN the cooked injected script defines the color-normalization regex THEN the cooked script SHALL contain a valid regular expression that matches an `rgb`/`rgba` value, and SHALL NOT contain an unterminated group produced by template-literal escape loss.
3. WHEN the Benchmark_Harness preserves regex backslashes in the injected instrumentation THEN it SHALL do so without breaking the `${BOARD_CELLS}` interpolation, the `${MEASURE_MS}` interpolation, the `\u0001` (U+0001) signature-join separator, or any other regex in the template.
4. WHEN the injected instrumentation installs in the browser THEN the passive observers and the board-signature functions SHALL initialize successfully rather than failing to install because of an invalid regular expression at compile time.
5. WHEN the Benchmark_Harness validates the injected instrumentation THEN it SHALL construct the injected script from the real native `perf/benchmark.mjs` template and SHALL compile that actual cooked script separately, rather than replicating the instrumentation function code in a test.
6. WHEN the Benchmark_Harness validates the cooked injected script THEN it SHALL execute the real color-normalization and signature functions under a minimal inert `window`, `document`, and `requestAnimationFrame` stub, or an equivalent non-timing check, and SHALL NOT require a browser or a measured timing run for this check.
7. WHEN the Benchmark_Harness validates color normalization THEN it SHALL confirm that `rgb(17,24,39)` and `#111827` normalize to the identical token across all `200` cells.
8. WHEN the Node-side `/move` request-and-response observer records a response THEN it SHALL set an explicit body-ready completion flag only after the response body parsing resolves, including when parsing fails, using a `finally` stage that also records real error flags.
9. WHEN `selectMoveCandidate` evaluates whether an observation is usable THEN it SHALL wait for the explicit body-ready completion state and SHALL NOT reject a still-parsing successful HTTP 200 response whose `colorGrid` is not yet populated.
10. WHEN the Benchmark_Harness records request-to-body-delivery round-trip time THEN it SHALL keep that time on the existing Node monotonic clock and SHALL NOT subtract timestamps across clock domains.
11. WHEN the round-08 corrections are applied THEN the Benchmark_Harness SHALL preserve the round-07 honest no-op exclusion, the exact expected-response-to-observed-signature matching, the required left, right, and soft-drop directional samples, and the strict fixed `30`-second measured window.
12. WHEN an action-latency sample is ambiguous, overlapping, a no-op, or timed-out THEN the Benchmark_Harness SHALL exclude that sample with a reported reason and SHALL NOT fabricate a successful sample.
13. WHEN the round-08 changes are scoped THEN they SHALL modify only `perf/benchmark.mjs` and `perf/README.md`, plus an optional native evidence note under `docs/native-checks/08`, and SHALL leave the accepted application code, tests, dependency locks, Docker artifacts, CI workflows, and earlier-stage specifications unchanged.
14. WHEN this round reports status THEN it SHALL record that round-08's own narrow change executed no timing-sensitive benchmark run and asserted no benchmark execution for that round; the controlled performance measurement that validates these corrections has since been executed and passed, and that closure is recorded in Material Ambiguities item 10.
