# Requirements Document — E-Commerce Stage 4 (Microservices + Real RabbitMQ, Option A)

## Introduction

Stage 4 performs an **architectural breaking change (Option A)**: it migrates the inherited Stage 3 monolithic FastAPI backend into **independently running Python/FastAPI microservices** coordinated by **real RabbitMQ business events**. No new end-user business features are added. The React/TypeScript frontend, the Stage 1 purchasing journey, the Stage 2 reviews-with-images-and-moderation workflow, bounded catalog caching, automated tests, and coverage artifacts are all preserved in observable behavior.

This document derives its scope from `SEED-4.md` and reads the tool-isolated deployment parameters from `stage4-runtime.json`. The seed deliberately leaves several design choices to the tool; each is recorded as a numbered **Assumption** and treated as a binding requirement. The researcher preauthorizes these assumptions, the specs, and the implementation; no approval gates apply.

Everything stays local: no paid cloud services, no external deployment. All artifacts, source, comments, UI, and documentation are in English.

## Relationship to earlier stages

- Stages 1–3 specs (`.kiro/specs/ecommerce-stage1..3/`) remain authoritative for application behavior and are **not modified**. This Stage 4 spec lives at `.kiro/specs/ecommerce-stage4/`.
- Stage 4 preserves the **nine HTTP endpoints** the frontend consumes (six Stage 1 + three Stage 2 route groups) and their request/response bodies, exposed through a thin HTTP **gateway** so the frontend's fixed base URL and the nine typed client methods keep working unchanged.
- The inherited monolith (`backend/`) is retained for reference and for its existing unit tests, but it is **no longer the running system**. The running system is the set of Stage 4 services under `services/`.

## Glossary

- **Service**: An independently startable Python/FastAPI process with its own port, its own storage, and an explicit ownership boundary. It does not import another service's in-process state.
- **Gateway**: A thin HTTP process that preserves the frontend API contract and delegates each call over HTTP to the owning service. It never executes monolithic business handlers.
- **Owned store**: A SQLite database file (and, for reviews, an on-disk image folder) written by exactly one service. No other service reads or writes it.
- **Business event**: A versioned JSON message published to RabbitMQ when a domain fact occurs (e.g. a review is approved), carrying event identity, correlation identity, type, timestamp, and payload.
- **Outbox**: A table in a service's own store where an outgoing event is written in the **same local transaction** as the domain change, then relayed to the broker by a background publisher, so a broker outage cannot silently lose an accepted change.
- **Public review projection**: A commerce-owned read model of approved reviews (and their image references) plus the rating summary, kept coherent by consuming moderation events.
- **Bounded eventual consistency**: Approved reviews become publicly visible within a short, documented window after approval (the time for the event to be published and consumed), not instantaneously.

## Assumptions (delegated design choices, binding)

- **A1 — Service decomposition.** Three business services plus one gateway:
  - **identity** (auth/accounts), **commerce** (catalog, simulated checkout, public review projection), **reviews** (submission, images, moderation). The **gateway** preserves the nine-endpoint frontend contract and routes to the owning service. More services are not justified for this scope.
- **A2 — Ownership & storage.** Each service owns a separate SQLite file: `identity.db`, `commerce.db`, `reviews.db`. Review image bytes remain on disk under the reviews service. No shared writable DB, no cross-service DB reads, no shared Python singleton, no in-process transport, no mounting all apps in one process. A shared, read-only **contracts** package (event schemas, token helpers, settings) is allowed because it carries no runtime state.
- **A3 — Session/authorization.** The frontend sends no token today (the monolith used one global in-process session). Stage 4 introduces a real **opaque bearer session token** issued by identity on login. The **gateway** holds a single httpOnly session cookie↔token binding (preserving the monolith's "one active demo session" UX) and forwards the token to services as an `Authorization: Bearer` header. Services validate the token against identity (or a signed token) and derive role from it; **no service trusts a client-supplied role header**. Demo credentials are unchanged: moderator `moderator` / `moderator123`.
- **A4 — Broker.** A real RabbitMQ AMQP broker is used via the `amqp_url` and `event_namespace` in `stage4-runtime.json` (vhost `stage4_kiro`, namespace `stage4.kiro`). A topic exchange `stage4.kiro.events` carries review-moderation events. No in-memory bus or logging-only substitute.
- **A5 — Event-driven projection.** On **approve**, reviews publishes `stage4.kiro.review.approved`; on **reject**, `stage4.kiro.review.rejected`. Commerce consumes them and updates its public review projection (and invalidates its catalog/review caches). Pending and rejected reviews are never public; an approved review and its images become public within a bounded window (target: under a few seconds locally; documented, not instantaneous).
- **A6 — Reliability.** Durable exchange/queues/messages; publisher confirms; manual consumer acknowledgements after successful processing; idempotent consumer keyed on event id (a `processed_events` table) so **duplicate delivery** is harmless; bounded retry with a dead-letter queue for poison messages; reconnect with backoff. Outgoing events are written to a SQLite **outbox** transactionally with the domain change and relayed by a background publisher, so a broker outage does not lose an accepted moderation change. **Exactly-once delivery is not claimed**; the design is at-least-once + idempotent.
- **A7 — Versioned contracts.** Every event envelope is JSON with fields `eventId` (UUID), `eventType` (namespaced string), `schemaVersion` (`"1"`), `occurredAt` (ISO-8601 UTC), `correlationId` (UUID), and `data` (typed payload). Contracts are documented in `design.md` and `contracts.md` and shared via the read-only contracts package.
- **A8 — Deployment parameters.** Ports and broker come from `stage4-runtime.json`, read via environment variables (`GATEWAY_PORT=18200`, `IDENTITY_PORT=18201`, `COMMERCE_PORT=18202`, `REVIEWS_PORT=18203`, `FRONTEND_PORT=18300`, `AMQP_URL`, `EVENT_NAMESPACE`). These are deployment parameters, not functional differences. Service-to-service base URLs are environment-based (`IDENTITY_URL`, `COMMERCE_URL`, `REVIEWS_URL`).
- **A9 — Operability.** PowerShell launch/stop scripts (`scripts/start-stack.ps1`, `scripts/stop-stack.ps1`) with deterministic readiness checks (poll each `/health` and the broker) and owned-process cleanup. A Compose stack (RabbitMQ + three services + gateway + frontend) and an updated CI workflow are provided. If Docker is unavailable it is validated natively and container execution is stated as unverified.
- **A10 — Frontend compatibility.** The frontend keeps its nine typed client methods and existing journeys. Its API base URL points at the gateway (`http://localhost:18200`), and it sends credentials so the gateway session cookie works. Views and journeys are unchanged.
- **A11 — Caching preserved.** The gateway (or commerce) preserves bounded caching for the two public catalog reads with the same `X-Cache`/`Cache-Control` semantics; session-varying and moderation responses stay `no-store`. A moderation event invalidates the affected projection/cache.

## Requirements

### Requirement 1 — Independent business services with owned storage

**User Story:** As a maintainer, I want at least three independently runnable FastAPI services with their own stores, so that the system is genuinely distributed rather than a decorated monolith.

#### Acceptance Criteria
1. The system SHALL run **identity**, **commerce**, and **reviews** as separate FastAPI processes, each startable on its own port with its own `/health` endpoint.
2. Each service SHALL own a separate SQLite database; no service SHALL read or write another service's database or import another service's in-process state.
3. The system SHALL NOT use an in-process HTTP transport, a shared Python singleton, or a single process hosting all apps as a substitute for microservices.
4. A shared **contracts** package MAY be imported by services but SHALL contain only stateless schema/utility code (event envelopes, token helpers, settings), no runtime business state.

### Requirement 2 — Thin HTTP gateway preserving the frontend contract

**User Story:** As a maintainer, I want the existing frontend to keep working unchanged, so that the migration is observably behavior-preserving.

#### Acceptance Criteria
1. The gateway SHALL expose the nine existing endpoints (`GET /products`, `GET /products/{id}`, `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `POST /checkout/confirm`, `GET|POST /products/{id}/reviews`, `GET /reviews/images/{id}`, `GET|POST /moderation/reviews[...]`) with the **same request/response bodies and status codes** as Stage 3, plus cache/freshness headers.
2. The gateway SHALL delegate each call over **HTTP** to the owning service and SHALL NOT execute the monolithic business handlers in-process.
3. The gateway SHALL translate between the browser session (httpOnly cookie) and the service bearer token, attaching the caller's authenticated identity to downstream requests.
4. WHEN a request carries no valid session THEN the gateway SHALL forward it as unauthenticated and the owning service SHALL apply the same authorization outcome as Stage 3 (401/403 as appropriate).

### Requirement 3 — Real RabbitMQ event-driven public review projection

**User Story:** As a maintainer, I want moderation decisions to propagate to the public catalog through a real broker, so that approved reviews become visible via genuine cross-process events.

#### Acceptance Criteria
1. WHEN a moderator approves a pending review THEN the reviews service SHALL publish a durable `review.approved` event to RabbitMQ, and the commerce service SHALL consume it and add the review (and its image references) to its public projection.
2. WHEN a moderator rejects a pending review THEN the reviews service SHALL publish `review.rejected`, and commerce SHALL ensure the review is absent from its public projection.
3. A pending or rejected review SHALL NOT appear in commerce's public projection; an approved review SHALL appear within a bounded, documented eventual-consistency window.
4. The system SHALL NOT substitute an in-memory bus or logging-only demonstration for broker integration.
5. WHEN commerce updates its projection from an event THEN it SHALL invalidate the affected cached catalog/review responses so the next public read is coherent.

### Requirement 4 — Reliable messaging (durability, confirms, acks, idempotency, outbox, recovery)

**User Story:** As a maintainer, I want messaging to survive duplicates and outages without losing an accepted moderation change, so that the distributed flow is trustworthy.

#### Acceptance Criteria
1. The exchange, queues, and messages SHALL be durable; the publisher SHALL use publisher confirms; the consumer SHALL use manual acknowledgement after successful processing.
2. The consumer SHALL be idempotent, keyed on `eventId`, so a duplicate delivery produces no additional visible effect.
3. The publisher SHALL write each outgoing event to a SQLite **outbox** in the **same transaction** as the domain change; a background relay SHALL publish unsent outbox rows and mark them sent only after a publisher confirm.
4. IF the broker is unavailable when a moderation decision is accepted THEN the decision SHALL still be committed locally and its event SHALL be delivered after the broker recovers, with no lost change.
5. The consumer SHALL apply bounded retry and route poison messages to a dead-letter queue; the publisher and consumer SHALL reconnect with backoff.
6. The system SHALL NOT claim exactly-once delivery; it SHALL document at-least-once + idempotent semantics.

### Requirement 5 — Authentication and authorization without trusting client roles

**User Story:** As a maintainer, I want internal operations authenticated and authorized server-side, so that a client cannot forge a moderator role.

#### Acceptance Criteria
1. Services SHALL authenticate internal HTTP operations using a token established by identity, NOT a client-supplied role header.
2. The moderator/customer separation and the seeded demo credentials (`moderator`/`moderator123`) SHALL be preserved.
3. A regular customer SHALL be denied the moderation queue and moderation actions (403), with no state change.
4. Private/session-varying responses SHALL remain uncached; public projection responses SHALL be coherent after events; image visibility SHALL be consistent with moderation (approved reviews' images reachable via the public path; the raw image endpoint is preserved as in Stage 3).

### Requirement 6 — Operability: launch/stop, Compose, CI, environment config

**User Story:** As a maintainer, I want simple local operation and updated automation, so that the distributed stack is reproducible.

#### Acceptance Criteria
1. The repository SHALL provide PowerShell scripts to start and stop the full local stack (broker assumed running per the runtime note), with deterministic readiness checks (poll `/health` of each service and the gateway) and owned-process cleanup.
2. Service and broker addresses SHALL be environment-based, defaulting to the values in `stage4-runtime.json`.
3. A Compose stack SHALL define RabbitMQ, the three services, the gateway, and the frontend.
4. CI SHALL install dependencies, run service unit tests with backend coverage (`coverage.xml`), run the real-broker integration/E2E acceptance, run frontend unit tests with coverage (`lcov.info`), and build the frontend; it SHALL NOT deploy.
5. No paid external service SHALL be required.

### Requirement 7 — Verification of the real distributed stack

**User Story:** As a maintainer, I want meaningful multi-process, real-broker tests, so that the migration is proven, not asserted.

#### Acceptance Criteria
1. There SHALL be service-level unit tests for each service's owned logic (auth, catalog/checkout/projection, review/moderation, outbox, idempotent consumer).
2. There SHALL be a **real multi-process, real-broker** acceptance test covering: purchasing; a customer submitting a review; the pending review hidden from the public projection; moderator approval; event-driven public visibility; and a customer being denied moderation.
3. The acceptance suite SHALL prove **actual cross-process event propagation**, and SHALL test **duplicate delivery** (no double effect) and a **broker/consumer outage followed by recovery** without losing the accepted change.
4. Raw coverage outputs SHALL be preserved (`coverage.xml` for Python, `lcov.info` for the frontend), the frontend production build SHALL succeed, and no coverage target SHALL be invented.
5. IF Docker is unavailable THEN native validation with the provisioned broker SHALL be performed and container execution SHALL be stated as unverified; no unexecuted Docker check SHALL be claimed as passed.

### Requirement 8 — Behavior preservation

**User Story:** As a maintainer, I want the end-user behavior unchanged, so that Stage 4 is a pure architectural migration.

#### Acceptance Criteria
1. The nine endpoints' request/response bodies SHALL be unchanged except for the added `X-Cache`/`Cache-Control` headers already present in Stage 3.
2. The frontend journeys and views SHALL be unchanged other than pointing the base URL at the gateway and sending credentials for the session cookie.
3. The Stage 1 purchasing journey and the Stage 2 review/moderation workflow SHALL remain observably identical from the UI.
