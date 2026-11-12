# Design

## Context

See proposal.md for the motivation. The current Stage 2 application runs a Python/FastAPI backend using SQLAlchemy with SQLite, and a React/TypeScript frontend with TailwindCSS and Vite. Testing infrastructure is minimal, lacking automated browser end-to-end verification, containerized orchestration, API caching, or a CI configuration.

## Goals / Non-Goals

**Goals:**
- Implement a thread-safe, bounded, in-memory API response cache for `/api/products`, `/api/products/{id}`, and `/api/products/{id}/reviews`.
- Implement cache invalidation specifically when a review is approved or rejected by a moderator.
- Prevent any authentication, registration, session, or moderator dashboard endpoints from being cached or leaked between users.
- Configure a complete Playwright end-to-end testing suite to test customer purchasing and product review workflows on a real browser against live services.
- Provide production-ready, multi-stage Docker build files for the frontend and backend, with a docker-compose setup and robust healthchecks.
- Create a GitHub Actions CI pipeline executing all linting, testing, and building, generating frontend `lcov.info` and backend `coverage.xml`.

**Non-Goals:**
- Setting up external caching services like Redis, Memcached, or Varnish (local thread-safe Python memory caching is sufficient and fits the zero-dependencies constraint).
- Multi-region replication, CDN integration, or production cloud deployments (this remains a local demonstration).
- Replacing mock payment systems with actual payment providers.

## Decisions

### 1. Custom Bounded, Thread-Safe In-Memory Cache in Python
- **Rationale**: Since we want a robust, lightweight local-only solution without external infrastructure (like Redis), we will build a dedicated, thread-safe, bounded caching class in `backend/app/cache.py`. It will support:
  - Cache size limit (e.g. max 100 entries) to prevent memory bloating (bounded memory cache).
  - Key-based expiration (Time-To-Live).
  - Grouping keys or invalidating keys matching a pattern (such as `/api/products/{id}*` and `/api/products/{id}/reviews*`).
  - Strict exclusion of auth-related endpoints and the moderation queue.
- **Alternatives Considered**: Using FastAPI third-party caching libraries (e.g., `fastapi-cache2`). However, custom caching is simpler to control, has zero new dependencies, and allows exact, surgically clean invalidation tailored perfectly to our reviews moderation model.

### 2. Playwright for End-to-End Testing
- **Rationale**: Playwright is extremely reliable, supports modern SPA testing with auto-waiting, runs headless across Chromium/Webkit/Firefox, and compiles very well in modern TypeScript/Vite environments.
- **Alternatives Considered**: Cypress. While Cypress is popular, Playwright integrates more easily into headless environments (especially on Windows and Linux CI environments), has less overhead, and has superior parallelization and multi-page capabilities.

### 3. Nginx for Frontend Container Delivery
- **Rationale**: The React frontend built with Vite compiles down to static HTML, CSS, and JS. Serving these via standard lightweight `nginx:alpine` in the Docker multi-stage container is the industry standard for performance, safety, and efficiency.
- **Alternatives Considered**: Using standard Node/Vite preview command inside the container. This is not production-grade, consumes excessive memory, and lacks robust HTTP features of web servers like Nginx.

### 4. GitHub Actions for CI Pipeline
- **Rationale**: GitHub Actions is the standard, modern, zero-overhead platform integrated directly into Git repositories, allowing clean, parallel step executions for npm, python, docker, and end-to-end browser suites.

## Risks / Trade-offs

- **[Risk] Cache Staleness**: A user approves a review, but the catalog still shows old ratings or review list because of the cache.
  - **Mitigation**: Implement strict cache invalidation on review actions. When a moderator approves or rejects a review for product `id`, the backend will instantly purge keys matching `/api/products` (the main catalog), `/api/products/{id}`, and `/api/products/{id}/reviews`.
- **[Risk] Cross-User Session/Queue Cache Leak**: A user requests their private moderation queue or user detail, and it gets cached and served to another user.
  - **Mitigation**: Caching will be explicitly white-listed only for public read-only endpoints: `get_products`, `get_product_detail`, and `get_product_reviews`. Any endpoints containing authorization, headers, or stateful actions (like `/api/moderation/*` or `/api/auth/*`) will bypass the cache completely.
