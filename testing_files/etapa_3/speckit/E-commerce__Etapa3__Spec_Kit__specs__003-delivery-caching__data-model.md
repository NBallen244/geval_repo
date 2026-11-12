# Data Model & Caching Schema: Stage 3 Delivery, Caching, CI and Containers

This document defines the in-memory caching schemas, data structures, and container network layout for Stage 3.

## Caching Data Structures

The backend implements an in-memory, thread-safe cache store that maps request paths to serialized responses with expiration metadata.

### Cache Store Representation (Internal State)

```python
from datetime import datetime
from typing import Dict, Any, TypedDict

class CacheEntry(TypedDict):
    content: Any          # The JSON response body
    expires_at: datetime  # The timestamp after which the entry is invalid
    etag: str            # Unique hash or token for client-side caching (optional)

# Dictionary representing the public response cache
PUBLIC_RESPONSE_CACHE: Dict[str, CacheEntry] = {}
```

### Cache Keys

Cache keys are constructed based on the normalized REST URL paths to uniquely identify resources:

1. **Product Catalog Cache Key**: `/api/products`
2. **Product Reviews Cache Key**: `/api/products/{product_id}/reviews` (e.g., `/api/products/1/reviews`)

### Cache Lifecycle Policy

| Parameter | Configuration / Behavior |
| :--- | :--- |
| **Default TTL** | 60 seconds (1 minute). |
| **Concurrency** | Read/write access protected by a threading `Lock` to prevent race conditions during concurrent requests. |
| **Eviction Policy** | Lazy eviction: expired keys are checked and deleted when a read request occurs. |
| **Invalidation (Review Approval)** | When a review for `{product_id}` is updated (approved/rejected), the cache key `/api/products/{product_id}/reviews` MUST be deleted immediately. |
| **Cache Exclusion** | Session endpoints (`/api/signin`, `/api/register`, `/api/signout`), checkout (`/api/checkout`), and the moderator's panel review queue (`/api/moderation/reviews`) MUST bypass caching. |

---

## Container Architecture and Networking

The application's containers are orchestrated in a single compose environment with localized DNS resolution.

### Networking Diagram

```text
               +-------------------------------------------+
               |            Local Docker Network           |
               |             (ecommerce-net)               |
               |                                           |
               |  +--------------------+                   |
               |  |  frontend-service  |                   |
               |  |  (Nginx/React App) |                   |
               |  +---------+----------+                   |
               |            |                              |
               |            | HTTP /api requests           |
               |            v                              |
               |  +--------------------+                   |
               |  |  backend-service   |                   |
               |  | (FastAPI / Uvicorn)|                   |
               |  +--------------------+                   |
               +-------------------------------------------+
```

### DNS and Host Names

- **Frontend Container Name**: `frontend` (exposes port `3000` to the host machine)
- **Backend Container Name**: `backend` (exposes port `8000` to the host machine and is reachable as `http://backend:8000` inside the container network)
- **Shared Network Name**: `ecommerce-net`
