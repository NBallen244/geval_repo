# Implementation Plan: Stage 4 Microservices Migration

## 1. Architectural Strategy

We will migrate the monolithic backend into three specialized services and an HTTP Gateway. Each service will run in its own process, listen on its own port, and own its SQLite database.

```
                  ┌─────────────────┐
                  │  React Frontend │ (Port 18700)
                  └────────┬────────┘
                           │ HTTP
                           ▼
                  ┌─────────────────┐
                  │   HTTP Gateway  │ (Port 18600)
                  └────┬────┬────┬──┘
         ┌─────────────┘    │    └──────────────┐
         │ HTTP             │ HTTP              │ HTTP
         ▼                  ▼                   ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ Identity Serv. │ │ Commerce Serv. │ │ Reviews Service│
│ (Port 18601)   │ │ (Port 18602)   │ │ (Port 18603)   │
│ [identity.db]  │ │ [commerce.db]  │ │ [reviews.db]   │
└────────────────┘ └────────▲───────┘ └────────┬───────┘
                            │                  │
                            │  RabbitMQ Event  │
                            └──────────────────┘
                             (Moderation event)
```

### Microservice Directory Layout
We will restructure the backend codebase to separate the services:
- `backend/src/services/identity/`: FastAPI application for registration, login, and identity verification.
- `backend/src/services/commerce/`: FastAPI application for catalog, cart, and simulated checkout. Contains public reviews projection.
- `backend/src/services/reviews/`: FastAPI application for reviews, uploads, and moderation.
- `backend/src/services/gateway/`: FastAPI-based thin routing gateway.
- `backend/src/common/`: Shared code (e.g., JWT decoding, schema definitions, common exceptions).

### State Separation
- **Identity Service**: `identity.db` handles `users` table.
- **Commerce Service**: `commerce.db` handles `products` (seed data), `carts`, `orders`, and `product_reviews` (read-only cached local projection of approved reviews).
- **Reviews Service**: `reviews.db` handles `reviews` (moderation state: pending, approved, rejected, with image path) and `outbox` table.

## 2. Reliability & Messaging Patterns

### Transactional Outbox Pattern (Reviews Service)
When a review is moderated (approved or rejected):
1. A transaction updates the review status in the `reviews` table.
2. The transaction inserts an event record into the `outbox` table:
   - `id`: UUID (Primary Key)
   - `event_type`: "review_moderated"
   - `payload`: JSON string with event details (review_id, product_id, status, rating, comment, user, image_url)
   - `status`: "PENDING"
   - `created_at`: TIMESTAMP
3. A background thread/worker in the Reviews Service periodically polls `outbox` where `status = 'PENDING'`, publishes messages to RabbitMQ with **publisher confirmations enabled**, and on successful broker acknowledgment, updates the status to `"SENT"` or deletes the row.

### Reliable Consumption & Idempotency (Commerce Service)
1. The Commerce Service runs an AMQP consumer in a background thread.
2. It listens to the queue `stage4.speckit.commerce.reviews`.
3. When a message is received:
   - It checks the `processed_events` table for the event's `event_id`. If already processed, it acknowledges the message and ignores it (idempotency).
   - Otherwise, it applies the projection update (inserting or deleting reviews in the `product_reviews` projection database table).
   - It invalidates the in-memory cache for that specific product ID.
   - It records the event ID in `processed_events`.
   - It issues a manual `basic_ack` to RabbitMQ.
4. If an exception occurs, the message is not ACKed (or is rejected/nacked) and can be retried. Reconnection logic will utilize an exponential backoff.

### Security and JWT
We will use HS256-signed JWTs.
- The Identity Service signs the JWT using a secret key (from environment variable `JWT_SECRET` or fallback).
- The HTTP Gateway passes the `Authorization: Bearer <token>` header downstream.
- The downstream services decode and verify the JWT locally, ensuring security.

## 3. Local Execution & Docker Compose

### Windows Launcher
- `Start-Services.ps1`: Clears old state, starts RabbitMQ check, starts all 4 services natively in the background, verifying they are healthy.
- `Stop-Services.ps1`: Terminates the background python processes cleanly.

### Docker Compose
A unified `docker-compose.yml` will launch:
- `rabbitmq`: Real RabbitMQ broker on port `5672` (and management interface on `15672`).
- `identity-service`, `commerce-service`, `reviews-service`, `gateway`: Mounted/built correctly.
- `frontend`: React app listening on `18700`.

## 4. Testing Strategy
- **Unit & Service Tests**: Pytest tests for individual microservice endpoints and models.
- **Outbox/Broker Integration Tests**: A dedicated integration test that stops the Commerce consumer, triggers a moderation change, verifies the outbox contains the pending event, restarts the consumer, and verifies the event propagates correctly with zero loss.
- **E2E Tests**: Playwright tests configured to target port `18600` (Gateway) and `18700` (Frontend) to run the full user flow.
