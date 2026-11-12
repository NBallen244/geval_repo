# Tasks

## 1. Backend Public API Caching

- [x] 1.1 Create `backend/app/cache.py` containing a thread-safe, bounded in-memory cache system. Verify it handles cache expiration (TTL) and size-bounding correctly by writing isolated tests or verification scripts.
- [x] 1.2 Integrate caching into the public read endpoints (`/api/products`, `/api/products/{id}`, `/api/products/{id}/reviews`) in `backend/app/main.py`. Verify that private/authenticated endpoints bypass the cache.
- [x] 1.3 Add cache invalidation logic inside `moderate_review` endpoint in `backend/app/main.py`. When a review is approved or rejected, invalidate the respective product detail, reviews, and catalog caches. Verify that invalidation occurs immediately.

## 2. Playwright End-to-End Testing

- [x] 2.1 Install Playwright in the `frontend` folder and create a configuration file. Verify that the Playwright binary and browser dependencies install successfully.
- [ ] 2.2 Create end-to-end tests under `frontend/e2e/shopping_and_reviews.spec.ts` covering:
    - Purchasing journey (catalog -> cart -> register/login -> checkout summary -> simulated checkout confirmation).
    - Review workflow (submission -> verification that it is pending and hidden -> moderator approval -> verification that it is now visible).
    - Access control (standard customer blocked from visiting `/moderation`).
  Verify that the tests run and pass against a locally running frontend and backend.

## 3. Docker Containerization & Orchestration

- [x] 3.1 Create `backend/Dockerfile` with a secure, multi-stage build structure. Verify that building and running the container manually starts the FastAPI server successfully.
- [x] 3.2 Create `frontend/Dockerfile` with a multi-stage build compiling React assets and serving them via lightweight Nginx. Verify that the container runs and serves the static files.
- [x] 3.3 Create `docker-compose.yml` at the project root to orchestrate the frontend and backend, configuring custom bridge networking and health checks. Verify that running `docker compose up` starts both services in a healthy state.

## 4. Continuous Integration Pipeline & Quality Reports

- [x] 4.1 Create `.github/workflows/ci.yml` with a multi-step execution pipeline (checkout, install, lint, backend tests with coverage, frontend tests, Playwright tests). Verify that the workflow file is syntactically valid.
- [x] 4.2 Document exact commands to run tests and collect raw coverage outputs (`coverage.xml` for backend, `lcov.info` for frontend) and update `README.md` with moderator credentials and simple exact startup/testing instructions. Verify that the documented commands run and generate the required coverage files as expected.
