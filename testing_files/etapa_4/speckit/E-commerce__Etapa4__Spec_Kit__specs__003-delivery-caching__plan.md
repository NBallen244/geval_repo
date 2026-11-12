# Implementation Plan: Stage 3 Delivery, Caching, CI and Containers

This document maps out the specific implementation phases, tasks, and validation strategies for Stage 3.

## Technical Context & Strategy

We are enhancing the existing stack:
- **Backend**: Python (FastAPI).
- **Frontend**: React (TypeScript, Vite/CRA).
- **Tooling**: Playwright for end-to-end tests, Docker & Docker Compose for containerization, GitHub Actions for CI.

### Phase 1: Bounded Caching on Backend
- Implement a thread-safe, generic caching mechanism in `backend/src/cache.py` or directly in `backend/src/main.py`.
- Integrate caching on `/api/products` and `/api/products/{product_id}/reviews`.
- Ensure invalidation of `/api/products/{product_id}/reviews` happens immediately inside the POST status update route `/api/moderation/reviews/{review_id}/status`.
- Add backend unit/integration tests to verify caching behavior (hits, misses, expiration, and invalidation).

### Phase 2: End-to-End Tests (Playwright)
- Initialize Playwright in the project directory (under `e2e/` or `frontend/` - we will put it in `frontend/playwright/` or a root-level `e2e/` folder to make it distinct and highly visible). Let's create an `e2e/` folder in the workspace root, as it is clean and covers both backend and frontend.
- Write a comprehensive E2E test suite covering:
  - **Test Case 1**: Customer purchasing journey (Register/Login -> Browse Catalog -> Add to Cart -> Checkout Form -> Verify confirmation disclaimer screen).
  - **Test Case 2**: Product review, moderation, and visibility journey (Submit a review as user -> Verify not visible on public details page -> Log in as `moderator` -> Navigate to moderator dashboard -> Approve review -> Verify review is now visible on public details page).
  - **Test Case 3**: Access control check (Log in as regular customer -> Attempt to load or call moderator endpoints/view dashboard -> Verify permission denied message).

### Phase 3: Containerization & Orchestration
- Create `backend/Dockerfile` (multi-stage build using a secure python-slim base, installing dependencies, copying source, and running Uvicorn).
- Create `frontend/Dockerfile` (multi-stage build compiling the React assets with Node, then copying and serving them with a web server like Nginx or a lightweight static file server, exposing port `3000`).
- Create `docker-compose.yml` in the project root to start both containers inside the `ecommerce-net` network with proper healthcheck declarations.

### Phase 4: CI Pipeline & Quality Reports
- Create `.github/workflows/ci.yml` defining the workflow triggered on pushes and pull requests to `main`.
- Add jobs for:
  - Python dependency installation, pytest execution, and producing `backend/coverage.xml`.
  - Node dependency installation, React unit tests, and producing `frontend/coverage/lcov.info`.
  - Frontend production compilation build.
  - Integration/E2E Playwright run against local running processes.

---

## Constitution Check & Architectural Gates

We align with the project constraints:
1. **Security**: We do not hardcode passwords or sensitive session info. Moderator credentials are standard (`moderator` / `moderator`) for demo purposes, as inherited.
2. **Language**: All comments, specifications, and user interfaces are strictly in English.
3. **No Mocking in E2E**: End-to-end tests run against real, fully running frontend and backend processes.
4. **No External Infrastructure**: All checks, databases, and caches run strictly in-memory or locally inside the containers.
