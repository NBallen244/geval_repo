# Spec Delta

## Purpose

Defines the requirements for automated delivery verification, CI pipeline automation, multi-stage Docker orchestration, and bounded public API caching with invalidation.

## ADDED Requirements

### Requirement: Public API Response Caching
The system SHALL cache GET responses for public read endpoints (`/api/products`, `/api/products/{id}`, and `/api/products/{id}/reviews`) using a bounded thread-safe in-memory cache with a default Time-To-Live (TTL). The system MUST NOT cache any authentication-specific endpoints, user sessions, or moderation queues.

#### Scenario: Cache public endpoint response
- **WHEN** a client requests `/api/products` twice within the cache TTL
- **THEN** the first request fetches from the database and caches the response, while the second request is served directly from the cache.

#### Scenario: Prevent caching of authenticated or moderation endpoints
- **WHEN** a user or moderator requests private or stateful endpoints like `/api/moderation/reviews` or `/api/auth/login`
- **THEN** the system does not cache these responses, ensuring no user sessions or sensitive dashboards are leaked.

### Requirement: Cache Invalidation on Moderator Action
The system SHALL automatically invalidate cached public read responses for `/api/products/{id}` and `/api/products/{id}/reviews` immediately when a moderator approves or rejects a review for that product ID.

#### Scenario: Invalidate cache on review approval
- **WHEN** a moderator approves a pending review for a product with ID 1
- **THEN** the system invalidates the cached responses for `/api/products/1` and `/api/products/1/reviews` immediately, making the approved review and the updated average rating visible on subsequent requests.

### Requirement: Playwright End-to-End Test Suite Verification
The system SHALL provide a Playwright end-to-end automated testing suite that validates the full purchasing journey, review-moderation lifecycle, and access restrictions against the real frontend and backend.

#### Scenario: E2E Purchasing Journey
- **WHEN** the Playwright test suite executes the purchasing journey
- **THEN** it browses the catalog, adds a product to the local cart, authenticates, completes checkout with minimal demonstration details, and verifies the simulated checkout confirmation displays in plain English without markdown markers.

#### Scenario: E2E Review and Moderation Journey
- **WHEN** the Playwright test suite executes the review and moderation journey
- **THEN** it submits a new product review, verifies it remains hidden on the public product details page, logs in as the moderator user to approve the review, and verifies that the review becomes publicly visible.

#### Scenario: E2E Access Control Check
- **WHEN** a standard customer attempts to access the moderator dashboard at `/moderation`
- **THEN** the system denies access and redirects them back to the login page or catalog.

### Requirement: Docker Multi-Stage Container Deployment
The system SHALL provide reproducible multi-stage Dockerfiles and a `docker-compose.yml` file that orchestrates the frontend and backend locally with appropriate container networking and health checks.

#### Scenario: Run orchestrated container stack
- **WHEN** a developer starts the orchestration using `docker compose up`
- **THEN** the backend and frontend containers start up, establish secure network communication, pass internal health checks, and serve the application locally.

### Requirement: Automated CI Quality Pipeline
The system SHALL provide an automated CI pipeline configuration file that installs dependencies, executes backend and frontend tests, runs Playwright E2E checks, and generates code coverage files (`coverage.xml` for Python and `lcov.info` for React).

#### Scenario: Execute CI workflow
- **WHEN** the CI configuration runs on a continuous integration server or local runner
- **THEN** it executes all linting, unit testing, and Playwright verification steps successfully, and outputs valid test coverage files.
