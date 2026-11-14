# Implementation Research: Persistent High Scores, Dockerization, Playwright Benchmarking, and CI

This document records the research, system analysis, and engineering decisions completed for the Stage 3 Option A Tetris features. It establishes the technical framework for the database, API validation, containerized deployment, performance metrics, and automated CI workflows as a brownfield extension of our Stage 2 application.

---

## Technical Research & Subsystem Designs

### 1. SQLite Database Storage, Directory Initialization, and Schema Migration

We need to store completed game achievements permanently. The system must use Python's built-in `sqlite3` module and read its database path from `TETRIS_DB_PATH` (defaulting to `./data/high-scores.sqlite3`).

- **Decision**: 
  - On backend application startup (during the lifespan events / startup hook of FastAPI), retrieve `TETRIS_DB_PATH`.
  - Use `os.path.dirname` and `os.makedirs(..., exist_ok=True)` to safely initialize the parent directory if it does not exist.
  - Connect to the SQLite database and execute `PRAGMA journal_mode=WAL;` and `PRAGMA foreign_keys=ON;` to configure optimal write performance and safety.
  - Execute a schema initialization query (`CREATE TABLE IF NOT EXISTS high_scores (...)`) with constraints:
    - `game_id` TEXT PRIMARY KEY (UUID format, unique)
    - `score` INTEGER NOT NULL (>= 0)
    - `total_lines` INTEGER NOT NULL (>= 0)
    - `level` INTEGER NOT NULL (>= 1)
    - `completed_at` TEXT NOT NULL (UTC ISO-8601 string, e.g., `YYYY-MM-DDTHH:MM:SSZ`)
- **Rationale**: 
  - Using standard `sqlite3` ensures zero external runtime database dependencies (excluding PostgreSQL or external processes) and guarantees instant local functionality.
  - Initializing on startup prevents runtime crashes from missing tables or missing folders.
  - Using Write-Ahead Logging (WAL) significantly reduces lock contention and improves reliability in concurrent single-process reads/writes.
- **Alternatives Considered**:
  - *SQLAlchemy / Tortoise ORM*: Rejected to minimize dependency overhead and keep database interaction simple, direct, and token-efficient.
  - *PostgreSQL / MySQL*: Explicitly excluded by the Stage 3 scope.

---

### 2. State-Mutation and Finalization Thread-Safety (Race Protection)

In a single-process, one-worker Uvicorn backend, requests are processed using synchronous standard `def` functions, which FastAPI executes in an external thread pool (`anyio`). This introduces race conditions if multiple requests target the same in-memory game session or try to finalize the same game concurrently.

- **Decision**: 
  - Introduce a global reentrant lock (`threading.RLock`) or a per-session lock dictionary to protect all mutating game session actions (`tick_session`, `move_session_piece`, `hold_session_piece`, and game over persistence).
  - Wrap these operations in a context manager:
    ```python
    import threading

    _session_lock = threading.Lock()

    def tick_session(session_id: str):
        with _session_lock:
            # retrieve session, compute next state, lock blocks, check for game-over
            # if game_over reached, immediately check if already finalized.
            # If not, persist to SQLite and mark session as finalized.
            # return updated state
    ```
  - Ensure that `GET` endpoints (`GET /api/games/{id}` and `GET /api/high-scores`) do NOT acquire the lock (unless inspecting session list) and are strictly read-only, never modifying in-memory state or triggering database write retries.
- **Rationale**: 
  - A thread-safe lock guarantees mutual exclusion across concurrent requests targeting the same session.
  - Relying solely on SQLite's database-level unique constraint or sequential writes would prevent duplicate database rows, but it would *not* protect the in-memory game state from being corrupted by simultaneous racing ticks/moves.
  - Serializing all mutations and finalization on the same thread-safe lock guarantees absolute correctness and prevents concurrency bugs.
- **Alternatives Considered**:
  - *Database-level locks only*: Rejected because in-memory game sessions reside outside the database, and concurrent threads could mutate the game state in memory while waiting on SQL locks.
  - *Asyncio locks*: Rejected because the existing endpoints are synchronous `def` running in threads, so `asyncio.Lock` would not provide thread-safety.

---

### 3. Rigorous Request Body Validation & Extra Field Rejection

Clients must not be able to forge game outcomes, submit client-supplied metadata, or inject arbitrary payloads.

- **Decision**: 
  - Configure `MoveRequest` and a new body schema for `POST /api/games` to strictly forbid extra fields using Pydantic's `extra="forbid"` model configuration (or Pydantic v2 `model_config = {"extra": "forbid"}`).
  - When creating a game, define an optional request body schema `CreateGameRequest` that has no fields, but has `model_config = {"extra": "forbid"}`:
    ```python
    class CreateGameRequest(BaseModel):
        model_config = {
            "extra": "forbid"
        }
    ```
  - Bind this schema to `POST /api/games` as an optional parameter. This accepts valid bodyless POSTs or an empty JSON body `{}`, but raises a `422 Unprocessable Entity` (a documented 4xx) if any extra fields (such as client-supplied scores, levels, or game-IDs) are included.
- **Rationale**: 
  - Forbidding extra fields at the Pydantic level prevents any forged inputs from passing the API boundary, protecting the server.
  - Using standard FastAPI/Pydantic validation returns a structured, documented 4xx response, keeping API compatibility.
- **Alternatives Considered**:
  - *Custom validation dictionary parsing*: Reimplementing extra key checking manually in the router. Rejected because declarative Pydantic schemas are more idiomatic, maintainable, and type-safe.

---

### 4. CORS Policy Configuration & Credentials Restrictions

A security-conscious application must configure a restrictive CORS policy that protects endpoints from unauthorized third-party cross-origin requests.

- **Decision**: 
  - Implement a configurable CORS policy using FastAPI's standard `CORSMiddleware`.
  - Read CORS allowed origins from an environment variable `TETRIS_CORS_ALLOWED_ORIGINS` (comma-separated strings, defaulting to empty or same-origin-only defaults).
  - Explicitly validate origins and set `allow_credentials=True` ONLY when the configured origins do not contain a wildcard `*`.
- **Rationale**: 
  - Prohibiting wildcard origins (`*`) with credentials is a foundational security mandate to prevent cross-origin credential leaks.
  - Reading from environment variables ensures deployment flexibility across development, staging, and production environments.
- **Alternatives Considered**:
  - *Hardcoded lists*: Rejected because different host port mappings in local development vs. Docker container networks require configurable origins.

---

### 5. Multi-Stage Non-Root Docker Packaging & Production Proxying

The containerized environment must be robust, secure, and easily reproducible using Docker Compose.

- **Decision**:
  - **Backend Dockerfile**: Uses a multi-stage Python alpine or slim build. Copies only production requirements, installs them, adds a non-root system user, and runs `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1` as that non-root user.
  - **Frontend Dockerfile**: Multi-stage build. Uses a Node.js stage to build the production Vite assets (`npm run build`), then copies the static output to a lightweight server stage (such as Nginx or a non-root custom node-static/Caddy server). It must run as a non-root user.
  - **Production Proxying**: Configure the frontend container to proxy `/api` requests directly to the backend service's internal hostname (e.g. `http://backend:8000/api`) within the Docker network, and expose only port 5183 of the frontend container on the host machine. Port 8000 is kept completely closed and internal.
  - **Named Volumes**: Map `./data` or the backend sqlite directory to a persistent named Docker volume (`tetris-high-scores-volume`) to persist database writes.
- **Rationale**: 
  - Operating containers as non-root reduces security vulnerability.
  - Restricting host port access to port 5183 prevents direct exposure of the backend service to the internet, forcing all client traffic to route through the secure proxy.
- **Alternatives Considered**:
  - *Single massive container*: Combining frontend and backend in one image. Rejected because separate service definitions are standard, allow clean health checks, and optimize scaling.

---

### 6. Playwright Chromium Rendering Performance & Cadence Benchmark

We need to verify frontend rendering performance under production builds objectively, ensuring visually smooth transitions.

- **Decision**:
  - Create a Node.js Playwright script under `frontend/tests/performance-benchmark.ts` using Playwright's Chromium driver in foreground mode (unless headless is forced by environment).
  - Configure viewport size to `1280x900` with device scale factor 1.
  - Run the benchmark in three distinct phases:
    1. **Warm-up**: Run 5 seconds of automated gameplay (using simulated keyboard events) to stabilize the browser JIT compiler and layout engine.
    2. **Measurement**: Run three independent 30-second trials.
    3. **Action Execution**: Programmatically dispatch actual input changes (`left`, `right`, `down`) and restart commands as necessary to maintain active gameplay.
  - Record the following independent parameters:
    - **Browser Frame Scheduling Cadence**: Use a custom `requestAnimationFrame` monitor inside the page to measure actual frame intervals and calculate median, p95, p99 intervals, and approximate FPS.
    - **Game DOM Updates**: Track the count of React component renders or board-grid updates by injecting a MutationObserver or a performance mark/measure event.
    - **API Transaction Timing**: Track times of roundtrips to the backend (tick, move, hold).
  - Output raw measurements and traces, and check against performance targets (scheduling rate >=55 FPS, p95 interval <=25 ms).
- **Rationale**: 
  - `requestAnimationFrame` (rAF) alone does not prove rendering throughput, physical display presentation, or causal input redraw, as browsers can schedule ticks without actually flushing layout or updating pixels if the DOM hasn't changed.
  - Separating scheduling cadence, actual DOM mutations, and API transaction latency is mandatory to deliver high-fidelity rendering measurements.
- **Alternatives Considered**:
  - *Standard Cypress / Vitest testing*: Inadequate for raw frame rendering tracing and physical browser JIT warm-up profiling.

---

### 7. Secret-Free GitHub Actions CI/CD Audits & Builds

A robust, secret-free automated testing pipeline ensures code quality and security without risking credential exposure.

- **Decision**:
  - Create a `.github/workflows/ci.yml` workflow pinning Python major version `3.11` and Node major version `24LTS`.
  - Install dependencies reproducibly using `requirements.txt` and `package-lock.json`.
  - Execute backend pytest (with `pytest-cov` for coverage reports).
  - Execute frontend unit tests and production Vite builds.
  - Execute security dependency audits (such as `pip-audit` / `safety` for Python, and `npm audit` for Node).
  - Run container build tests (`docker compose build` or docker build commands) to verify Dockerfiles compile without baking in secrets.
  - Clearly document that since push/dispatch is restricted, hosted runs are reported as not executed.
- **Rationale**: 
  - Pinning major software versions prevents pipeline breakages from upstream package updates.
  - Keeping the workflow secret-free allows anyone to run fork pull-requests securely and verifies all build and compilation paths locally.
- **Alternatives Considered**:
  - *Using repository secrets for container registry push*: Rejected as pushing or publishing runtime images is explicitly excluded by the Stage 3 scope.
