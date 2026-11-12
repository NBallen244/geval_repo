# Feature Specification: Stage 4 Microservices Migration

**Feature Branch**: `004-stage4-microservices`

**Created**: 2026-11-07

**Status**: Approved

**Input**: User description: "Migrate this inherited Stage 3 e-commerce backend to independently running Python/FastAPI microservices with real RabbitMQ business events, preserving the React/TypeScript app and existing purchasing/review/moderation flows."

## User Scenarios & Testing

### User Story 1 - Secure Identity & User Sessions (Priority: P1)
As a customer or moderator, I want to register, sign in, and obtain a secure JWT session token so that I can access personalized or restricted parts of the site safely, with my role verified by cryptographic signatures rather than client-supplied headers.

**Why this priority**: Core authentication is necessary for both buying and moderating products. Security boundary.

**Independent Test**: Register a user and sign in to obtain a JWT. Call protected microservice endpoints with and without this token, and with modified roles in headers, verifying that access is strictly controlled.

**Acceptance Scenarios**:
1. **Given** a new user registrations request is made to `/api/register`, **When** valid credentials are provided, **Then** the Identity service stores the user and registers them.
2. **Given** a user attempts to sign in via `/api/login`, **When** valid credentials are provided, **Then** the Identity service returns a signed JWT containing user identity and role.
3. **Given** a microservice receives an internal or external HTTP request, **When** validating authorization, **Then** it MUST decode and verify the cryptographically signed JWT rather than trusting a client role header.

---

### User Story 2 - Distributed E-Commerce Commerce Core (Priority: P2)
As a customer, I want to browse the product catalog, add items to my cart, and complete a simulated checkout, so that I can buy products.

**Why this priority**: This is the core transactional capability of the business.

**Independent Test**: Add products to cart, proceed to checkout, submit checkout form, and confirm transaction completion.

**Acceptance Scenarios**:
1. **Given** the product catalog, **When** I request `/api/products` from the Commerce service (via the Gateway), **Then** I receive a complete list of products and their reviews (which are synchronized via review projection events).
2. **Given** items in my cart, **When** I submit the simulated checkout form to `/api/checkout`, **Then** the Commerce service processes the checkout, records the purchase locally in `commerce.db`, and clears the cart.

---

### User Story 3 - Event-Driven Reviews & Moderation (Priority: P3)
As a customer, I want to submit reviews for products, and as a moderator, I want to approve or reject reviews, with approved reviews propagating eventually to the catalog projection and invalidating relevant public read caches via a real RabbitMQ message broker.

**Why this priority**: Implements the event-driven microservices architecture using reliable messaging (RabbitMQ).

**Independent Test**: Submit a review (verify it remains pending and hidden in catalog). Sign in as moderator, approve the review, and verify that it propagates to the commerce projection, invalidates the commerce read caches, and becomes visible in the product detail catalog.

**Acceptance Scenarios**:
1. **Given** a customer submits a review to `/api/reviews`, **When** the review is saved in the Reviews service local db, **Then** it is marked as pending and is not visible in the public product view.
2. **Given** a pending review, **When** a moderator approves the review via `/api/moderation/reviews/{id}/status`, **Then** the Reviews service saves the state change, records an outgoing event in an SQLite Outbox table in the same transaction, and publishes it reliably to RabbitMQ.
3. **Given** a RabbitMQ review moderation event is published, **When** the Commerce service consumes it, **Then** the Commerce service updates its local `product_reviews` projection table, invalidates its public product cache, and manually acknowledges (ACK) the message.
4. **Given** a broker outage, **When** a moderation change is processed, **Then** the change is saved, and the event remains in the Outbox until the broker recovers, ensuring zero lost events.
5. **Given** a duplicate message delivery from RabbitMQ, **When** the Commerce service receives it, **Then** the consumer handles it idempotently without creating duplicate reviews.

## Requirements

### Functional Requirements

#### Microservice Architecture
- **FR-001**: The system MUST run as three independent FastAPI services:
  - **Identity Service**: Handles `/api/register`, `/api/login`, `/api/me`. (Port 18601)
  - **Commerce Service**: Handles catalog browsing, shopping cart, and simulated checkout. Manages the public projection of reviews. (Port 18602)
  - **Reviews Service**: Handles review submissions, image uploads, and moderation. (Port 18603)
- **FR-002**: The system MUST include a thin HTTP Gateway service (Port 18600) that routes incoming frontend requests to the appropriate microservices over HTTP. No business logic can run inside the gateway.
- **FR-003**: Each microservice MUST own its data storage (independent SQLite files: `identity.db`, `commerce.db`, `reviews.db` or similar). Cross-service database direct reads/writes are STRICTLY prohibited.

#### Reliable Event-Driven Integration
- **FR-004**: The system MUST integrate a real RabbitMQ AMQP broker to propagate review moderation events from the Reviews service to the Commerce service.
- **FR-005**: All published events MUST use a standardized versioned JSON schema containing `event_id` (UUID), `correlation_id` (UUID), `event_type`, `timestamp` (ISO-8601), and a `payload`.
- **FR-006**: The Reviews service MUST implement the **Transactional Outbox** pattern: events are written to an `outbox` database table within the same transaction as the moderation state update. A background worker reads the outbox, publishes to RabbitMQ with publisher confirmations, and deletes/marks sent events upon confirmation.
- **FR-007**: The Commerce consumer MUST use manual message acknowledgments (`basic_ack` only after successful database processing) and implement consumer idempotency (e.g., tracking processed `event_id`s in a local table).
- **FR-008**: The Commerce consumer MUST handle reconnections with backoff and retry when the broker is temporarily unavailable.

#### Security & Sessions
- **FR-009**: The Identity service MUST issue cryptographically signed JSON Web Tokens (JWT) upon successful authentication.
- **FR-010**: All microservices receiving JWTs MUST verify the cryptographic signature locally or via a shared secret key, refusing to trust unverified headers or client-supplied roles.
- **FR-011**: Moderator dashboards and moderation endpoints MUST be protected and restricted to users with the `moderator` role.

#### Developer Utilities & Environments
- **FR-012**: The system MUST supply PowerShell scripts `Start-Services.ps1` and `Stop-Services.ps1` to launch and cleanly stop all services natively, including checking service readiness.
- **FR-013**: The system MUST supply a `docker-compose.yml` orchestrating RabbitMQ, the microservices, the gateway, and the frontend.
- **FR-014**: The system MUST supply CI configurations, code coverage hooks generating `backend/coverage.xml` and `frontend/coverage/lcov.info`.

## Success Criteria
- **SC-001**: Zero lost moderation events during a 10-second RabbitMQ consumer outage.
- **SC-002**: Independent, concurrent operation of all services on defined ports.
- **SC-003**: Full E2E suite passes cleanly against the distributed architecture.
