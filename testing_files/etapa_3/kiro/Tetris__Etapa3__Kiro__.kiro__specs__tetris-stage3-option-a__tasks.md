# Implementation Plan: Tetris Stage 3 Option A

## Overview

This plan turns the approved Stage 3 design into an incremental, test-driven set of coding tasks for the brownfield extension of the existing Stage 2 backend (`backend/app`, Python + FastAPI) and frontend (`frontend/src`, React + TypeScript). The work builds from the persistence module outward: SQLite high-score store, finalization service and in-memory `Game` bookkeeping, controller wiring with the controlled 503, the leaderboard endpoint and strict body validation, CORS and startup wiring, the frontend API base and High Scores panel, Docker packaging, the Playwright benchmark harness, and the CI workflows.

The engine (`app/rules/engine.py`, `app/rules/pieces.py`, `app/rules/scoring.py`) stays pure and unchanged. The inherited specs under `.kiro/specs/tetris-stage1-option-a/` and `.kiro/specs/tetris-stage2-option-a/` are never edited. Each task references the file(s) from the design and the requirement clauses it satisfies. Test-authoring sub-tasks sit next to or before the code they verify. Every task is left unchecked; no command is executed as part of this planning phase.

## Tasks

- [x] 1. Implement the SQLite high-score persistence module
  - [x] 1.1 Create `HighScoreRecord` carrier and `HighScoreStore` skeleton in `backend/app/persistence/store.py`
    - Create the `app/persistence/` package (`__init__.py`) and `app/persistence/store.py`
    - Define the frozen dataclass `HighScoreRecord` with exactly `game_id`, `score`, `total_lines`, `level`, `completed_at`
    - Define the `StorageError` exception whose string form carries no sensitive detail forwarded to clients
    - Define the `HighScoreStore` class with `__init__(db_path)`, `from_env`, `initialize`, `finalize`, `top_ten` signatures
    - _Requirements: 1.7, 2.3, 7.5_
  - [x] 1.2 Implement path resolution and safe startup in `HighScoreStore`
    - Implement `from_env` to read `TETRIS_DB_PATH`, defaulting to `./data/high-scores.sqlite3` when unset or empty
    - Implement `initialize` to create the parent directory with `os.makedirs(parent, exist_ok=True)` before opening the connection, then run `CREATE TABLE IF NOT EXISTS high_scores (...)` with a `UNIQUE(game_id)` constraint and the five columns, leaving existing rows untouched
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 4.4_
  - [x] 1.3 Implement atomic `finalize` write in `HighScoreStore`
    - Use a single parameterized `INSERT` inside one transaction (`with connection:`) so failure rolls back and no partial row persists
    - Return `True` on insert; catch `sqlite3.IntegrityError` from the `UNIQUE(game_id)` constraint and return `False` (idempotent duplicate, not an error)
    - Raise `StorageError` for any other failure, leaving no partial row
    - _Requirements: 2.1, 2.5, 2.9, 3.2, 7.2_
  - [x] 1.4 Implement read-only `top_ten` in `HighScoreStore`
    - Issue a single `SELECT ... ORDER BY score DESC, completed_at ASC, game_id ASC LIMIT 10` and map rows to `HighScoreRecord`
    - Perform no write; raise `StorageError` on any failure
    - _Requirements: 3.4, 5.2, 5.3, 7.1_
  - [x] 1.5 Write unit tests for startup, schema, and persistence durability in `backend/tests/test_stage3_store.py`
    - Assert `initialize` creates a missing parent directory and the schema, leaves existing rows intact on re-init, and enforces `UNIQUE(game_id)`
    - Assert a freshly constructed `HighScoreStore` opening the same database file reads previously persisted rows without reinitializing or clearing them
    - _Requirements: 1.3, 1.4, 1.5, 1.6, 4.1, 4.4, 17.6_
  - [x] 1.6 Write unit tests for tie-break ordering and the ten-row cap in `backend/tests/test_stage3_store.py`
    - Assert equal `score` values order by `completed_at` ascending then `game_id` ascending, and the result is capped at ten
    - _Requirements: 5.2, 5.3, 17.2_

- [x] 2. Add in-memory finalization bookkeeping to the `Game` model
  - [x] 2.1 Extend `Game` in `backend/app/domain/models.py`
    - Add in-memory-only fields: `finalized: bool = False`, `pending_finalization: bool = False`, `completed_at: Optional[str] = None`, and `finalization_record: Optional[HighScoreRecord] = None` (an immutable/frozen `HighScoreRecord` snapshot captured once at the first terminal transition)
    - These fields are never persisted as game state; only the `High_Score_Record` summary is persisted
    - The `completed_at` is written once at the first terminal transition and `finalization_record` is captured once BEFORE any storage I/O; neither is re-mutated by any later retry or action
    - Keep all existing Stage 1/2 fields unchanged
    - _Requirements: 18.4, 2.6, 3.1, 7.6, 7.8_

- [x] 3. Implement the finalization service
  - [x] 3.1 Create `backend/app/service/finalization.py`
    - Create the `app/service/` package (`__init__.py`) and `app/service/finalization.py`
    - Add a module-level NON-REENTRANT `threading.Lock` scoped to the single in-memory game worker; document that it is acquired exactly ONCE per request by the CONTROLLER (held across mutation, finalization, AND response serialization) and that `run_mutation`/`_finalize_if_needed` MUST NOT re-acquire it (re-acquiring a non-reentrant `Lock` on the same thread deadlocks)
    - Implement `run_mutation(game, mutate, store)` assuming the caller already holds the lock: run the pure engine mutator, then if the authoritative status is now `game_over`, call `_finalize_if_needed`
    - Implement `_finalize_if_needed(game, store)` assuming the caller holds the lock: return early if `game.finalized`; on the FIRST terminal transition only, set `game.completed_at` once via a `_utc_now_iso` helper and capture an immutable frozen `HighScoreRecord` into `game.finalization_record` BEFORE any storage write; on every attempt/retry reuse that SAME `game.finalization_record` (never regenerate `completed_at`, never re-read terminal state, never re-mutate the terminal game); call `store.finalize(record)`; on success set `finalized = True` and `pending_finalization = False`
    - Implement a `_utc_now_iso` helper producing a UTC ISO-8601 timestamp
    - On `StorageError`, set `pending_finalization = True`, leave `game.finalization_record` and `game.completed_at` unchanged, preserve the terminal state and the game's `board`/`score`/`level`/`total_lines`/active piece, and re-raise so the controller maps it to 503
    - _Requirements: 2.1, 2.2, 2.4, 2.6, 2.7, 2.8, 2.9, 3.1, 3.2, 3.5, 4.5, 6.1, 7.6, 7.7, 7.8, 12.4_
  - [x] 3.2 Write unit tests for finalization happy path and zero score in `backend/tests/test_stage3_finalization.py`
    - Drive a game to `game_over` and assert exactly one `High_Score_Record` with server-authoritative `score`/`total_lines`/`level` and a UTC ISO-8601 `completed_at`
    - Assert a game reaching `game_over` with `score == 0` is still finalized
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 3.3 Write unit tests for finalize-once idempotency and UNIQUE/concurrency dedup in `backend/tests/test_stage3_finalization.py`
    - Assert repeated terminal mutations keep exactly one record with unchanged `score`/`total_lines`/`level`/`completed_at`
    - Assert two finalization attempts for the same `game_id`, including from concurrent threads, resolve to exactly one record via the service gate plus the `UNIQUE` backstop
    - Assert a still-`playing` game and an abandoned previous game (new game created mid-play) produce no record
    - _Requirements: 2.5, 2.7, 2.8, 3.1, 3.2, 3.5, 17.3, 17.4_

- [x] 4. Wire finalization into mutating controllers with the controlled 503
  - [x] 4.1 Add the shared storage-failure message and 503 mapping in `backend/app/api/`
    - Define a module-level `STORAGE_UNAVAILABLE_MESSAGE` constant: a generic English message indicating storage failure with no filesystem path, SQL text, exception/class name, or stack trace
    - _Requirements: 7.3, 7.4, 7.5_
  - [x] 4.2 Route `/tick`, `/move`, `/hold` through `run_mutation` in `backend/app/api/games.py`
    - Replace direct engine calls in the tick/move/hold handlers with `run_mutation(game, engine.<op>, high_score_store)`
    - Catch `StorageError` and raise `HTTPException(status_code=503, detail=STORAGE_UNAVAILABLE_MESSAGE)`
    - Keep `_get_or_404` and the serialized state shape unchanged so Stage 2 behavior and the 404 contract are preserved
    - Ensure `GET /api/games/{id}` performs no finalization and no retry (returns current terminal state for a pending game)
    - _Requirements: 2.4, 3.3, 6.7, 7.2, 7.9_
  - [x] 4.3 Write integration tests for failure, recovery, and GET purity in `backend/tests/test_stage3_api.py`
    - Inject a storage failure on the FIRST finalization attempt and assert a controlled 503 with `application/json`, a valid JSON body, a human-readable storage message, and NO filesystem path / SQL text / exception or class name / stack trace
    - Capture the record/`completed_at` attempted on that first (failed) attempt; after a DELAY, send a later mutating request that triggers the retry and succeeds; assert the record written on the successful retry is byte-for-byte the SAME captured record (same `game_id`/`score`/`total_lines`/`level` AND the identical `completed_at` captured at the first terminal transition), proving `completed_at` was NOT regenerated at retry/recovery time and the terminal game was not re-mutated
    - Assert the game stays terminal and pending between the failure and the recovery; a `GET` on the pending terminal game during that window never retries, never captures/writes a record, and never changes pending status
    - Assert exactly one `High_Score_Record` exists after recovery
    - _Requirements: 2.6, 2.9, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 17.1_
  - [x] 4.4 Write synthetic 3-row and 4-row clear fixtures in `backend/tests/test_stage3_clears.py`
    - Use only the real pure engine API from `app/rules/engine.py` (`new_game`, `spawn`, `clear_lines`, `lock`, `tick`, `move`, `hold` operating on a `Game`); reference no nonexistent API and no changed engine shape
    - Prefill complete rows **directly on `game.board`** and position a controlled canonical **unrotated** piece, then drive the **unchanged production path** by calling `engine.tick` / `engine.lock` on the real `Game` so that `lock(game)` settles the active piece and then calls `clear_lines(game)`, which operates on `game.board`
    - Assert the resulting awards and `total_lines`/`level`/`gravity_interval_ms` via the real scoring path; do not rotate pieces or invent gameplay pieces
    - Note that three- and four-line clears are **unreachable through ordinary unrotated gameplay**, which is why these are synthetic fixtures over the real engine path
    - _Requirements: 17.7_

- [x] 5. Add the leaderboard endpoint and strict body validation
  - [x] 5.1 Add schemas in `backend/app/api/schemas.py`
    - Add `MoveRequest` with `model_config = ConfigDict(extra="forbid")` and `direction: Literal["left","right","down"]`
    - Add `CreateGameRequest` with `extra="forbid"` and no fields
    - Add `HighScoreEntryOut` (exactly `game_id`, `score`, `total_lines`, `level`, `completed_at`) and `HighScoresOut` with a `scores` list
    - Keep `GameStateOut` unchanged
    - _Requirements: 6.1, 6.2, 6.3, 5.4_
  - [x] 5.2 Create the leaderboard controller `backend/app/api/high_scores.py`
    - Add an `APIRouter` with `GET /api/high-scores` calling `high_score_store.top_ten()`
    - Return `HighScoresOut(scores=[...])`; on `StorageError` raise `HTTPException(status_code=503, detail=STORAGE_UNAVAILABLE_MESSAGE)`
    - Return an empty `scores` array when no rows exist; perform no state mutation and create no record
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 3.4, 7.1_
  - [x] 5.3 Write tests for the exact leaderboard contract and read-side 503 in `backend/tests/test_stage3_api.py`
    - Assert `GET /api/high-scores` returns `{"scores": [...]}` with each entry containing exactly the five fields, and an empty array when no rows exist
    - Assert a storage failure while serving `GET /api/high-scores` yields the controlled 503 contract
    - _Requirements: 5.1, 5.4, 5.5, 7.1, 7.3, 7.4, 7.5, 17.8_
  - [x] 5.4 Write tests for injection-like input rejection in `backend/tests/test_stage3_api.py`
    - Assert extra body fields on `POST /api/games` and `POST /api/games/{id}/move`, and arbitrary `game_id`/score metadata, are rejected with 422 or ignored for persistence
    - Assert a valid bodyless `POST /api/games` still returns HTTP 200 and valid moves (`left`/`right`/`down`) behave as Stage 2; missing/invalid `direction` yields 422
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 17.5, 17.8_

- [x] 6. Wire CORS, startup initialization, and app composition
  - [x] 6.1 Update `backend/app/main.py` wiring
    - Replace hardcoded `allow_origins` with a restrictive configurable policy (e.g. `TETRIS_ALLOWED_ORIGINS`, comma-separated) defaulting to local dev origins; never combine `allow_credentials=True` with a wildcard `*` origin
    - Use a FastAPI lifespan/startup handler to construct `HighScoreStore.from_env()` and call `initialize()` once, sharing the instance with the game and leaderboard controllers
    - Register the new `high_scores` router; retain the `/health` endpoint; add no authentication and collect no player names
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 10.3, 10.4, 10.5_
  - [x] 6.2 Write tests for CORS policy and startup init in `backend/tests/test_stage3_api.py`
    - Assert the CORS policy is restrictive and configurable and never pairs credentials with a wildcard origin
    - Assert startup initializes the store and that the leaderboard endpoint is reachable
    - _Requirements: 10.3, 10.4_

- [x] 7. Checkpoint - backend persistence and contracts
  - Ensure all backend tests pass, ask the user if questions arise.

- [x] 8. Add the frontend API base, types, and leaderboard fetch
  - [x] 8.1 Add leaderboard types in `frontend/src/types.ts`
    - Add `HighScoreEntry` (`game_id`, `score`, `total_lines`, `level`, `completed_at`) and `HighScoresResponse` with a `scores` array; leave `GameState` untouched
    - _Requirements: 8.1_
  - [x] 8.2 Update `frontend/src/api.ts`
    - Introduce a configurable `API_BASE` (`import.meta.env.VITE_API_BASE ?? "/api"`) and rebase existing game calls onto it
    - Add `getHighScores()` fetching `${API_BASE}/high-scores`, throwing on non-ok responses
    - _Requirements: 10.1, 10.2_
  - [x] 8.3 Write tests for the configurable base in `frontend/src/api.test.ts`
    - Assert the client uses the configurable base defaulting to same-origin `/api` and never hardcodes `localhost` in the production path
    - _Requirements: 10.1, 10.2_

- [x] 9. Build the High Scores panel and game-over-edge fetch
  - [x] 9.1 Create the `frontend/src/HighScores.tsx` component
    - Render explicit `loading`, `error`, `empty`, and `loaded` states; the loaded list shows each entry's `score`, `total_lines`, and `level`
    - Keep all visible labels, statuses, and messages in English; never crash the page on a failed fetch
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.8_
  - [x] 9.2 Add an isolated leaderboard fetch hook/effect (`useHighScores`) and wire it in `frontend/src/App.tsx`
    - Fetch once on initial load and again only on the `playing -> game_over` transition (detected with a ref), not on every render and not on every automatic tick
    - Give the leaderboard fetch its own in-flight guard and stale-response/generation protection for overlapping leaderboard requests
    - Ensure the fetch never calls `cancelTick`, never touches `queueRef`/`timeoutRef`/`tickBusyRef`, and never enqueues onto the per-generation FIFO
    - Render `<HighScores />` in the layout; keep all existing Stage 2 controls, labels, and sidebar intact
    - _Requirements: 8.5, 8.6, 8.7, 9.1, 9.2, 9.3, 9.4_
  - [x] 9.3 Write tests for panel states and fetch cadence in `frontend/src/HighScores.test.tsx`
    - Assert loading, empty, error, and loaded rendering of `score`/`total_lines`/`level` with English text
    - Assert the leaderboard is fetched once on initial load and again on the `playing -> game_over` transition, and not on every automatic tick
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_
  - [x] 9.4 Write lifecycle non-disturbance tests in `frontend/src/useGame.highscores.test.tsx`
    - Cover a DELAYED `fetch` promise AND a DELAYED `response.json()` promise, asserting the stale-generation check runs after BOTH resolve (not only after `fetch`)
    - Cover a stale SUCCESS not overwriting a newer result, a stale ERROR not overwriting a newer result or the current state, and the `finally`/cleanup path running on restart, unmount, and React StrictMode teardown (double mount/cleanup/remount) so no in-flight response commits after cleanup
    - Cover a game-over refresh that fires WHILE the initial leaderboard read is still pending/unresolved, asserting the mandated game-over refresh still runs and commits the latest leaderboard rather than being silently dropped by a naive in-flight boolean
    - Assert adding the leaderboard fetch does NOT clear, block, or reschedule the per-generation automatic-tick scheduler or the manual FIFO queue, and that Stage 2 controls, Hold restrictions, stale-response/generation protections, and the R1-R5 guarantees still hold
    - _Requirements: 8.6, 9.1, 9.2, 9.3, 9.4, 17.9_

- [x] 10. Checkpoint - frontend panel and lifecycle safety
  - Ensure all frontend tests pass, ask the user if questions arise.

- [x] 11. Add Docker packaging
  - [x] 11.1 Create the multi-stage `backend/Dockerfile`
    - Multi-stage build on the concrete `python:3.12-slim` base: a build/deps stage installs ONLY the production runtime dependency set (`fastapi`, `uvicorn`, `pydantic` and their resolved transitive locks) and a slim runtime stage copies the app plus the installed runtime packages
    - Explicitly EXCLUDE all dev/test/audit dependencies (`pytest`, `httpx`, `pytest-cov`, `pip-audit`) from the runtime image; note the exact resolved transitive runtime locks are produced during implementation, and the inherited dev test assertions stay satisfied at dev time via the separate dev/audit set (do not alter any manifest or lockfile here)
    - Run as a non-root user; start exactly one uvicorn worker (`--workers 1`); set `TETRIS_DB_PATH` to the mounted volume directory; add a `/health` health check; bake in no credentials and no dev deps
    - _Requirements: 11.1, 11.5, 12.1, 12.2, 12.3, 12.4, 12.5_
  - [x] 11.2 Create the multi-stage `frontend/Dockerfile`
    - Node build stage runs `npm ci` + `npm run build`; runtime stage (e.g. `nginx:alpine`) serves the production bundle and reverse-proxies `/api` to the backend over the internal network
    - Run as a non-root user distinct from the backend's; include no dev deps or source toolchain; add a health check against the served frontend
    - _Requirements: 11.1, 11.4, 11.5, 12.3, 12.5_
  - [x] 11.3 Create `.dockerignore` at the workspace root
    - Exclude `node_modules`, `.venv`, test/coverage artifacts, `docs/`, `perf/`, local `data/`, and VCS metadata from build context
    - _Requirements: 11.2, 12.5_
  - [x] 11.4 Create `docker-compose.yml` at the workspace root
    - Define `backend` and `frontend` services on an internal network; publish only the frontend on host port `5183`; keep the backend unpublished
    - Mount a named volume with write permissions for the backend SQLite directory and resolve `TETRIS_DB_PATH` inside it; define a health check per service; run exactly one backend worker; use distinct non-root users
    - _Requirements: 11.3, 11.5, 11.6, 12.1, 12.2, 12.3, 12.4_
  - [x] 11.5 Document container operations in `backend/README.md` (or a Stage 3 section)
    - Document the exact commands to build the images, start the stack, stop the stack, and verify persistence across a container restart
    - Note that image-size and build-time values are measured only when Docker is available and are otherwise reported as not executed, with no fabricated values or invented optimization percentages
    - _Requirements: 12.6, 12.7, 12.8_

- [x] 12. Build the Playwright performance benchmark harness
  - [x] 12.1 Create the benchmark driver under `perf/`
    - Drive the production frontend in a real Chromium browser via Playwright, outside the shipped images and outside ordinary unit CI
    - Use a visible foreground window at 1280x900, device scale factor 1, a recorded 60 Hz target, a 5-second warm-up, and exactly three independent measured runs of 30 seconds each
    - Exercise real left/right/soft-drop movements and restart to keep gameplay active; capture geometry evidence that the full 10x20 board stays visible and evidence that the page has input focus
    - Do not change gravity, add an inflating animation loop, rotate pieces, migrate rendering to Canvas/WebGL, or issue sixty API requests per second
    - _Requirements: 13.1, 13.4, 13.5, 13.6, 15.1, 15.2, 15.3, 15.4_
  - [x] 12.2 Implement separated measurement and evidence capture under `perf/`
    - Record browser frame scheduling (rAF interval sampling) separately from game DOM updates (`MutationObserver`/`PerformanceObserver` on the board) separately from API timing; never treat rAF frequency alone as proof of throughput
    - Retain raw frame intervals, DOM mutation/update counts, action-to-visible-update samples, and a performance trace with real screenshot frames (PNG images or screenshot-bearing traces)
    - _Requirements: 13.2, 13.3, 14.5_
  - [x] 12.3 Implement benchmark reporting and target evaluation under `perf/`
    - Record browser, runtime, OS, hardware, display configuration, headless-vs-foreground mode, and scenario parameters
    - Report frame-interval median, p95, p99, approximate FPS, count of intervals above 33.34 ms, and action latency
    - Evaluate the operational target (mean >= 55 FPS and p95 <= 25 ms in every run), framed as a tolerance around 60 Hz and not a display-presentation guarantee; report unsupported environments or unmet targets honestly without fabrication
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.6_

- [x] 13. Add continuous-integration workflows
  - [x] 13.1 Create `.github/workflows/ci.yml`
    - Define jobs for backend tests with coverage (install the dev/audit set — `pytest`, `httpx`, `pytest-cov` layered on the runtime set — then run `pytest --cov=app --cov-report=xml`), frontend tests (`npm ci`, coverage), the frontend production build, and the backend/frontend Docker image builds that install only the production runtime set
    - Pin Python 3.12 and Node 24 concretely (no placeholders); document reproducible installation and preserve/update lockfiles coherently; require no private secrets
    - Add basic dependency audit commands (`pip-audit`, `npm audit`) reporting actual findings without suppression; separate these checks from timing-sensitive performance checks
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.7_
  - [x] 13.2 Create `.github/workflows/perf.yml`
    - Define a separate, explicitly triggered (`workflow_dispatch`) job that runs the `perf/` harness and is never part of the ordinary unit pipeline
    - Treat the workflow file as a configuration artifact only, not evidence of a hosted Actions run
    - _Requirements: 15.5, 16.6, 16.7_

- [x] 14. Verify inherited Stage 1/2 regression suites remain green
  - [x] 14.1 Confirm inherited backend regression coverage is intact
    - During a later implementation invocation, run the inherited Stage 1/2 backend rules/scoring/API tests and confirm they pass unchanged; do not alter inherited assertions or the inherited spec directories
    - _Requirements: 18.1, 18.3_
  - [x] 14.2 Confirm inherited frontend regression coverage is intact
    - During a later implementation invocation, run the Stage 2 frontend request-ordering/lifecycle tests (`useGame.test.tsx`, `useGame.races.test.tsx`, `useGame.queued-timers.test.tsx`) and confirm they pass unchanged
    - _Requirements: 18.1_

- [x] 15. Final checkpoint - measurement and honest reporting
  - [x] 15.1 Collect checks, coverage, audit, and Docker measurements (later implementation invocation only)
    - During a later implementation invocation, run backend tests with coverage, frontend tests and build, and dependency audits, reporting actual findings without suppression
    - Measure Docker image sizes and build time only when Docker is available; otherwise report that the measurement could not be executed, fabricating no values, optimization percentages, or Docker/CI/benchmark results
    - Run `pip-audit` on BOTH the production runtime set and the dev/audit set and report actual findings without suppression, and confirm the selected remediation versions via `pip check`, recording evidence under the Stage 3 native-checks evidence directory
    - Perform no commits, pushes, image publishing, or external deployment
    - (These checks were run as local researcher-agent evidence — backend tests with coverage, frontend tests and build, dependency audits over 13 pinned production packages with no advisories, a SonarQube gate reported OK with new-code coverage 97.3% and global coverage 94.8%, and a Docker verification showing the container healthy, non-root, published only on 5183 with the backend internal and its own volume — NOT a hosted GitHub Actions run; no commits, pushes, image publishing, or deployment were performed.)
    - _Requirements: 12.7, 12.8, 16.5, 16.6, 18.5, 18.6_

## Notes

- The verification (test-authoring) sub-tasks are mandatory, not optional: they cover the required frozen-seed failure/recovery/concurrency/idempotency/injection/persistence/UI cases called out in Requirement 17 (and related clauses) and are left unchecked for later execution. There is no skip-for-MVP path for them.
- Each task references specific requirement clauses for traceability.
- Checkpoints (tasks 7, 10, 15) provide incremental validation boundaries.
- The engine files (`app/rules/*`) stay pure and unchanged; finalization lives in the service/controller boundary.
- No command is executed during this planning phase; measurement and regression steps are authored to be performed in a later implementation invocation and must report honestly.
- The inherited spec directories under `.kiro/specs/tetris-stage1-option-a/` and `.kiro/specs/tetris-stage2-option-a/` are never edited.
- The dependency security remediation (the exact runtime/dev-audit version selections and the two-set pinned lock strategy recorded in design.md for Requirement 19) must be reflected in the manifests/lockfiles ONLY after being documented in design, and verified with `pip check` and `pip-audit` in the owned Python 3.12 environment during the later implementation/measurement tasks (task 15.1 scope).

## Post-Implementation Corrections (Round 04)

These tasks apply the verified round-04 corrections. Each is reflected in the revised requirements/design first (done), then in code/tests/infra/harness. Evidence under `docs/native-checks/04/`; behavior recorded in `docs/native-checks/04/CORRECTIONS-04.md` before each repair.

- [x] 16. CORS wildcard-with-credentials fix (Req 10.3-10.7)
  - [x] 16.1 Fix `backend/app/main.py::_resolve_allowed_origins` to reject (fail closed) any resolved list containing `*` while credentials are enabled, including mixed lists; keep concrete allow-lists and the local-dev default working
  - [x] 16.2 Add tests in `backend/tests/test_stage3_api.py` for default/untrusted, explicit allowed, and wildcard/mixed rejection; preserve generic controlled errors and existing response fields
    - _Requirements: 10.3, 10.4, 10.5, 10.6, 10.7_

- [x] 17. Restart leaderboard ownership fix (Req 8.8-8.10, 9.3, 9.4)
  - [x] 17.1 Add an `invalidate()` restart signal to `frontend/src/useHighScores.ts` that synchronously bumps the request generation (covering delayed fetch, delayed JSON, success/error/finally) and sets a neutral current state, without touching the game FIFO/timers
  - [x] 17.2 Wire `App.tsx` so the Restart button (and keyboard restart path) invalidates the leaderboard generation before `useGame.restart`
  - [x] 17.3 Add hook/App tests for delayed fetch after restart, delayed JSON after restart, and stale error/finally after restart; keep initial fetch, game-over-while-initial-pending refresh, and no per-tick polling; preserve all inherited frontend assertions
    - _Requirements: 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 9.3, 9.4_

- [x] 18. Sonar new-finding corrections (new findings only, no suppression)
  - [x] 18.1 `api/games.py`: document 503 in `responses=` metadata (S8415) and remove redundant `response_model=` (S8409)
  - [x] 18.2 `api/high_scores.py`: remove redundant `response_model=` (S8409) and document 503 (S8415)
  - [x] 18.3 `persistence/store.py`: replace the repeated storage-unavailable literal with a shared constant (S1192)
  - [x] 18.4 `tests/test_stage3_finalization.py`: keep only the single throwing invocation inside `pytest.raises`, move non-throwing setup out (S5778)
  - [x] 18.5 `frontend/src/HighScores.tsx`: mark props readonly (S6759)
    - _Requirements: 16.5, 18.6_

- [x] 19. Reproducible dependency locks (Req 16.3, 19.10, 19.11)
  - [x] 19.1 Generate complete resolved `backend/requirements.lock.txt` (prod) and `backend/requirements-dev.lock.txt` (dev) in the owned Python 3.12.14 env, pinning every transitive with markers; keep input manifests distinct
  - [x] 19.2 Wire the backend Dockerfile to install the prod lock and CI to install the dev lock; document inputs vs locks in `backend/README.md`
  - [x] 19.3 Validate fresh install, `pip check`, native tests, and BOTH runtime and dev audits; audit the perf dependency set and confirm frontend pins; report actual resolved packages under `docs/native-checks/04/`
    - _Requirements: 16.3, 19.4, 19.6, 19.7, 19.10, 19.11_

- [x] 20. Benchmark harness fix (Req 13.7-13.9, 14.7-14.11, 15.6)
  - [x] 20.1 Rewrite `perf/benchmark.mjs`: full 200-cell signatures (no 4-char truncation); observe the board only after readiness/full board exists before warm-up
  - [x] 20.2 Set `chromiumSandbox: true`, support documented `PERF_BROWSER_CHANNEL`, record actual browser/version/channel + Playwright version
  - [x] 20.3 Fixed page-clock window `end = start + 30000`; select intervals with both endpoints in-window; explicit boundary/warm-up exclusions; all summaries use the same measured window
  - [x] 20.4 Causal action->visible-update: await authoritative response and a real signature transition; retain IDs/associations/timestamps; exclude+report ambiguous/unchanged/out-of-window samples; guard gravity overlap; honest Resource-Timing clock labeling
  - [x] 20.5 Separate numeric targets from measurement-validity qualification (focus/geometry/evidence); capture real viewport PNGs + screenshot-bearing trace; record browser/Playwright/Node/OS/CPU/RAM + GPU/display; unknown physical presentation stays unknown
  - [x] 20.6 Robust `finally` preserving partial datasets/metadata/exception; close only owned browser/context; stop sampler; no orphaned children; keep documented manual command separate from unit CI (benchmark NOT run this round)
    - _Requirements: 13.7, 13.8, 13.9, 14.7, 14.8, 14.9, 14.10, 14.11, 15.6_

## Post-Implementation Corrections (Round 06)

Task renumbered from 18 to 21 (and sub-tasks 18.x to 21.x) to resolve a collision with Round 04's task 18; the original raw run notes and snapshots under docs/ are unchanged. This renumbering is a documentation/traceability fix only; the historical docs/ artifacts keep their original numbering.

These tasks apply the six verified round-06 benchmark-measurement-contract corrections, reflected in requirements (new Requirement 20) and design (new "Round 06" subsection) first (done), then in the harness (`perf/benchmark.mjs`) and its docs; no timing-sensitive benchmark run is executed this round, so real performance evidence does not yet exist.

- [x] 21. Correct the benchmark measurement contract in `perf/benchmark.mjs` (Req 20)
  - [x] 21.1 Fix action association and windowing in `perf/benchmark.mjs`
    - Generate run-wide monotonically unique action ids that persist across driving sub-calls; retain per-id dispatch/update association in an id-keyed map; never overwrite a completed sample via a reused id
    - Complete an action only on its real successful authoritative API response AND an attributable displayed board-state DOM transition; never let ordinary gravity complete an action; preserve raw request/response ids, method, route, payload, status, timestamps, response state identity, and DOM-signature evidence; exclude and report ambiguous/overlapping/no-op/timed-out samples with reasons; allow an explicitly limited eligible-action subset
    - Keep input pacing at most 4 actions/second, ordinary gravity, real keyboard controls, and no fake responses; record Node API round-trip time on its own monotonic clock separate from the page-clock dispatch-to-DOM stream with no cross-clock subtraction; do not interfere with application request bodies/queues
    - Require BOTH dispatch and matched-update timestamps inside the fixed [start, start+30000] ms page-clock window for a latency sample; retain excluded boundary samples with reasons
    - _Requirements: 20_
  - [x] 21.2 Fix sampler lifecycle, qualification, failure telemetry, and timestamps in `perf/benchmark.mjs`
    - Stop/release all passive samplers at capture end and record the real capture-end separately; mark a capture unqualified if the full fixed window was not observed; require exactly 200 visible board cells and adequate valid samples per claimed stream; define DOM batch count as changed-signature observer batches (never cell-mutation count); preserve all raw timestamps and full 200-cell signatures
    - On ANY failure, fetch best-effort partial telemetry from the surviving page BEFORE closing; always save raw data, exception, and real success flags for the PNG and trace; set trace-taken/screenshot-taken only after real success (never on a swallowed stop failure); verify artifact existence and non-zero size before claiming evidence
    - Capture batch/per-run startedAt at the real start and finishedAt at the real finish (not both after completion)
    - Preserve exactly the three fresh headed sandboxed sessions, 1280x900 DSF1, 60 Hz target, >=5s warm-up excluded from latency, fixed 30s windows, rAF both-endpoint filtering, full 200-cell signatures, focus/geometry throughout, screenshot-bearing traces plus a final PNG per trial, PERF_BROWSER_CHANNEL support, numeric targets mean>=55/p95<=25ms kept separate from qualification, fail exit on invalid capture or unmet targets, and honest unknown physical display presentation
    - _Requirements: 20_
  - [x] 21.3 Update `perf/README.md` and record a concise native evidence note under `docs/native-checks/06`
    - Document the corrected round-06 measurement contract in `perf/README.md` and keep the measurement status PENDING (no numbers claimed until a real run)
    - Record a concise native evidence note under `docs/native-checks/06` capturing the syntax check and structural review performed this round and the remaining manual real-run work
    - _Requirements: 20_
  - [x] 21.4 Execute the corrected benchmark on a real foreground display (executed — real foreground-display run)
    - Run the documented manual command on a real machine with a physical foreground display; the harness writes an actual report.json across three qualified runs; report numeric targets and qualification honestly without fabrication; do NOT mark this complete until real evidence exists
    - The real run produced the recorded report across three qualified 30 s runs with the numeric targets met and qualification reported honestly.
    - _Requirements: 13.4, 14.3, 14.6, 20_

## Post-Implementation Corrections (Round 07)

Task renumbered from 19 to 22 (and sub-tasks 19.x to 22.x) to resolve a collision with Round 04's task 19; original raw notes/snapshots are unchanged. This renumbering is a documentation/traceability fix only; the historical docs/ artifacts keep their original numbering.

These tasks apply the two verified round-07 benchmark-measurement-contract corrections (Requirement 21), already reflected in requirements (new Requirement 21) and design (new "Round 07" subsection) first (done), then in the harness (`perf/benchmark.mjs`) and its docs; no timing-sensitive benchmark run is executed this round, so real performance evidence does not yet exist.

- [x] 22. Implement auditable action-to-visible-update association and nonempty valid-sample qualification in `perf/benchmark.mjs` (Req 21)
  - [x] 22.1 Add a passive Playwright request/response observer that assigns each `/api/.../move` request a unique per-run id and records method, URL, direction parsed from the POST body, response status, successful response JSON state identity (game id + board/active_piece), and Node monotonic request-to-body-end timestamps; never read/clone the application fetch body in page context and never alter request bodies or queues
    - _Requirements: 21_
  - [x] 22.2 Associate each dispatched action with the single NEW matching-direction `/move` request started after dispatch; exclude and report (no candidate / multiple candidates / overlap / failure / no-op / timeout) with reasons and never attribute an action to arbitrary gravity; compute the expected full 200-cell displayed signature from the matched response `board` + `active_piece` using the production Board overlay and COLORS mapping with shared color normalization; complete only on observing that exact expected signature; exclude never-observed coalesced states; retain matched request id, expected/observed signatures, and page-clock dispatch/observed-update timestamps; keep Node API RTT on the Node clock and dispatch-to-observed-DOM on the page clock with no cross-clock subtraction
    - _Requirements: 21_
  - [x] 22.3 Require qualified runs to have a nonempty set of valid action-latency samples covering actual left/right/soft-drop; report every excluded sample with its reason; require `captureEndAt >= windowEnd` strictly (remove the earlier-stop tolerance) and retain any actual late stop separately; preserve all round-04/round-06 controls; update `perf/README.md` with the round-07 contract and keep the measurement status PENDING; record a concise native evidence note under `docs/native-checks/07` for the syntax/structural checks performed this round
    - _Requirements: 21_
  - [x] 22.4 Execute the corrected benchmark on a real foreground display (executed — real foreground-display run)
    - Run the documented manual command on a real machine with a physical foreground display; the harness writes an actual report.json across three qualified runs that each include nonempty left/right/soft-drop-covered valid action samples; report numeric targets and qualification honestly without fabrication; do NOT mark complete until real evidence exists
    - The real run collected nonempty valid action samples covering left/right/soft-drop.
    - _Requirements: 13.4, 14.3, 14.6, 21_

## Post-Implementation Corrections (Round 08)

These tasks apply the two verified round-08 benchmark-harness corrections (Requirement 22), reflected in requirements (new Requirement 22) and design (new "Round 08" subsection) first (done), then applied narrowly to the harness (`perf/benchmark.mjs`) and its docs; no timing-sensitive benchmark run is executed this round, so real performance evidence still does not exist.

- [x] 23. Correct injected-instrumentation integrity and observation body-readiness in `perf/benchmark.mjs` (Req 22)
  - [x] 23.1 Preserve regex-escape integrity in the injected instrumentation in `perf/benchmark.mjs`
    - Convert the `INSTRUMENT` template so cooked regex backslashes survive (e.g. `String.raw`)
    - Emit the U+0001 signature join as a single real U+0001 via an interpolated sentinel (NOT a raw `\u0001` that would cook to literal characters)
    - Keep the `${BOARD_CELLS}`/`${MEASURE_MS}` interpolations and all other regexes (hex `#rgb`/`#rrggbb` matchers, `background[^;]*`, the `#[0-9a-fA-F]{3,6}|rgba?\(...\)` extractor) intact
    - _Requirements: 22_
  - [x] 23.2 Validate the ACTUAL cooked injected script (non-timing) in `perf/`
    - Construct the injected script from the real native template, compile it separately, and execute its real color/signature functions under a minimal inert window/document/requestAnimationFrame stub (not a replica of the function code)
    - Confirm `rgb(17,24,39)` and `#111827` normalize to the identical token across all 200 cells; no browser or measured run
    - _Requirements: 22_
  - [x] 23.3 Fix the observation body-readiness race in `perf/benchmark.mjs`
    - Set an explicit body-ready/completed flag in a `finally` after parsing (with real error flags), and make `selectMoveCandidate` wait for that completed/body-ready state rather than falsely reject a still-parsing successful 200
    - Keep request-to-body RTT on the existing Node monotonic clock (no clock mixing)
    - Preserve round-07's honest no-op exclusion, exact expected/observed signature matching, directional samples, and the strict 30 s window
    - _Requirements: 22_
  - [x] 23.4 Update `perf/README.md` and project READMEs with round-08 semantics
    - Update `perf/README.md` with the round-08 measurement semantics and KEEP the measurement status PENDING (no numbers claimed until a real run)
    - Record a concise native evidence note under `docs/native-checks/08` capturing the actual cooked-script compile+normalization check and the structural review performed this round, plus the remaining manual real-run work
    - Update the root `README.md` and `frontend/README.md` to the current Stage 3 run instructions (Docker compose up --build -> frontend 5183, internal backend, persistent named high-score volume, Python 3.12 / Node 24 CI majors, production-vs-dev lock install commands, same-origin `/api` default, local-dev override `VITE_API_BASE=http://localhost:8000/api` which must include `/api`, restrictive `TETRIS_ALLOWED_ORIGINS` defaults, ranking order, and the manual perf command / Chrome channel), while PRESERVING the protected app H1 `Tetris - Stage 2` and not changing app/tests/locks/workflows/Docker
    - _Requirements: 22, 8.1, 10.1, 10.2, 12.6_
  - [x] 23.5 Execute the corrected benchmark on a real foreground display (executed — real foreground-display run)
    - Run the documented manual command on a real machine with a physical foreground display and confirm telemetry actually installs and nonempty valid samples are collected; report numeric targets and qualification honestly; do NOT mark complete until real evidence exists
    - Telemetry actually installed (the cooked script now compiles) and nonempty valid samples were collected across three qualified runs, with the numeric targets met and qualification reported honestly.
    - _Requirements: 13.4, 14.3, 14.6, 22_

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4"] },
    { "id": 2, "tasks": ["1.5", "1.6", "2.1"] },
    { "id": 3, "tasks": ["3.1"] },
    { "id": 4, "tasks": ["3.2", "3.3", "4.1"] },
    { "id": 5, "tasks": ["4.2", "5.1"] },
    { "id": 6, "tasks": ["4.3", "4.4", "5.2"] },
    { "id": 7, "tasks": ["5.3", "5.4", "6.1"] },
    { "id": 8, "tasks": ["6.2", "8.1", "8.2"] },
    { "id": 9, "tasks": ["8.3", "9.1", "9.2"] },
    { "id": 10, "tasks": ["9.3", "9.4"] },
    { "id": 11, "tasks": ["11.1", "11.2", "11.3"] },
    { "id": 12, "tasks": ["11.4", "11.5", "12.1"] },
    { "id": 13, "tasks": ["12.2", "12.3", "13.1", "13.2"] },
    { "id": 14, "tasks": ["14.1", "14.2"] },
    { "id": 15, "tasks": ["15.1"] }
  ]
}
```

