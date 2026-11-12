# Spec Delta

## MODIFIED Requirements

### Requirement: Moderation Workflow
The system SHALL support a moderation workflow. All submitted reviews SHALL initially be saved in a `pending` state. The system SHALL provide a Moderation Dashboard at `/moderation` accessible only to users logged in with the account identifier `moderator`. The moderator SHALL be able to approve or reject pending reviews.

Upon a moderation action, the Reviews microservice SHALL transactionally record and publish a business event to the RabbitMQ broker. The Commerce microservice SHALL consume these events, update its local projection, and invalidate corresponding public endpoint caches to make approved reviews visible.

#### Scenario: Approve pending review
- **WHEN** the moderator views the Moderation Dashboard and clicks approve on a pending review
- **THEN** the review's status is updated to `approved` in the Reviews service, and an event is published via RabbitMQ to update the Commerce public projection asynchronously.

#### Scenario: Reject pending review
- **WHEN** the moderator views the Moderation Dashboard and clicks reject on a pending review
- **THEN** the review's status is updated to `rejected` in the Reviews service, and an event is published via RabbitMQ to update the Commerce public projection asynchronously.

#### Scenario: Prevent unauthorized access to moderation
- **WHEN** a normal authenticated user or an unauthenticated visitor attempts to access `/moderation`
- **THEN** the system redirects them to the login page or home catalog with an error message indicating unauthorized access.

## ADDED Requirements

### Requirement: Reliable Messaging and Event Propagation
To prevent loss of moderation actions during network or broker outages, the system MUST implement reliable messaging patterns. The Reviews service SHALL persist outgoing events transactionally using a local outbox. The system MUST employ publisher confirmations, manual message acknowledgements, idempotent consumers with duplicate detection, and a bounded retry with reconnection backoff.

#### Scenario: Transactional Outbox and Event Recovery
- **WHEN** the broker is temporarily unavailable when a review is moderated
- **THEN** the Reviews service commits the moderation action and the outbox event locally, and successfully recovers and publishes the event once the broker connection is restored.

#### Scenario: Idempotent Consumer and Manual Acknowledgement
- **WHEN** a duplicate event is delivered to the Commerce service
- **THEN** the Commerce service detects the duplicate using the event's unique ID, ignores the duplicate payload, and manually acknowledges the message to RabbitMQ to avoid re-delivery loops.

#### Scenario: Non-Destructive Durable Queue Declaration
- **WHEN** the Commerce consumer starts or reconnects to RabbitMQ
- **THEN** it SHALL idempotently declare the queue topology with durable settings and dead-lettering parameters WITHOUT unconditionally deleting the queue, thereby preserving any offline accepted and queued events.
- **AND** if a structural mismatch of the queue parameters occurs (producing a broker precondition failure), the consumer SHALL catch the exception, safely delete and re-declare the queue as a one-time migration step, and continue startup.
