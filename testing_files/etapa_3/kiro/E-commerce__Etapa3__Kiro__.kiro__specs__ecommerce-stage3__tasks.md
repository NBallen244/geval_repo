# Implementation Plan: E-Commerce Stage 3 (Architecture & Automated Delivery Verification)

## Overview

This plan converts the approved Stage 3 design into an ordered set of incremental steps. All work is additive: no Stage 1 or Stage 2 endpoint body, view, or journey changes, except for added cache/freshness response headers. Work spans the FastAPI backend (caching + container + CI wiring) and the Vite frontend (Playwright E2E + coverage + container). Each implementation step is paired with the verification that proves it. All identifiers, comments, and user-facing text are in English.

## Tasks

- [x] 1. Bounded TTL response cache (backend)
  - Implement `backend/app/services/response_cache.py`: `BoundedTTLCache` with `get`/`set`/`invalidate`/`clear`, insertion-ordered eviction at `max_entries`, per-entry TTL expiry, and a `threading.Lock`. Expose a module-level singleton configured from `CATALOG_CACHE_TTL_SECONDS` (default 30, 0 disables) and `CATALOG_CACHE_MAX_ENTRIES` (default 256), plus an `invalidate()` hook function.
  - _Requirements: 5.2, 5.3, 5.5_

- [x] 2. Catalog cache middleware (backend)
  - Implement `backend/app/api/cache_middleware.py`: `CatalogCacheMiddleware` caching only `GET /products` and `GET /products/{id}`; HIT/MISS via `X-Cache`; `Cache-Control: public, max-age=<ttl>` on cacheable responses; `Cache-Control: no-store` on `/auth`, `/moderation`, and `/products/{id}/reviews`; only `200` responses stored. Register it additively in `backend/app/main.py`.
  - _Requirements: 5.1, 5.4, 7.1_

- [x] 3. Moderation cache-invalidation hook (backend)
  - In `backend/app/services/review_service.py`, call `response_cache.invalidate()` after a successful `approve_review`/`reject_review` terminal transition. Keep the review-listing endpoint uncached so newly approved reviews are immediately visible.
  - _Requirements: 5.5_

- [x] 4. Backend cache tests
  - Add `backend/tests/test_response_cache.py` (TTL expiry, eviction) and `backend/tests/test_cache_middleware.py` (HIT/MISS on catalog, no-store on reviews/moderation, 404 not cached) using `TestClient`.
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 5. Frontend coverage + E2E scripts and deps
  - Add `@playwright/test` and a coverage-capable test script to `frontend/package.json`: `test:coverage` (vitest with V8 coverage → `coverage/lcov.info`) and `test:e2e` (`playwright test`). Add `@vitest/coverage-v8` and configure coverage reporters (`text`, `lcov`) in `vite.config.ts`.
  - _Requirements: 6.2, 3.3_

- [x] 6. Playwright config booting the real stack
  - Add `frontend/playwright.config.ts` with a `webServer` array that starts the real backend (`uvicorn` from `../backend`) and the real frontend (`vite preview` of the production build), waits for readiness, and runs Chromium. Add `frontend/.gitignore` entries for `playwright-report/`, `test-results/`, and `coverage/`.
  - _Requirements: 1.1, 1.3, 2.1_

- [x] 7. E2E specs
  - [x] 7.1 `frontend/e2e/purchasing-journey.spec.ts`: browse → add to cart → register/sign-in → confirm checkout → assert confirmation + reset. _Requirements: 1.1, 1.2, 1.3_
  - [x] 7.2 `frontend/e2e/review-lifecycle.spec.ts`: customer submits review → hidden while pending → moderator approves → publicly visible with updated summary. _Requirements: 2.1, 2.2_
  - [x] 7.3 `frontend/e2e/moderation-access.spec.ts`: a regular customer is denied moderation access; no state change. _Requirements: 2.3_

- [x] 8. Multi-stage containers + orchestration
  - [x] 8.1 `backend/Dockerfile` (multi-stage `python:3.11-slim`) + `backend/.dockerignore`. _Requirements: 4.1, 4.5_
  - [x] 8.2 `frontend/Dockerfile` (`node:20-alpine` build → `nginx:1.27-alpine`) + `frontend/nginx.conf` + `frontend/.dockerignore`. _Requirements: 4.2, 4.5_
  - [x] 8.3 `docker-compose.yml`: backend `8000:8000` with `/health` healthcheck, frontend `8080:80`, user-defined bridge network, one-command `docker compose up --build`. _Requirements: 4.3, 4.4_

- [x] 9. CI pipeline
  - Add `.github/workflows/ci.yml`: install backend + frontend deps; backend tests with `coverage.xml`; frontend unit tests with `lcov.info`; `npm run build`; Playwright install + E2E run; upload artifacts; no deploy.
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 6.1, 6.2_

- [x] 10. Verification and documentation
  - Run the real backend suite with `coverage.xml`, the frontend unit suite with `lcov.info`, the production build, and the Playwright E2E suite. Document any unavailable runtime (e.g. Docker) honestly without claiming a container run. Update root `README.md` with exact PowerShell startup/testing commands, the caching/containers/CI/E2E notes, and the moderator demo credentials. Do not invent a coverage target.
  - _Requirements: 1, 2, 3.4, 4, 5, 6, 7_

## Notes

- Stage 3 is additive: the nine existing endpoints' bodies are unchanged; only cache/freshness response headers are added.
- Caching is restricted to the two session-independent catalog GETs; session-varying and moderation responses are `no-store` and never shared-cached (prevents cross-user leakage; keeps newly approved reviews correct).
- Docker validation runs only if Docker is available locally; otherwise the limitation is documented honestly and the artifacts are validated by inspection + the CI definition.

## Completion status

All Stage 3 tasks are implemented and verified locally:

- **Backend:** the bounded TTL cache, catalog cache middleware, and moderation invalidation hook are implemented and wired additively. The full backend suite passes (**105 tests**) and a raw `backend/coverage.xml` (Cobertura) is produced via `coverage run -m pytest` + `coverage xml`.
- **Frontend:** the unit/integration suite passes (**151 tests**) via `npm run test:coverage`, producing a raw `frontend/coverage/lcov.info` (LCOV). The production build (`npm run build`) succeeds.
- **E2E:** the Playwright suite runs against the **real** stack (fresh `uvicorn` backend + `vite preview` of the production build, Chromium) and all **3 specs pass** — the purchasing journey, the review submit→pending→approve→public lifecycle, and the regular-customer moderation access-denied check.
- **Containers / CI:** multi-stage `backend/Dockerfile` and `frontend/Dockerfile` (+ `nginx.conf`, `.dockerignore` files), a one-command `docker-compose.yml` with a `/health` healthcheck, and a `.github/workflows/ci.yml` pipeline (install → test+coverage → build → E2E, artifacts only, no deploy).

**Runtime limitation (honest):** Docker is **not installed** in the local validation environment (`docker` is unavailable on PATH). The Dockerfiles, `nginx.conf`, and `docker-compose.yml` were validated by inspection and are exercised by the CI definition; **no container run is claimed locally.** When Docker is available, `docker compose up --build` starts the stack (backend on host 8000, frontend on host 8080). No coverage target is invented and no unexecuted check is claimed as passed.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2", "3", "5"] },
    { "id": 2, "tasks": ["4", "6", "8.1", "8.2"] },
    { "id": 3, "tasks": ["7.1", "7.2", "7.3", "8.3", "9"] },
    { "id": 4, "tasks": ["10"] }
  ]
}
```
