# Requirements Specification: Browser-Based Tetris Study - Stage 3, Option A (Persistent High Scores & Production Architecture)

## Post-Implementation Corrections & Independent Findings (Stage 3 Verification)
An independent audit identified key failures and security/correctness issues with the previous Stage 3 implementation. This document has been revised to retract previous premature completion and security claims, and keep the affected checklist items OPEN.

### Documented Failures & Required Corrections:
1. **Insecure CORS Wildcard Option:** Configuring CORS_ORIGINS='["*"]' in backend environment granted arbitrary origins and credentials, violating security best practices. Wildcard origins must be rejected or sanitized when credentials are enabled. Meaningsful tests for allowed origin, rejected origin, and wildcard configuration must be added.
2. **Missing Startup Dependency (Uvicorn):** The existing Python 3.10.11 backend virtual environment lacked the `uvicorn` dependency, preventing startup during HTTP suite evaluation. A new Python 3.12 virtual environment must be established at `docs/runtime/.venv` using the Study Python 3.12.14 interpreter at `D:/KEVIN/UNIVERSIDAD/Trabajos/Proyecto/Caso 2-Tetris/Etapa 1/_toolchain/venv/Scripts/python.exe` (pointing launcher `UV_PROJECT_ENVIRONMENT` and `PATH` to it).
3. **Empty Dependency Lock File:** The previous `uv.lock` had zero packages, and `pyproject.toml` used legacy Poetry format. We must fix the dependency strategy coherently (PEP621 standard + genuine populated `uv.lock` with prod/dev groups).
4. **Vulnerable Production Dependencies:** The container Starlette version (0.46.2) has 14 advisory records representing 7 distinct IDs. We must fix this with locked, secure compatible versions of FastAPI and Starlette (minimum fixed Starlette >= 1.3.1).
5. **CI Workflow Deficiencies:** CI installed unpinned tools, ignored audit failures via `|| echo`, and omitted the frontend build step. CI must propagate audit failures, pin all runner/tooling versions, and execute all tests, lint, typecheck, production build, and Docker builds.
6. **False-Positive Docker Alert Handling:** A Docker checking tool falsely flagged third-party packages inside the container. We must NOT strip or patch third-party packages to appease false positives, but we must rebuild the actual images from the corrected lock inputs.
7. **Performance Benchmark Rejection:** The Playwright performance run from native04 was rejected because its headless, no-sandbox, summary-only approach did not satisfy the physical browser execution and trace evidence required by the common seed. Therefore, all affected benchmark, measurement, data collection, and trace validation tasks have been reopened and remain explicitly OPEN. We must execute a corrected, fully-sandboxed, headed browser benchmark capturing raw perf metrics, visible screenshots, and complete execution traces.
8. **Sonar Violations Gate ERROR:** Sonar reported 13 new violations (such as `logging.exception()`, fixture yields, manual global state monkeypatching in tests, React optional chaining, component readonly props, `typeof` comparisons, unhandled catches, and CSS contrast). These must be fully resolved.

### Independent07audit Findings & Required Corrections on run_2026-11-02T08-02-51-695Z_pzh8cu:
An independent07audit (51 checks, 47 pass, 4 fail) of run_2026-11-02T08-02-51-695Z_pzh8cu identified precise defects. All 07data is preserved as real and highly accurate but not fully protocol-accepted because of these four specific issues, and we have reopened the corresponding evidence/metadata tasks:
- **Captured Browser Version:** The actual measured-run browser version was missing from performance-report.json. We must capture `browser.version()` WHILE that actual browser is alive, store it in the emitted report (e.g. as `browser_version`), and retain it after `browser.close()`. Optionally, we must record the actual CDP launch arguments before timing without disabling the sandbox, ensuring we do not fabricate defaults.
- **Reference Target and Refresh Rate Labels:** We must include an explicit "60Hz" reference-target label and state that the OS-reported "165Hz" is configured metadata (not a physical-presentation proof).
- **Mislabeled Warmup Samples / Classification Bug:** 92/77/89 intervals before the final declared warmupStart (including one crossing into warmup per trial) were mislabeled as 'warmup'. Initial hooks start recording about 0.6s before warmupStart is reset, so these samples are real and MUST be kept. The mathematical classification must be corrected while keeping raw timestamps unchanged: after nonpositive handling, intervals ending at/before warmupStart are 'pre-window'; intervals with t_prev < warmupStart < t_curr are 'cross-boundary-pre-to-warmup'; then warmup intervals end at/before measureStart; measured eligibility remains positive with BOTH endpoints inside [measureStart, measureEnd]; and we retain existing measurement cross-boundary/post-window categories. Classification counts must be emitted and reproducible.
- **Directory Collision Safety:** `fs.mkdirSync(RUN_DIR_PATH, {recursive: true})` does not refuse an existing batch directory. We must ensure the parent directory exists, and then create the new timestamp+nonce batch directory using exclusive/nonrecursive creation and fail on collision, never overwriting or cleaning old directory traces.

## 1. Superseding Statement & Scope Boundaries
The legacy exclusion of database persistence and score storage specified in Stage 2 (including Group S2-H Req-S2-40 and all Stage 1/2 documents) is **explicitly and fully superseded** by this Stage 3 Option A specification. 

This specification ONLY supersedes the database persistence exclusion. All other legacy exclusions—specifically, tetromino piece rotation, wall kicks, ghost piece rendering, T-Spins, gameplay achievements, time attack/specialized modes, PostgreSQL/external multi-user databases, player authentication, multiplayer, global real-time leaderboards, and cloud/external hosting—remain strictly in effect and MUST NOT be implemented.

The inherited FIFO is the CLIENT MUTATING HTTP REQUEST queue (tick/move/hold), not a tetromino spawn-preview queue. The system MUST preserve the actual previous FIFO, React `StrictMode` and stale/falsey response protections. It MUST explicitly retain HTTP 200 creation, the actual `active_piece`/`origin`/`cells` payload, and every earlier test assertion.

The local host environment uses Python 3.10.11 (Native01) and Node 25.6.1, while the researcher logs represent a separate Python 3.12.14 environment. CI and Docker containers will target Python 3.12 and Node 24. No tool or model updates are allowed. The local Python 3.10 virtual environment must not be altered, but may be replaced/extended by a fresh, separate Python 3.12 environment inside this directory only.

---

## 2. Atomic Requirements (Req-S3-1 to Req-S3-50)

### Group S3-A: SQLite Persistence & Database Lifecycle
- **Req-S3-1 (SQLite Engine):** Persistent high scores MUST be stored in a local SQLite database using Python's standard library `sqlite3` module. The system MUST NOT use an external ORM (such as SQLAlchemy or SQLModel) or any database engine other than SQLite.
- **Req-S3-2 (Configurable DB Path):** The file path to the SQLite database MUST be configurable via the environment variable `TETRIS_DB_PATH`, which MUST default to `./data/high-scores.sqlite3` if not provided in the environment.
- **Req-S3-3 (Startup Path & Schema Init):** On backend service startup (within the FastAPI lifespan handler), the system MUST safely verify and initialize the database's parent directory if it does not exist (e.g., creating `./data`). This filesystem setup (`os.makedirs`) and the database initialization (`sqlite3.connect`) MUST run inside appropriate try-except blocks handling `OSError` and `sqlite3.Error`. `init_db` MUST initialize the database connection variable to `None` prior to calling `sqlite3.connect`, so that any connection failure is not masked by an `UnboundLocalError` in the `finally` block. It must close only successfully opened resources and avoid masking any original exceptions, while producing controlled generic API errors on storage failures. Original terminal timestamps/snapshots MUST be preserved across retries.
- **Req-S3-4 (Game Over Eligibility):** A game session's score is eligible for persistence in the SQLite high scores database ONLY when its authoritative in-memory state has reached the `"game_over"` status.
- **Req-S3-5 (Unique Completed Games Only):** The database MUST persist every completed game exactly once per game session ID, including zero scores, utilizing a SQL primary key or uniqueness constraint on `game_id` and atomic, parameterized writes (`INSERT INTO high_scores ...`) to prevent SQL injection and guarantee transaction integrity.
- **Req-S3-6 (Database Table Schema):** The database schema for the high scores table MUST record exactly the following columns:
  - `game_id` (TEXT PRIMARY KEY)
  - `score` (INTEGER NOT NULL)
  - `total_lines` (INTEGER NOT NULL)
  - `level` (INTEGER NOT NULL)
  - `completed_at` (TEXT NOT NULL, storing the UTC ISO-8601 string timestamp of completion, e.g. `"YYYY-MM-DDTHH:MM:SSZ"`).
- **Req-S3-7 (Finalization Endpoints):** A game that ends through a gravity tick (`POST /api/games/{id}/tick`), a manual soft drop (`POST /api/games/{id}/move` with direction "down"), or an obstructed Hold action (`POST /api/games/{id}/hold`) MUST trigger the same database finalization rules and save its results upon transitioning to `"game_over"`.
- **Req-S3-8 (Abandoned/Restarted Games Exclusion):** If a player restarts a game (by calling `POST /api/games`) or abandons an active game session without reaching `"game_over"`, the system MUST NOT write any record to the high scores database for that session.
- **Req-S3-9 (Terminal Idempotency & Original Timestamps):** Repeated terminal requests (such as a tick or move command executed on a game session that is already `"game_over"`) and concurrent database insertion attempts for the same game session MUST be idempotent. They MUST NOT duplicate, replace, or alter the original database entry or its original `completed_at` timestamp.
- **Req-S3-10 (No-Mutation Reads):** Retrieving an active game state (`GET /api/games/{id}`) or reading the high scores leaderboard (`GET /api/high-scores`) MUST be strictly read-only and MUST NOT mutate any game state or trigger any database write.
- **Req-S3-11 (Single-Process Thread Safety):** To protect the transient in-memory games directory (`GAMES` dict) and the database file from race conditions during concurrent requests, the single-process backend MUST synchronize state changes and database finalization using `threading.RLock` around mutations and finalization. SQLite connections MUST be scoped safely per operation, opened and closed strictly within the scope of the operation to ensure thread safety.
- **Req-S3-12 (In-Memory Game State Transient Lifecycle):** Active live games remain transient and reside exclusively in memory. They are NOT resumed or persisted across backend process restarts. High scores in the SQLite database file MUST survive backend process and container restarts.
- **Req-S3-13 (No Multi-Worker Claim):** The application architecture, code, and documentation MUST NOT claim or promise multi-worker, multi-node, or distributed scalability for active, in-memory games.

### Group S3-B: Leaderboard API Endpoints
- **Req-S3-14 (Leaderboard Route):** The backend MUST expose a new public API endpoint `GET /api/high-scores`.
- **Req-S3-15 (Leaderboard Schema):** The endpoint `GET /api/high-scores` MUST return a JSON object with a `scores` key containing an array of at most ten high score entries. Each entry in the array MUST contain exactly these fields:
  ```json
  {
    "game_id": "string-uuid",
    "score": integer,
    "total_lines": integer,
    "level": integer,
    "completed_at": "string-utc-timestamp"
  }
  ```
- **Req-S3-16 (Leaderboard Sorting):** The array returned by `GET /api/high-scores` MUST be ordered by:
  1. `score` descending.
  2. `completed_at` ascending.
  3. `game_id` ascending.
- **Req-S3-17 (Leaderboard Response Model):** The `GET /api/high-scores` route decorator MUST declare an explicit Pydantic response model to comply with the `maria/fastapi` pii-sanitisation rule.
- **Req-S3-18 (No Client-Supplied Writes):** No public API endpoint may accept a client-supplied score, level, lines count, completion timestamp, or arbitrary game ID to insert a record. High scores MUST be derived solely from the authoritative in-memory backend state upon transitioning to game over.
- **Req-S3-19 (Strict Request Body Validation):** The backend MUST reject any extra fields in game creation (`POST /api/games`) and move request bodies (`POST /api/games/{id}/move`) rather than silently trusting or ignoring submitted score/metadata. Valid bodyless game creation and existing valid movement bodies MUST be preserved (i.e. `extra = "forbid"` and optional body support must coexist, allowing a standard bodyless POST).
- **Req-S3-20 (Standard Error Statuses):**
  - An invalid direction in `POST /api/games/{id}/move` MUST return a documented 400 or 422 status code.
  - Attempting to access an unknown game UUID via any API endpoint MUST return an HTTP 404 response.
- **Req-S3-21 (Controlled Storage Failures):** Any storage, filesystem (e.g. `OSError`), or database operational failure (such as `sqlite3.Error`) during a leaderboard read or game finalization MUST produce a controlled HTTP 503 Service Unavailable JSON response (e.g., `{"detail": "High scores database is temporarily unavailable."}`). The response body MUST NOT leak file paths, database schemas, database structure, raw SQL statements, cause strings, or Python stack traces. The system MUST preserve raw failure evidence (e.g., logging the details internally) and produce generic controlled API errors wherever requests can observe the storage failure. Meaningful tests MUST be added for connection/parent-directory failures and request failure/recovery. Original terminal timestamps/snapshots MUST be preserved across retries.
- **Req-S3-22 (Safe Finalization Retries):** If finalization fails and returns a 503 error on game over, a subsequent mutating request (tick, move, or hold) on that terminal game session MUST retry the persistence safely while preserving its original `completed_at` timestamp and game-over state. A GET request MUST NEVER trigger a database write or retry.

### Group S3-C: Frontend High Scores Panel
- **Req-S3-23 (High Scores Panel UI):** The frontend application MUST render a dedicated High Scores panel showing the top ten high scores, detailing each entry's score, lines, and level.
- **Req-S3-24 (Panel UI States):** The High Scores panel MUST gracefully handle and display:
  - **Loading State:** a visual spinner or indicator while the scores are being fetched from the API.
  - **Empty State:** a clear message (e.g. "No high scores yet") if the database has no records.
  - **Error State:** a user-friendly error message if the API call fails or returns an error.
- **Req-S3-25 (Fetch Timing):** The frontend MUST fetch the high scores on initial application load and immediately after a game transitions to the game over state. It MUST NOT poll the leaderboard endpoint on every gravity tick or active piece movement.
- **Req-S3-26 (Configurable API Base):** The frontend MUST use a configurable API base URL that defaults to `/api` (same-origin), so that development servers (e.g. Vite proxying) and production Docker deployments function without any hardcoded `localhost` URLs.
- **Req-S3-27 (CORS Policy):** The backend FastAPI app MUST define and document a restrictive, configurable CORS policy. Wildcard origins (`"*"`) MUST NOT be allowed when credentials are enabled.
- **Req-S3-28 (No Authentication or Names):** The frontend and backend MUST NOT collect, store, or display player names, and MUST NOT require any authentication.

### Group S3-D: Production Docker Packaging & Compose
- **Req-S3-29 (Multi-Stage Dockerfiles):** Separate, production-optimized, multi-stage Dockerfiles MUST be provided for the backend (`backend/Dockerfile`) and frontend (`frontend/Dockerfile`) to ensure minimal, reproducible runtime images.
- **Req-S3-30 (Docker Ignore):** Context-specific `.dockerignore` files MUST be included in both `backend/` and `frontend/` context directories to exclude node_modules, Python virtual environments, local sqlite databases, and dev files from the Docker context. A root-level `.dockerignore` is not sufficient because backend and frontend use their respective subdirectories as active build contexts.
- **Req-S3-31 (Docker Compose Configuration):** Docker Compose using the explicit project name `tetris-stage3-tessl` MUST be provided as the local runner orchestrating the services.
- **Req-S3-32 (Production Build & Proxy):** The frontend container MUST serve the production static files and reverse-proxy any `/api` requests to the backend service (using Nginx or another lightweight server).
- **Req-S3-33 (Security Constraints):**
  - Both frontend and backend application containers MUST run as non-root users (e.g. UID 10001 for backend, UID 101/nginx for frontend).
  - Only the frontend service port 5183 is published to the host machine (`5183:5183`). The backend service MUST remain internal and accessible only within the shared Docker Compose network.
- **Req-S3-34 (Persistent Storage):** The database directory MUST be stored on a named Docker volume `tetris-stage3-tessl-db-vol` with write permissions assigned to the backend service's non-root user.
- **Req-S3-35 (Single Worker):** The backend server MUST be configured to run with exactly one worker (e.g. `uvicorn --workers 1`) to ensure single-process in-memory game state consistency.
- **Req-S3-36 (Container Health Checks):** Docker Compose configuration MUST declare health checks for both the backend (e.g. calling `/`) and frontend containers.
- **Req-S3-37 (No Secrets or Dev Deps):** No credentials, private API keys, or development-only dependencies (e.g. Vitest, Poetry dev groups in the final runtime step) may be baked into the final runtime images.

### Group S3-E: Playwright Browser Performance Benchmark
- **Req-S3-38 (Benchmark Harness):** An executable performance benchmark using Playwright Chromium MUST be provided, running against the production frontend.
- **Req-S3-39 (Throughput Tracking and Frame Metrics):** `requestAnimationFrame` (rAF) only measures callback scheduling; DOM mutation evidence is separate and neither proves physical presentation nor action causality. The benchmark script MUST count actual DOM mutations (cell updates) separately from rAF scheduling.
- **Req-S3-40 (Benchmark Scenario):** The test scenario MUST be controlled and run in a visible foreground browser at 1280x900 resolution with a device scale factor of 1, targeting a 60 Hz display.
  - **Browser Choice:** Use installed Chrome if bundled Chromium cannot launch, recording the variation, actual browser version, headed mode, and `chromiumSandbox: true`.
  - **Trials:** It consists of THREE independent trials. Each trial consists of:
    - Warm-up: exactly 5000ms.
    - Measurement: exactly 30000ms declared in-page monotonic measurement window.
    - Declared window bounds and observed scheduling start/stop times MUST be kept separate.
  - **Capture snapshots:** Record fresh `document.hasFocus` and visibility snapshots after each trial reset and at measured start/end plus during key events. Focus MUST NOT be faked, and prior arrays MUST NOT be erased before saving.
  - **Simulation:** Simulated active gameplay dispatching left, right, and soft-drop keys at normal human-scale action rates, and restarting as needed. Maintain normal gravity, keys, and React DOM.
  - **Outputs:** Retain per-run raw JSON, genuine screenshot, and performance trace without overwriting previous labels.
- **Req-S3-41 (Benchmark Metrics):** The benchmark MUST record and report:
  - Browser, runtime, OS, and hardware specifications.
  - Display refresh rate and mode (headed vs headless).
  - Frame interval statistics: median, p95, and p99.
  - Approximate FPS (counting only positive intervals fully inside the measured window).
  - Occurrences of frame drops (intervals > 33.34 ms).
  - Action latency and action-to-DOM samples with their attribution limits.
- **Req-S3-42 (Operational Target):** The target for a standard execution environment is a mean frame scheduling rate >= 55 FPS and a p95 frame interval <= 25 ms in every run. This is specified as a tolerance around a 60 Hz target and does not guarantee hardware presentation.
- **Req-S3-43 (Benchmark Safety Constraints):** The benchmark MUST NOT:
  - Alter game gravity or speed to inflate performance metrics.
  - Add artificial permanent loops solely to inflate the FPS or high-frequency API timers just for metrics.
  - Rotate pieces (as rotation remains strictly excluded).
  - Migrate the DOM renderer to Canvas or WebGL (the 10-by-20 React DOM board must be preserved).
  - Exceed 60 API requests per second (actions must be throttled naturally).
- **Req-S3-44 (Execution Separation):** The benchmark suite MUST be run sequentially and separately from ordinary unit tests, with an explicit performance CI job or documented manual command.

### Group S3-F: GitHub Actions Continuous Integration Workflow
- **Req-S3-45 (Continuous Integration):** A GitHub Actions workflow (`.github/workflows/ci.yml`) MUST be defined to build, lint, and test the code on push or pull request.
- **Req-S3-46 (Workflow Scope):** The workflow MUST cover:
  - Backend tests and code coverage.
  - Frontend tests and production build.
  - Docker image builds (frontend and backend).
- **Req-S3-47 (Reproducible Environments):** The workflow MUST pin the major versions of Python 3.12 (with actual host running 3.10.11 reported truthfully) and Node 24 (with actual host running 25.6.1 reported truthfully), and utilize frozen dependency lockfiles (`poetry.lock`/`uv.lock`/`package-lock.json`) for reproducible installations.
- **Req-S3-48 (No Secrets):** The workflow MUST run successfully without requiring any private repository secrets or tokens.
- **Req-S3-49 (Dependency Auditing):** The CI pipeline MUST include basic dependency security auditing commands (`npm audit` and `pip-audit` or `safety`) and log/report their findings and scope.

### Group S3-G: Scope Boundaries & Exclusions
- **Req-S3-50 (Stage 3 Scope Boundaries):** The following features MUST remain strictly excluded from the Stage 3 implementation:
  - Rotation and wall kicks.
  - Ghost piece rendering.
  - T-Spins.
  - Time attack or other specialized gameplay modes.
  - Gameplay achievements.
  - Saved or resumable game sessions (active games remain transient in memory).
  - PostgreSQL or any external multi-user database (SQLite is the exclusive database).
  - Authentication or player profile systems.
  - Multiplayer or global real-time leaderboards.
  - External cloud deployment.

---

## 3. Acceptance Criteria

| ID | Description | Detailed Acceptance Criteria |
| --- | --- | --- |
| **AC-S3-1** | Database Lifespan & Schema Initialization | On service startup, directory `TETRIS_DB_PATH`'s parent is created if missing, schema is initialized cleanly with no crashes if already existing. Active games are in-memory; high scores are persistent and survive a service restart. No multi-worker claim. |
| **AC-S3-2** | Authoritative High Score Recording | Upon entering `"game_over"` status (due to gravity, soft drop, or obstructed Hold), a unique game's score, lines, level, and timestamp are inserted into the SQLite database. Abandoned or restarted games write no record. |
| **AC-S3-3** | Parameterized Writing, Synchronization, and Idempotency | SQL insert commands are parameterized to prevent SQL injection. Concurrent mutations and finalization are synchronized via a `threading.RLock` and atomic writes. Repeated terminal actions or concurrent calls on the same game UUID return the original record without duplicating entries or modifying the original timestamp. |
| **AC-S3-4** | Leaderboard Retrieval & Read Isolation | `GET /api/high-scores` returns exactly at most 10 scores sorted by score descending, completed_at ascending, and game_id ascending. The endpoint is read-only and does not mutate any game state or create database rows. |
| **AC-S3-5** | Strict API Input Validation | Rejecting extra fields on `POST /api/games` and `POST /api/games/{id}/move` using Pydantic `extra = "forbid"`. Standard bodyless game creation and valid move payloads remain functional. Invalid directions return documented 400/422, and unknown games return 404. |
| **AC-S3-6** | Database Storage Failures & Retries | Database locks, full-disk, or filesystem (`OSError`) conditions return a controlled HTTP 503 Service Unavailable JSON response with no leaked file paths, database structure, or stack traces. Mutating commands retry persistence safely if game over was reached, preserving the original completion timestamp. GET does not retry. |
| **AC-S3-7** | Frontend Leaderboard Panel & Configurable API | High Scores panel shows the top 10 scores with graceful Loading/Empty/Error state displays. Re-fetches only on initial load and post game over. App uses configurable `/api` default same-origin routing and restrictive CORS. |
| **AC-S3-8** | Multi-Stage Docker Packaging | Separate backend/frontend multi-stage Dockerfiles, non-root users, named volumes for database storage, health checks, and 1 backend worker. Only the frontend is exposed on port 5183. Context-specific `.dockerignore` files are placed inside `backend/` and `frontend/` contexts. |
| **AC-S3-9** | Playwright Performance Benchmark | Chromium performance benchmark measures DOM mutations, frame statistics, and input-to-visible-update latency. Under 1280x900, 60Hz target, and 30-second active play runs, it records median/p95/p99 intervals, verifying target rates. |
| **AC-S3-10** | GitHub Actions CI & Auditing | CI workflow pins Node and Python major versions, tests and builds the frontend, backend, and Docker images without private secrets. Dependency auditing commands are run and logged successfully. |

---

## 4. Run, Test and Benchmark Commands

All verification commands are structured cleanly, separated by domain. These commands are planned and will correspond exactly to the generated files.

### Backend Commands (run from `backend/` directory):
- **Initialize database and start dev server:**
  ```bash
  export TETRIS_DB_PATH="./data/high-scores.sqlite3"
  uv run uvicorn app.main:app --port 8000 --reload
  ```
- **Run backend tests:**
  ```bash
  .venv\Scripts\python -m pytest -v
  ```

### Frontend Commands (run from `frontend/` directory):
- **Run dev server:**
  ```bash
  npm run dev
  ```
- **Run frontend tests (TypeScript checking & unit tests):**
  ```bash
  npm run test
  ```
  *(Note: npm run lint performs TypeScript compilation checking `tsc --noEmit`, which is not ESLint.)*
- **Build frontend:**
  ```bash
  npm run build
  ```

### Docker Commands (run from repository root):
- **Build and start services with explicit project name:**
  ```bash
  docker compose --project-name tetris-stage3-tessl up --build -d
  ```
- **Stop services and preserve volumes:**
  ```bash
  docker compose --project-name tetris-stage3-tessl down
  ```
- **Verify persistence by restarting container (without volume wipe):**
  ```bash
  docker compose --project-name tetris-stage3-tessl down
  docker compose --project-name tetris-stage3-tessl up -d
  ```

### Playwright Benchmark Command (run from repository root):
- **Run the performance benchmark sequentially:**
  ```bash
  npx playwright test tests/benchmark.spec.ts --headed
  ```

---

## 5. Explicit Unchecked Project Verification Tasks

The following checklist tracks exact, empirical verification tasks that MUST be executed and recorded:

- [ ] **Docker Build Performance & Metadata:** Measure and document the actual Docker build wall time, final image byte sizes, and generated Docker Image IDs for both the frontend and backend production images.
- [ ] **Effective Non-Root User Verification:** Verify that the running containers are indeed executing as non-root users (e.g., inspecting container processes to verify UID 10001 for backend and UID 101/nginx for frontend).
- [ ] **Health Check Validation:** Validate that the container-defined health checks execute successfully and update the container status to `healthy`.
- [ ] **Port Isolation Verification:** Verify that only the frontend port `5183` is exposed to the host machine, while the backend port remains fully internal to the private network.
- [ ] **Writable Named Volume Persistence:** Validate that the backend container can write to the SQLite database within the named volume `tetris-stage3-tessl-db-vol`.
- [ ] **Container Recreation Persistence:** Perform a full restart cycle (`docker compose down` followed by `docker compose up -d` without a volume wipe), verifying that recorded scores survive container teardown and recreation.
- [ ] **Dependency Audit Scope & Reproducibility:** Perform a comprehensive dependency security audit using exact reproducible locks (`uv.lock`/`poetry.lock` for Python, `package-lock.json` for Node) using pinned audit tools (`pip-audit` or `safety` for Python, `npm audit` for Node) with no unjustified advisory suppression.

