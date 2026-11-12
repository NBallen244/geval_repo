# Requirements Document

## Introduction

Stage 2 extends the existing Stage 1 demonstration e-commerce application with **product reviews that support images and moderation**. A signed-in customer can submit a review for a product, optionally attaching one or more images, and give a star rating and written text. Every submitted review enters a moderation workflow: a moderator reviews the pending submission and either approves it (making it publicly visible on the product) or rejects it (keeping it hidden). Visitors and customers see only the reviews that moderation has approved, shown on the relevant product together with an aggregate rating summary.

Stage 2 is purely additive. The Stage 1 purchasing journey — browse the catalog, manage a local cart, register or sign in, and complete a simulated checkout — is preserved unchanged. This document derives its scope from the Stage 2 canonical seed. The seed intentionally leaves several details undecided (review eligibility, rating fields, image limits and storage, moderation states, moderator identity and permissions, persistence, and edit/delete behavior) and delegates those choices to the tool. Each such choice is recorded as a numbered assumption in the **Assumptions** section below and is treated as a first-class requirement.

Like Stage 1, the application stays local and easy to demonstrate: no paid external services, no production infrastructure, and a simple in-process demonstration data store. All artifacts, source code, comments, documentation, and user-facing text are in English.

## Relationship to Stage 1

- Stage 1 artifacts remain authoritative for the catalog, cart, authentication, and simulated checkout and are not modified by Stage 2. The Stage 1 spec lives at `.kiro/specs/ecommerce-stage1/`; this Stage 2 spec lives at `.kiro/specs/ecommerce-stage2/` and references Stage 1 where it builds on it.
- Stage 2 reuses the Stage 1 credential contract (`identifier` + `password`), the Stage 1 `Product` catalog data and its stable product identities, and the Stage 1 in-process demonstration store mechanism.
- Stage 2 adds new backend endpoints and new frontend views/components; it does not remove or change the six Stage 1 endpoints or the existing journey behavior.

## Glossary

- **Application**: The integrated demonstration e-commerce web system, now including product reviews and moderation in addition to the Stage 1 catalog, cart, authentication, and checkout.
- **Product**: An item offered in the catalog, carried over unchanged from Stage 1 (stable `id`, name, image, description, price, availability).
- **Customer**: A person with an account who has an active Session (Stage 1 definition).
- **Visitor**: A person using the Application without an active Session (Stage 1 definition).
- **Moderator**: A person with moderator permissions who can view pending reviews and approve or reject them. A Moderator is identified by signing in with a moderator account.
- **Review**: A customer-authored opinion about a specific Product, consisting of a star rating, written text, and zero or more attached Review_Images, together with moderation state and author identity.
- **Review_Image**: An image attached to a Review, stored locally and associated with that Review.
- **Rating**: An integer star value from 1 to 5 that a Review carries (see Assumption A2).
- **Moderation_State**: The lifecycle state of a Review: `pending`, `approved`, or `rejected` (see Assumption A4).
- **Moderation_Queue**: The set of reviews awaiting a moderation decision (Moderation_State `pending`), presented to a Moderator.
- **Visible_Review**: A Review whose Moderation_State is `approved`; only Visible_Reviews are shown to Visitors and Customers on a Product.
- **Rating_Summary**: The aggregate view of a Product's Visible_Reviews — the count of visible reviews and their average rating.

## Assumptions

The seed delegates the following decisions to the tool. Each is a deliberate, documented, simple local-demo choice and is binding for Stage 2.

- **A1 — Review eligibility.** Any Customer with an active Session may submit a review for any Product. A review does not require a prior purchase (there is no persisted order in Stage 1, so purchase history cannot be verified). Visitors (no active Session) may not submit reviews; they may only read Visible_Reviews. A Customer may submit at most one review per Product; submitting again for the same Product is rejected with a clear message (this keeps the Rating_Summary meaningful and the demo simple).
- **A2 — Rating fields.** A Review carries a required integer **rating** from 1 to 5 (inclusive) and a required **text** body. The text must be non-empty after trimming and at most 2000 characters. A short optional **title** (at most 120 characters) is also accepted. These bounds are demonstration conveniences, not business rules.
- **A3 — Image limits and storage.** A Review may have between 0 and 3 attached images. Each image must be a JPEG, PNG, GIF, or WebP and at most 2 MB. Images are uploaded as part of review submission and stored locally on the backend: the bytes are written to an on-disk demonstration folder (`backend/app/data/review_images/`, git-ignored) and served back through a backend endpoint. No external object storage or CDN is used. Images are transferred as base64-encoded data in the JSON submission to keep the local demo simple and dependency-free (no multipart parser needed beyond what FastAPI provides).
- **A4 — Moderation states.** A Review has exactly one Moderation_State at a time: `pending` (just submitted, not yet decided), `approved` (made visible), or `rejected` (kept hidden). A newly submitted Review always starts as `pending`. Only a Moderator can move a Review from `pending` to `approved` or `rejected`. A moderation decision is terminal in the demo: once `approved` or `rejected`, a Review is not returned to `pending` (this keeps the state machine simple and predictable).
- **A5 — Moderator identity and permissions.** Moderators are a distinct kind of account. A single built-in demonstration moderator account is seeded at startup so the workflow can be demonstrated immediately. Moderator capabilities (viewing the Moderation_Queue and approving/rejecting) require an active moderator Session; a regular Customer Session cannot access them, and the moderation endpoints reject non-moderator requests. The seeded moderator credentials are documented in the project README for the demo.
- **A6 — Persistence.** Reviews and their moderation state are kept in the same in-process demonstration store style as Stage 1 account data: in memory for the lifetime of the running backend process, not a durable database. Review image **bytes** are the one exception — they are written to the local on-disk demonstration folder (A3) so that image serving works through normal HTTP, but this folder is a demonstration artifact and is not a production datastore. Nothing about this introduces external services.
- **A7 — Edit and delete behavior.** To keep the moderation workflow unambiguous, submitted reviews are immutable to their authors: a Customer cannot edit or delete a review after submission. A Moderator's only actions are approve and reject. There is no author-facing edit/delete surface in Stage 2. (A Customer may see the current state of their own submitted review.)
- **A8 — Visibility and aggregation.** Only `approved` reviews are shown to Visitors and Customers on a Product, and only `approved` reviews contribute to the Rating_Summary (count and average). `pending` and `rejected` reviews are never shown publicly. A Review author may additionally see the state of their own submission (pending/approved/rejected) so they understand what happened to it.

## Requirements

### Requirement 1: Submit a Product Review

**User Story:** As a signed-in customer, I want to submit a review for a product, so that I can share my opinion with other shoppers.

#### Acceptance Criteria

1. WHILE a Customer has an active Session, THE Application SHALL provide a mechanism to submit a Review for a given Product.
2. WHEN a Visitor (no active Session) attempts to submit a Review, THE Application SHALL prevent submission and indicate that identification is required.
3. WHEN a Customer submits a Review in which the rating is missing or outside the range 1 to 5, THE Application SHALL reject the submission and display an error identifying the invalid rating.
4. WHEN a Customer submits a Review in which the required text body is empty after trimming, THE Application SHALL reject the submission and display an error identifying the empty text.
5. WHEN a Customer submits a Review whose text exceeds the maximum length or whose title exceeds the maximum length, THE Application SHALL reject the submission and display an error identifying the offending field.
6. WHEN a Customer submits a Review in which all required fields are present and conform to their expected format, THE Application SHALL create the Review associated with the identified Product and the authoring Customer.
7. WHEN a Review is created, THE Application SHALL set its Moderation_State to `pending`.
8. WHEN a Customer who already has a Review for a Product submits another Review for the same Product, THE Application SHALL reject the submission and display a message that one review per product is allowed.
9. WHEN a Review is submitted successfully, THE Application SHALL display a visible confirmation that the Review was submitted and is awaiting moderation.

### Requirement 2: Attach Images to a Review

**User Story:** As a signed-in customer, I want to attach images to my review, so that I can show the product in real use.

#### Acceptance Criteria

1. WHEN a Customer composes a Review, THE Application SHALL allow attaching between 0 and 3 images to that Review.
2. WHEN a Customer attaches more than the allowed number of images, THE Application SHALL reject the submission and display an error identifying the image-count limit.
3. WHEN a Customer attaches an image whose type is not one of the allowed image types, THE Application SHALL reject the submission and display an error identifying the unsupported image type.
4. WHEN a Customer attaches an image whose size exceeds the allowed maximum, THE Application SHALL reject the submission and display an error identifying the size limit.
5. WHEN a Review with attached images is created, THE Application SHALL store each image locally and associate it with that Review.
6. WHEN a Visible_Review has attached images, THE Application SHALL display those images with the Review on the Product.
7. THE Application SHALL serve stored Review_Images over the local backend interface and SHALL NOT depend on any external image hosting or paid service.

### Requirement 3: Moderation Workflow

**User Story:** As a moderator, I want to review pending submissions and decide whether they become visible, so that only appropriate reviews are shown.

#### Acceptance Criteria

1. WHILE a Moderator has an active moderator Session, THE Application SHALL present the Moderation_Queue of all reviews whose Moderation_State is `pending`.
2. WHEN a Moderator views a pending Review, THE Application SHALL display its Product association, rating, text, any attached images, and the authoring account identity.
3. WHEN a Moderator approves a pending Review, THE Application SHALL set that Review's Moderation_State to `approved`.
4. WHEN a Moderator rejects a pending Review, THE Application SHALL set that Review's Moderation_State to `rejected`.
5. WHEN a Moderator approves or rejects a Review, THE Application SHALL remove that Review from the Moderation_Queue.
6. IF a request to view the Moderation_Queue or to approve or reject a Review is made without an active moderator Session, THEN THE Application SHALL deny the request without performing the action.
7. WHEN a moderation decision has already been made for a Review (`approved` or `rejected`), THE Application SHALL NOT allow that Review to be moved back to `pending`.
8. WHEN a Moderator performs an approve or reject action, THE Application SHALL display a visible confirmation of the decision.

### Requirement 4: View Approved Reviews and Rating Summary

**User Story:** As a shopper, I want to read approved reviews and see an overall rating for a product, so that I can make a better purchase decision.

#### Acceptance Criteria

1. WHEN any person views a Product, THE Application SHALL display the Visible_Reviews (Moderation_State `approved`) for that Product, including each review's rating, text, optional title, and attached images.
2. THE Application SHALL NOT display `pending` or `rejected` reviews to Visitors or Customers in the public product view.
3. WHEN a Product has one or more Visible_Reviews, THE Application SHALL display a Rating_Summary consisting of the count of visible reviews and their average rating.
4. WHEN a Product has no Visible_Reviews, THE Application SHALL display an empty-state indication that there are no reviews yet.
5. THE Application SHALL compute the Rating_Summary average only from the ratings of Visible_Reviews for that Product.
6. WHEN a review author views the Product for which they submitted a Review, THE Application MAY display the current Moderation_State of their own submission so the author understands its status.

### Requirement 5: Review Author Identity and Immutability

**User Story:** As a stakeholder, I want review authorship and immutability to be well defined, so that moderation and display stay consistent.

#### Acceptance Criteria

1. WHEN a Review is created, THE Application SHALL record the authoring Customer's account identity on the Review.
2. THE Application SHALL NOT provide a mechanism for a Review author to edit a submitted Review.
3. THE Application SHALL NOT provide a mechanism for a Review author to delete a submitted Review.
4. WHEN a Review's author identity is displayed, THE Application SHALL display only a non-sensitive account identity and SHALL NOT display any password or credential value.

### Requirement 6: Secure and Safe Handling

**User Story:** As a stakeholder, I want reviews and moderation handled safely within the academic scope, so that the demo does not leak sensitive data or accept unsafe input.

#### Acceptance Criteria

1. IF a review submission or moderation request fails validation or authorization, THEN THE Application SHALL return a structured error that indicates the problem without exposing internal system details, stack traces, password hashes, or submitted credential values.
2. THE Application SHALL treat review text as data and SHALL render it as text so that stored markup is not executed as active content in the interface.
3. THE Application SHALL accept only the allowed image types and SHALL reject any attachment that does not conform, without storing the rejected attachment.
4. THE moderation endpoints SHALL verify an active moderator Session before performing any moderation action.

### Requirement 7: Feedback and System States

**User Story:** As a person using the reviews features, I want visible feedback and clear states, so that I understand what is happening.

#### Acceptance Criteria

1. WHILE a review submission, image upload, moderation list load, or moderation decision request is in flight, THE Application SHALL display a visible loading indicator until the request completes or fails.
2. WHEN invalid review or image data is encountered, THE Application SHALL display a visible message identifying the invalid data.
3. IF a reviews or moderation request fails, THEN THE Application SHALL display a visible error indication describing what happened and what the person can do next.
4. WHEN the Moderation_Queue is empty, THE Application SHALL display an empty-state indication that there is nothing to moderate.

### Requirement 8: Usable and Accessible Interface

**User Story:** As a person on desktop or mobile, I want the reviews and moderation interface to be clear and usable, so that I can complete these tasks.

#### Acceptance Criteria

1. WHEN a user accesses the reviews or moderation interface on a desktop or mobile screen, THE Application SHALL present an interface that is clear, consistent, and usable on that screen.
2. THE Application SHALL provide an understandable accessible name for each primary reviews and moderation control.
3. WHEN a review or moderation form is displayed, THE Application SHALL associate each input field with its visible label and messages.
4. WHEN a Review_Image is displayed, THE Application SHALL provide descriptive alternative text for that image.

### Requirement 9: Technology, Architecture, and Language Constraints

**User Story:** As a stakeholder, I want Stage 2 to respect the established technology, architecture, and language constraints, so that it integrates cleanly with Stage 1.

#### Acceptance Criteria

1. THE Application SHALL implement the Stage 2 frontend additions with React and TypeScript, consistent with Stage 1.
2. THE Application SHALL implement the Stage 2 backend additions with Python and FastAPI, consistent with Stage 1.
3. THE Application SHALL keep the user interface separated from server-side logic and communicate over the existing HTTP/JSON interface.
4. THE Application SHALL keep presentation, business logic, and data access separated (API layer, service layer, data-access layer on the backend).
5. THE Application SHALL preserve the Stage 1 catalog, cart, authentication, and simulated checkout behavior without regression.
6. THE Application SHALL use a simple in-process demonstration mechanism for review data, consistent with Stage 1, and a local on-disk folder only for review image bytes (Assumption A6).
7. THE Application SHALL write all Stage 2 specification artifacts, source-code identifiers, code comments, technical documentation, and user-facing interface text in English.

## Scope Restrictions

The following items are out of scope for Stage 2 and must not be implemented as functionality:

- Review helpfulness voting, replies, comment threads, or review reactions.
- Author-facing editing or deletion of submitted reviews (Assumption A7).
- Returning a decided review to `pending`, or any additional moderation states beyond `pending`/`approved`/`rejected` (Assumption A4).
- Automated or AI content moderation, spam scoring, or profanity filtering (moderation is a manual moderator decision).
- External object storage, CDN, image transcoding pipelines, or any paid image service (Assumption A3).
- Durable databases or production infrastructure; persistence stays in-process as in Stage 1 (Assumption A6), with the single local on-disk image folder as a demonstration artifact.
- Purchase-verified reviews or any dependency on a persisted order (Stage 1 stores no orders; Assumption A1).
- Email notifications, moderation audit logs beyond the in-memory state, or role management UIs for creating additional moderators.
- Any change to the Stage 1 six endpoints, the Stage 1 credential contract, or the Stage 1 purchasing journey beyond additive integration points (for example, surfacing reviews on the product view).
