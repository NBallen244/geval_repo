# Design Document — E-Commerce Stage 3 (Architecture & Automated Delivery Verification)

## Overview

Stage 3 layers four cross-cutting concerns onto the unchanged Stage 1 + Stage 2 application: real end-to-end tests, a CI pipeline, reproducible multi-stage containers with one-command orchestration, and bounded caching for public catalog reads. No application endpoint behavior changes beyond the addition of cache/freshness response headers. The stack stays React + TypeScript (Vite) on the frontend and Python + FastAPI on the backend, communicating over HTTP/JSON, with an in-process demonstration data store and local on-disk review images.

The design goals are: (1) verify the real running stack, not mocks; (2) keep caching provably safe against cross-user leakage and review-visibility staleness; (3) make packaging reproducible and runnable with a single command; (4) keep everything local and free of paid services and deployments.

## Architecture

```
            ┌─────────────────────────────────────────────┐
            │                 CI (GitHub Actions)          │
            │  install → unit tests + coverage → build →   │
            │           Playwright E2E (real stack)        │
            └───────────────┬──────────────────────────────┘
                            │ orchestrates the same commands a developer runs
        ┌───────────────────┴───────────────────┐
        ▼                                         ▼
┌───────────────┐   HTTP/JSON (8000)   ┌───────────────────────┐
│  Frontend     │ ───────────────────▶ │  Backend (FastAPI)    │
│  Vite build   │                      │                       │
│  served by    │                      │  CacheMiddleware ──┐  │
│  nginx:80     │                      │   (public GETs)    │  │
│  (host 8080)  │                      │                    ▼  │
└───────────────┘                      │  routers: catalog, auth,
                                        │  checkout, reviews, moderation
                                        │  in-process stores + on-disk images
                                        └───────────────────────┘
        ▲                                         ▲
        └────────── docker compose up --build ────┘
```

### Caching layer (backend)

A small, self-contained caching module is added and wired as FastAPI middleware. It is the only new backend code and is deliberately minimal.

- `app/services/response_cache.py` — a `BoundedTTLCache`: an in-process dict with insertion-ordered eviction (max N entries) and per-entry TTL. Operations: `get(key)`, `set(key, value)`, `invalidate(predicate=None)`, `clear()`. Entries store the serialized response body, media type, and an expiry timestamp. Thread-unsafe simplicity is acceptable for a single-process demo; a `threading.Lock` guards the dict to be safe under Uvicorn's default worker.
- `app/api/cache_middleware.py` — `CatalogCacheMiddleware` (Starlette `BaseHTTPMiddleware`). On a request it:
  1. Caches **only** `GET /products` and `GET /products/{id}` (exact path match via a compiled allow-list). Everything else passes through untouched and receives `Cache-Control: no-store` if it is an authenticated or session-varying route group (`/moderation`, `/auth`, and `/products/{id}/reviews`), otherwise no cache header is added.
  2. For a cacheable request, builds a key from method + path (no query string is used by these endpoints; no auth/session participates, so the key is user-independent).
  3. On a cache hit that has not expired, returns the stored body with `X-Cache: HIT` and `Cache-Control: public, max-age=<ttl>`.
  4. On a miss, calls downstream, and if the response is `200` stores the body and returns it with `X-Cache: MISS` and the same `Cache-Control`.
- TTL and max size come from environment variables with safe defaults: `CATALOG_CACHE_TTL_SECONDS` (default `30`, `0` disables), `CATALOG_CACHE_MAX_ENTRIES` (default `256`). When TTL is `0` the middleware is a pass-through that still sets `no-store` on the sensitive route groups.

**Why reviews are not shared-cached.** `GET /products/{id}/reviews` returns `ownReview`, which depends on the current in-process session. Caching it could serve one user's own-review view to another. It is therefore excluded from the allow-list and explicitly marked `no-store`. Catalog endpoints carry no session data, so a single shared entry is correct for every caller.

**Invalidation on moderation.** Although review listings are uncached (so approval is already immediately visible), `review_service.approve_review`/`reject_review` call a module-level `response_cache.invalidate()` hook after a successful terminal transition. This keeps a single, obvious invalidation point and makes the cache safe to extend later. The hook is a no-op for the catalog entries (catalog is unaffected by moderation) but documents and enforces the "newly approved reviews become visible correctly" requirement.

### Containers

- `backend/Dockerfile` — stage 1 (`python:3.11-slim`) installs `requirements.txt` into a virtualenv; stage 2 (`python:3.11-slim`) copies the venv and `app/`, creates the git-ignored `app/data/review_images/` directory, exposes 8000, and runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- `frontend/Dockerfile` — stage 1 (`node:20-alpine`) runs `npm ci` and `npm run build`; stage 2 (`nginx:1.27-alpine`) copies `dist/` into the nginx html root with a minimal SPA `nginx.conf` (history-fallback to `index.html`). Serves on container port 80.
- `docker-compose.yml` — two services (`backend`, `frontend`) on a user-defined bridge network. Backend publishes `8000:8000` with a healthcheck hitting `GET /health`; frontend publishes `8080:80` and `depends_on` backend health. The frontend keeps its existing absolute base URL `http://localhost:8000`, which resolves from the host browser because the backend is published on host 8000 — so no frontend code changes are needed.
- `.dockerignore` files keep `node_modules`, `.venv`, test artifacts, and coverage out of build contexts.

### CI pipeline

`.github/workflows/ci.yml`, one job on `ubuntu-latest`:

1. Checkout, set up Python 3.11 and Node 20.
2. Backend: create venv, `pip install -r requirements.txt coverage`, run `coverage run -m pytest` then `coverage xml -o coverage.xml`.
3. Frontend: `npm ci`, `npm run test:coverage` (emits `coverage/lcov.info`), `npm run build`.
4. E2E: `npx playwright install --with-deps chromium`, `npm run test:e2e` (Playwright starts backend + preview via its `webServer` config).
5. Upload `backend/coverage.xml`, `frontend/coverage/lcov.info`, and the Playwright report as artifacts. No deploy step.

### E2E suite (Playwright)

- Config `frontend/playwright.config.ts` defines a `webServer` array that boots the **real** backend (`uvicorn app.main:app --port 8000` from `../backend`) and the **real** frontend (`vite preview` of the production build on a dedicated port), waits for both, and runs Chromium. `reuseExistingServer` is enabled locally.
- Specs under `frontend/e2e/`:
  - `purchasing-journey.spec.ts` (Requirement 1): browse → add to cart → register/sign-in → checkout confirmation → reset.
  - `review-lifecycle.spec.ts` (Requirement 2): customer submits review → not visible while pending → moderator approves → visible with updated summary.
  - `moderation-access.spec.ts` (Requirement 2.3): a regular customer is denied the moderation queue/actions.
- Tests reset backend session/review state between runs by signing out and by using unique product/account data so runs are independent; because the store is in-process and non-persistent, a fresh `uvicorn` start (or the webServer boot) gives a clean baseline.

## Components and Interfaces

| Component | File | Responsibility |
| --- | --- | --- |
| BoundedTTLCache | `backend/app/services/response_cache.py` | Bounded, TTL-expiring in-process cache + invalidation hook |
| CatalogCacheMiddleware | `backend/app/api/cache_middleware.py` | Cache only public catalog GETs; set cache/no-store headers |
| Moderation invalidation | `backend/app/services/review_service.py` | Call cache invalidation after terminal transitions |
| App wiring | `backend/app/main.py` | Register middleware (additive) |
| Backend container | `backend/Dockerfile`, `.dockerignore` | Multi-stage slim runtime |
| Frontend container | `frontend/Dockerfile`, `frontend/nginx.conf`, `.dockerignore` | Build + serve static assets |
| Orchestration | `docker-compose.yml` | One-command local run + networking + healthcheck |
| CI | `.github/workflows/ci.yml` | Install → test+coverage → build → E2E, no deploy |
| E2E config | `frontend/playwright.config.ts` | Boot real stack, run Chromium |
| E2E specs | `frontend/e2e/*.spec.ts` | Purchasing, review lifecycle, moderation access-denied |

## Data Models

No application data model changes. The cache stores transient entries of the shape `{ body: bytes, media_type: str, expires_at: float }` keyed by `"GET <path>"`. Nothing is persisted to disk.

## Error Handling

- Cache middleware never alters error responses: non-`200` responses are passed through and never stored, so errors are never cached.
- On any downstream exception the middleware does not swallow it; FastAPI's normal error handling applies.
- E2E tests fail loudly if a server fails to boot (Playwright `webServer` timeout) rather than passing against a dead stack (Requirement 1.3).

## Testing Strategy

- **Backend unit tests** (`tests/test_response_cache.py`, `tests/test_cache_middleware.py`): TTL expiry, max-entry eviction, `X-Cache` HIT/MISS on catalog, `no-store` on `/products/{id}/reviews` and `/moderation/*`, and that a `200` is stored while a `404` is not. These use FastAPI's `TestClient`.
- **Regression**: the full existing Stage 1 + Stage 2 backend and frontend suites must still pass (Requirement 7.3).
- **E2E** (Playwright): the three specs above against the real stack (Requirements 1, 2).
- **Coverage artifacts**: `coverage.xml` (backend) and `lcov.info` (frontend) produced by the documented commands (Requirement 6). No numeric target is asserted.
- **Build**: `npm run build` must succeed (Requirement 3.4).
- **Docker**: validated via `docker compose build`/`up` **if Docker is available**; otherwise the limitation is documented honestly and the Dockerfiles/compose are validated by inspection and by the CI definition (seed constraint).

## Assumptions Realized

All assumptions A1–A9 from the requirements are realized by the components above: Playwright E2E (A1, A2); catalog-only bounded cache with no-store on sensitive routes (A3, A5); 30s TTL + invalidation hook (A4); slim multi-stage images on documented ports (A6); Docker Compose with healthcheck (A7); GitHub Actions pipeline (A8); no application behavior change beyond headers (A9).
