# Requirements Verification Checklist: Stage 4 Microservices Migration

This checklist ensures all functional, non-functional, and operational requirements specified in `spec.md` are fully implemented and verified.

## 1. Architectural & Isolation Requirements

- [ ] **CH-ARCH-01**: Three independently running FastAPI microservices on ports `18601` (Identity), `18602` (Commerce), and `18603` (Reviews).
  - *Verification*: Verified by checking active network listeners during local startup.
- [ ] **CH-ARCH-02**: HTTP Gateway running on port `18600` that routes frontend requests to the proper microservice.
  - *Verification*: Verified by fetching `/api/products` and checking routing.
- [ ] **CH-ARCH-03**: Complete database separation with SQLite files (`identity.db`, `commerce.db`, `reviews.db`). No shared SQL sessions or cross-database file reads.
  - *Verification*: Inspected imports and configuration; verified each service reads and writes strictly to its own file.

## 2. Event-Driven Messaging Requirements

- [ ] **CH-EVT-01**: Real RabbitMQ AMQP broker used for review status synchronization.
  - *Verification*: Checked AMQP exchange, routing keys, and queue setups.
- [ ] **CH-EVT-02**: Standardized versioned JSON event payloads with UUID IDs, correlations, and ISO-8601 timestamps.
  - *Verification*: Verified event payload validation in test suite.
- [ ] **CH-EVT-03**: Transactional Outbox implemented in the Reviews Service. Review status update and outbox insertion occur in a single SQL transaction.
  - *Verification*: Unit tests verifying atomic outbox commits.
- [ ] **CH-EVT-04**: Publisher confirmations enabled for background outbox worker.
  - *Verification*: Verified in outbox publisher code.
- [ ] **CH-EVT-05**: Manual message acknowledgments (ACK) in Commerce consumer after successful projection write and cache invalidation.
  - *Verification*: Code review and integration tests.
- [ ] **CH-EVT-06**: Idempotency guard on Commerce consumer via `processed_events` tracking table.
  - *Verification*: Duplicate message delivery test in test suite.

## 3. Security & Sessions

- [ ] **CH-SEC-01**: Secure cryptographically signed HS256 JWT generation on login.
  - *Verification*: Decoded generated tokens in unit tests.
- [ ] **CH-SEC-02**: Local signature verification in downstream microservices. Clients cannot supply unverified roles in headers.
  - *Verification*: Tested with modified headers and invalid tokens.
- [ ] **CH-SEC-03**: Moderator dashboard routes strictly protected.
  - *Verification*: Tested with normal user credentials attempting moderation routes, confirming 401/403 responses.

## 4. Operational Utilities & Testing

- [ ] **CH-OPS-01**: PowerShell native launch scripts `Start-Services.ps1` and `Stop-Services.ps1` with service health checks.
  - *Verification*: Run and confirm all 4 services launch and terminate gracefully.
- [ ] **CH-OPS-02**: Complete `docker-compose.yml` defining rabbitmq, services, and frontend app.
  - *Verification*: Inspected compose file.
- [ ] **CH-OPS-03**: Integration tests covering:
  - Purchasing journey
  - Submitting hidden pending reviews
  - Moderator approvals
  - RabbitMQ outage and post-recovery message reconciliation
  - Idempotent duplicate event handling
  - *Verification*: Executed `pytest` suite.
