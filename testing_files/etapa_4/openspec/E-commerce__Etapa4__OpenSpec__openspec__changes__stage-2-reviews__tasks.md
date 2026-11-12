# Tasks

## 1. Backend Database and Schema Setup

- [x] 1.1 Create the database model `Review` in `backend/app/database.py` with fields: id, product_id, user_id, rating, comment, image_data, status, created_at. Verify that running python starts successfully and tables are created.
- [x] 1.2 Define Pydantic schemas in `backend/app/schemas.py` for submitting a review, listing reviews, and updating moderation actions. Verify that schemas load correctly.

## 2. Backend API Implementation

- [x] 2.1 Implement `/api/products/{id}` to fetch a specific product's detail in `backend/app/main.py`. Verify that calling this endpoint returns 404 for missing and the product object for valid products.
- [x] 2.2 Implement `/api/products/{id}/reviews` to fetch approved reviews for a specific product in `backend/app/main.py`. Verify it returns only `approved` reviews.
- [x] 2.3 Implement authenticated `POST /api/products/{id}/reviews` to submit a review in `backend/app/main.py`. Verify that unauthenticated requests fail with 401, and authenticated requests with invalid ratings fail with 400.
- [x] 2.4 Implement `/api/moderation/reviews` to list reviews for moderation in `backend/app/main.py` (restricted to the moderator user). Verify that unauthorized users get 403.
- [x] 2.5 Implement `/api/moderation/reviews/{id}/action` to approve or reject a review in `backend/app/main.py` (restricted to moderator user). Verify it successfully updates the review's status.

## 3. Frontend Routing and Navigation

- [x] 3.1 Register the `/product/:id` route for the Product Detail page and `/moderation` route for the Moderation page in `frontend/src/App.tsx`. Verify that accessing unhandled routes still redirects to the catalog.
- [x] 3.2 Update `frontend/src/components/Header.tsx` to display a navigation link to the Moderation page when the user logged in is exactly `moderator`. Verify that the moderation link is hidden for normal users.

## 4. Frontend Product Detail and Review Submission Page

- [x] 4.1 Implement `frontend/src/pages/ProductDetailPage.tsx` showing the product's name, image, description, price, availability, average rating, and a list of approved reviews. Verify it links back to the catalog.
- [x] 4.2 Add the Review Submission form inside `ProductDetailPage.tsx` requiring a star rating (1-5), comments, and a file input for image attachment. Verify that when no user is logged in, it prompts to log in instead.
- [x] 4.3 Add file-to-base64 conversion utility in `ProductDetailPage.tsx` for review images and wire the submit button to call the review API. Verify successful submission provides feedback and re-fetches reviews.

## 5. Frontend Moderation Dashboard

- [x] 5.1 Implement `frontend/src/pages/ModerationPage.tsx` fetching and showing all reviews in `pending` status. Verify that it allows clicking "Approve" or "Reject".
- [x] 5.2 Add redirect logic to `ModerationPage.tsx` to block unauthorized users from viewing the dashboard. Verify that unauthorized users are redirected away.

## 6. End-to-End and Verification

- [x] 6.1 Create a Python unit test script `backend/app/test_reviews.py` using `unittest` to programmatically verify the backend reviews flow (submission, moderation, retrieval). Verify tests pass successfully.
- [x] 6.2 Perform manual end-to-end verification of the full Stage 2 reviews flow in the browser. Verify and document moderator credentials and startup instructions.
