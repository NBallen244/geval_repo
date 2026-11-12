# Proposal

## Why

Product reviews are essential to build trust and help visitors make informed purchase decisions. This proposal extends the existing Stage 1 academic e-commerce application with a robust product reviews system, including rating stars, base64-encoded review images, and a moderation workflow to ensure safety and quality control.

## What Changes

- **Product Detail View**: Introduce an expanded product view at `/product/:id` showing complete product information, a submission form for product reviews, and a list of approved reviews.
- **Product Reviews Submission**: Allow authenticated users to submit reviews with a 1-5 rating, a review comment, and an optional image.
- **Base64 Image Uploads**: Enable users to upload review images locally, converting them to Base64 on submission to avoid paid external services.
- **Moderation Workflow**: Provide a simple Moderation Dashboard at `/moderation` accessible by a dedicated `moderator` user, allowing pending reviews to be approved or rejected.
- **Approved Reviews Visibility**: Filter reviews displayed on product pages to show only those marked as `approved` by a moderator.

## Capabilities

### New Capabilities
- `product-reviews`: Covers submitting product reviews (with ratings and base64-encoded images), viewing approved reviews on the product details page, and the moderator review approval/rejection dashboard.

### Modified Capabilities
<!-- None -->

## Impact

- **Database**: Add a new `reviews` table linked to products and users, with fields: id, product_id, user_id (account_identifier), rating, comment, image_data (base64 string), status (pending/approved/rejected), and created_at timestamp.
- **Backend API**:
  - `GET /api/products/{id}`: Return product detail.
  - `GET /api/products/{id}/reviews`: Retrieve approved reviews for a product.
  - `POST /api/products/{id}/reviews`: Submit a new review (requires authentication).
  - `GET /api/moderation/reviews`: Retrieve reviews for moderation (requires moderator session).
  - `POST /api/moderation/reviews/{id}/action`: Approve or reject a review (requires moderator session).
- **Frontend Routes**:
  - Add `/product/:id` for Product Details with Reviews.
  - Add `/moderation` for the Moderator Dashboard.
- **Frontend Components**:
  - Link product card title and image to `/product/:id`.
  - Add Header links for the moderation dashboard when logged in as the moderator user.
