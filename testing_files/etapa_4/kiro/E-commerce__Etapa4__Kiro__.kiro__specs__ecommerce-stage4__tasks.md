# Implementation Plan — E-Commerce Stage 4

- [x] 1. Shared contracts package
  - [x] 1.1 Create `services/contracts` (envelope, events, tokens, settings) with `pyproject.toml` for editable install. (R1.4, R5.1, A7)
  - [x] 1.2 Unit tests: envelope build/parse round-trip; token issue/verify + tamper rejection. (R7.1)

- [x] 2. identity service (18201, identity.db)
  - [x] 2.1 SQLite accounts store + bcrypt password (Stage 3 parity) + moderator seed. (R5.2)
  - [x] 2.2 `/auth/register|login|logout`, `/internal/verify`, `/health`; login issues a signed token. (R2.1, R5.1)
  - [x] 2.3 Unit tests: register validation (422 fields), duplicate (409), login success/failure (uniform 401), moderator flag. (R7.1)

- [x] 3. commerce service (18202, commerce.db)
  - [x] 3.1 Catalog fixture + `/products`, `/products/{id}` + bounded cache; `/checkout/confirm`. (R8.1, A11)
  - [x] 3.2 Projection store (`projection_reviews`, `processed_events`) + `/products/{id}/reviews` reading approved projection and resolving `ownReview` via reviews `/internal/own-review`. (R3.1, R5.4)
  - [x] 3.3 RabbitMQ consumer: durable queue bound to review.* ; manual ack, idempotent on eventId, bounded retry + DLQ, reconnect backoff; applies upsert/remove and invalidates cache. (R3.1, R3.2, R3.5, R4.1, R4.2, R4.5)
  - [x] 3.4 Unit tests: catalog/checkout parity; projection apply approved/rejected; idempotent duplicate; cache invalidation. (R7.1)

- [x] 4. reviews service (18203, reviews.db + images)
  - [x] 4.1 SQLite reviews store (unique author+product) + on-disk image store (Stage 3 parity) + outbox table. (R1.2, A2)
  - [x] 4.2 `POST /products/{id}/reviews` (Bearer customer; product existence via commerce HTTP), `GET /moderation/reviews`, approve/reject writing outbox in same transaction, `GET /reviews/images/{id}`, `GET /internal/own-review`. (R2.1, R3.1, R4.3, R5.3)
  - [x] 4.3 Outbox relay publisher: publisher confirms, mark sent after confirm, reconnect backoff. (R4.1, R4.3, R4.4)
  - [x] 4.4 Unit tests: submission validation/duplicate/auth; terminal moderation + outbox row written; moderator-only enforcement. (R7.1)

- [x] 5. gateway (18200)
  - [x] 5.1 Nine endpoints routed to owning services over HTTP; identical bodies/status codes; edge catalog cache + no-store rules. (R2.1, R2.2, R8.1, A11)
  - [x] 5.2 Session cookie <-> token binding; login stores token and strips it from the browser body; logout clears; downstream Bearer injection; no client role trusted. (R2.3, R2.4, R5.1)
  - [x] 5.3 Unit tests: routing + session cookie behavior + cache headers (using stubbed/real services where practical). (R7.1)

- [x] 6. Operability
  - [x] 6.1 `scripts/provision-broker.ps1` (idempotent vhost/user/permissions; no-op if already present), `scripts/start-stack.ps1` (env from stage4-runtime.json, deterministic readiness polling, background processes), `scripts/stop-stack.ps1` (owned-process cleanup). (R6.1, R6.2)
  - [x] 6.2 `docker-compose.stage4.yml` (RabbitMQ + 3 services + gateway + frontend). (R6.3)
  - [x] 6.2.1 Container packaging correction: `services/Dockerfile` installed the shared `contracts` package **editable** (`pip install -e /build/contracts`) in the builder and then copied the source to `/app/contracts` in the runtime. A setuptools editable install writes an absolute finder mapping back to the *build-time* source path (`/build/contracts`), so the runtime venv imported from a directory that no longer exists, making the runtime image not self-contained. Fix: install `contracts` **non-editably** in the builder so the package is baked into the copied venv; the local editable dev setup (`services/.venv`) is unchanged. (R6.3)
  - [x] 6.3 Update `.github/workflows/ci.yml` for the distributed stack (service coverage, real-broker acceptance via a RabbitMQ service container, frontend tests + build). (R6.4)
  - [x] 6.4 Point the frontend base URL at the gateway and send credentials; keep journeys/views unchanged; update Playwright config ports. (R8.2, A10)

- [x] 6.5 Windows launcher operational correction: start the frontend via the installed `node` executable and the local Vite JS entry (`frontend/node_modules/vite/bin/vite.js`) with quoted paths instead of `Start-Process npm` (which fails on Windows with `%1 is not a valid Win32 application`). Launch every service and the frontend hidden with redirected stdout/stderr log files (no `-NoNewWindow` console-handle inheritance). Record each owned PID immediately on spawn and clean up partial-start children if a later step throws. Verify frontend HTTP readiness in addition to all backend `/health` endpoints. Make `stop-stack.ps1` act only on still-owned processes, guarding against stale/reused PIDs via recorded identity (process name + start time). (R6.1, R6.2)

- [x] 7. Verification
  - [x] 7.1 Real multi-process real-broker acceptance: purchase, submit (pending hidden), approve → public within window (cross-process proof), customer denied moderation. (R7.2)
  - [x] 7.2 Duplicate delivery (no double effect) and broker/consumer outage + recovery (no lost change). (R7.3)
  - [x] 7.3 Collect backend `coverage.xml` + frontend `lcov.info`; run frontend production build; document Docker as unverified if not executed. (R7.4, R7.5)
  - [x] 7.4 Update README with exact PowerShell start/stop/test commands, demo credentials, and honest limitations. (R6.1)
