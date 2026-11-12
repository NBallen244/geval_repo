# Requirements Document

## Introduction

Stage 3 evolves the inherited Stage 2 demonstration e-commerce application along **Stage 3 Option A: architecture and automated delivery verification**. It adds real end-to-end (E2E) tests against the running frontend and backend, a continuous-integration (CI) pipeline that installs, tests, measures coverage, builds, and runs the E2E checks, reproducible multi-stage Docker builds with a simple local orchestration command, and bounded response caching for suitable public read endpoints.

Stage 3 is purely additive to application behavior. The Stage 1 purchasing journey (browse the catalog, manage a local cart, register or sign in, complete a simulated checkout) and the Stage 2 reviews-with-images-and-moderation workflow are preserved unchanged. Stage 3 changes how the application is verified, packaged, and served, not what the application does for an end user.

This document derives its scope from `SEED-3.md`. The seed deliberately leaves several operational details undecided (E2E tool choice, cache TTLs, container base images, orchestration tooling) and delegates those choices to the tool. Each such choice is recorded as a numbered assumption in the **Assumptions** section and treated as a first-class requirement. The researcher preauthorizes these assumptions, the specs, and the implementation; no approval gates apply.

Like earlier stages, the application stays local and easy to demonstrate: no paid external services, no external deployment, and no architecture rewrite. All artifacts, source code, comments, documentation, and user-facing text are in English.

## Relationship to Stages 1 and 2

- Stage 1 (`.kiro/specs/ecommerce-stage1/`) and Stage 2 (`.kiro/specs/ecommerce-stage2/`) artifacts remain authoritative for application behavior and are not modified by Stage 3. This Stage 3 spec lives at `.kiro/specs/ecommerce-stage3/` and references the earlier stages where it builds on them.
- Stage 3 keeps the existing stack: a React + TypeScript (Vite) frontend and a Python + FastAPI backend that run and are reviewed separately and communicate over HTTP/JSON.
- Stage 3 preserves the nine HTTP endpoints across Stages 1 and 2 (six Stage 1 + three Stage 2 route groups) and the existing in-process demonstration data store plus local on-disk review images. It adds no new application endpoints; caching, containers, CI, and E2E are cross-cutting concerns layered on top.

## Glossary

- **E2E test**: An automated browser-driven test that exercises the real frontend talking to the real backend over HTTP, with no request mocking at the boundary under test.
- **CI pipeline**: An automated workflow that installs dependencies, runs backend and frontend tests with coverage, builds the frontend, and runs the E2E checks, without deploying anywhere.
- **Multi-stage build**: A Docker build that separates a build/dependency stage from a slim runtime stage to produce a smaller, reproducible runtime image.
- **Orchestration command**: A single documented command that starts the frontend and backend containers together with correct networking.
- **Public read endpoint**: A `GET` endpoint whose response does not depend on the caller's session or identity. In this application these are the catalog endpoints `GET /products` and `GET /products/{id}`.
- **Bounded cache**: An in-process response cache with a fixed maximum entry count and a fixed time-to-live (TTL) per entry, so memory and staleness are both bounded.
- **Coverage artifact**: A machine-readable coverage report — backend `coverage.xml` (Cobertura) and frontend `lcov.info` (LCOV) — produced by documented commands for later quality analysis.

## Assumptions

The seed delegates the following decisions to the tool. Each is a deliberate, documented, simple local-demo choice and is binding for Stage 3.

- **A1 — E2E tool.** Playwright is used for E2E tests, driven from the frontend workspace (`frontend/`), because it bundles browser management and a test runner with low setup cost and integrates cleanly with a Vite app. The E2E suite starts the real backend (`uvicorn`) and the real frontend (Vite preview of the production build) and drives a real browser against them. No API calls are mocked inside the browser for the journeys under test.
- **A2 — E2E coverage of journeys.** The E2E suite covers (a) the Stage 1 purchasing journey through simulated checkout, (b) the Stage 2 review lifecycle — submit as a customer, review is hidden while pending, a moderator approves it, and it becomes publicly visible — and (c) an access-denied check: a regular customer cannot reach the moderation queue/actions.
- **A3 — Backend cache scope and policy.** Only the two catalog read endpoints (`GET /products`, `GET /products/{id}`) are cached. They carry no session-specific data, so a shared cache cannot leak between users. `GET /products/{id}/reviews` is **never** shared-cached because its body varies with the caller's session (it includes the caller's own non-approved review); moderation queue responses and any authenticated response are likewise never cached. The cache is in-process, bounded by a maximum entry count, and each entry expires after a short TTL.
- **A4 — Cache TTL and invalidation.** The catalog cache TTL default is 30 seconds (overridable by the `CATALOG_CACHE_TTL_SECONDS` environment variable; `0` disables caching). The catalog is static demonstration data, so TTL expiry is the primary freshness mechanism. Because the seed requires that newly approved reviews become publicly visible correctly, the review-listing endpoint is left uncached; an explicit cache-invalidation hook is additionally invoked on any moderation state change so that, even if review caching were introduced later, approval would immediately invalidate affected entries. No stale catalog entry can outlive its TTL.
- **A5 — Cache correctness headers.** Cached public responses carry an `X-Cache: HIT|MISS` response header for observability and a short `Cache-Control: public, max-age=<ttl>` header. Non-cacheable endpoints send `Cache-Control: no-store` so intermediaries do not cache per-user data.
- **A6 — Container images and ports.** The backend image is based on `python:3.11-slim` and runs `uvicorn` on container port 8000. The frontend is built to static files in a build stage and served by `nginx:1.27-alpine` on container port 80, published to host port 8080. A reverse-proxy rule in nginx forwards `/api/*`-style calls is **not** introduced to avoid changing the frontend's existing absolute `http://localhost:8000` base URL; instead the backend is published on host port 8000 so the existing client base URL keeps working unchanged in the local Docker run.
- **A7 — Orchestration tooling.** Docker Compose (`docker-compose.yml`) provides the single orchestration command (`docker compose up --build`). Services share a user-defined bridge network; the backend exposes a `/health` readiness endpoint (already present) used as the Compose healthcheck.
- **A8 — CI platform.** GitHub Actions (`.github/workflows/ci.yml`) runs the pipeline on push and pull request. It installs backend and frontend dependencies, runs backend tests with `coverage.xml`, runs frontend unit tests with `lcov.info`, builds the frontend, installs Playwright browsers, and runs the E2E suite. It uploads coverage and Playwright artifacts but does not deploy. The CI definition is authoritative documentation of the commands even where a runtime (e.g. Docker) is unavailable locally.
- **A9 — No behavior change.** Stage 3 does not change any request/response body of the nine existing endpoints beyond adding caching/freshness response headers. The frontend's API base URL, views, and journeys are unchanged.

## Requirements

### Requirement 1 — End-to-end purchasing journey test

**User Story:** As a maintainer, I want an automated E2E test of the purchasing journey, so that catalog → cart → authentication → simulated checkout is verified against the real running stack.

#### Acceptance Criteria

1. WHEN the E2E suite runs the purchasing-journey test THEN it SHALL start the real backend and the real frontend production build and drive a real browser against them without mocking the API boundary.
2. WHEN a user browses the catalog, adds a product to the cart, registers or signs in, and confirms checkout THEN the test SHALL assert a visible checkout confirmation and a reset-to-new-purchase state.
3. IF the backend or frontend is not reachable THEN the test SHALL fail with a clear error rather than passing silently.

### Requirement 2 — End-to-end review lifecycle test

**User Story:** As a maintainer, I want an automated E2E test of the review-and-moderation lifecycle, so that the Stage 2 workflow is verified against the real running stack.

#### Acceptance Criteria

1. WHEN a signed-in customer submits a review for a product THEN the test SHALL assert the submission is accepted and the review is NOT publicly visible while pending.
2. WHEN a moderator signs in and approves the pending review THEN the test SHALL assert the review becomes publicly visible with the rating summary updated.
3. WHEN a regular customer attempts to access the moderation queue or a moderation action THEN the test SHALL assert access is denied and no moderation state changes.

### Requirement 3 — CI pipeline

**User Story:** As a maintainer, I want a CI pipeline, so that every change is installed, tested, measured, built, and E2E-checked automatically without deploying.

#### Acceptance Criteria

1. WHEN CI runs THEN it SHALL install backend and frontend dependencies.
2. WHEN CI runs the backend tests THEN it SHALL produce a backend `coverage.xml` artifact.
3. WHEN CI runs the frontend unit tests THEN it SHALL produce a frontend `lcov.info` artifact.
4. WHEN CI builds the frontend THEN the production build SHALL succeed.
5. WHEN CI runs the E2E suite THEN it SHALL start the real stack and execute the Playwright tests.
6. CI SHALL NOT publish or deploy to any external infrastructure.

### Requirement 4 — Reproducible multi-stage containers and orchestration

**User Story:** As a maintainer, I want multi-stage Docker builds and a one-command local orchestration, so that the stack runs reproducibly without a bespoke setup.

#### Acceptance Criteria

1. The backend SHALL have a multi-stage `Dockerfile` producing a slim runtime image that runs the FastAPI app.
2. The frontend SHALL have a multi-stage `Dockerfile` that builds the static assets and serves them from a slim web server image.
3. A single documented orchestration command SHALL start both services with correct container networking.
4. The orchestration SHALL use a documented health/readiness strategy for the backend.
5. The containers SHALL NOT depend on any paid external service or perform any deployment.

### Requirement 5 — Bounded public API caching

**User Story:** As a maintainer, I want bounded caching on suitable public read endpoints, so that repeated catalog reads are cheaper without serving stale or cross-user data.

#### Acceptance Criteria

1. The backend SHALL cache only public read endpoints whose response is independent of the caller's session (`GET /products`, `GET /products/{id}`).
2. The cache SHALL be bounded by a maximum entry count and a per-entry TTL, both documented.
3. A cached response SHALL expire after its TTL so it cannot be served indefinitely.
4. Session-specific or moderation responses SHALL NOT be served from the shared cache and SHALL be marked non-cacheable.
5. WHEN a review is approved THEN the public visibility of that review SHALL be correct on the next read (the review-listing endpoint is uncached, and a cache-invalidation hook fires on moderation state changes).

### Requirement 6 — Coverage artifacts

**User Story:** As a maintainer, I want documented commands that produce standard coverage artifacts, so that quality can be analyzed later.

#### Acceptance Criteria

1. A documented backend command SHALL produce `coverage.xml` (Cobertura).
2. A documented frontend command SHALL produce `lcov.info` (LCOV).
3. The documentation SHALL NOT invent a coverage target nor claim an unexecuted check passed.

### Requirement 7 — Preservation of earlier stages

**User Story:** As a maintainer, I want Stages 1 and 2 preserved, so that Stage 3 adds verification/packaging without regressing behavior.

#### Acceptance Criteria

1. The nine existing endpoints' request/response bodies SHALL remain unchanged except for added cache/freshness response headers.
2. The existing frontend journeys and views SHALL remain unchanged.
3. The existing backend and frontend unit/integration test suites SHALL continue to pass.
