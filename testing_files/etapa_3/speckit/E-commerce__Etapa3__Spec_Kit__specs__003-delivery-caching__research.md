# Research Report: Stage 3 Delivery, Caching, CI and Containers

This report details the architectural inspection of the inherited system and analyzes the technology options for implementing Stage 3.

## Architectural Inspection

### 1. Backend Codebase (Python / FastAPI)
- **State Management**: The backend is fully stateless relative to persistent files; all users, sessions, and reviews are stored in-memory using module-level variables inside `backend/src/storage.py` (`USERS_DB`, `SESSIONS_DB`, `REVIEWS_DB`).
- **Endpoint Structure**:
  - GET `/api/products` (Loads catalog from `catalog.json` and returns it). Perfect candidate for public API caching.
  - GET `/api/products/{product_id}/reviews` (Returns approved reviews for a specific product). Perfect candidate for public API caching.
  - POST `/api/moderation/reviews/{review_id}/status` (Updates review status). This route updates the state and MUST trigger selective cache invalidation for the corresponding product's reviews.
  - GET `/api/moderation/reviews` (Returns all reviews in the system). Accessible only to the `moderator` user. Must NEVER be cached or leak to unauthenticated users.

### 2. Frontend Codebase (React / TypeScript / Vite or CRA)
- Let's check: Is the frontend built with Create React App (CRA) or Vite?
  Looking at `frontend/package.json` will tell us what test scripts and building toolchain are defined.
  (We will inspect `frontend/package.json` in the code phase, but we assume CRA or Vite, and we'll configure E2E to test against port `3000` which is standard).

---

## Technology Choice Analysis

### 1. Public API Response Caching
- **Option A: Custom Thread-Safe Caching Utility (Selected)**
  - *Pros*: Extreme lightweight footprint; zero external packages or Docker services required; easy to control, inspect, and unit-test; allows targeted, instant cache invalidation on review status changes.
  - *Cons*: Keeps cached responses in-memory (highly suited for our in-memory backend).
- **Option B: FastAPI-Cache package (with Redis)**
  - *Pros*: Industry-standard for large production setups.
  - *Cons*: Violates the "local demonstration without external paid/unnecessary services" constraint, adding immense environment complexity.

### 2. End-to-End Testing Framework
- **Option A: Playwright (Selected)**
  - *Pros*: Native TypeScript support, fast execution speed, extremely reliable auto-waiting, easy browser installation, and rich HTML reporting.
  - *Cons*: None for this scenario.
- **Option B: Cypress**
  - *Pros*: Interactive GUI.
  - *Cons*: Slightly slower CI performance and heavier package footprint.

### 3. Containerization
- **Backend Dockerfile**: A multi-stage build starting with `python:3.11-slim` for compiling dependencies, and generating a minimal execution image.
- **Frontend Dockerfile**: A multi-stage build compiling React TS code in `node:18` and serving the static folder via `nginx:alpine` or a lightweight `node` static server, configured to proxy API calls to the backend service.

---

## Quality Metrics & Coverage Strategy
- **Backend Coverage**: Use `pytest-cov` to run unit tests and output `coverage.xml`.
- **Frontend Coverage**: Use standard `jest` / `react-scripts` coverage flag to generate `coverage/lcov.info`.
- **E2E Validation**: The Playwright suite will run in a dedicated folder `/e2e` to prevent dependency conflicts with the frontend.
