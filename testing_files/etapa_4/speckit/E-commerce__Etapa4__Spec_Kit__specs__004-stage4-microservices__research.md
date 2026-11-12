# Research Findings: Stage 4 Microservices Migration

## 1. Monolith Endpoint and Middleware Mapping

The inherited Stage 3 backend consists of a single FastAPI application in `backend/src/main.py`. The key patterns identified are:
- **Authentication**: Uses a `get_token_from_header` helper function. We noticed a typo in the frontend's signout request where `"Bearer {token}"` is used instead of the template literal `${token}`. This means our token parser must safely strip any literal `{` and `}` surrounding the token string.
- **State Management**: Historically stored entirely in-memory using Python dictionaries in `storage.py`. For the microservice migration, this will be upgraded to separated SQLite files (`identity.db`, `commerce.db`, `reviews.db`) to ensure process isolation and persistent states across independent process lifecycles.
- **Image Uploads**: Reviews can include base64-encoded image payloads (`image_base64`). These are stored directly within the review record.

## 2. Ports and Broker Settings

Based on `stage4-runtime.json`, the following deployment environment constraints are established:
- **HTTP Gateway Port**: `18600` (frontend talks directly here)
- **Identity Service Port**: `18601`
- **Commerce Service Port**: `18602`
- **Reviews Service Port**: `18603`
- **Frontend App Port**: `18700` (built React server)
- **AMQP URL**: `amqp://ecommerce:stage4-demo@127.0.0.1:5672/stage4_speckit`
- **Event Namespace**: `stage4.speckit`

The broker resides inside the Windows/WSL environment. Since the broker is shared, but vhosts are isolated, outage testing should involve stopping our own consumer connection or stopping the consumer background thread rather than shutting down the global RabbitMQ service.

## 3. Reliability Analysis

- **Outbox Pattern**: Essential to prevent losing events if the broker goes offline or drops the connection. By writing to the `outbox` table during the same SQLite database transaction that approves the review, we guarantee zero lost events. A background thread will handle publishing with publisher confirmations.
- **Consumer Idempotency**: Required to prevent duplicate processing of the same message (which can happen under manual AMQP retry/recovery scenarios). The Commerce consumer will check `processed_events` before applying updates.
- **Manual Acknowledgments**: The Commerce consumer must process the message, successfully write to the database projection table, invalidate the memory caches, and then explicitly call `basic_ack`.
- **Reconnection resilience**: The rabbitmq connections will use a try-except backoff loop so that if the broker drops, they gracefully attempt reconnection.
