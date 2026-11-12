# Design

## Context

See proposal.md for the motivation. The current Stage 1 application runs a Python/FastAPI backend using SQLAlchemy with SQLite (`ecommerce.db`), and a React/TypeScript frontend with TailwindCSS. There is an active authentication system storing users in the `users` table.

## Goals / Non-Goals

**Goals:**
- Implement robust persistence for reviews with SQLite.
- Create secure endpoints for review submission, fetching, and moderation.
- Create a clear, beautiful, responsive UI for product details, including star selection, image upload, and review history.
- Design an elegant moderation page for approving and rejecting reviews.
- Convert uploaded files locally on the client-side to base64, storing them directly in SQLite as text, avoiding third-party image hosting services.

**Non-Goals:**
- External image hosting (e.g. S3, Cloudinary).
- Advanced image processing (resizing, compression) on the server, though we can restrict client-side sizes.
- Rich-text editor for reviews (standard text area is sufficient).
- Multiple images per review (single image is sufficient).

## Decisions

### 1. Store images as Base64 in SQLite
- **Rationale**: Since we want a purely local-demo default with zero external dependencies and paid services, storing review images as Base64 `TEXT` directly in the database is the most robust and simplest approach. It is highly portable and doesn't require setting up a local file system storage directory with media-serving routes on FastAPI.
- **Alternatives Considered**: Saving images as files in a local `uploads/` directory on the server. However, this increases complexity due to multi-part form data processing, filepath management, static file serving configuration in FastAPI, and makes deployment and testing less self-contained.

### 2. Dedicated Product Details Route (`/product/:id`)
- **Rationale**: Providing a dedicated route for detailed product inspection allows a clean, uncluttered layout where users can read reviews and fill the review form without overcrowding the main catalog grid.
- **Alternatives Considered**: An expanded view modal on the Catalog page. While this works, a dedicated route behaves like a real e-commerce platform, supports direct linking, and offers a better separation of concerns.

### 3. Moderator Authentication and Access
- **Rationale**: Anyone logged in with the exact account identifier `moderator` is recognized as a moderator. This is extremely simple to configure in a local demo environment, requires no complex Role-Based Access Control (RBAC) database schema changes for Stage 2, and is easy for the evaluator/researcher to test. We can add an `is_moderator` column or simply match the `account_identifier` string. We will support checking if the account identifier is `"moderator"`.
- **Alternatives Considered**: Creating a dedicated `roles` table. This is overkill for Stage 2 given the "simple local-demo defaults" guidance.

## Risks / Trade-offs

- **[Risk] Large Base64 Payloads**: Large image files could bloat the SQLite database and cause high memory usage on fetch.
  - **Mitigation**: Implement a client-side limit in React that restricts uploaded files to less than 1MB and converts them to standard formats before encoding.
- **[Risk] Unauthorized Moderation Submissions**: A normal user could try to spoof moderation approval endpoints.
  - **Mitigation**: Check in the FastAPI moderation backend endpoint that the current authenticated user has the identifier `moderator`. If not, return a `403 Forbidden` response.
