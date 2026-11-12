# Tasks: Stage 2 Product Reviews & Moderation

**Input**: Design documents from `/specs/002-product-reviews/`

## Phase 1: Setup
- [x] T001 Initialize Stage 2 Spec Kit structure and templates

## Phase 2: Backend Implementation (Product Reviews & Moderation APIs)

- [x] T002 Update `backend/src/storage.py` to define `REVIEWS_DB = []` and auto-register a default `moderator` user with hashed password `moderator`.
- [x] T003 Implement `POST /api/reviews` endpoint in `backend/src/main.py` (with auth token check, rating validation, and empty comment validation).
- [x] T004 Implement `GET /api/products/{product_id}/reviews` endpoint in `backend/src/main.py` (public endpoint returning approved reviews only).
- [x] T005 Implement `GET /api/moderation/reviews` endpoint in `backend/src/main.py` (moderator-only check, returns all reviews).
- [x] T006 Implement `POST /api/moderation/reviews/{review_id}/status` endpoint in `backend/src/main.py` (moderator-only check, sets status to `"approved"` or `"rejected"`).
- [x] T007 Create `backend/tests/test_reviews.py` and implement unit/integration tests for review submission and moderation workflows.

## Phase 3: Frontend Implementation (Reviews UI & Moderation Dashboard)

- [x] T008 Update `frontend/src/services/api.ts` to add client fetch functions for:
  - `getReviews(productId)`
  - `submitReview(productId, rating, comment, imageBase64)`
  - `getModerationReviews()`
  - `updateReviewStatus(reviewId, status)`
- [x] T009 Implement a `ProductDetails` section within the catalog (e.g. at the bottom of the product page when a product is clicked) inside `frontend/src/components/Catalog.tsx` or as a new component `frontend/src/components/ProductDetails.tsx`, displaying existing approved reviews and a Review Form with image upload.
- [x] T010 Implement `frontend/src/components/ModeratorDashboard.tsx` displaying pending, approved, and rejected reviews with "Approve" and "Reject" actions.
- [x] T011 Update navigation header/navbar in `frontend/src/App.tsx` and `frontend/src/components/AuthStatus.tsx` to conditionally display a "Moderation Dashboard" link for the `moderator` user.
- [x] T012 Integrate `ModeratorDashboard` page/view in `frontend/src/App.tsx` router/tabs.
- [x] T013 Create frontend unit test `frontend/src/tests/Reviews.test.tsx` to verify review submission and dashboard actions.

## Phase 4: Verification & Polish
- [x] T014 Run backend tests using `pytest` to confirm they all pass.
- [x] T015 Run frontend tests using `npm run test`.
- [x] T016 Build frontend using `npm run build` to verify a successful production build.
