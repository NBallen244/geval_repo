# Proposal

## Why

To guarantee the reliability, performance, and long-term maintainability of the academic e-commerce system, we must establish automated quality gates and robust deployment infrastructure. Introducing bounded in-memory API response caching will optimize public-facing page loads without compromising user-specific session security, while real end-to-end tests and automated CI pipelines will prevent functional regressions as the codebase evolves.

## What Changes

- **Bounded Public API Caching**: Implement thread-safe, bounded in-memory response caching for public read endpoints (`/api/products`, `/api/products/{id}`, and `/api/products/{id}/reviews`) with a documented TTL (Time-To-Live).
- **Cache Invalidation on Mutation**: Automatically invalidate cached responses when a review is approved or when the database state changes, ensuring immediate public visibility of approved content.
- **Leak Prevention**: Ensure that authentication-specific endpoints, user sessions, and moderation dashboards are never served from a shared cache, avoiding security or cross-user data leakage.
- **Playwright End-to-End Tests**: Implement an end-to-end automated testing suite with Playwright. This covers the complete customer purchasing journey (catalog to confirmation) and the entire review-moderation lifecycle (submission, pending state, moderator dashboard approval, public visibility, and access-denied check for standard customers).
- **Docker Multi-Stage Containers**: Create production-ready, multi-stage Dockerfiles for both frontend and backend, and coordinate them locally using a single docker-compose configuration with health checks.
- **Continuous Integration (CI) Pipeline**: Introduce a local and server-executable GitHub Actions CI pipeline that installs dependencies, executes unit/integration tests, runs the Playwright E2E suite, generates raw coverage outputs, and builds the frontend production bundle.

## Capabilities

### New Capabilities
- `delivery-automation-and-caching`: Covers public API response caching, automatic invalidation on review approval, multi-stage Docker orchestration, automated CI pipeline configuration, coverage collection, and comprehensive Playwright end-to-end test scenarios.

### Modified Capabilities
<!-- None -->

## Impact

- **Backend API (`backend/app/main.py`)**:
  - Integrate a bounded thread-safe in-memory cache for public read endpoints.
  - Clear relevant product and review cache entries upon review moderation (approval).
  - Produce a test coverage report in XML format (`coverage.xml`).
- **Frontend App (`frontend`)**:
  - Ensure compatibility with automated Playwright browser automation.
  - Produce a test coverage report in LCOV format (`lcov.info`).
- **DevOps/Infrastructure**:
  - `backend/Dockerfile`: Multi-stage build for Python FastAPI.
  - `frontend/Dockerfile`: Multi-stage build compiling React/Vite assets and serving via Nginx or a lightweight static file server.
  - `docker-compose.yml`: Orchestrates frontend, backend, networks, ports, and container health checking.
  - `.github/workflows/ci.yml`: CI configuration defining the pipeline steps.
- **Tests**:
  - `frontend/e2e/`: End-to-end tests written using Playwright.
