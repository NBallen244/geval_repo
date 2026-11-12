# Task Specifications: Stage 4 Microservices Migration

## Phase 1: Native Specifications & Architecture Definitions
- [x] **Task 1.1**: Define high-level feature requirements (`spec.md`).
- [x] **Task 1.2**: Author architectural design and outbox implementation plan (`plan.md`).
- [x] **Task 1.3**: Document internal and external HTTP endpoints and RabbitMQ JSON contracts (`contracts/api.md`).
- [x] **Task 1.4**: Define database schemas for isolated SQLite stores including the Outbox and Processed Events (`data-model.md`).
- [x] **Task 1.5**: Draft requirements validation criteria (`checklists/requirements.md`).
- [x] **Task 1.6**: Prepare quickstart guidelines for execution and testing (`quickstart.md`).

## Phase 2: Refactoring Codebase Structure & Isolation
- [x] **Task 2.1**: Establish the new directory layout in `backend/src/` with subdirectories for `common`, `services/identity`, `services/commerce`, `services/reviews`, and `services/gateway`.
- [x] **Task 2.2**: Implement the JWT generation and verification logic in `backend/src/common/security.py` using HS256-signed tokens. Ensure it handles roles, expirations, and user identifiers securely.
- [x] **Task 2.3**: Build the **Identity Service** (Port 18601). Implement `/api/register`, `/api/login`, and `/api/me`. Use isolated `identity.db` SQLite store.
- [x] **Task 2.4**: Build the **Commerce Service** (Port 18602). Implement `/api/products`, `/api/products/{product_id}`, and `/api/checkout`. Integrate in-memory caching and reviews projection table `product_reviews` (which is populated via consumed events). Use isolated `commerce.db`.
- [x] **Task 2.5**: Build the **Reviews Service** (Port 18603). Implement `/api/reviews` (for submitting pending reviews and uploading images) and `/api/moderation/reviews` (for listing and moderating reviews). Implement isolated `reviews.db` with the `outbox` table and atomic database transactions.

## Phase 3: Reliable Messaging & Event-Driven Flows
- [x] **Task 3.1**: Implement the Transactional Outbox background worker in the **Reviews Service**. It periodically scans the local `outbox` table, publishes pending events with publisher confirmations to RabbitMQ, and updates event statuses in `reviews.db`.
- [x] **Task 3.2**: Implement the Event Consumer background worker in the **Commerce Service**. It connects to RabbitMQ, handles reconnections, subscribes to the review events queue, tracks processed message IDs in `processed_events` for idempotency, updates the `product_reviews` local projection, invalidates the catalog cache, and manually ACK's the messages.
- [x] **Task 3.3**: Build the **HTTP Gateway** (Port 18600). Use FastAPI and `httpx` to route incoming frontend requests to the appropriate microservices over HTTP. Pass JWT/Authorization headers downstream and return clean error fallbacks.

## Phase 4: Integration, Orchestration & Tooling
- [x] **Task 4.1**: Create `Start-Services.ps1` and `Stop-Services.ps1` PowerShell launch scripts to handle starting services natively, checking readiness, and cleaning up background processes.
- [x] **Task 4.2**: Write the multi-container orchestration configuration in `docker-compose.yml` to bring up RabbitMQ, all microservices, and the frontend on the configured ports.
- [x] **Task 4.3**: Update the CI pipeline config `.github/workflows/ci.yml` and the E2E Playwright test configurations to work seamlessly with the new port mapping.

## Phase 5: Verification & Quality Metrics
- [x] **Task 5.1**: Write backend tests (`backend/tests/`) verifying microservice behaviors, JWT security, outbox reliability, broker-recovery resilience, and deduplication.
- [x] **Task 5.2**: Execute tests, collect raw code coverage XML reports, run the production-grade frontend compilation, and ensure all browser E2E checks pass.
