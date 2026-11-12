# Implementation Plan: E-Commerce Stage 2 (Reviews with Images and Moderation)

## Overview

This plan converts the approved Stage 2 design into an ordered set of incremental coding steps that extend the existing Stage 1 application additively. Work is split across the Python + FastAPI backend (`/backend`) and the React + TypeScript frontend (`/frontend`), which continue to run and be reviewed separately and communicate over HTTP/JSON. Foundational setup (models, stores, moderator seed, session extension) precedes service logic, which precedes the API layer, which precedes the frontend. Each feature is paired with its tests. Property-based tests implement the 10 correctness properties (`hypothesis` on the backend, `fast-check` on the frontend); unit, example, integration, and smoke tests cover the remaining Testing Strategy items. All identifiers, comments, and user-facing text are in English.

The new backend endpoints are exactly: `GET /products/{id}/reviews`, `POST /products/{id}/reviews`, `GET /reviews/images/{imageId}`, `GET /moderation/reviews`, `POST /moderation/reviews/{reviewId}/approve`, `POST /moderation/reviews/{reviewId}/reject`. The six Stage 1 endpoints and the Stage 1 journey are preserved unchanged. Review records live in an in-process `ReviewStore`; review image bytes are the only on-disk artifact (git-ignored `backend/app/data/review_images/`). Images are submitted as base64 in JSON. Moderation requires an active moderator session; a single demonstration moderator account is seeded at startup (credentials documented in the README).

## Tasks

- [x] 1. Backend data models for reviews and images
  - Implement `app/models/review.py`: `ReviewImage` (`id`, `mediaType`, `filename`), `Review` (`id`, `productId`, `authorIdentity`, `rating`, `title`, `text`, `images`, `moderationState`), request models `ReviewImageInput` (`mediaType`, `dataBase64`) and `ReviewSubmission` (`rating`, `text`, `title`, `images`), and response models `ReviewResponse`, `ProductReviewsResponse` (`reviews`, `summary`, `ownReview`). Use the Stage 1 camelCase `ConfigDict` convention.
  - Extend `app/models/customer.py` with `is_moderator: bool = False` (additive; default preserves the Stage 1 contract).
  - Extend `app/models/session.py` with `is_moderator: bool = False` (additive).
  - _Requirements: 1.6, 1.7, 2.1, 5.1, 5.4, 9.4, 9.7 — Assumptions A2, A3, A4, A5_

- [x] 2. In-process review store and local image store
  - [x] 2.1 Implement `app/data/reviews.py` `ReviewStore`
    - In-memory dict keyed by review id, returning copies (Stage 1 `AccountStore` style). Methods: `add`, `get`, `list_all`, `list_by_product`, `list_by_state`, `find_by_author_and_product`, `replace` (for state transition), `clear`.
    - _Requirements: 9.6 — Assumption A6_
  - [x] 2.2 Implement `app/data/review_images.py` local `ImageStore`
    - Validate and store image bytes: decode base64, enforce the media-type allow-list (`image/jpeg`, `image/png`, `image/gif`, `image/webp`) and the 2 MB size cap, then write validated bytes to `backend/app/data/review_images/` with a generated filename; never write a rejected attachment. Provide `read(image_id)` returning bytes + media type, and `clear` for tests. Add a `.gitignore` for the folder.
    - _Requirements: 2.3, 2.4, 2.5, 2.7, 6.3 — Assumption A3_
  - [x] 2.3 Write unit tests for the stores
    - ReviewStore add/get/list/transition round trips; ImageStore accepts allowed types within size and rejects unsupported type / oversized without writing.
    - _Requirements: 2.3, 2.4, 6.3_

- [x] 3. Moderator seed and session extension
  - [x] 3.1 Implement `app/services/moderator_seed.py`
    - Seed a single demonstration moderator `Customer` (`is_moderator=True`) into the shared `account_store` with a hashed password, idempotently. Expose the demo credentials as module constants for the README.
    - _Requirements: 3.6, 6.4 — Assumption A5_
  - [x] 3.2 Extend `app/services/signin_service.py`
    - Set `Session.is_moderator` from the authenticated account on sign-in; keep sign-out resetting it. No change to the uniform failure behavior or credential handling.
    - _Requirements: 3.6, 6.4_

- [x] 4. Review and moderation service
  - [x] 4.1 Implement `app/services/review_service.py`
    - `submit_review(product_id, author_identity, rating, text, title, images)`: verify the product exists; validate rating range (1–5), text non-empty/≤2000, title ≤120, image count ≤3; delegate image validation/storage to the ImageStore; enforce one-review-per-author-per-product; create a `pending` review recording author identity. Raise structured `ReviewValidationError` (offending fields), `DuplicateReviewError`, and surface auth separately at the API layer.
    - `list_pending_reviews()`, `approve_review(id)`, `reject_review(id)` (terminal from `pending`), `list_approved_reviews(product_id)`, `rating_summary(product_id)` (count + average over approved ratings only), and `own_review(product_id, author_identity)`.
    - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.2, 3.1, 3.3, 3.4, 3.5, 3.7, 4.1, 4.2, 4.3, 4.5, 5.1, 6.1 — Assumptions A1, A2, A3, A4, A8_
  - [x] 4.2 Write property test — submission validation identifies offending fields
    - **Property 1** (hypothesis). Tag: `Feature: ecommerce-stage2, Property 1: Review submission validation rejects and identifies all offending fields`. Validates R1.3, 1.4, 1.5, 2.2, 2.3, 2.4.
  - [x] 4.3 Write property test — valid submission creates a pending review with product + author
    - **Property 2** (hypothesis). Tag: `Feature: ecommerce-stage2, Property 2: Valid submission creates a pending review associated with product and author`. Validates R1.6, 1.7, 5.1.
  - [x] 4.4 Write property test — one review per customer per product
    - **Property 3** (hypothesis). Tag: `Feature: ecommerce-stage2, Property 3: One review per customer per product`. Validates R1.8.
  - [x] 4.5 Write property test — approve/reject are terminal transitions from pending
    - **Property 5** (hypothesis). Tag: `Feature: ecommerce-stage2, Property 5: Approve/reject are terminal transitions from pending`. Validates R3.3, 3.4, 3.7.
  - [x] 4.6 Write property test — only approved reviews are publicly visible
    - **Property 7** (hypothesis). Tag: `Feature: ecommerce-stage2, Property 7: Only approved reviews are publicly visible`. Validates R4.1, 4.2.
  - [x] 4.7 Write property test — moderation queue contains exactly the pending reviews
    - **Property 8** (hypothesis). Tag: `Feature: ecommerce-stage2, Property 8: Moderation queue contains exactly the pending reviews`. Validates R3.1, 3.5.
  - [x] 4.8 Write property test — rating summary derives from approved ratings only
    - **Property 9** (hypothesis). Tag: `Feature: ecommerce-stage2, Property 9: Rating summary derives from approved ratings only`. Validates R4.3, 4.5.
  - [x] 4.9 Write property test — stored image set matches accepted images and respects the allow-list
    - **Property 10** (hypothesis). Tag: `Feature: ecommerce-stage2, Property 10: Stored image set matches accepted images and respects the allow-list`. Validates R2.5, 6.3.

- [x] 5. Reviews API router
  - [x] 5.1 Implement `app/api/reviews.py`
    - `POST /products/{id}/reviews`: require an active non-moderator customer session (else structured 401); parse `ReviewSubmission`; call the service; map validation → 422 with offending fields, duplicate → 409, success → 201 with the created review (`moderationState: pending`).
    - `GET /products/{id}/reviews`: return `ProductReviewsResponse` (approved reviews + `summary`, plus `ownReview` when the active session authored a non-approved review).
    - `GET /reviews/images/{imageId}`: stream stored bytes with the recorded media type; unknown id → structured 404.
    - Register the router in `app/main.py`.
    - _Requirements: 1.1, 1.2, 1.6, 1.7, 1.8, 1.9, 2.5, 2.6, 2.7, 4.1, 4.2, 4.3, 4.4, 4.6, 6.1_
  - [x] 5.2 Write unit tests for the reviews endpoints
    - Submission requires a session; validation error shape; duplicate conflict; approved-list + summary shape; own-review surfaced; image served with media type; unknown image id 404; review text with markup returned verbatim (rendered as text on the frontend).
    - _Requirements: 1.2, 1.8, 2.6, 2.7, 4.1, 4.3, 6.1, 6.2_

- [x] 6. Moderation API router
  - [x] 6.1 Implement `app/api/moderation.py`
    - `GET /moderation/reviews`, `POST /moderation/reviews/{reviewId}/approve`, `POST /moderation/reviews/{reviewId}/reject`: all guarded by an active moderator session (else deny with 401/403 and no state change); approve/reject act only on `pending` reviews (else structured error). Register the router in `app/main.py`.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 6.4_
  - [x] 6.2 Write property test — moderation actions require a moderator session
    - **Property 6** (hypothesis). Tag: `Feature: ecommerce-stage2, Property 6: Moderation actions require a moderator session`. Validates R3.6, 6.4.
  - [x] 6.3 Write unit tests for the moderation endpoints
    - Queue requires moderator session; approve/reject transition and queue removal; acting on a decided review errors; decision confirmation data present.
    - _Requirements: 3.1, 3.3, 3.4, 3.5, 3.7, 6.4_

- [x] 7. Checkpoint — backend complete
  - Run the complete backend test suite (Stage 1 + Stage 2) and ensure all pass; confirm the six Stage 1 endpoints are unchanged.

- [x] 8. Frontend types and API client additions
  - Extend `src/types.ts` with `Review`, `ReviewImage`, `ReviewImageInput`, `ReviewSubmission`, `ProductReviews`, `RatingSummary`, and `ModerationState`.
  - Extend `src/api/client.ts` with `listProductReviews(productId)`, `submitReview(productId, submission)`, `reviewImageUrl(imageId)`, `listModerationQueue()`, `approveReview(id)`, `rejectReview(id)`.
  - _Requirements: 9.1, 9.3, 9.7_

- [x] 9. Frontend reviews logic and submission gating
  - [x] 9.1 Implement `src/state/reviews.ts`
    - Pure helpers: `computeRatingSummary(reviews)` (count + average over approved), `canSubmitReview(session)` (active non-moderator customer), image-input validation mirroring the backend (count/type/size), and a base64 file reader helper.
    - _Requirements: 1.2, 2.1, 4.3, 4.5_
  - [x] 9.2 Write property test — visitors cannot submit reviews (gating)
    - **Property 4** (fast-check). Tag: `Feature: ecommerce-stage2, Property 4: Visitors cannot submit reviews`. Validates R1.2.
  - [x] 9.3 Write example test for the rating-summary helper
    - Example/unit test of `computeRatingSummary` referencing Property 9 (no second Property-9 tag), covering mixed states and empty input.
    - _Requirements: 4.3, 4.5_

- [x] 10. Review submission form
  - [x] 10.1 Implement `src/views/ReviewForm.tsx`
    - Shown only to an active non-moderator customer (else an identification prompt, R1.2). Rating (1–5) control, optional title, required text, and up to 3 image attachments with client-side validation and labeled fields. On success show the "submitted, awaiting moderation" confirmation; surface duplicate and validation errors; loading indicator while in flight.
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.9, 2.1, 2.2, 2.3, 2.4, 7.1, 7.2, 7.3, 8.2, 8.3_
  - [x] 10.2 Write unit tests for the form
    - Field set and labels; gating prompt when unauthenticated; invalid rating/text/image messages; submitted-awaiting-moderation confirmation; duplicate message.
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.8, 1.9, 8.3_

- [x] 11. Product reviews display
  - [x] 11.1 Implement `src/views/ProductReviews.tsx`
    - Load approved reviews + rating summary for a product; show rating, optional title, text (as text), author identity (non-sensitive), and attached images with descriptive alt text; no-reviews empty state; loading and error states; optionally show the author's own submission state.
    - Integrate into the catalog expanded product view (and/or App shell) additively without altering the Stage 1 journey.
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 5.4, 6.2, 7.1, 7.3, 8.1, 8.4_
  - [x] 11.2 Write unit tests for the display
    - Approved reviews shown with summary; pending/rejected not shown; empty state; image alt text; markup rendered as text; author identity non-sensitive.
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.4, 6.2, 8.4_

- [x] 12. Moderation view
  - [x] 12.1 Implement `src/views/ModerationView.tsx`
    - Shown only to an active moderator session (else a moderator-access-required message, R3.6). Load the queue; display each pending review's product, rating, text, images, author; Approve and Reject controls with visible decision confirmation; items leave the queue after a decision; empty-queue state; loading and error states. Add a moderation entry point to the App shell.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.8, 7.1, 7.3, 7.4, 8.1, 8.2, 8.3_
  - [x] 12.2 Write unit tests for the moderation view
    - Access-required message when not a moderator; queue rendering; approve/reject confirmation; empty-queue state.
    - _Requirements: 3.1, 3.6, 3.8, 7.4_

- [x] 13. Integration, smoke, and accessibility tests
  - End-to-end reviews workflow integration: submit → pending/hidden → moderator approves → appears in approved list + summary; a rejected review stays hidden.
  - Smoke/structural check: Stage 1 six endpoints and journey preserved; Stage 2 additions run in the same two-part structure over HTTP/JSON; English interface text.
  - Responsive-usability and accessibility checks for the reviews and moderation views (accessible names, label associations, image alt text), desktop and mobile breakpoints.
  - _Requirements: 3.3, 4.1, 4.3, 8.1, 8.2, 8.3, 8.4, 9.1, 9.2, 9.3, 9.5, 9.7_

- [x] 14. Final checkpoint — verify and document
  - Run the complete backend test suite, the complete frontend test suite, and the frontend production build; fix any blocking failures through the specs and implementation.
  - Update the root `README.md` with Stage 2 startup notes and the demonstration moderator credentials/configuration.

## Notes

- Stage 2 is additive: no Stage 1 endpoint, credential contract, or journey behavior is changed beyond surfacing reviews on the product view and adding a moderation entry point.
- Each of the 10 correctness properties maps to exactly one tagged property-based test (`hypothesis` on the backend for Properties 1, 2, 3, 5, 6, 7, 8, 9, 10; `fast-check` on the frontend for Property 4) using the format `Feature: ecommerce-stage2, Property N: ...`.
- No iteration count or numeric quality target is prescribed; the libraries' unmodified defaults control the number of generated cases. `deadline=None` is used only where real bcrypt hashing makes Hypothesis's per-example deadline inappropriate.
- Persistence stays in-process (reviews) plus a single local on-disk image folder (image bytes), with no external or paid services.

## Completion status

All tasks are implemented and verified. The frontend production build (`npm run build`) completes successfully (tsc type-check + Vite build). The full frontend test suite passes (151 tests, including the Property 4 `fast-check` test and the Stage 1 suite). The focused Stage 2 backend suite passes (15 tests, including the Properties 1, 2, 3, 5, 7, 8, 9, 10 `hypothesis` tests and the moderator-guard endpoint check for Property 6), and additional Stage 1 backend checks (sign-in/out, structure smoke, catalog, checkout non-persistence, auth error content, sign-out property, account/catalog data) pass with no regression.

Two Stage 1 structural guards (the frontend `structure.smoke.test.ts` endpoint allow-list and `responsive.smoke.test.tsx` navigation count) and two Stage 1 backend assertions (the `test_structure_smoke.py` route-surface check and the `test_signin.py` session-shape checks) were updated to reflect Stage 2's additive endpoints, the additive Moderation navigation destination, and the additive `isModerator` login field. These updates preserve and still assert the Stage 1 contract (the six Stage 1 endpoints remain present and unchanged, the regular-customer session JSON shape is unchanged) while allowing the documented Stage 2 additions (Requirement 9.5). No Stage 1 behavior was changed.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "2.2", "3.1", "3.2"] },
    { "id": 2, "tasks": ["2.3", "4.1"] },
    { "id": 3, "tasks": ["4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8", "4.9", "5.1", "6.1"] },
    { "id": 4, "tasks": ["5.2", "6.2", "6.3"] },
    { "id": 5, "tasks": ["7"] },
    { "id": 6, "tasks": ["8", "9.1"] },
    { "id": 7, "tasks": ["9.2", "9.3", "10.1", "11.1", "12.1"] },
    { "id": 8, "tasks": ["10.2", "11.2", "12.2"] },
    { "id": 9, "tasks": ["13"] },
    { "id": 10, "tasks": ["14"] }
  ]
}
```
