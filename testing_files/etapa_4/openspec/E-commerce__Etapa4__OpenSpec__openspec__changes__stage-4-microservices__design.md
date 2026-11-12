# Design

## Context

The system is being migrated from a monolithic Python/FastAPI backend using a single SQLite database (`ecommerce.db`) into three distinct microservices coordinated by a lightweight HTTP API Gateway. We are also integrating a real RabbitMQ broker for asynchronous review moderation event propagation to maintain a public review projection.

## Goals / Non-Goals

**Goals:**
- Decompose the monolith into three independent service processes: Identity, Commerce, and Reviews, plus a thin HTTP API Gateway.
- Eliminate shared writable databases; each microservice has its own isolated SQLite schema and file.
- Support asynchronous, eventually consistent public review projection updates in the Commerce service via RabbitMQ events published by the Reviews service.
- Implement reliable messaging via Transactional Outbox (producer), manual message acknowledgements (consumer), idempotent duplicate detection (consumer), and reconnection backoff.

**Non-Goals:**
- Modifying frontend application code. The gateway must completely mask the distributed architecture and preserve the exact original API contracts and port layout (port 18000).
- Using third-party hosted broker services or paid infrastructure. All services run locally or in lightweight containers.

## Decisions

### 1. Service Port and Routing Strategy
We decompose the system into the following components conforming to `stage4-runtime.json`:
- **Gateway Service** (Port 18000): Fast and lightweight reverse proxy using `httpx` to route requests:
  - `POST /api/auth/*` $\to$ **Identity Service** (Port 18001)
  - `GET /api/products` $\to$ **Commerce Service** (Port 18002)
  - `GET /api/products/{id}` $\to$ **Commerce Service** (Port 18002)
  - `GET /api/products/{id}/reviews` $\to$ **Commerce Service** (Port 18002) *(Approved reviews projection)*
  - `POST /api/products/{id}/reviews` $\to$ **Reviews Service** (Port 18003) *(Submission)*
  - `GET /api/moderation/*` $\to$ **Reviews Service** (Port 18003)
  - `POST /api/moderation/*` $\to$ **Reviews Service** (Port 18003)
  - `GET /health` $\to$ **Gateway Health** directly, plus optional sub-service status checks.

### 2. Isolated Storage Partitioning
We split `ecommerce.db` into three separate local databases:
- `identity.db`: Contains `users` table.
- `commerce.db`: Contains `products` catalog and `public_reviews` (projection) table, plus `processed_events` for idempotency.
- `reviews.db`: Contains `reviews` (moderation state) and `outbox` table for transactional reliability.

### 3. Authentication and Authorization
We share the JWT token signature configuration (`SECRET_KEY`, hashing algorithm, and token verification helpers) as a shared code module. Each service verifies incoming Bearer tokens independently using the secret without requiring synchronous cross-service API checks.

### 4. Event Schema Contract
The Reviews service publishes a versioned event message when a review is moderated.
```json
{
  "event_id": "string (UUIDv4)",
  "correlation_id": "string (UUIDv4)",
  "event_type": "review_moderated",
  "timestamp": "string (ISO-8601)",
  "payload": {
    "review_id": 123,
    "product_id": 456,
    "user_id": "string",
    "rating": 5,
    "comment": "string",
    "image_data": "string (Base64 or null)",
    "status": "approved" | "rejected"
  }
}
```

### 5. Transactional Outbox & Reliable Consumer Strategy
- **Outbox Pattern**: In the Reviews service, moderation actions and outbox logging run in a single SQL transaction. A background publisher process polls the `outbox` table, publishes pending events to RabbitMQ with publisher confirmations enabled, and deletes/updates successful records.
- **Idempotency**: The Commerce consumer checks a `processed_events` unique key index before applying the event to `public_reviews`. If the ID exists, the event is ignored, but the message is manually acknowledged to prevent redelivery.
- **Outage Recovery**: If the RabbitMQ connection is lost, publisher/consumer tasks retry connection setup using an exponential backoff loop with jitter, continuing to function offline and syncing pending outbox events immediately upon reconnection.

## Risks / Trade-offs

- **Eventual Consistency**: Approved/rejected reviews do not display in the catalog instantly; they wait for the broker event loop.
  - *Mitigation*: The E2E tests and manual checks must accommodate a brief bounded eventual-consistency window. Local cache invalidation happens immediately inside the consumer processing loop.
- **Network Flapping / Retries**: Connection loss might cause duplicate event publishing.
  - *Mitigation*: The Commerce consumer's `processed_events` lookup ensures strict idempotency.
