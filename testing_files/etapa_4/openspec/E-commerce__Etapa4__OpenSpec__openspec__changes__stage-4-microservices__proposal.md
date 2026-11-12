# Proposal

## Why

The current monolithic backend architecture binds commerce, authentication, and product review submission / moderation into a single process and database. To support independent scaling, separate deployment lifecycles, and isolated database schemas, this change migrates the backend into three distinct microservices coordinated via a thin API gateway and integrated through real RabbitMQ business events.

## What Changes

- **Microservice Decomposition**: **BREAKING** Split the backend into three independent FastAPI microservices running on isolated ports: Identity/Auth (18001), Commerce/Catalog (18002), and Reviews/Moderation (18003).
- **API Gateway**: **BREAKING** A lightweight HTTP Gateway running on port 18000 that routes incoming traffic to the appropriate backend microservices, preserving the original frontend API contract.
- **Database Partitioning**: **BREAKING** Give each service its own dedicated SQLite database to eliminate shared writable state. No cross-service database reads or synchronous shared state.
- **Event-Driven Integration**: Use a real RabbitMQ AMQP broker to propagate approved reviews from the Reviews microservice to a public reviews projection owned by the Commerce microservice.
- **Transactional Outbox & Reliable Messaging**: **BREAKING** Implement a local transactional outbox in the Reviews service to guarantee event durability. Implement consumer manual acknowledgements, duplicate message detection (idempotency), and automatic reconnection with backoff to handle network or broker outages.
- **Unified Local Orchestration**: Provide startup, stop, and readiness scripts for Windows PowerShell, along with a multi-container Docker Compose setup.

## Capabilities

### New Capabilities

*(None. This is an architectural migration preserving existing functional capabilities).*

### Modified Capabilities

- `product-reviews`: Review moderation now updates the Commerce-owned public reviews projection asynchronously via RabbitMQ events instead of direct synchronous DB writes. The Commerce service invalidates its local GET caches upon receiving the approval event.

## Impact

- **Backend**: The original `backend/` directory will be restructured into independently running services (`gateway`, `identity`, `commerce`, `reviews`).
- **Data Store**: The single `ecommerce.db` is replaced by three separate SQLite databases: `identity.db`, `commerce.db`, and `reviews.db`.
- **E2E & CI**: The Playwright and backend unit testing suites must be updated to target the distributed gateway (port 18000) and orchestrate multiple backend services plus RabbitMQ during testing.
- **Launch scripts**: `Start-Gemini.ps1` and associated run files will start/stop the new microservices stack.
