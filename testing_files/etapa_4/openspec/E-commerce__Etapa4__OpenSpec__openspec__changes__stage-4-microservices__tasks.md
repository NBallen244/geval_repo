# Tasks

## 1. Directory Structure and Database Scaffolding

- [x] 1.1 Restructure backend directory into four independent application services (`gateway`, `identity`, `commerce`, `reviews`) and a shared contract utilities module, and verify the files are scaffolded correctly.
- [x] 1.2 Implement independent database files (`identity.db`, `commerce.db`, `reviews.db`) with automatic table creation and catalog seeding on startup, and verify each database contains only its owned tables.

## 2. Implement Microservices and Gateway Routing

- [x] 2.1 Implement the Identity service with `/api/auth/register` and `/api/auth/login` endpoints on port 18001, and verify registration and login function correctly.
- [x] 2.2 Implement the Reviews service review submission (`POST /api/products/{id}/reviews`) and moderation dashboard APIs (`/api/moderation/reviews`) on port 18003, and verify reviews are saved to `reviews.db` in a pending status.
- [x] 2.3 Implement the Commerce service product catalog (`/api/products`), product detail (`/api/products/{id}`), and approved reviews (`/api/products/{id}/reviews`) endpoints on port 18002 with in-memory caching, and verify catalog loads products correctly.
- [x] 2.4 Implement the Gateway service on port 18000 to reverse-proxy client requests to the respective ports (18001-18003) according to routing prefix rules, preserving CORS, and verify the frontend can communicate with all backend features through port 18000.

## 3. RabbitMQ Asynchronous Reliable Messaging

- [x] 3.1 Implement a local transactional outbox table in `reviews.db` and background outbox publisher thread with publisher confirmations, and verify a moderation action transactionally writes to both reviews and outbox tables.
- [x] 3.2 Implement the AMQP consumer in the Commerce service to handle review approval/rejection events, employing manual acknowledgements, idempotent event tracking, and local cache invalidation, and verify approved reviews propagate asynchronously.
- [x] 3.3 Implement an exponential backoff connection retry loop in both publisher and consumer to survive RabbitMQ broker outages, and verify the consumer reconnects and processes pending events once the broker is back online.
- [x] 3.4 Establish non-destructive durable queue declaration on consumer startup (avoiding unconditional queue_delete), handling one-time schema migration via catch-and-migrate channel fallbacks on precondition mismatch, and introduce comprehensive real-broker subprocess acceptance tests.

## 4. Verification and Local Orchestration

- [x] 4.1 Provide startup and stop PowerShell and Bash scripts for local native multi-process orchestration, and verify the full distributed stack boots cleanly.
- [x] 4.2 Restructure automated backend pytest tests and Playwright E2E suites to target the port 18000 Gateway, and verify all tests pass with backend coverage and production build.
- [x] 4.3 Wire GitHub Actions CI startup to all four actual service processes, stage4_openspec RabbitMQ vhost, service-owned stores, configured service URLs, and the gateway/frontend ports with deterministic readiness and teardown.
