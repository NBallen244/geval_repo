# Implementation Plan: Stage 2 Product Reviews & Moderation

**Branch**: `002-product-reviews` | **Date**: 2026-11-06 | **Spec**: [specs/002-product-reviews/spec.md](spec.md)

**Input**: Feature specification from `specs/002-product-reviews/spec.md`

## Summary
Implement product reviews supporting rating (1-5), text comment, and one optional Base64 attached image. Reviews will use a simple backend in-memory DB list and start in `"pending"` status. A logged-in customer can submit reviews. A user logged in as `"moderator"` can view and moderate (approve/reject) all reviews in a dedicated Moderation Dashboard. Normal users (and visitors) see approved reviews on the product details section.

## Technical Context

- **Language/Version**: Python 3.11+, TypeScript 4.9+, React 18
- **Primary Dependencies**: FastAPI (backend), React, standard DOM FileReader (frontend)
- **Storage**: In-memory Python list `REVIEWS_DB` on the backend
- **Testing**: `pytest` for backend, `jest` for frontend
- **Target Platform**: Local demonstration web application

## Project Structure

### Documentation (this feature)

```text
specs/002-product-reviews/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Technology decisions & choices
├── data-model.md        # Data entities schema
├── quickstart.md        # Startup & validation guide
├── contracts/
│   └── api.md           # Backend REST API contracts
└── checklists/
    └── requirements.md  # Requirements verification checklist
```

### Source Code modifications

We will modify:
- **Backend**:
  - `backend/src/storage.py`: Define `REVIEWS_DB` and auto-seed `moderator` user.
  - `backend/src/main.py`: Add API endpoints for:
    - `POST /api/reviews` (submit a review, authenticated)
    - `GET /api/products/{product_id}/reviews` (get approved reviews for a product, public)
    - `GET /api/moderation/reviews` (get all reviews, moderator only)
    - `POST /api/moderation/reviews/{review_id}/status` (approve or reject review, moderator only)
  - `backend/tests/`: Add `test_reviews.py` to verify backend reviews and moderation APIs.
- **Frontend**:
  - `frontend/src/services/api.ts`: Add API client methods for reviews and moderation.
  - `frontend/src/components/Catalog.tsx` / `frontend/src/components/ProductDetails.tsx`: Add product selection details, rendering reviews, and review form with image upload.
  - `frontend/src/components/ModeratorDashboard.tsx`: Add a dashboard for reviewing/moderating pending reviews, accessible when logged in as `moderator`.
  - `frontend/src/App.tsx`: Integrate the Moderation Dashboard page/tab and product details rendering.
  - `frontend/src/tests/`: Add `Reviews.test.tsx` to verify review submission and moderation.
