# API Contracts: Product Reviews & Moderation Endpoints

This document defines the REST API contract between the frontend and backend for Stage 2 Product Reviews & Moderation.

## Endpoint Interfaces

### 1. Retrieve Approved Product Reviews
Retrieve all approved reviews for a specific product. This is a public, unauthenticated endpoint.

- **Method**: `GET`
- **Path**: `/api/products/{product_id}/reviews`
- **Response Status**: `200 OK`
- **Response Body**:
  ```json
  [
    {
      "review_id": "<REVIEW_ID_UUID>",
      "product_id": "<PRODUCT_ID>",
      "user_id": "<CUSTOMER_IDENTIFIER>",
      "rating": 5,
      "comment": "Excellent coffee maker! High quality.",
      "image_base64": "data:image/png;base64,...",
      "status": "approved",
      "created_at": "2026-11-06T12:00:00.000Z"
    }
  ]
  ```

---

### 2. Submit a Product Review
Submit a new review for a product. Must be authenticated with a valid session token in the authorization header.

- **Method**: `POST`
- **Path**: `/api/reviews`
- **Headers**:
  - `Authorization: Bearer <session_token>`
- **Request Body**:
  ```json
  {
    "product_id": "<PRODUCT_ID>",
    "rating": 5,
    "comment": "Very durable stainless steel kettle.",
    "image_base64": "data:image/png;base64,..."
  }
  ```
- **Response Status**: `201 Created`
- **Response Body**:
  ```json
  {
    "message": "Review submitted successfully and is pending moderation.",
    "review": {
      "review_id": "<REVIEW_ID_UUID>",
      "product_id": "<PRODUCT_ID>",
      "user_id": "<CUSTOMER_IDENTIFIER>",
      "rating": 5,
      "comment": "Very durable stainless steel kettle.",
      "image_base64": "data:image/png;base64,...",
      "status": "pending",
      "created_at": "2026-11-06T12:01:00.000Z"
    }
  }
  ```
- **Error Responses**:
  - `401 Unauthorized` (Invalid or missing token)
  - `400 Bad Request` (Validation failure, e.g., empty comment, rating out of 1-5, or invalid product_id)

---

### 3. Retrieve All Reviews (Moderator Only)
Retrieve all reviews in the system (pending, approved, rejected). Accessible only to the user logged in as `moderator`.

- **Method**: `GET`
- **Path**: `/api/moderation/reviews`
- **Headers**:
  - `Authorization: Bearer <session_token>`
- **Response Status**: `200 OK`
- **Response Body**:
  ```json
  [
    {
      "review_id": "<REVIEW_ID_UUID>",
      "product_id": "<PRODUCT_ID>",
      "user_id": "<CUSTOMER_IDENTIFIER>",
      "rating": 4,
      "comment": "Pretty good.",
      "image_base64": null,
      "status": "pending",
      "created_at": "2026-11-06T12:02:00.000Z"
    }
  ]
  ```
- **Error Responses**:
  - `401 Unauthorized` (Missing token or user is not `moderator`)

---

### 4. Moderate a Review Status (Moderator Only)
Approve or reject a review. Accessible only to the user logged in as `moderator`.

- **Method**: `POST`
- **Path**: `/api/moderation/reviews/{review_id}/status`
- **Headers**:
  - `Authorization: Bearer <session_token>`
- **Request Body**:
  ```json
  {
    "status": "approved" 
  }
  ```
  *(Note: status must be "approved" or "rejected")*
- **Response Status**: `200 OK`
- **Response Body**:
  ```json
  {
    "message": "Review status updated successfully.",
    "review": {
      "review_id": "<REVIEW_ID_UUID>",
      "product_id": "<PRODUCT_ID>",
      "user_id": "<CUSTOMER_IDENTIFIER>",
      "rating": 4,
      "comment": "Pretty good.",
      "image_base64": null,
      "status": "approved",
      "created_at": "2026-11-06T12:02:00.000Z"
    }
  }
  ```
- **Error Responses**:
  - `401 Unauthorized` (Missing token or user is not `moderator`)
  - `400 Bad Request` (Invalid status or review not found)
