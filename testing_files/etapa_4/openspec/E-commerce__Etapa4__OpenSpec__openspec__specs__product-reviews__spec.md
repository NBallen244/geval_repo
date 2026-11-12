# Product Reviews Specification

## Purpose

Defines the functional requirements for product reviews, allowing users to submit ratings, text feedback, and images, which are then subject to moderator approval before being displayed on product detail views.

## Requirements

### Requirement: Product Details Page with Reviews
The system SHALL provide an expanded product details page at `/product/:id` displaying the product's name, image, description, price, availability, its average rating, and a list of its approved reviews.

#### Scenario: View product details with approved reviews
- **WHEN** a user visits the product details page for a product that has approved reviews
- **THEN** the system displays the product details, the average star rating, and the list of approved reviews.

#### Scenario: Hide unapproved or rejected reviews
- **WHEN** a user visits the product details page for a product with pending or rejected reviews
- **THEN** the system does not display those reviews on the product details page.

### Requirement: Submit Product Review
The system SHALL allow authenticated users to submit a product review. The review submission form SHALL require a star rating from 1 to 5 and a text comment. The system SHALL support an optional review image.

#### Scenario: Submit a valid product review
- **WHEN** an authenticated user fills out the review form with a 5-star rating and a valid comment and submits it
- **THEN** the review is successfully submitted, starting in a pending state, and the system displays feedback confirming submission.

#### Scenario: Block unauthenticated users from submitting reviews
- **WHEN** an unauthenticated visitor attempts to view or submit the review form on the product details page
- **THEN** the system prompts the visitor to sign in or register to submit a review.

### Requirement: Review Image Upload
The system SHALL allow users to select and attach an image file when submitting a product review. The system SHALL convert the selected image file into a Base64-encoded string for local storage and demonstration purposes.

#### Scenario: Attach image to review
- **WHEN** a logged-in user selects a local image file and submits the review
- **THEN** the system converts the image to Base64, submits it, and displays the image on the review after moderator approval.

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

### Requirement: Reliable Messaging and Event Propagation
To prevent loss of moderation actions during network or broker outages, the system MUST implement reliable messaging patterns. The Reviews service SHALL persist outgoing events transactionally using a local outbox. The system MUST employ publisher confirmations, manual message acknowledgements, idempotent consumers with duplicate detection, and a bounded retry with reconnection backoff.

#### Scenario: Transactional Outbox and Event Recovery
- **WHEN** the broker is temporarily unavailable when a review is moderated
- **THEN** the Reviews service commits the moderation action and the outbox event locally, and successfully recovers and publishes the event once the broker connection is restored.

#### Scenario: Idempotent Consumer and Manual Acknowledgement
- **WHEN** a duplicate event is delivered to the Commerce service
- **THEN** the Commerce service detects the duplicate using the event's unique ID, ignores the duplicate payload, and manually acknowledges the message to RabbitMQ to avoid re-delivery loops.
