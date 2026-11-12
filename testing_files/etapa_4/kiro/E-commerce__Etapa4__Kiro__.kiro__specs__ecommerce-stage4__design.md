# Design Document — E-Commerce Stage 4 (Microservices + Real RabbitMQ)

## Overview

Stage 4 splits the Stage 3 FastAPI monolith into four independently running processes and wires a real RabbitMQ broker into the moderation→public-visibility flow. The React/TypeScript frontend is unchanged except for its API base URL (now the gateway) and sending credentials for the session cookie.

```
                        Browser (React, port 18300)
                              │  httpOnly session cookie, 9 endpoints
                              ▼
                 ┌──────────────────────────────┐
                 │  Gateway (FastAPI, 18200)     │  thin HTTP compatibility layer
                 │  - session cookie <-> token   │  - no business logic
                 │  - catalog response cache     │  - injects Bearer token downstream
                 └───┬───────────┬───────────┬───┘
            HTTP     │           │           │     HTTP
        ┌────────────▼──┐  ┌─────▼───────┐  ┌▼───────────────┐
        │ identity 18201│  │commerce18202│  │ reviews 18203  │
        │ accounts/auth │  │ catalog     │  │ submission     │
        │ opaque tokens │  │ checkout    │  │ images (disk)  │
        │ identity.db   │  │ projection  │  │ moderation     │
        └───────────────┘  │ commerce.db │  │ reviews.db     │
                           └──────▲──────┘  └──────┬─────────┘
                                  │ consume        │ publish (outbox relay,
                                  │ (manual ack,   │  publisher confirms)
                                  │  idempotent,   │
                                  │  retry+DLQ)    │
                              ┌───┴────────────────▼───┐
                              │  RabbitMQ (vhost        │
                              │  stage4_kiro)           │
                              │  topic exchange         │
                              │  stage4.kiro.events     │
                              └─────────────────────────┘
```

Design goals: (1) genuine process/data isolation; (2) a behavior-preserving gateway; (3) real at-least-once + idempotent broker propagation with transactional outbox and recovery; (4) server-side authorization that never trusts a client role; (5) fully local, no paid services.

## Repository layout (new)

```
services/
  contracts/            shared, stateless package (installed editable into each venv)
    __init__.py
    envelope.py         Event envelope model + builder/parser (A7)
    events.py           Event type constants + payload models
    tokens.py           Opaque token issue/verify helpers (HMAC-signed)
    settings.py         Env-based settings loader (ports, URLs, AMQP)
  identity/
    app/main.py         FastAPI app: /auth/*, /internal/verify, /health
    app/db.py           SQLite (identity.db) accounts + password hashing + tokens
    app/service.py      register/login/logout/verify logic (+ moderator seed)
    tests/
  commerce/
    app/main.py         FastAPI app: /products, /products/{id}, /checkout/confirm,
                        /products/{id}/reviews (public projection read), /health
    app/db.py           SQLite (commerce.db) projection + processed_events + cache
    app/projection.py   projection read/write
    app/consumer.py     RabbitMQ consumer (manual ack, idempotent, retry, DLQ)
    app/cache.py        bounded TTL cache (ported from Stage 3)
    tests/
  reviews/
    app/main.py         FastAPI app: POST /products/{id}/reviews, moderation, images
    app/db.py           SQLite (reviews.db) reviews + outbox + images metadata
    app/service.py      submission/validation, approve/reject (writes outbox)
    app/images.py       on-disk image store (ported from Stage 3)
    app/relay.py        outbox relay publisher (publisher confirms, backoff)
    tests/
  gateway/
    app/main.py         FastAPI app: nine endpoints, session cookie, cache, routing
    app/session.py      cookie<->token store (single-process demo authority)
    tests/
scripts/
  start-stack.ps1  stop-stack.ps1  provision-broker.ps1
tests_e2e/
  conftest.py            boots all 4 services + frontend preview, real broker
  test_distributed.py    purchase, review lifecycle, access denial, duplicate, outage/recovery
docker-compose.stage4.yml
backend/                 inherited monolith (reference + its unit tests), NOT the running system
```

The inherited `backend/` monolith is kept so its unit tests and Stage 1–3 specs remain intact, but it is not started by the Stage 4 scripts/Compose.

## Services

### Shared contracts package (`services/contracts`)
Stateless and installable editable (`pip install -e ../contracts`) into each service venv. Holds:
- `envelope.py` — `EventEnvelope` (pydantic): `eventId`, `eventType`, `schemaVersion="1"`, `occurredAt`, `correlationId`, `data`. `build(event_type, data, correlation_id=None)` and `parse(raw_bytes)`.
- `events.py` — namespaced type constants from `EVENT_NAMESPACE` (default `stage4.kiro`): `REVIEW_APPROVED = f"{ns}.review.approved"`, `REVIEW_REJECTED = f"{ns}.review.rejected"`. Payload models `ReviewProjectionData` (the public fields commerce needs: `reviewId`, `productId`, `authorIdentity`, `rating`, `title`, `text`, `images[]`, `moderationState`).
- `tokens.py` — HMAC-SHA256 signed opaque tokens: `issue(customer_id, identifier, is_moderator) -> token`; `verify(token) -> TokenClaims | None`. The signing key comes from `STAGE4_TOKEN_SECRET` (default a fixed demo secret). Tokens are stateless and self-validating so any service can verify without calling identity on every request; identity remains the only **issuer**. This satisfies "do not trust client-supplied role headers" because the role is inside a signed token the client cannot forge.
- `settings.py` — reads env vars with defaults from `stage4-runtime.json` values.

### identity service (18201, `identity.db`)
Ports the Stage 3 accounts + password + moderator-seed logic onto SQLite.
- `POST /auth/register` → 201 `{id, identifier}`; 422 `{error:"validation_error", message, emptyFields, nonConformingFields}`; 409 `{error:"identifier_taken", message}`. Same validation as Stage 3.
- `POST /auth/login` → 200 `{active:true, customerId, token, isModerator?}` (adds `token`; the gateway strips it before replying to the browser, so the browser-visible body stays `{active, customerId, isModerator?}`). 401 `{error:<uniform message>}`.
- `POST /auth/logout` → 200 `{active:false, customerId:null}` (stateless tokens; logout is handled by the gateway dropping the cookie/token binding; identity returns the inactive body for contract parity).
- `GET /internal/verify` (Bearer) → 200 `TokenClaims` or 401. Used by services that prefer central verification; the default path verifies the signed token locally via `contracts.tokens`.
- Password hashing: bcrypt with the same >72-byte SHA-256 pre-hash as Stage 3. Moderator seeded at startup (idempotent).

### commerce service (18202, `commerce.db`)
Owns catalog (static fixture, identical 6 products), checkout simulation, and the **public review projection**.
- `GET /products`, `GET /products/{id}` → identical Product shape; cacheable.
- `POST /checkout/confirm` → identical `CheckoutConfirmation`; same error codes.
- `GET /products/{id}/reviews` → `{reviews[], summary{count,average}, ownReview}`. `reviews` and `summary` come from the **projection** (approved only). `ownReview` is resolved from the caller's token identity by asking the reviews service for the caller's own non-approved review (a small authenticated internal call `GET /internal/own-review?productId=&author=`), so the session-varying field is preserved without commerce storing private data. If unauthenticated, `ownReview` is null.
- RabbitMQ **consumer** (`consumer.py`): binds a durable queue `stage4.kiro.commerce.projection` to the exchange with routing keys `*.review.approved` and `*.review.rejected`. On message: parse envelope; if `eventId` already in `processed_events`, ack and skip (idempotent); else apply to projection in a transaction, insert `eventId` into `processed_events`, invalidate cache, then manual-ack. On transient failure, nack/requeue with bounded retry; after N attempts, publish to DLQ and ack. Reconnect with exponential backoff.
- `app/cache.py` — the Stage 3 `BoundedTTLCache`, invalidated on projection change.

### reviews service (18203, `reviews.db` + image folder)
Owns submission, image storage, moderation, and the **outbox**.
- `POST /products/{id}/reviews` (Bearer customer) → 201 `ReviewResponse`; same 401/404/422/409 bodies. Validates product existence by calling commerce `GET /products/{id}` (catalog is commerce-owned) — read over HTTP, not a DB read.
- `GET /products/{id}/reviews` is **not** served here; the public read is commerce's projection. Reviews exposes `GET /internal/own-review` (Bearer) for the gateway/commerce to fetch the caller's own non-approved review.
- `GET /moderation/reviews` (Bearer moderator) → pending list; 403 otherwise.
- `POST /moderation/reviews/{id}/approve` / `/reject` (Bearer moderator) → in one SQLite transaction: update `moderation_state` (terminal; 409 `already_decided`/`review_not_found`) **and** insert an outbox row with the event envelope. Return `ReviewResponse`.
- `GET /reviews/images/{id}` → raw bytes, same as Stage 3 (image visibility preserved; the public projection only references images of approved reviews, so the public UI only surfaces approved images).
- `app/relay.py` — background outbox relay: on an interval, read unsent outbox rows, open a confirm-select channel, publish each durable/persistent message to the exchange, and mark the row sent **only after** the broker confirm. Reconnect with backoff on broker outage. This makes acceptance survive a broker outage (R4.3, R4.4).

### gateway (18200)
Thin compatibility layer; **no business logic**.
- Exposes the nine endpoints with identical bodies/status codes.
- `app/session.py`: a single-process cookie→token map (preserves the monolith's "one active demo session" UX and keeps the frontend unchanged beyond sending credentials). On `POST /auth/login`, calls identity, stores `{cookie_id -> token}` server-side, sets an httpOnly cookie, and returns the browser body **without** the token. On other calls, looks up the token by cookie and forwards it as `Authorization: Bearer` to the owning service. On `POST /auth/logout`, drops the binding and clears the cookie.
- Routing: `/products*`, `/checkout/*`, and the public `GET /products/{id}/reviews` → commerce; `POST /products/{id}/reviews`, `/reviews/images/*`, `/moderation/*` → reviews; `/auth/*` → identity.
- Ports the Stage 3 catalog cache (`X-Cache`, `Cache-Control`) at the edge so caching behavior is preserved; `no-store` on `/auth/*`, `/moderation/*`, and `/products/{id}/reviews`.

## Data models (per store)

- **identity.db** `accounts(id TEXT PK, identifier TEXT UNIQUE, password_hash TEXT, is_moderator INT)`.
- **commerce.db** `projection_reviews(review_id TEXT PK, product_id TEXT, author_identity TEXT, rating INT, title TEXT, text TEXT, images_json TEXT, moderation_state TEXT)`; `processed_events(event_id TEXT PK, processed_at TEXT)`. Catalog is a static in-code fixture (immutable, so it needs no table).
- **reviews.db** `reviews(id TEXT PK, product_id TEXT, author_identity TEXT, rating INT, title TEXT, text TEXT, images_json TEXT, moderation_state TEXT, UNIQUE(author_identity, product_id))`; `outbox(id INTEGER PK, event_id TEXT, event_type TEXT, payload TEXT, created_at TEXT, sent_at TEXT NULL, attempts INT DEFAULT 0)`.

The `ReviewResponse`/`Product`/`CheckoutConfirmation`/`ProductReviewsResponse` wire shapes (camelCase via pydantic alias) are reproduced exactly from Stage 3; see `contracts.md`.

## Messaging topology

- Exchange: `stage4.kiro.events` (topic, durable).
- Routing keys: `stage4.kiro.review.approved`, `stage4.kiro.review.rejected`.
- Commerce queue: `stage4.kiro.commerce.projection` (durable), bound to `*.review.*` (or the two explicit keys), with `x-dead-letter-exchange = stage4.kiro.events.dlx` and a DLQ `stage4.kiro.commerce.projection.dlq`.
- Messages: `delivery_mode=2` (persistent), published on a confirm-select channel.
- Consumer: `prefetch=1`, manual ack; idempotency via `processed_events`; bounded retry counter carried per delivery (redelivery count / in-memory attempt map) before DLQ.

## Error handling

- Gateway maps downstream non-2xx bodies through unchanged (same JSON/status) so the frontend's `ApiError` parsing still works.
- Services return the exact Stage 3 structured error bodies.
- Consumer never crashes the service on a poison message: it retries up to the bound, then dead-letters and acks.
- Relay never loses an accepted change: the outbox row persists across broker outages and is retried until confirmed.

## Testing strategy

- **Service unit tests** (pytest per service, FastAPI `TestClient`): identity auth/validation; commerce catalog/checkout/projection apply + idempotency + cache invalidation; reviews submission/validation/moderation terminal transitions + outbox write; token issue/verify; envelope build/parse. A focused consumer idempotency unit test may use a direct function call (adapter) — but this does not replace the real-broker run.
- **Real multi-process, real-broker acceptance** (`tests_e2e/test_distributed.py`): boots identity, commerce, reviews, gateway as real subprocesses against the provisioned RabbitMQ; drives the gateway over HTTP. Covers: purchase; submit review (pending, hidden from commerce projection); moderator approve; **poll** commerce projection until the review is public (proves cross-process event propagation within the bounded window); customer denied moderation (403). Then: **duplicate delivery** (publish the same event twice; projection count unchanged); **outage/recovery** (stop the commerce consumer or simulate broker refusal during an approve so the event waits in the outbox/queue, then restart and assert the change is not lost).
- **Frontend**: existing unit tests unchanged; Playwright E2E updated to point at the gateway; `npm run build` must succeed; `lcov.info` produced.
- **Coverage**: `coverage.xml` across services via `coverage run -m pytest` with combined source; `lcov.info` from the frontend. No numeric target asserted.
- **Docker**: validated by inspection + CI definition; a local container run is **not claimed** unless executed. Native validation uses the provisioned broker.

## Delegated decisions (explicit)

- Signed stateless tokens (not server-side session store in identity) keep services independent while letting the gateway hold the one-session demo UX. Role lives inside the signed token → clients cannot forge it.
- `ownReview` is resolved by commerce calling reviews' `/internal/own-review` with the caller's token, avoiding any cross-service DB read while preserving the exact `ProductReviewsResponse` shape.
- Product-existence check in reviews is an HTTP read to commerce, not a DB read, honoring ownership.
- Python AMQP client: `pika` (already available), used with a background thread per publisher/consumer.
