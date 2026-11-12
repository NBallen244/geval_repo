# Research: Stage 2 Product Reviews & Moderation

This document details the architectural choices, assumptions, and technology options researched for implementing product reviews with optional images and a moderation dashboard.

## Key Decisions & Assumptions

### 1. Simple, Local, In-Memory Storage
Just like Stage 1 stores users, sessions, and orders in-memory (inside Python global structures in `storage.py`), Stage 2 will store reviews in-memory:
```python
REVIEWS_DB: List[dict] = []
```
This ensures zero external dependencies, no database configuration, and extremely fast, self-contained demonstration capabilities. The database resets whenever the backend restarts.

### 2. Client-Side Base64 Image Handling
To support attached images cleanly and avoid multipart forms, folder creation, file system permission problems, or static path configurations:
- The React frontend will use a standard file input `<input type="file" accept="image/*" />`.
- When an image is selected, the frontend converts the file to a Base64-encoded string using `FileReader`.
- The Base64-encoded string is sent to the backend as a string property `image_base64` in the JSON request body.
- The backend stores this string.
- When reviews are requested, the backend returns the Base64 string directly, and the React app displays it using `<img src={review.image_base64} />`.
This is a standard, robust solution for lightweight local-demo image uploading.

### 3. Moderation Identity (`moderator` user)
To distinguish normal users from the moderator:
- A user account with the identifier `moderator` is treated as a moderator.
- On backend startup, we can automatically pre-register the user `moderator` with hashed password `moderator` in `USERS_DB` (or allow registering it dynamically, but pre-registering is much better for demonstration!).
- Only the user signed in with identifier `moderator` can see the "Moderation Dashboard" in the frontend and use the review state modification endpoints.

### 4. Moderation States
Reviews can have one of three statuses:
- `"pending"` (Default: visible only on Moderation Dashboard).
- `"approved"` (Visible on product details page and Moderation Dashboard).
- `"rejected"` (Visible only on Moderation Dashboard).

### 5. Seamless Product Page Integration
- In Stage 1, there is a list of products. To view reviews and the review form, we will enhance the frontend so clicking on a product in the catalog displays its expanded details view (either in a modal, a separate tab, or below the product card).
- Let's check how the catalog is structured currently. In `frontend/src/components/Catalog.tsx` and `frontend/src/pages/CatalogPage.tsx`, is there an expanded product details view? Let's check.
- If there is none, or if it is simple, we will expand it by showing a reviews list and form for the selected product.

Let's do a quick read of `frontend/src/components/Catalog.tsx` to understand what UI we already have.
Let's keep research concise and focused. Let's write this research artifact now.
