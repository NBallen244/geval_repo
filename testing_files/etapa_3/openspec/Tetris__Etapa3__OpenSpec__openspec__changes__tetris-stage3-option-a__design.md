# Design

See `proposal.md` for motivation and general summary of requirements.

## Context

The existing system consists of a stateless Python FastAPI backend storing active game sessions in an in-memory `SessionManager`, and a React/TypeScript frontend rendering the game grid. This architecture is single-process and synchronous. Currently, no scores are stored across restarts. 

To transition this into a persistent brownfield application (Stage 3), we will integrate an SQLite database using Python's standard `sqlite3` module. Pydantic's strict request parsing will be activated to prevent metadata injection. Multi-stage Dockerfiles and Docker Compose will orchestrate the non-root container deployment. Playwright Chromium will run automated performance benchmarking, and GitHub Actions will enforce CI.

To handle high-volume and concurrent requests safely, we will implement in-memory locking per game ID inside the single-process backend, ensuring database write consistency and immutability.

## Goals / Non-Goals

**Goals:**
- Implement durable, atomic SQLite high-score persistence for game-over sessions.
- Secure API endpoints by explicitly rejecting request bodies with extra fields (injection-like requests).
- Synchronize in-memory game mutations and finalization via thread-safe/asyncio locking to prevent concurrency races.
- Set up responsive, robust CORS policies and a dynamic, configurable frontend API base defaulting to same-origin path structure.
- Containerize both applications with secure, non-root configurations, health checks, single backend worker, and persistent named volume writeability.
- Create an automated, timing-sensitive Playwright rendering performance benchmark script capturing raw rendering metrics and screenshot traces.
- Establish a complete continuous-integration pipeline.

**Non-Goals:**
- Resuming active, non-game-over sessions after a process restart (active games remain transiently in-memory).
- Multi-worker or multi-process concurrency backend database support (designed for single-process SQLite with a single backend ASGI worker).
- Client-side database writes or authentication/identity management.
- Transitioning game grid rendering from React DOM to HTML5 Canvas/WebGL.
- Running performance benchmarks as part of standard unit-testing CI (timing-sensitive benchmarks run separately to prevent virtualized environment noise).

## Decisions

### 1. Database Engine, Schema, and Reload Persistence
- **Decision**: SQLite3 using Python's native `sqlite3` module.
- **Rationale**: SQLite is a standard-library, single-file relational database engine, matching the single-process backend constraint without introducing heavy operational dependencies.
- **Schema**:
  ```sql
  CREATE TABLE IF NOT EXISTS high_scores (
      game_id TEXT PRIMARY KEY,
      score INTEGER NOT NULL,
      total_lines INTEGER NOT NULL,
      level INTEGER NOT NULL,
      completed_at TEXT NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_high_scores_score_completed ON high_scores(score DESC, completed_at ASC, game_id ASC);
  ```
- **Reload Survival**: Since SQLite writes to a persistent file specified by `TETRIS_DB_PATH`, any database connection initialized subsequently or after container restart/recreation will attach to the same file, keeping all previous entries intact.

### 2. Connection Lifecycle & Safe Initialization
- **Decision**: On backend startup (lifespan startup event), the parent directory of `TETRIS_DB_PATH` is initialized via `os.makedirs(exist_ok=True)`. A connection is opened to initialize the schema, and subsequent query transactions open/close connections or use thread-local contexts.
- **Rationale**: Ensures the database folder is always available when writing and prevents connection/lock leakage. Since SQLite connections in Python are tied to threads, each FastAPI request thread will manage its connection context using a context manager.

### 3. State Mutation Synchronization Boundary & Concurrency
- **Decision**: Introduce an `asyncio.Lock` per game session inside the in-memory `SessionManager` (or backend engine). Every endpoint request mutating game state (`move`, `tick`, `hold`) or attempting finalization MUST acquire this lock for the specific game ID.
- **Rationale**: SQLite busy timeouts handle disk-level locks, but do not prevent in-memory races in FastAPI's asynchronous event loop. An in-memory lock guarantees that game mutations (e.g. concurrent user moves or gravity ticks) are processed sequentially. If a late concurrent request tries to finalize an already-finalized game session, the lock and unique database constraints reject the duplicate, preserving the original stored result and `completed_at` timestamp.
- **Hold Obstruction Paths**: This lock also protects both first-Hold (empty hold slot) and occupied-Hold (swapping pieces) obstruction pathways, serializing collisions and ensuring game-over state finalization runs exactly once.

### 4. Strict Request Body Validation & Rejected Injection-Like Bodies
- **Decision**: Update Pydantic models in `backend/models.py` to use `model_config = ConfigDict(extra="forbid")` (for Pydantic v2) or `class Config: extra = Extra.forbid` (for Pydantic v1), and define a specific empty schema `GameCreateRequest` with `extra="forbid"` to parse inputs for game creation.
- **Rationale**: Rejects invalid payloads or client-injected score parameters at the gateway, returning an HTTP 422 error and leaving active game sessions completely unchanged.

### 5. CORS, API Base URL, and Development Proxy
- **Decision**: Restrict backend CORS to specific origins configurable via an environment variable `ALLOWED_ORIGINS` (with a secure fallback default), disabling wildcard `*` while enabling `allow_credentials=True`. On the frontend, Vite's environment variable `import.meta.env.VITE_API_BASE_URL` will be used as the base API path, defaulting to `/api`. Vite dev server (`vite.config.ts`) will configure a proxy routing `/api` requests to `http://localhost:8000/api`.
- **Rationale**: Adheres to security best practices and allows simple reverse-proxying via Docker Compose or custom web servers.

### 6. Multi-Stage Docker Containerization and Operational Isolation
- **Decision**:
  - **PACKAGING-ISOLATION-01**: Fully namespace the Compose project, both container names, and the named database volume specifically to this tool/stage, utilizing the name `tetris-stage3-openspec` (e.g. `tetris-stage3-openspec-backend`, `tetris-stage3-openspec-frontend`, and `tetris_stage3_openspec_data`).
  - **PACKAGING-CONTEXT-01**: Configure `.dockerignore` to explicitly exclude all local runtime and build caches, specifically including `docs/`, `.gemini/`, `.git/`, all local venvs, `node_modules/`, `caches/`, `build/`, `coverage/`, `runtimeDB`, and `credentials`.
  - **RUNTIME-POLICY-01**: Use `node:24-slim` consistently for frontend builds and CI (as checked on 2026-10-28, Node 20 is EOL). Use the official maintained stable `nginx:stable-alpine` (representing current stable branch Nginx as checked on 2026-10-28) for production rendering. Python 3.11 remains unchanged.
  - **Backend**: Use `python:3.11-slim` multi-stage build. Creates a dedicated non-root system user `appuser` (UID 10001), exposes internal port 8000, and writes database files to a mounted `/app/data` volume owned by `appuser`. The container runs exactly one worker process (`uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1`).
  - **Frontend**: Use `node:24-slim` to build production assets, then serve them using the stable non-root `nginx:stable-alpine` image running on host port 5183. Reverse proxies `/api` to the backend.
  - **Health Checks**: Both images define `HEALTHCHECK` instructions to confirm service status.
  - **Volume Ownership**: Ownership of the mounted namespaced `tetris_stage3_openspec_data` volume is verified by making actual SQLite write tests on startup, ensuring persistence across container recreation.

### 7. Playwright Performance Benchmarking & Detailed Evidence (PERF-EVIDENCE-01)
- **Decision**: Write a standalone Playwright script running inside Chromium that adheres to precise evidence-gathering constraints:
  - **Fresh Context per Run**: Each run initializes a completely independent context and page, performing a separate 5-second warmup before the 30-second measurement.
  - **Deterministic Key Sequences**: Uses a deterministic, replayable key sequence to simulate gameplay.
  - **Active Board Observer**: Attaches a MutationObserver directly to the current board element, re-initializing/re-attaching it after any game reset or restart.
  - **Outcome Tracking & Action Evidence**: Saves raw per-run JSON arrays of `frameIntervals` and `actionLatencies`. Records every action outcome (success, timeout, blocked, or no-change), `browser.version()`, timestamps, visibility state, metadata, trace paths, and SHA256 hashes. Retains every key dispatch attempt with unique IDs, key name, timestamp, expected/blocked/rejected/nochange/timeout classification, and raw latency observations. Correlates actual backend API request, response status, and round-trip timing with each dispatch. Documents attribution limitations (e.g., that the first DOM mutation after dispatch may be due to gravity rather than user action). Never drops 200ms timeouts from the evidence.
    - *Action/Request Clock Attribution*: Since Node's `performance.now()` and browser's `performance.now()` have differing time origins (and the browser origin resets on every fresh context run, causing Run 1 to misalign and Runs 2/3 to report unknown), both API requests and browser keyboard actions are timestamped using comparable absolute epoch-based timestamps derived from `performance.timeOrigin + performance.now()`.
    - *Causal Mapping Heuristic*: API requests are mapped to keyboard actions only when they are causally valid: the request must start after dispatch (allowing a strict clock precision tolerance of 10ms) and within a max temporal window of 250ms, and must match the expected method, route, and key-specific parameters (e.g., left/right/down payloads for move endpoints or the /hold endpoint). Gravity `/tick` requests, game creations, and leaderboard reads are explicitly excluded from keyboard action attribution. Unresolvable, blocked, or ambiguous cases remain null/unknown with a detailed reason.
    - *Internal Consistency Validation*: Includes an executable, self-contained integrity check that halts and fails the benchmark if any impossible linked pair (such as a request starting before its causal action beyond the tolerance, or incorrect endpoints/payloads) is generated.
  - **Execution Constraint & Environment Controls**: Enforces explicit headful/foreground run for full compliance; headless mode is labeled unsupported. Chromium's sandbox is NOT disabled globally. To support HOST headed capability where bundled Playwright Chromium fails with spawnUNKNOWN, an explicit `BROWSER_CHANNEL=chrome` override (or equivalent flag/config) MUST be supported to launch the installed official Chrome via `Playwright.chromium` with `chromiumSandbox: true`, disclosing the brand/version/channel as a controlled Chromium-family variation without modifying any personal browser profiles or tabs. Headless fallback data may be retained but MUST NOT earn headed acceptance.
  - **Timing Window Precision**: Frame intervals and DOM update counts MUST only be captured inside the precise active 30000ms measurement window (defined by `measurementActive` and browser-monotonic start/end timestamps, which begins AFTER restart settles and warmup completes). Raw data collection MUST be frozen and copied/serialized BEFORE screenshots are taken, tracing is stopped, or zip ZIP I/O operations occur, to prevent I/O lag from contaminating the performance measurements.
  - **Fail State Enforced**: Enforces non-zero exit on failed targets (FPS < 55 or p95 > 25 ms) while fully preserving raw traces and metrics.
  - **Screenshots**: Captures PNG/JPG screenshots at meaningful game states (e.g. gameplay active, game over, leaderboard loaded) to serve as visual QA.
- **Statistical Evidence Collected**:
  - Retained RAW frame intervals (all intervals in ms).
  - DOM board mutation/update counts.
  - Action-to-visible-update latency samples.
  - Complete browser performance trace with screenshot frames.
  - Calculations: median, p95, and p99 frame intervals, count of intervals > 33.34 ms (dropped frames relative to 60Hz), approximate FPS.
  - Environment Disclosure: CPU, GPU, memory, OS, browser version, foreground/headless mode.
- **Timing Sensitivity**: Runs as a separate executable benchmark command with 5s warmup and three independent 30s runs, keeping checks independent of normal CI testing to preserve data integrity and prevent virtualized environments from causing false CI failures.

### 8. GitHub Actions CI & Sonar Quality Gate Compliance
- **Decision**: `.github/workflows/ci.yml` runs:
  1. Python tests and coverage, outputting XML reports (`backend/coverage.xml`).
  2. Frontend ESLint/Oxlint, Vitest, and production build, outputting LCOV reports (`frontend/coverage/lcov.info`).
  3. Security dependency audits (`npm audit` and `pip-audit`).
  4. Docker compilation checks to verify Dockerfile syntax and Compose setup.
- **Verification Integrity**: This represents a local template for the CI workflow and does not claim remote hosted execution. All coverage file paths are specified strictly.
- **Sonar qa07 Quality Gate Fixes**: To resolve Quality Gate failures from analysis `24b87da3-2e58-4087-a9aa-17dae3c27c05`, we address the following violations:
  - **python:S1192** in `backend/main.py77`: Duplicated Hold rejection messages are refactored into a named constant.
  - **python:S9100** in `backend/test_stage3.py23`: Unnecessary yield fixture is refactored to use standard return values.
  - **typescript:S6582 / S7741** in `frontend/src/api.ts33`: Refactor typescript code to use explicit direct comparison against `undefined` or robust checks instead of improper optional chain usages.

### 9. Separation of Runtime and Development/Test Dependencies
- **Decision**: Clearly separate runtime-only dependencies from development, auditing, and testing dependencies.
- **Rationale**: Production runtime Docker containers must be lean, fast to build, and secure. Having `pytest`, `coverage`, `pip-audit`, or `playwright` in production images unnecessarily increases container size and the security attack surface. We will split requirements into:
  - `backend/requirements.txt` (Runtime dependencies: `fastapi`, `uvicorn`, `pydantic`).
  - `backend/requirements-dev.txt` (Development and test dependencies: `pytest`, `httpx`, `pytest-cov`, `pytest-anyio`, etc.).
  - Frontend production builds will run via standard `npm ci` using the committed `package-lock.json` manifest to guarantee exact, reproducible dependency installations.
  - **Packaging COPY Exclusions**: Exclude runtime-unnecessary test files (`test*.py` and `requirements-dev.txt`) from the production backend Docker build by omitting them from the runtime COPY instruction in `Dockerfile`, while preserving them in the source repository for local/CI tests and their analysis scope.
  - **Stage Labelling Consistency**: If UI still labels the running release Stage2, update its stage label consistently with Stage3.

## Risks / Trade-offs

- **[Risk] SQLite Concurrent Locking** → SQLite can raise `OperationalError: database is locked` if parallel threads write concurrently.
  - *Mitigation*: The backend is a single-process FastAPI system; we will configure `sqlite3.connect(..., timeout=10.0)` to allow busy-waiting on locks, and handle write operations atomically using transactions. Furthermore, the backend `asyncio.Lock` per game session prevents concurrent requests for the same session from clashing.
- **[Risk] Path/SQL Leaks on Database Failures** → Database errors might expose system pathways or query layouts.
  - *Mitigation*: Pervasive `try-except sqlite3.Error` blocks on all storage actions. On exception, write the traceback to server logs, and raise an HTTP 503 HTTP exception returning a sanitized error payload `{ "detail": "Storage service unavailable" }` on both reads and writes.
- **[Risk] Playwright Benchmarking Fluctuations in Headless/CI** → Virtualized environments can introduce frame drop.
  - *Mitigation*: The performance test explicitly runs three separate 30-second runs and records raw frame intervals, allowing for clear separation of environment-induced hiccups from core architectural degradation.
- **[QA] Test Isolation (TEST-ISOLATION-01)** → Running tests with real or hardcoded `./data` directories risk filesystem clashing, deleting user database files, or mutating production-configured scores during test execution.
  - *Mitigation*: We mandate that all test modules configure `TETRIS_DB_PATH` dynamically inside a unique temporary directory (e.g., using pytest's `tmp_path` fixture combined with `monkeypatch` to redirect environment variables). This isolates tests, prevents filesystem conflicts, and completely avoids destructive directory removal (like `shutil.rmtree`) of configured workspace data paths.
- **[QA] Hold Collision Testing Integrity (TEST-FIXTURE-02)** → Using artificial single-cell pieces or wrong spawn obstruction coordinate assumptions in tests doesn't align with the game's actual canonical tetromino geometries and fails to establish realistic obstruction conditions.
  - *Mitigation*: We mandate that Hold/Swap collision tests utilize legal, canonical four-cell tetromino shapes (e.g., `"O"` at origin `[17, 0]`) and place board obstructions at specific spawn-obstructing cells (such as `[1, 4]`) to genuinely obstruct newly spawning pieces (`"S"` or `"T"`) and verify terminal game-over finalization.
