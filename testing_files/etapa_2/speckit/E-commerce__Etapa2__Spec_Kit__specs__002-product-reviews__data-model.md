# Data Model: Stage 2 Product Reviews & Moderation

This document defines the data entities and properties for Stage 2 Product Reviews, representing our chosen in-memory technical choices.

## Data Schema & Entities

### 1. Review (Technical Schema)
Represents a review submitted by a customer for a specific product.

- **Properties**:
  - `review_id` (String): Unique identifier (e.g. UUID).
  - `product_id` (String): Reference to the Product being reviewed.
  - `user_id` (String): The identifier of the logged-in customer who submitted the review.
  - `rating` (Integer): Numeric rating value from 1 to 5.
  - `comment` (String): Text feedback comment from the user.
  - `image_base64` (String or Null): Optional Base64 representation of an attached image.
  - `status` (String): Moderation state, which MUST be one of: `"pending"`, `"approved"`, or `"rejected"`.
  - `created_at` (String): ISO timestamp representing when the review was submitted.
