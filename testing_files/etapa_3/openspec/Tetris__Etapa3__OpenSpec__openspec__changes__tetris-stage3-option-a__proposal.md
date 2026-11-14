# Proposal

## Why

Currently, game sessions exist purely in memory, meaning that scores are transient and lost as soon as the server restarts, a new session is initialized, or the browser is refreshed. This change introduces high-score persistence using an SQLite database, allowing players to view their best performances in a leaderboard, while also establishing reproducible containerized deployments, rigorous Playwright performance benchmarks, and automated continuous-integration workflows to ensure long-term stability and high-quality user experience.

## What Changes

- **SQLite Persistence & Integrity**: Integration of a single-process SQLite backend database to persist final game outcomes (score, total lines, level, and timestamp) upon game over, with automatic parent directory and schema initialization on startup. High scores survive process reloads and container recreation.
- **Single-Process Concurrency and Synchronization**: Implementation of an asynchronous lock per game ID as a synchronization boundary. This protects authoritative in-memory game state mutations and finalization writes from concurrent requests within the single-process backend, ensuring late or duplicate finalization attempts never duplicate, overwrite, or mutate original stored results or completed_at timestamps.
- **REST Leaderboard API & Truncation**: A new GET `/api/high-scores` endpoint retrieving the top 10 scores (strict top 10 truncation), sorted by score descending, then completion timestamp (chronological) ascending, then game ID (lexicographical) ascending. It supports GET idempotency and returns exactly 5 schema fields: `game_id`, `score`, `total_lines`, `level`, and `completed_at`.
- **Strict Input Validation**: Prevention of metadata injection by rejecting any extra fields in game creation (POST `/api/games`) and movement/hold request bodies, leaving game state unchanged.
- **Robust Storage Error Handling**: Connection, locking, or query errors return a controlled 503 response without leaking internal paths, SQL queries, or traceback details.
- **High Scores Frontend UI**: A persistent leaderboard panel displaying score, lines, and level, with appropriate UX states for loading, empty lists, and error feedback, without polling on every gravity tick.
- **Dynamic Same-Origin API base & CORS**: Configurable frontend API base (defaulting to the same-origin `/api` structure with Vite dev proxy configuration) and a secure, configurable backend CORS policy (no wildcard origin when credentials are used).
- **Multi-stage Docker Packaging**: Production-ready, non-root multi-stage Dockerfiles for both backend and frontend images, run with a Compose file exposing only the frontend on port 5183. Serves the production bundle, restricts backend to internal-only, runs exactly one worker process, implements health checks, and verifies persistent SQLite storage via a named writable volume surviving container recreation.
- **Automated Playwright Performance Benchmarking**: Executable browser frame and update performance testing using Playwright Chromium. It tracks and retains raw frame intervals, DOM board mutation counts, action-to-visible-update latency, and browser performance traces with screenshot evidence over repeated runs (with 5s warmup, visible foreground browser, 1280x900). Does not misname rAF cadence as physical rendered display presentation FPS. These timing-sensitive checks are separate from ordinary CI.
- **GitHub Actions CI/CD**: Workflow automation checking backend unit tests (producing fresh XML coverage), frontend unit tests/build (producing LCOV), security dependency audits (`npm audit` and `pip-audit`), and Docker builds without relying on private secrets and without fabricating remote hosted execution claims.

## Capabilities

### New Capabilities
- `high-scores`: Manages database schema initialization, atomic high-score persistence, GET leaderboard requests, strict endpoint payload validation, frontend High Scores panel UI, and secure CORS configurations.
- `concurrency-synchronization`: Enforces synchronization locks on the single-process backend to prevent concurrent mutation and finalization race conditions.
- `performance-benchmarking`: Standalone Playwright performance measurement suite providing concrete rendering frame aggregates, raw interval arrays, and action latency metrics.

### Modified Capabilities
- `tetris-core`: Refines game over finalization to trigger persistence, updates game endpoint specifications to enforce strict body validation, preventing extra fields in requests, and ensures both first-Hold and occupied-Hold obstruction paths trigger game-over.

## Impact

- **Backend**: Python FastAPI backend updated with a new routing layer for high scores, custom middleware/exception handlers for 503 errors, asyncio locks for session serialization, and database connection lifecycle management. Game model definitions will require Pydantic validation adjustments to ban extra fields.
- **Frontend**: React client will include a new component for the leaderboards, update API calls to dynamically use a configurable API base, and trigger high-score refetching upon loading or game over.
- **Infrastructure**: Addition of `Dockerfile` (backend), `Dockerfile.frontend` (frontend), `docker-compose.yml` (Compose runner), and `.github/workflows/ci.yml`.
- **Testing**: Python tests will be extended to test SQLite persistence, concurrency synchronization, and failure recovery. Frontend tests will include loading/error assertions for the High Scores component. Playwright performance benchmarks will be added in a separate suite.
