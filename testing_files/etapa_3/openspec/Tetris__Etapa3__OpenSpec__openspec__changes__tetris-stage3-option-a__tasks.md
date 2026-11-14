# Tasks

## 1. Database Setup, Schema Initialization, and Reload Persistence

- [x] 1.1 Implement schema initialization function in a new module `backend/database.py` that safely creates the parent directory of `TETRIS_DB_PATH` (defaulting to `./data/high-scores.sqlite3`) and executes the DDL schema with a UNIQUE constraint on `game_id`. Write tests to verify directory and DB file initialization, and verify that scores survive when a new store/connection instance opens the same DB file (reload persistence). Ensure all tests use isolated temporary SQLite databases per test (e.g., using pytest `tmp_path` fixture and `monkeypatch` to set `TETRIS_DB_PATH` under a unique temporary folder), and completely avoid recursive directory deletion (`shutil.rmtree`) of non-temporary directories (TEST-ISOLATION-01).
- [x] 1.2 Hook database initialization into FastAPI's startup lifespan event in `backend/main.py`. Verify that starting the FastAPI server creates the database file at the configured path when it does not exist.

## 2. In-Memory Concurrency Protection & Strict Payload Validation

- [x] 2.1 Implement an in-memory lock mechanism (e.g. `asyncio.Lock` per game session) in `backend/engine.py` or `backend/main.py` as a synchronization boundary. Ensure all mutating requests (`move`, `tick`, `hold`) and finalization processes are serialized per game ID.
- [x] 2.2 Write concurrent integration tests verifying that duplicate/concurrent tick/move/hold finalizations do not duplicate or replace the original stored result, and that the original result and `completed_at` remain immutable.
- [x] 2.3 Refactor `backend/models.py` to add `extra = "forbid"` configuration (using `model_config` or `ConfigDict`) to Pydantic models `MoveRequest` and a new empty schema `GameCreateRequest`. Verify with unit tests that passing extra parameters (such as client-supplied scores, levels, or completion timestamps) raises a `ValidationError` and leaves game state unchanged (preventing injection-like metadata manipulation).
- [x] 2.4 Update backend endpoints in `backend/main.py` (`POST /api/games` and `POST /api/games/{game_id}/move`) to strictly parse request bodies using the updated Pydantic models. Verify that invalid requests with extra fields are rejected with an HTTP 422 validation error, while valid bodyless game creation is preserved.

## 3. Persistent Game Recording & Graceful Error Handling

- [x] 3.1 Implement persistent score recording on game over within `backend/main.py` or `backend/engine.py`. Record `game_id`, `score`, `total_lines`, `level`, and `completed_at` (UTC ISO-8601). Enforce that gravity ticks, soft drops, and obstructed hold game-overs (including both first-Hold empty-slot collision and occupied-Hold swap-collision paths) trigger persistence exactly once. Verify with unit tests that use legal, canonical 4-cell tetromino geometries (such as `"O"` at origin `[17, 0]`) and correct spawn obstruction locations (such as cell `[1, 4]`) to genuinely obstruct newly spawning pieces (`"S"` or `"T"`) (TEST-FIXTURE-02).
- [x] 3.2 Add validation rules to prevent score persistence for restarted, active, or abandoned games. Verify with unit tests that creating a new game or closing a session does not write high-score rows for unfinished sessions.
- [x] 3.3 Add global Exception handlers in `backend/main.py` to trap `sqlite3.Error` operations and return a controlled, clean HTTP 503 Service Unavailable response payload (`{ "detail": "Storage service unavailable" }`) on both read (leaderboard) and write (finalization) endpoints. Verify with unit tests that database errors produce a controlled 503 status code without leaking traceback, SQL statements, or file paths.
- [x] 3.4 Implement persistence retry logic so that subsequent state-mutating requests (move, tick, or hold) on a terminal game retry persistence if it initially failed, while read-only GET requests never trigger a retry and do not modify state. Verify with unit tests.

## 4. REST Leaderboard API & CORS Security

- [x] 4.1 Implement GET `/api/high-scores` endpoint retrieving at most 10 scores (top 10 truncation), sorted by `score` descending, then `completed_at` ascending, then `game_id` ascending. Verify via unit tests that all ties are broken correctly and outputs match the specification schema exactly.
- [x] 4.2 Verify that GET `/api/high-scores` and GET `/api/games/{game_id}` are fully idempotent and do not write or mutate any database or active game state.
- [x] 4.3 Configure restrictive CORS policies on the backend using `CORSMiddleware`, explicitly setting origins via `ALLOWED_ORIGINS`, disabling wildcard origins (`*`) and using specified origins when credentials are enabled. Verify via CORS headers check in server unit tests.

## 5. Frontend Leaderboard UI & Configurable Base URL

- [x] 5.1 Implement a High Scores panel component in the frontend displaying top scores, lines, and levels. Handle and display loading, empty, and error feedback states gracefully. Refetch high scores on initial load and after game over, without any polling on every gravity tick. Add stale-response protection to ignore out-of-order API responses. Verify with Vitest assertions.
- [x] 5.2 Configure frontend network requests to use a dynamic API base, defaulting to the same-origin `/api` path. Set up Vite's development server proxy in `frontend/vite.config.ts` to route `/api` to the local backend. Verify with frontend mock network tests that requests default to same-origin path structures.
- [x] 5.3 Audit and update dependencies to address known high Vite and moderate Vitest advisories, recording actual audit outputs and applying coherent manifest/lock updates.

## 6. Reproducible Containerized Environment and Operational Isolation

- [x] 6.1 Create multi-stage `Dockerfile` (backend) running as a non-root system user (`appuser` with UID 10001), copying only runtime dependencies, and configured with exactly one worker process (`uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1`).
- [x] 6.2 Create multi-stage `Dockerfile.frontend` (frontend) running as a non-root system user (`nginx`), utilizing Node 24 LTS consistent with the runtime policy (RUNTIME-POLICY-01) to build production assets, and utilizing the official stable maintained `nginx:stable-alpine` image to serve assets and proxy `/api` to the backend.
- [x] 6.3 Update the root-level `.dockerignore` file (PACKAGING-CONTEXT-01) to include explicit complete exclusions for `docs/`, `.gemini/`, `.git/`, all local venvs, `node_modules/`, `caches/`, `build/`, `coverage/`, `runtimeDB`, and `credentials`.
- [x] 6.4 Update `docker-compose.yml` to fully isolate and namespace the project as `tetris-stage3-openspec` (PACKAGING-ISOLATION-01), with containers named `tetris-stage3-openspec-backend`/`frontend` and utilizing the isolated named SQLite database volume `tetris_stage3_openspec_data`. Expose only port 5183 with the backend remaining internal, and perform container health checks.
- [x] 6.5 Verify that volume ownership is writable after a fresh start by executing write tests, and verify high-score persistence survives container destruction and recreation (`docker compose down && docker compose up -d`) as long as the volume is not deleted. Document the exact build, start, stop, and volume persistence-verification commands, measuring actual image sizes and build duration.

## 7. Playwright Chromium Performance Benchmark and Detailed Evidence (PERF-EVIDENCE-01)

- [x] 7.1 Rewrite the executable browser benchmark script `playwright-benchmark.js` to utilize a completely fresh context and page per independent run, executing its own 5s warmup followed by a 30s measurement run. Use a deterministic, replayable action sequence of left/right/soft-drop/hold key controls to maintain active gameplay.
- [x] 7.2 Implement detailed evidence gathering (PERF-EVIDENCE-01): capture and save per-run raw JSON arrays of `frameIntervals` and `actionLatencies`, and record every single action outcome (success, timeout, blocked, or no-change), `browser.version()`, timestamps, foreground state, metadata, trace paths, and SHA256 hashes.
- [x] 7.3 Implement active board observation: attach a MutationObserver directly to the active current board DOM container, re-attaching/re-initializing the observer directly to the newly mounted board DOM node after any restart or reset.
- [x] 7.4 Enforce non-zero exit on failed targets (mean FPS < 55 or p95 interval > 25 ms) while fully preserving raw traces and metrics. Chromium's sandbox must not be disabled. Capture PNG/JPG screenshots at meaningful game states (e.g. gameplay active, game over, leaderboard loaded) to serve as visual QA. Preserve prior run results (e.g., initial06 traces) and save outputs in a unique evidence directory per invocation.
- [x] 7.5 Correct the action/request clock attribution defect (PERF-EVIDENCE-01) by using comparable absolute timestamps (`performance.timeOrigin + performance.now()`), applying a key-matching and timing-based causal heuristic, and implementing an executable internal consistency check that halts and fails on impossible pairs (e.g., requests starting before its causal action beyond tolerance, or incorrect endpoints/payloads).

## 8. Continuous Integration Workflow and Auditing

- [x] 8.1 Write a GitHub Actions continuous-integration workflow `.github/workflows/ci.yml` that pins Node 24 (LTS) and Python 3.11, runs backend tests with coverage (writing to `backend/coverage.xml`), frontend Vitest tests (writing to `frontend/coverage/lcov.info`), frontend production builds, security dependency audits (`npm audit`, `pip-audit`), and verifies Docker builds.
- [x] 8.2 Define a clear audit policy: fix available advisory patches coherently via package manifests/locks first. Report unresolved findings accurately with severity/scope/rationale, rather than hiding or ignoring them with silent bypasses like `|| true`. Ensure exact install commands are used and no false hosted Actions claims are made. Verify current backend 31 and frontend 9 regressions after changes.
- [x] 8.3 Verify all-source coverage including `main.tsx` (native 95%-style excluded bootstrapper percentage must not be confused with full source or Sonar global coverage). Include instructions for executing these checks locally using exact CLI commands.

## 9. Sonar Quality Gate Compliance (QA07 Issues)

- [x] 9.1 (python:S1192) Define a constant for the three identical Hold rejection literals in `backend/main.py`.
- [x] 9.2 (python:S9100) Remove unnecessary fixture yield without weakening, deleting or skipping any tests/assertions or cleanup/isolation in `backend/test_stage3.py`.
- [x] 9.3 (typescript:S6582 / S7741) Use idiomatic safe optional chaining/direct undefined handling in frontend/src/api.ts.
- [x] 9.4 Execute regression checks and verify that all backend and frontend tests pass cleanly with isolated temporary DB.
