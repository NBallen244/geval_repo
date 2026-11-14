# Tasks: Persistent High Scores, Dockerization, Playwright Benchmarking, and CI

**Input**: Design documents from `/specs/003-tetris-stage3-option-a/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are requested in the specification. Therefore, explicit unit and integration test tasks are included and must be implemented before the respective features are completed.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/app/`, `frontend/src/`
- Paths below utilize specific files matching this structure.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic database environment structure

- [x] T001 Setup the SQLite database service file at `backend/app/services/database.py` to manage connections and handle `TETRIS_DB_PATH` environment variable configuration (defaulting to `./data/high-scores.sqlite3`).
- [x] T001B [P] Create fully pinned Python runtime requirements (in backend/requirements.txt) based on the production container reference and dev/audit installation requirements (in backend/requirements-dev.txt) for Python 3.11, keeping them reproducible and isolated.
- [x] T001C [P] Resolve Vite 6.4.4 advisory GHSA-8g5g-mxqh-grgj via compatible patched dependency/lock update in `frontend/package.json` and package-lock.json.
- [x] T002 Implement table initialization in `backend/app/services/database.py` with SQL schema containing constraints: `game_id TEXT PRIMARY KEY NOT NULL`, `score INTEGER NOT NULL CHECK(score >= 0)`, `total_lines INTEGER NOT NULL CHECK(total_lines >= 0)`, `level INTEGER NOT NULL CHECK(level >= 1)`, and `completed_at TEXT NOT NULL`, plus an index `idx_high_scores_leaderboard` on `(score DESC, completed_at ASC, game_id ASC)`.
- [x] T003 [P] Add directory verification logic in `backend/app/services/database.py` using `os.makedirs(..., exist_ok=True)` to safely construct the database parent directory on startup, and trigger this initialization within FastAPI's lifespan startup handler in `backend/app/main.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core synchronization, thread-safety structure, response copying, and strict validation middleware

- [x] T004 Define and implement a global thread-safety locking scheme (e.g. `threading.Lock`) in `backend/app/services/game_engine.py` to serialize all state mutations (tick, move, hold) and prevent concurrent request races in the single-process backend.
- [x] T005 Implement coherent session snapshotting in `backend/app/services/game_engine.py` to make a deep copy (e.g., `.model_copy(deep=True)`) of the `GameSessionSchema` under lock synchronization for read-only actions, ensuring `GET` operations do not inspect mutable live state outside protection.
- [x] T006 Ensure nested finalization does not reacquire a non-reentrant lock and deadlock by design (the lock is acquired once per mutating endpoint call and covers the whole state update and optional database write).
- [x] T007 [P] Configure strict input payload verification in `backend/app/models/schemas.py` using Pydantic v2 `extra="forbid"` on `CreateGameRequest` and `MoveRequest` to reject unexpected parameters inside POST requests with a 4xx error.

**Checkpoint**: Foundation ready - thread safety, strict model validation, and schema definitions are ready. Implementation of user stories can begin.

---

## Phase 3: User Story 1 - SQLite-Backed Persistent High Scores & Database Isolation (Priority: P1)

**Goal**: finished games (including zero scores) are permanently and reliably persisted on the backend server using an SQLite database once per UUID, thread-safely and atomically.

**Independent Test**: Complete a game via gravity, soft drop, or obstructed Hold, verify that a database transaction is immediately executed under the configured `TETRIS_DB_PATH`, and that the record survives a complete backend service kill and restart.

### Tests for User Story 1
- [x] T008 [P] [US1] Create unit tests in `backend/tests/unit/test_persistence_us1.py` to verify safe database parent directory creation, table initialization, and SQL-injection path-parameter rejections.
- [x] T009 [P] [US1] Create integration tests in `backend/tests/integration/test_api_us1.py` verifying that a game completing through natural gravity, soft-drop collision, or obstructed Hold (legal empty-firstHold or occupied-Hold obstruction) immediately executes the database write with correct snake_case fields.
- [x] T010 [P] [US1] Create integration tests in `backend/tests/integration/test_api_us1.py` verifying that a restart or abandoned game does not create a record, and that repeated terminal actions or concurrent finalization attempts do not duplicate or replace the original SQLite row or completion timestamp.

### Implementation for User Story 1
- [x] T011 [US1] Update `backend/app/services/game_engine.py` to maintain an in-memory `is_persisted` boolean flag per game session, preventing duplicate SQL executions.
- [x] T012 [US1] Implement parameterized SQL insertion inside `backend/app/services/database.py` to atomically persist completed games (recording game_id, score, total_lines, level, and completed_at in UTC ISO-8601).
- [x] T013 [US1] Integrate the finalization database write inside the synchronized state mutation block in `backend/app/services/game_engine.py` when a game reaches `"game_over"` status (through gravity tick, soft drop collision, or obstructed Hold).

**Checkpoint**: User Story 1 fully functional - game metrics successfully written to SQLite upon game over with strict thread-safe isolation.

---

## Phase 4: User Story 2 - Secure High-Scores REST API with Rigorous Body Validation (Priority: P2)

**Goal**: Expose a read-only leaderboard endpoint, enforce strict extra-key validation in request bodies, handle storage failures elegantly with controlled 503s, and support finalization retry.

**Independent Test**: Run manual API requests using cURL or HTTP client, confirm that any extra fields in payload (e.g. `POST /api/games` or `/api/games/{id}/move`) return a 422/400, unknown game returns 404, database failures during finalization produce a controlled 503 JSON response, and subsequent mutations retry persistence safely.

### Tests for User Story 2
- [x] T014 [P] [US2] Create integration tests in `backend/tests/integration/test_api_us2.py` verifying extra field rejection in game creation and move bodies, invalid movement direction 4xx rejection, and unknown game 404.
- [x] T015 [P] [US2] Create integration tests in `backend/tests/integration/test_api_us2.py` simulating database locking/storage failures and verifying that a controlled 503 JSON response is returned without leaking SQL, files, or tracebacks, and that subsequent mutations on the dead game retry persistence while GET never does.
- [x] T016 [P] [US2] Create unit tests in `backend/tests/unit/test_persistence_us1.py` verifying that the leaderboard database read correctly orders scores descending, then completed_at ascending, then game_id lexicographically ascending.

### Implementation for User Story 2
- [x] T017 [US2] Implement `GET /api/high-scores` endpoint in `backend/app/api/endpoints.py` returning at most 10 sorted high scores based on sorting rules (score DESC, completed_at ASC, game_id ASC). Note: Mount this endpoint outside the inherited `/api/games` router prefix.
- [x] T018 [US2] Enforce strict Pydantic extra key validation in `backend/app/api/endpoints.py` for `POST /api/games` and `POST /api/games/{id}/move` using `CreateGameRequest` and `MoveRequest` to reject any extra fields.
- [x] T019 [US2] Add try/catch blocks inside `backend/app/api/endpoints.py` for 503 error handling, raising `HTTPException(status_code=503)` with a sanitized error message and hiding SQL exceptions.
- [x] T020 [US2] Implement safe retry logic in `backend/app/services/game_engine.py` allowing subsequent mutating operations on a terminal game session to retry database persistence if `is_persisted` is `False`.

**Checkpoint**: REST API is completely secure, leaderboard is sort-deterministic, extra payloads are blocked, and storage failures are gracefully handled.

---

## Phase 5: User Story 3 - High Scores UI Panel and Stale-Response Protection (Priority: P2)

**Goal**: Display a modern High Scores visual panel in the frontend that renders leaderboard data with loading, empty, and error fallbacks, stale-response protection, and configurable API base proxying.

**Independent Test**: Open the web application, see the leaderboard panel loading, view empty state ("No high scores yet"), complete a game, and observe the high score panel refresh instantly with the new score. Verify that rapid restarts do not result in stale data rendering.

### Tests for User Story 3
- [x] T021 [P] [US3] Create unit tests in `frontend/tests/HighScoresPanel.test.tsx` to verify loading indicator, empty table state, populated table state, and error message rendering.
- [x] T022 [P] [US3] Create integration tests in `frontend/tests/useGame.test.ts` to verify stale-response protection (out-of-order API responses are discarded) and that the high-score list is fetched on startup and once game over is hit, without polling on gravity ticks.

### Implementation for User Story 3
- [x] T023 [US3] Create the leaderboard component at `frontend/src/components/HighScoresPanel.tsx` that maps rows containing rank, score, lines, and level.
- [x] T024 [US3] Implement leaderboard state hook in `frontend/src/hooks/useGame.ts` to fetch `/api/high-scores` on initial load and after game over.
- [x] T025 [US3] Implement stale-response protection in `frontend/src/hooks/useGame.ts` by tracking request sequence IDs (or timestamps) and discarding out-of-order HTTP responses.
- [x] T026 [US3] Integrate `HighScoresPanel` into the main application layout in `frontend/src/App.tsx`.
- [x] T027 [US3] Define a configurable API base URL (defaulting to `/api` for same-origin proxying) in `frontend/vite.config.ts` or environment settings, avoiding hardcoded localhost URLs.
- [x] T028 [US3] Define and document a restrictive CORS policy in `backend/app/main.py` allowing configurable origins via environment variables, and disabling wildcard `*` with credentials.

**Checkpoint**: Leaderboard visual panel is complete, integrated, handles errors and stale results, and uses configurable same-origin API bases.

---

## Phase 6: User Story 4 - High-Performance Containerized Packaging (Priority: P3)

**Goal**: Provide reproducible Docker packaging using Compose, non-root users, persistent named volumes for SQLite, closed backend ports, and health checks.

**Independent Test**: Build and run using `docker compose up --build -d`. Access port 5183, play a game, write a score, run `docker compose down`, run `docker compose up -d`, and verify that the high score persists. Verify that backend port 8000 is blocked on the host.

### Implementation for User Story 4
- [x] T029 Create `.dockerignore` to exclude all development environments, local caches, node_modules, `.env` files, and researcher/private homes from build context.
- [x] T030 Create backend `Dockerfile` using multi-stage Python 3.11 base, installing production dependencies, mapping SQLite directory, configuring non-root user execution, and setting Uvicorn to run with 1 worker.
- [x] T031 Create frontend `Dockerfile` using multi-stage Node 24LTS base to compile production static build and serve it using a lightweight non-root static server proxying `/api` requests to backend internal host.
- [x] T032 Create `docker-compose.yml` to define frontend on host port 5183, keep backend completely internal, configure SQLite write directories with a named volume `tetris-high-scores-volume`, and add lightweight, non-intrusive container health checks.
- [x] T032B [US4] Implement and verify actual clean-volume ownership, write, and persistence confirmation procedures to prove that SQLite high scores are correctly retained when containers are recreated.
- [x] T033 [P] Document exact build, start, stop, down/up persistence-verification, container user checks, image sizes, and real build stopwatch/cache disclosure instructions in `specs/003-tetris-stage3-option-a/quickstart.md`.

**Checkpoint**: Docker Compose runs the multi-tier application securely with non-root privileges, persistent volumes, and locked-down ports.

---

## Phase 7: User Story 5 - Automated Browser Performance Benchmarking & CI Pipeline (Priority: P4)

**Goal**: Create an executable Playwright Chromium benchmark against the production frontend measuring frames scheduling, DOM mutations, and API timing; establish a secret-free GitHub Actions CI pipeline running backend/frontend tests and audits.

**Independent Test**: Execute the Playwright performance test locally, verifying it launches a foreground 1280x900 Chromium browser, performs 5s warm-up and 3 independent 30s runs, collects intervals and mutations, checks scheduling cadence thresholds, and outputs trace evidence.

### Implementation for User Story 5
- [x] T034 Create or update the performance benchmark script at `frontend/tests/performance-benchmark.ts` using Playwright Chromium to launch a visible foreground browser at 1280x900, device scale factor 1, targeting a recorded 60 Hz layout. Explicitly set `chromiumSandbox: true` in EVERY browser launch branch, record full configuration in raw metadata, and never use `--no-sandbox` or silent fallback overrides.
- [x] T034B [US5] Install and lock Playwright dev dependency cleanly in frontend package.json, and provide a runnable manual benchmark command for execution outside standard CI.
- [x] T035 Implement raw interval logging (using an independent in-page `requestAnimationFrame` sampler owned by the external benchmark harness, NOT a permanent app loop), board DOM mutation counts (via `MutationObserver`), action-latency samples with causal mapping, and API timing/failures.
- [x] T036 Configure the benchmark script to run a separate 5-second warm-up and a fixed 30-second measurement window for *each* of the three independent runs, continuously monitoring and recording page visibility and focus throughout (retaining a snapshot of visibility and focus after EACH collector reset, at the start and end of each trial, and all visibility/focus events, proving zero focus loss).
- [x] T037 Establish a single declared in-page timeline per trial (`warmupStart = now`, `warmupEnd = warmupStart + 5000`, `measurementStart = warmupEnd`, `declaredEnd = measurementStart + 30000`). Freeze buffers precisely at `declaredEnd` before any trace/screenshot I/O. Record `observedWarmupStop` and `observedStop` separately. Classify samples by their clock bounds. Zero/nonpositive intervals are explicitly ineligible. Save all evidence (traces, screenshots, raw JSON, summary) under a unique, non-overwriting attempt directory named with a UTC timestamp and random ID. If the destination directory already exists, fail or allocate a new directory.
- [x] T038 [S3-CI-01] [S3-CI-02] Create `.github/workflows/ci.yml` pinning Python `3.11` and Node `24LTS` to run backend tests and coverage, frontend tests, production build, unsuppressed basic security audits (`npm audit` and `pip-audit` without suppressing GHSA-vv3r-rc64-8847), and Docker image builds without secrets, using pinned dependencies.
- [x] T039 [P] Document performance run manual command, test targets, unsupported environment handling, and GHA setup details in `specs/003-tetris-stage3-option-a/quickstart.md` or a dedicated perf workflow file.

**Checkpoint**: Performance benchmark script collects rich frame/DOM/API data, and the automated CI workflow validates backend/frontend builds on every commit.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: High-quality document cleanup, style unification, and final verification checks

- [x] T040 [P] Standardize all error handling, logging messages, code comments, and test scripts to use English exclusively.
- [x] T041 Review and verify that all Stage 1 and Stage 2 files, tests, and specifications under `specs/001-build-tetris-core/` and `specs/002-extend-tetris-stage2/` remain completely untouched and unmodified.
- [x] T042 Validate all Stage 3 task implementations locally by running unit/integration tests and verifying that the final task coverage matches requirements perfectly.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all subsequent user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
  - User Story 1 (P1) is the core database persistence feature. It must be completed before other stories.
  - User Story 2 (P2, API) depends on User Story 1 (Database) completion.
  - User Story 3 (P2, UI) depends on User Story 2 (API) completion.
  - User Story 4 (P3, Docker) depends on User Stories 1-3 completion.
  - User Story 5 (P4, Perf & CI) depends on User Stories 1-4 completion.
- **Polish (Final Phase)**: Depends on all user stories being complete.

### Within Each User Story

- Test files MUST be written and fail before writing actual feature implementations (TDD).
- Database models and schema structures before service logic.
- Services and operations before router endpoint integration.
- Backend API endpoints before frontend component integration.

---

## Parallel Execution Examples

### Parallel Example 1: Schema & Environment Setup (Phase 1)
```powershell
# Both tasks are independent and can be written in parallel
Task T001: "Setup the SQLite database service file at backend/app/services/database.py"
Task T003: "Add directory verification logic in backend/app/services/database.py"
```

### Parallel Example 2: API Request Validation & Testing (Phase 4)
```powershell
# While implementing API endpoints, write tests and handlers concurrently
Task T014: "Create integration tests in backend/tests/integration/test_api_us2.py verifying extra field rejection"
Task T016: "Create unit tests in backend/tests/unit/test_persistence_us1.py verifying database read ordering"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Implement Phase 3 (User Story 1 - Database Persistence).
3. **STOP and VALIDATE**: Spin up the backend, run `pytest`, and verify a dead game writes its final score immediately into SQLite at `./data/high-scores.sqlite3` and survives restarts.

### Incremental Delivery

1. **Step 1**: SQLite database setup and local game state locking/synchronization complete.
2. **Step 2**: Add Leaderboard API and strict payload validation (reject extra keys) -> Verify via automated cURL.
3. **Step 3**: Introduce Frontend Leaderboard visual panel with loading/empty states -> Verify visually in browser.
4. **Step 4**: Dockerize backend/frontend and setup Compose network -> Verify port isolation and persistent volume.
5. **Step 5**: Write Playwright Chromium rendering benchmark and establish GitHub Actions CI -> Verify frame metrics report and CI build.
6. **Step 6**: Execute final audits, linting checks, and documentation polish.
