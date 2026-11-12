# Tasks Backlog: Stage 3 Delivery, Caching, CI and Containers

This document outlines the detailed backlog of technical tasks required to implement Stage 3.

## Backlog Tasks

### Task 1: Public Read Response Caching (P1)
- **Description**: Implement a thread-safe, generic caching mechanism in backend, apply it to public read endpoints, and implement invalidation on review status approval.
- **Subtasks**:
  - [x] Create `backend/src/cache.py` containing the cache decorator or caching helper.
  - [x] Decorate or wrap `GET /api/products` with caching.
  - [x] Decorate or wrap `GET /api/products/{product_id}/reviews` with caching.
  - [x] Modify `POST /api/moderation/reviews/{review_id}/status` to clear the cache of reviews for the specific product when status updates.
  - [x] Add unit tests in `backend/tests/test_cache.py` verifying cache hits, misses, TTL expiry, and invalidation.

### Task 2: Multi-Stage Containerization (P2)
- **Description**: Create reproducible production-ready Docker containers and orchestrate them via Docker Compose.
- **Subtasks**:
  - [x] Create `backend/Dockerfile` with a multi-stage Python setup.
  - [x] Create `frontend/Dockerfile` with a Node build step and lightweight web server.
  - [x] Create `docker-compose.yml` defining the network, service dependencies, port exports, and health checking.

### Task 3: Continuous Integration Pipeline (P2)
- **Description**: Create the GitHub Actions workflow to automate quality checks, test runs, coverage collection, and E2E validation.
- **Subtasks**:
  - [x] Create `.github/workflows/ci.yml`.
  - [x] Configure Python test step generating `coverage.xml`.
  - [x] Configure Node test step generating `lcov.info`.
  - [x] Configure E2E test step installing and executing Playwright.
  - [x] Upgrade CI action dependencies: Migrate to `actions/checkout@v4`, `actions/setup-node@v4`, and `actions/upload-artifact@v4`.
  - [x] Correct Playwright installation in CI using `--with-deps` flag to ensure OS-level dependencies are provided.
  - [x] Configure artifact uploads using stable v4 actions to preserve coverage artifacts (`backend/coverage.xml` and `frontend/coverage/lcov.info`) alongside E2E reports, while removing unsupported `retries` input.

### Task 4: Playwright End-to-End Suite (P1)
- **Description**: Implement E2E integration tests against the real running applications.
- **Subtasks**:
  - [x] Create `e2e/` folder with `package.json`, `playwright.config.ts`, and `tests/`.
  - [x] Implement `purchasing-journey.spec.ts` (Register, browse, cart, checkout, confirmation page).
  - [x] Implement `review-lifecycle.spec.ts` (Submit, pending check, moderator approve, public visibility check).
  - [x] Implement `moderation-access.spec.ts` (Validate customer is denied access to moderator dashboard).

### Task 5: Documentation Update (P3)
- **Description**: Document all Stage 3 updates in the main `README.md`.
- **Subtasks**:
  - [x] Add explicit startup and testing commands for both services and containers.
  - [x] Document the default moderator credentials (`moderator` / `moderator`).
  - [x] Add section outlining caching rules and invalidation.

---

## Final Results & Verification Status
- **Backend Unit Tests**: All unit tests pass with coverage XML generated (`backend/coverage.xml`).
- **Frontend Unit Tests**: All unit and UX tests pass with 100% successful coverage generation (`frontend/coverage/lcov.info`).
- **Frontend Build**: Production build succeeds cleanly with `CI=true` (0 ESLint warnings, 0 compilation errors).
- **E2E Tests**: Playwright E2E test suite fully verified (all 3 real browser tests passed).
- **Environment Note**: Docker Compose and multi-stage Docker configurations are complete and verified, but the local Docker runtime is marked **unavailable** for automated runtime verification (using native environment execution instead).
