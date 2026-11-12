# Feature Specification: Stage 3 Delivery, Caching, CI and Containers

**Feature Branch**: `003-delivery-caching`

**Created**: 2026-11-06

**Status**: Approved

**Input**: User description: "Implement Stage 3 of this existing e-commerce project using SEED-3.md as the functional source. Create all native Stage 3 specification artifacts before implementing code, tests, containers, caching and CI. Keep the scope aligned with Stage 3 Option A: real end-to-end tests, CI, multi-stage containers, and safe bounded public API caching. Preserve Stage 2 reviews with images and moderation as well as the original purchasing journey. All output must be in English. Keep the same existing stack and avoid external paid services or deployments."

## User Scenarios & Testing

### User Story 1 - Secure and Fast Product Catalog Browsing (Priority: P1)

As a user (visitor or customer), I want to browse the product catalog and reviews quickly and reliably through API response caching so that I have a fast shopping experience.

**Why this priority**: Public read performance and server resource protection. Core caching requirement.

**Independent Test**: Request the product catalog multiple times and verify that the backend returns cached results within a specific expiry window (e.g., 60 seconds). Submit a review, approve it as a moderator, and verify that the product's review cache is invalidated and the newly approved review is immediately visible on the product details page.

**Acceptance Scenarios**:

1. **Given** a user is viewing the product catalog, **When** they request `/api/products` for the first time, **Then** the request is fetched from storage and cached. Subsequent requests within the expiry duration MUST return the cached response.
2. **Given** a user is viewing a product details page, **When** they request `/api/products/{product_id}/reviews`, **Then** the response is cached. Subsequent requests for that product's reviews within the expiry duration MUST return the cached response.
3. **Given** a review is pending moderation, **When** the moderator approves the review via `/api/moderation/reviews/{review_id}/status`, **Then** the review cache for that specific product MUST be immediately invalidated.
4. **Given** the review cache is invalidated, **When** any user requests `/api/products/{product_id}/reviews`, **Then** the updated list of approved reviews is served directly and cached anew.
5. **Given** an authenticated user or a moderator accessing their dashboard, **When** they request active session data or `/api/moderation/reviews`, **Then** these requests MUST NOT be cached in any shared public cache to prevent data leaks.

---

### User Story 2 - Automated Delivery Pipeline (Priority: P2)

As a developer or release manager, I want an automated CI workflow that installs dependencies, runs tests, collects coverage, builds the frontend, and executes E2E verification so that changes are verified before release.

**Why this priority**: Continuous Integration and automated validation of the full application stack.

**Independent Test**: Trigger the CI pipeline (e.g., via GitHub Actions) and verify that it completes successfully, producing test reports and coverage outputs.

**Acceptance Scenarios**:

1. **Given** the repository receives a push or pull request, **When** the CI workflow runs, **Then** it MUST install python and node dependencies, compile/build the frontend, run backend and frontend tests, generate coverage reports (`coverage.xml` and `lcov.info`), and execute the full E2E test suite.
2. **Given** the CI pipeline runs, **When** a test fails in the backend, frontend, or E2E suite, **Then** the pipeline MUST fail immediately and report the error.

---

### User Story 3 - Reproducible Container Orchestration (Priority: P3)

As a developer or system operator, I want to deploy and run the application locally using multi-stage Docker builds and Docker Compose so that the system runs identically across all environments.

**Why this priority**: Clean deployment, isolation, and production-like local orchestration.

**Independent Test**: Run `docker compose up --build` and verify both frontend and backend start, form a container network, and are accessible and fully functional with proper health checking.

**Acceptance Scenarios**:

1. **Given** Docker and Docker Compose are installed, **When** a developer runs the compose build/up command, **Then** the multi-stage Dockerfiles build minimal images for backend and frontend.
2. **Given** the containers are starting up, **When** they undergo health checks, **Then** the backend reports healthy only after its server is ready, and the frontend starts serving only when the backend is accessible.
3. **Given** the containerized environment is running, **When** a user performs checkout or submits/moderates reviews, **Then** the entire journey succeeds seamlessly over the internal container network.

---

### Edge Cases

- **Cache Expiry Boundary**: A request made exactly at the expiration timestamp is evicted and fetches fresh data.
- **Concurrent Cache Requests**: Simultaneous requests to the same public endpoint should not cause race conditions or duplicate cache-population writes on the backend.
- **Moderator Access Denied E2E Check**: Regular users attempting to request moderator routes are blocked with a clear 401/403 message, and this constraint is actively validated in the end-to-end tests.

## Requirements

### Functional Requirements

#### Public Response Caching
- **FR-001**: The system MUST implement in-memory response caching for public read endpoints: `/api/products` and `/api/products/{product_id}/reviews`.
- **FR-002**: Cached responses MUST have a configurable Time-To-Live (TTL) of 60 seconds by default.
- **FR-003**: The response cache for a product's reviews MUST be immediately invalidated when a review for that product is approved by a moderator.
- **FR-004**: Authentication-specific responses, user profiles, and the moderation queue (`/api/moderation/reviews`) MUST NOT be cached, preventing data leaks across users.

#### End-to-End Testing (Real Verification)
- **FR-005**: The system MUST include a complete end-to-end test suite using Playwright.
- **FR-006**: The E2E tests MUST run against the real running frontend and backend (no mock servers for E2E).
- **FR-007**: The E2E tests MUST cover the complete user purchasing journey (add to cart, checkout form submission, and verification of the confirmation screen).
- **FR-008**: The E2E tests MUST cover the review journey: submission by customer, verified as hidden/pending, approved by moderator, and verified as visible to the public.
- **FR-009**: The E2E tests MUST explicitly verify that regular customers are denied access to the moderator dashboard or moderator endpoints.

#### Containerization & Orchestration
- **FR-010**: The project MUST provide multi-stage `Dockerfile` configurations for both frontend and backend to produce minimal, secure production-ready images.
- **FR-011**: The project MUST provide a `docker-compose.yml` file to orchestrate both services, setting up a shared container network.
- **FR-012**: The container setup MUST implement a documented health/readiness checking strategy (e.g., using `curl` or health endpoints).

#### CI Pipeline & Quality Analysis
- **FR-013**: The project MUST contain a continuous integration workflow configuration (GitHub Actions).
- **FR-014**: The CI pipeline MUST run tests and collect coverage reports: `coverage.xml` for Python backend, and `lcov.info` for React frontend. It MUST upload these reports and Playwright E2E reports as artifacts using stable v4 actions.
- **FR-014-A**: The CI workflow MUST migrate to `actions/checkout@v4`, `actions/setup-node@v4`, and `actions/upload-artifact@v4`, ensuring deprecated `actions/upload-artifact@v3` is replaced, the unsupported `retries` option is removed, and Playwright is installed with OS-level dependencies via `--with-deps`.
- **FR-015**: The frontend production build MUST succeed with the environment variable `CI=true` set, ensuring there are no ESLint warnings or compilation errors.

## Success Criteria

### Measurable Outcomes
- **SC-001**: Public catalog and reviews endpoints return cached responses under 10ms for hit requests.
- **SC-002**: Approved reviews are visible on the public product page within 100ms of moderation approval due to proactive cache invalidation.
- **SC-003**: 100% of the defined E2E scenarios pass successfully on a local run.
- **SC-004**: Docker images build successfully, and backend image is under 200MB in compressed size (using slim/alpine base images).

## Assumptions

- **Local Storage Assumption**: Since database state is in-memory, container restarts will reset reviews and user accounts (except pre-configured users like `moderator`).
- **No External Dependencies**: Docker Compose and CI run without requiring any external paid cloud caching, CDN, database, or E2E services.
