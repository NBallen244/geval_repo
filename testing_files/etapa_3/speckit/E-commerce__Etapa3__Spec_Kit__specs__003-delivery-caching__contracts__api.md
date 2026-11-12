# API Caching Contract: Stage 3 Delivery, Caching, CI and Containers

This document outlines the API response headers, caching behaviors, and invalidation rules for Stage 3.

## Public Cached Endpoints

### 1. Retrieve Catalog Products
- **Endpoint**: `GET /api/products`
- **Authentication**: None (Public)
- **Response Caching**: Enabled
- **Caching Policy**: Bounded response cache with 60 seconds TTL.
- **Response Headers**:
  - `X-Cache-Status`: `HIT` or `MISS` (indicates whether response came from cache or origin).
  - `X-Cache-Expires`: RFC 1123 datetime indicating when the cache entry expires.

---

### 2. Retrieve Product Reviews
- **Endpoint**: `GET /api/products/{product_id}/reviews`
- **Authentication**: None (Public)
- **Response Caching**: Enabled
- **Caching Policy**: Bounded response cache with 60 seconds TTL.
- **Response Headers**:
  - `X-Cache-Status`: `HIT` or `MISS`.
  - `X-Cache-Expires`: RFC 1123 datetime.

---

## State Mutating Endpoints (Invalidation Rules)

### 1. Update Review Status (Moderator Only)
- **Endpoint**: `POST /api/moderation/reviews/{review_id}/status`
- **Authentication**: Required (Bearer Token, must be `moderator`)
- **Caching**: Disabled (Never cached).
- **Side Effect (Proactive Cache Invalidation)**:
  - This endpoint updates a review's status (e.g. approved or rejected).
  - On successful update, the backend MUST instantly identify the review's `product_id`.
  - The cache key `/api/products/{product_id}/reviews` MUST be evicted immediately from the cache store to guarantee the next user gets the newly updated reviews list.

---

## Uncached Endpoints (Cache Excluded)

The following endpoints MUST NEVER have their responses cached or served from any cache:
- `POST /api/register`
- `POST /api/signin`
- `POST /api/signout`
- `POST /api/checkout`
- `GET /api/moderation/reviews` (Moderation Queue)
