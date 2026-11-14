---
title: "Product Requirements Document: Stage 3 Tetris Study (Option A)"
status: final
created: 2026-11-02T12:17
updated: 2026-11-02T12:17
---

# PRD: Stage 3 Tetris Study (Option A)

## 0. Document Purpose
This Product Requirements Document (PRD) outlines the behavioral, functional, and user-experience requirements for Stage 3 (Option A) of the Tetris Study. This phase represents a brownfield extension of our decoupled client-server Tetris application. It introduces persistent SQLite high scores, environment-configurable API bases, robust Docker containerization, a Playwright-driven browser performance benchmark, and a GitHub Actions continuous-integration pipeline.

This document builds directly upon the Stage 2 specifications (`_bmad-output/stage2/planning-artifacts/prds/prd-stage2-option-a/prd.md`) and the original Stage 1 baseline. It maintains Glossary-anchored terminology, stable Functional IDs, and explicit user journeys, designed to maintain full backward compatibility with all original regression assertions and client-server REST API contracts.

---

## 1. Vision
The core design principle of the Tetris Study is a strictly decoupled, stateless React client driven by an authoritative, single-process Python FastAPI backend. Stage 3 completes this architectural blueprint by adding persistent, high-integrity data storage and full-lifecycle operational scaffolding.

High score tracking must be completely authoritative, with game scores validated, finalized, and persisted in SQLite strictly on game over. The entire transaction is protected from race conditions via single-process mutex locks. This release also establishes high-quality, production-ready local deployment using multi-stage Docker packaging, non-root isolation, and automated performance verification using Playwright to empirically measure frame rendering and input latency under active gameplay.

---

## 2. Target User

### 2.1 Jobs To Be Done
- **High Score Validation (Functional):** As a Study Reviewer, I want a reliable leaderboard that records every completed game exactly once without double-submissions or client metadata injection.
- **Resilience Reviewing (Functional/Technical):** As a Software Architect, I want to confirm that backend database lock failures or disk-full states produce clean, controlled 503 responses without crashing the engine, and that client mutations can retry finalization safely.
- **Performance Benchmarking (Contextual):** As a QA Engineer, I want an executable Playwright browser performance benchmark that tests real DOM updates, frame scheduling rates, and input latency under active physical play.
- **Reproducible Deployments (Operational):** As a DevOps Engineer, I want to build and run backend and frontend non-root containers using Docker Compose, storing database files in a mounted persistent volume.

### 2.2 Non-Users (v1)
- **Rotation-seeking Gamer:** A player seeking piece rotation, wall kicks, or complex spin setups. This remains strictly out of scope for Stage 3.
- **Multiplayer/Social Gamer:** A user looking for real-time multiplayer, global cloud leaderboards, or player name registration.

### 2.3 Key User Journeys
*Note: The following user journeys utilize illustrative personae and scenarios to describe designed operational paths, and are not intended to represent actual historic individuals or absolute security guarantees.*

- - **UJ-6: Priya completes a high-scoring game and views the leaderboard**
  - **Persona + context:** Priya, a QA Engineer evaluating backend-to-frontend high score finalization.
  - **Entry state:** Game is active with status `"playing"`. The board is nearly full. Priya has scored 1200 points.
  - **Path:**
    1. Priya drops her active piece, which locks at the top of the grid and triggers an Obstructed Spawn game over.
    2. The backend intercepts the lock event, transitions `status` to `"game_over"`, sets `active_piece` to `null`, and automatically executes an atomic parameterized transaction to insert a new high-score record (`game_id`, `score`, `total_lines`, `level`, `completed_at` in UTC) into the SQLite database.
    3. The frontend receives the terminal `GameState` response, clears the gravity timer, displays the "Game Over" message, and immediately dispatches a request to `GET /api/high-scores`.
  - **Climax:** Priya sees her game's score, cleared lines, and level immediately appear in the frontend High Scores panel at the correct descending rank position, without having to enter her name.
  - **Resolution:** Priya clicks "Restart", starting a clean in-memory game. She confirms that restarting does not write any abandoned or partial scores to the database.

- **UJ-7: Winston simulates database write failures during game over**
  - **Persona + context:** Winston, a software architect reviewing resilience and error-handling.
  - **Entry state:** Game is active with status `"playing"`. The database file is temporarily marked read-only or the SQLite volume is locked.
  - **Path:**
    1. Winston triggers a move that results in game over.
    2. The backend transitions the game to `"game_over"`, but the database insert fails, throwing a database lock error.
    3. The backend catches the exception, rolls back, and returns a controlled `HTTP 503 Service Unavailable` JSON response with a safe message (`"High score storage temporarily unavailable"`), without leaking file paths or SQL details.
    4. The client UI displays an error state in the High Scores panel.
    5. Winston triggers another mutating request on that same terminal game (e.g. sending a manual `POST /api/games/{id}/tick` or movement).
    6. The backend interceptor recognizes that the game is in `"game_over"` but its database record is still unpersisted. It retries the SQLite write transaction under a process-wide mutex.
  - **Climax:** The SQLite database lock is now cleared. The retry succeeds, inserting the record safely. The backend returns `200 OK` with the terminal state.
  - **Resolution:** The frontend updates, fetches the leaderboard, and displays Winston's score correctly.

---

## 3. Glossary
- **High Score Record** — An immutable persisted record containing `game_id` (UUID), `score` (integer), `total_lines` (integer), `level` (integer), and `completed_at` (UTC ISO-8601 string) indicating a completed Tetris game.
- **Leaderboard** — A sorted list of at most ten High Score Records returned by the backend, ordered by score descending, then completed_at ascending, and finally game_id ascending.
- **Database File** — A local SQLite database file located at `TETRIS_DB_PATH` used to persist high scores.
- **Atomic Snapshot** — A single database transaction executing parameterized SQL queries to ensure a record is fully written or rolled back safely, preventing partial database updates.
- **Single-Process Lock** — An in-memory process-wide reentrant lock (`threading.RLock`) in the FastAPI application that synchronizes all state registry creation, lookup, mutation, database persistence, and detached state responses, ensuring thread safety within the threadpool of our single-worker server.
- **Same-Origin Proxy** — A reverse proxy configuration in Vite (or Nginx in production) that maps `/api/*` requests from the frontend port to the backend API port, avoiding hardcoded localhost URLs.
- **Frame Scheduling Rate** — The actual rate at which game frames are scheduled for rendering, measured via a browser's `requestAnimationFrame` (rAF) callbacks during a performance test.
- **Multi-Stage Build** — A Dockerfile design separating build-time environments (with dev dependencies and compilers) from production runtimes, keeping deployment images lean.
- **Non-root user** — A restricted container user account (UID != 0) that runs the application process, preventing privilege-escalation vulnerabilities in Docker.

---

## 4. Features

### 4.1 Persistent SQLite High Scores Database
**Description:** Automates high-score storage upon game over using an embedded SQLite database, protecting data integrity from race conditions and exposing a strict leaderboard. Realizes UJ-6, UJ-7.

**Functional Requirements:**

#### FR-55: Persistent Database Path and Initialization
The backend must read the environment variable `TETRIS_DB_PATH` (defaulting to `./data/high-scores.sqlite3`) and safely initialize the database file, creating its parent directories and the required high scores table with appropriate columns and constraints on service startup.
- *Consequence:* If the parent directory is missing (e.g. `./data`), the application creates it automatically during startup. Schema creation is idempotent.

#### FR-56: High Score Eligibility
A game score is eligible for leaderboard persistence only when its authoritative backend game state transitions to game over (due to gravity, soft drop, or obstructed Hold).
- *Consequence:* Active or abandoned live games, and restarting an active game, must never insert records. Completed games with a score of zero (0) are fully eligible and must be saved.

#### FR-57: Uniqueness and Atomic Writes
The backend must write high scores using atomic parameterized SQL writes. A unique constraint must be enforced on the `game_id` column.
- *Consequence:* The `completed_at` timestamp is assigned exactly once on the first game over event and retained through any subsequent 503/retries. Database conflicts or subsequent terminal mutations must never overwrite or duplicate original records or alter the original completion timestamp.

#### FR-58: Single-Process Backend RLock Thread Synchronization
To protect against race conditions under concurrent requests within the single-process backend threadpool (due to FastAPI executing `def` handlers in separate worker threads), state registry creation, game state lookup, mutation, database persistence, and detached response snapshotting must be synchronized under a process-wide reentrant lock (`threading.RLock`).
- *Consequence:* Active games remain in memory (un-persisted during active play), but all completed scores survive process restarts. Only one thread can perform any registry operations, state transitions, or SQLite transactions at any given time, ensuring complete thread-safety.

#### FR-59: High Scores Retrieval Endpoint (`GET /api/high-scores`)
The backend shall expose an endpoint `GET /api/high-scores` that returns a JSON payload containing an array of at most ten scores, ordered by:
1. `score` descending,
2. `completed_at` ascending,
3. `game_id` ascending.
- *Consequence:* This endpoint is read-only and must perform exactly zero (0) mutations, state saves, or database writes. To prevent concurrent mutation side-effects during reads, it must acquire the same `threading.RLock` to retrieve a consistent, write-free snapshot of the leaderboard. No public API endpoint shall accept user-supplied scores or arbitrary IDs for manual inserts.

#### FR-60: Strict Request Payload Validation
All game state mutation endpoints (such as `POST /api/games` for creation, and move/hold/tick endpoints) must perform strict validation:
- The game creation endpoint must reject extra fields in the request body (returning `422 Unprocessable Entity`), while continuing to accept valid bodyless calls.
- Movement request bodies must reject extra fields, while continuing to accept valid movement bodies.
- An invalid movement direction must return a documented 4xx error. An unknown game ID must return a documented `404 Not Found`.

#### FR-61: Storage Error Handling (HTTP 503)
If a database transaction fails (due to database locks, disk-full, file write permissions, or any startup/connect/query/write/cleanup failures), the backend must return a controlled `HTTP 503 Service Unavailable` JSON response.
- *Consequence:* The response must hide file paths, SQL syntax, or stack traces, return a clean error message, and preserve game state in-memory. Connection and startup failures must be handled gracefully to prevent app crashes.

#### FR-62: Terminal Persistence Failure Mutation Retry
If finalization and database insertion fail on game over, a subsequent mutating request (such as a tick or move) sent to that terminal game must safely retry the database write under the process `threading.RLock`, using its existing state.
- *Consequence:* If the database becomes writable again, the score is successfully saved. A `GET` request on the game state must never perform or trigger this database retry.

---

### 4.2 Frontend High Scores Integration
**Description:** Displays the high scores board in a modern React panel, matching the theme and responding immediately to gameplay events without polling. Realizes UJ-6.

**Functional Requirements:**

#### FR-63: High Scores Panel Display
The frontend must render a "High Scores" panel showing `score`, `lines`, and `level` for each leaderboard entry.
- **Loading, Empty, and Error States:** The panel must support explicit rendering for:
  1. *Loading:* Indicated visually while fetching the leaderboard.
  2. *Empty:* Indicated visually if no high scores are recorded in the database.
  3. *Error:* Indicated visually if the leaderboard request fails or returns a 503 error.
- **Fetch Triggers:** The frontend fetches the leaderboard on initial application load and immediately after a game-over event. It must not poll the backend on every gravity tick.

#### FR-64: Configurable Same-Origin API Base
The frontend must use a configurable API base URL that defaults to same-origin `/api` (meaning it automatically targets the same host and port serving the frontend, proxied via Vite/Docker).
- *Consequence:* Production deployments do not hardcode a `localhost` URL, making the bundle fully portable across Docker containers. Note that since VITE env variables are evaluated at compile-time and do not change a compiled static production bundle at runtime, dynamic routing must rely on the same-origin reverse-proxy.

#### FR-65: Restrictive Configurable CORS Policy
The backend must define and enforce a configurable, restrictive CORS policy on startup. No wildcard origins (`*`) are allowed if credentials are enabled.
- *Consequence:* The policy must align with security standards, restricting requests to authorized domains.

---

### 4.3 Containerized Runtime and Local Deployment
**Description:** Package the backend and frontend into standardized, non-root Docker images to enable reproducible multi-service orchestration. Realizes JTBD.

**Functional Requirements:**

#### FR-66: Reproducible Multi-Stage Docker Packaging
The project must include multi-stage Dockerfiles for both services:
1. **Frontend Image:** Runs as a non-root user, serves the compiled production build, and reverse-proxies `/api` requests to the internal backend.
2. **Backend Image:** Runs as a non-root user, installs production dependencies, and hosts the FastAPI server with a single worker.
- *Consequence:* Development-only dependencies, local compilers, and credential secrets must not be baked into the final runtime images. Dockerfiles must use context-specific ignores (`.dockerignore`) to prevent copying dev artifacts, and copy only production-only dependencies.

#### FR-67: Docker Compose Orchestration
The local runtime is managed via Docker Compose (`docker-compose.yml` or `compose.yaml`):
1. **Port Isolation:** Only the frontend port is published on host `5183` (`127.0.0.1:5183` or `0.0.0.0:5183`). The backend remains internal and unreachable from the public host.
2. **SQLite Persistence Volume:** A named volume (e.g. `tetris_sqlite_data`) with read-write permissions is mounted to the backend's non-root writable SQLite storage directory to persist database entries across container restarts.
3. **Health Checks:** Container startup order and status are validated using built-in Docker health checks with installed health tools (like curl).
4. **Data Protection Guardrail:** Running `docker compose down` must never destroy or delete the persistent database volume unless `-v` is explicitly called, and the workflow documentation must explicitly warn against destructive commands.

---

### 4.4 Playwright Browser Performance Benchmarking
**Description:** Automated client performance testing under active gameplay to ensure consistent frame rates and low latency. Realizes JTBD.

**Functional Requirements:**

#### FR-68: Reproducible Playwright Performance Script
The codebase must provide an automated Playwright Chromium performance benchmark executing three independent runs under the following strict conditions:
1. **Scenario Parameters:** Foreground visible browser, viewport `1280x900`, device scale factor 1, targeting a 60 Hz display frequency. 60Hz is a reference, not physical-presentation proof.
2. **Execution Timing:** Each run executes a 5-second gameplay warm-up, followed by 30 seconds of monotonic measurement.
3. **Continuous Actions:** The script simulates physical movements (ArrowLeft, ArrowRight, ArrowDown) and restart triggers as needed to maintain active gameplay without crashing or stopping.
4. **Isolated Frame Analysis:** The script records actual frame intervals (via `requestAnimationFrame` timestamps), DOM mutation/update counts, and action-to-visible-update latency. It must not rely on simple CPU timers. Eligible positive intervals are counted only if BOTH of their endpoints fall inside the fixed 5000+30000ms window (i.e., from t = 5,000ms to t = 35,000ms).
5. **Operational Targets:** The mean frame scheduling rate (calculated strictly as `frame_count / 30s`, not based on median FPS) must be `>= 55 FPS`, and the `p95` frame interval must be `<= 25 ms` in every run (representing standard tolerances for 60 Hz environments) across three independent unrounded contexts, with immutable whole unique batches and collision refusal.
- *Consequence:* Benchmark execution must not modify game gravity, use Canvas/WebGL migrations, rotate pieces, or spam more than 60 API requests per second to artificially boost metrics. No heavy checks are run concurrently with timing. Foreground/focus events, actual measured browser version, interval classifications, raw DOM/keyboard/API/heuristic latency, screenshots, and traces are fully logged. Unsupported environments must be reported honestly.

---

### 4.5 GitHub Actions Continuous Integration (CI)
**Description:** Automates testing, security auditing, and compilation verification on every push. Realizes JTBD.

**Functional Requirements:**

#### FR-69: Continuous Integration Pipeline
The repository must contain a `.github/workflows/ci.yml` pipeline that executes automatically:
1. **Platform Matrix & Pinning:** Pins Node (major 20) and Python (major 3.11) matching verified local setups.
2. **Dependency Management:** Performs clean, reproducible installations in actual working directories using lockfiles (e.g., `package-lock.json`, `requirements.txt`).
3. **Backend Quality Gates:** Runs unit tests via pytest, measures code coverage, and audits dependencies for security vulnerabilities using supported public audits.
4. **Frontend Quality Gates:** Runs unit tests via `npm run test` (vitest run) and verifies compilation by running the production build (`npm run build`).
5. **Docker Build Checks:** Builds the Docker images to confirm that multi-stage compilation completes without errors.
- *Consequence:* The workflow must run entirely without requiring private tokens, secrets, or cloud environments. Simple security checks do not use broad bypasses like `|| true`.

---

## 5. Non-Goals (Explicit)
- **Piece Rotation & SRS:** Standard rotation remains completely out of scope.
- **Ghost Piece Preview:** No shadow or projection of where the piece will land.
- **PostgreSQL Migration:** SQLite remains the sole database engine; no migration to larger database management systems (RDBMS) is authorized.
- **Player Authentication:** No user profiles, login, or session tracking are included.
- **Hosted Cloud Deployment:** Continuous deployment (CD) or hosting on external cloud environments (AWS, GCP, Vercel) is out of scope.

---

## 6. MVP Scope

### 6.1 In Scope
- SQLite backend initialization at startup, reading `TETRIS_DB_PATH`.
- Atomic, parameterized high-score saves when game state reaches `"game_over"`.
- Single-process RLock thread synchronization to prevent race conditions during state mutation and database finalization.
- REST endpoint `GET /api/high-scores` returning top 10 scores.
- Frontend High Scores sidebar panel with loading, empty, and error states.
- Portable same-origin `/api` proxy config for Vite and Docker Compose.
- Multi-stage Dockerfiles running as non-root on port 5183.
- Playwright Chromium performance benchmark reporting unrounded frame metrics.
- Pinned GitHub Actions workflow file.

### 6.2 Out of Scope for MVP
- Storing player names or custom avatars on the leaderboard.
- Real-time global WebSocket-based leaderboards.
- Canvas/WebGL rendering (retains pure React 10-by-20 grid rendering).

---

## 7. Success Metrics
- **SM-5 (Leaderboard Accuracy):** Target of 100% of validated valid leaderboard requests return at most 10 records, correctly sorted by score descending, completed_at ascending, and game_id ascending.
- **SM-6 (Uniqueness Enforcement):** Zero duplicate high-score records can be created for any given unique `game_id`.
- **SM-7 (Controlled Failures):** Storage write failures trigger clean HTTP 503 JSON responses, keeping in-memory gameplay state un-corrupted and retriable.
- **SM-8 (Performance Fidelity):** Automated Playwright performance tests demonstrate mean frame scheduling rates `>= 55 FPS` and `p95` frame intervals `<= 25 ms` across three independent 30-second trials.

---

## 8. Open Questions
1. **Should the leaderboard fetch support pagination?**
   *Decision:* No. The leaderboard is strictly limited to the top 10 scores. No pagination query parameters are required or supported.
2. **What happens to active games when the Docker container restarts?**
   *Decision:* Active games reside strictly in memory and are not resumed after process restart. The High Scores list, however, is persisted on disk and fully survives container restarts.

---

## 9. Assumptions Index
- **[ASSUMPTION-8]**: The `TETRIS_DB_PATH` directory is writable by the non-root backend Docker user.
- **[ASSUMPTION-9]**: The Playwright benchmark runs in a sandboxed, hardware-accelerated local or self-hosted runner; headless/foreground execution differences are logged truthfully.
- **[ASSUMPTION-10]**: Pinned dependencies in lockfiles ensure identical environment replication in both local runs and CI pipelines.
