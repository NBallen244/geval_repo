# Technical Design - Stage 1 E-Commerce

This document provides a minimal, high-level technical design for Stage 1. It is directly traceable to the canonical seed and avoids prescribing unestablished details.

## 1. Architectural Style & Separation of Concerns
The application is structured as a decoupled client-server architecture consisting of:
1. **Frontend Component**: A single-page application built using React and TypeScript. Responsible for rendering the user interface, managing local shopping cart state, and capturing user actions.
2. **Backend Component**: A server-side application built using Python and FastAPI. Responsible for serving product catalog data, managing user registration/sessions, and validating checkout requests.

*Traceability: REQ-TEC-1, REQ-TEC-2, REQ-TEC-3, REQ-TEC-4.*

## 2. Component Layout & Execution Model
- **Structure**: The project directory will separate the frontend and backend into individual root-level subdirectories to ensure they can be run and reviewed independently.
- **Build & Run**: Each component will contain its own instructions/scripts so that the frontend developer can run the UI, and the backend developer can run the server separately.

*Traceability: REQ-TEC-4.*

## 3. Communication Interface
- **Mechanism (Derived Decision)**: To communicate between the client and server, the React frontend and FastAPI backend will interact using standard HTTP REST endpoints with JSON payloads. This derived decision is the minimal standard mechanism to support a decoupled client-server setup.
- **Endpoints (High-Level)**:
  - **Catalog**: The backend will expose a read-only catalog interface to fetch products.
  - **Authentication**: The backend will expose interfaces for customer registration and session verification (sign-in, sign-out).
  - **Checkout**: The backend will expose a fictitious checkout validation interface.

*Traceability: REQ-TEC-3, REQ-CAT-1, REQ-ATH-1, REQ-ATH-3, REQ-CHK-1.*

## 4. Data Persistence & Demonstration Mechanisms
- **Demonstration Data Store (Derived Decision)**: As established by the seed, the application does not require a production database or persistent database management system.
- **Implementation Strategy**:
  - **Catalog Data**: Hardcoded or loaded from a simple JSON file on the backend server.
  - **Account Data**: Stored using a simple server-side in-memory mechanism (e.g., in-memory dictionaries or lists). Data will persist for the duration of the active backend process lifecycle.
  - **Cart Data**: Managed completely in-memory on the frontend (local state), satisfying the requirement that durable persistence across browser closures is not mandatory.

*Traceability: REQ-TEC-5, REQ-CRT-5.*

## 5. Security & Academic Constraints
- **Password Security**: Passwords sent during registration/login must never be logged or stored in plain text. The backend will hash passwords using a standard hashing algorithm before saving them in the simple demo data store.
- **Error Handling**: Forms and API validation will return meaningful errors to the user but will omit internal system stack traces or sensitive environment variables.

*Traceability: REQ-ATH-4, REQ-ATH-5.*

## 6. Product Reviews & Moderation Architecture - Stage 2 Extension
- **Review Data Model**:
  - `id`: unique integer/string id.
  - `product_id`: integer referencing the product.
  - `rating`: integer (1 to 5).
  - `comment`: string.
  - `image_base64`: optional string (Base64 data URI).
  - `status`: string (`"pending"`, `"approved"`, or `"rejected"`).
  - `username`: string (the reviewer).
  - `created_at`: timestamp or string.
- **Moderation Role**:
  - The backend and frontend will recognize a user with the username `"moderator"` (hashed password `"moderator"`) as a Moderator. Alternatively, a visible "Demo Moderator Toggle" can be added for quick evaluation.
- **Database Storage**:
  - Reviews will be stored in-memory in `REVIEWS = []` in the backend (`app/database.py`).
- **REST APIs**:
  - `GET /api/products/{id}/reviews`: Returns all *approved* reviews for a product.
  - `POST /api/products/{id}/reviews`: Submits a new review (authenticates via Bearer token, sets status to `pending`).
  - `GET /api/moderation/reviews`: Returns *all* reviews (or just `pending` ones) for moderation. Requires Bearer token for user `"moderator"`.
  - `POST /api/moderation/reviews/{id}/status`: Updates status to `"approved"` or `"rejected"`. Requires Bearer token for user `"moderator"`.

*Traceability: REQ-REV-1 to REQ-REV-10.*

## 7. Stage 3 - Architecture & Automated Delivery Verification Design
This section outlines the detailed architectural, testing, and containerization designs to fulfill Stage 3.

### 7.1 Playwright End-to-End Test Suite Design
We will implement E2E tests using **Playwright** in the `frontend` project. Playwright is chosen for its superior speed, multi-browser support, and modern syntax.
- **Directory Structure**: All E2E files will reside in `frontend/e2e/`.
- **Test Scenarios**:
  - `purchasing-journey.spec.ts`:
    1. Visitors can browse products.
    2. Add product to local cart.
    3. Click "Proceed to Checkout" -> redirected / prompted to login.
    4. Register a new customer user (with a dynamic username like `customer_e2e_timestamp`).
    5. Access checkout summary (verify items & totals).
    6. Confirm simulated checkout (verify success feedback, verify NO order ID).
  - `reviews-moderation.spec.ts`:
    1. Log in as a newly registered customer user.
    2. Go to product reviews and submit a new review (rating: 5, comment: "Playwright E2E test comment", optional image).
    3. Submit and verify confirmation of "pending" status.
    4. Verify that logging out and visiting the catalog DOES NOT show this review.
    5. Log in as the `moderator` user.
    6. Navigate to the **Moderation Dashboard** and find the pending review.
    7. Click **Approve**.
    8. Log out and browse as an anonymous visitor or regular customer.
    9. Verify the approved review is now publicly visible on the product's review list.
  - `access-control.spec.ts`:
    1. Log in as a standard registered customer user.
    2. Verify they cannot see the **Moderation Dashboard** in the header.
    3. Verify that trying to navigate directly to the dashboard URL or calling `GET /api/moderation/reviews` via HTTP returns access denied (forbidden) feedback or 403 Forbidden.

*Traceability: REQ-E2E-1, REQ-E2E-2, REQ-E2E-3, REQ-E2E-4.*

### 7.2 Continuous Integration (CI) Design
We will design a unified CI workflow using **GitHub Actions** (`.github/workflows/ci.yml`) and a local PowerShell pipeline script (`run-ci.ps1`) for seamless local and remote validation.
- **CI Pipeline Steps**:
  1. **Checkout & Install**: Clone repository and run `pip install` on backend and `npm ci` / `npm install` on frontend.
  2. **Backend Checks**: Run backend unit/integration tests with `pytest` and generate coverage using `pytest-cov` resulting in `backend/coverage.xml`.
  3. **Frontend Checks**: Run frontend unit tests using `vitest` (or a simple React test suite if configured) and generate coverage resulting in `frontend/coverage/lcov.info`.
  4. **Frontend Production Build**: Build the production bundle using `npm run build`.
  5. **E2E Execution**: Run the backend and frontend servers concurrently, and trigger the Playwright E2E suite (`npx playwright test`).
  6. **Teardown**: Properly terminate background server processes.

*Traceability: REQ-CI-1, REQ-CI-2, REQ-COV-1, REQ-COV-2, REQ-COV-3.*

### 7.3 Multi-Stage Docker & Compose Orchestration Design
To ensure high reproducibility and isolated networking, we will create Docker builds.
- **Backend Dockerfile** (`backend/Dockerfile`):
  - Uses `python:3.10-slim` base image.
  - Copies requirements and installs them.
  - Copies code and runs using `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- **Frontend Dockerfile** (`frontend/Dockerfile`):
  - **Stage 1 (Build)**: Uses `node:18-alpine`, copies package files, installs dependencies, and builds production static files via `npm run build`.
  - **Stage 2 (Preview)**: Uses `node:18-alpine`, installs lightweight static server or utilizes Vite preview to serve build output (`frontend/dist`) on host `0.0.0.0` port `3000`.
- **Docker Compose** (`docker-compose.yml`):
  - Configures a backend service and a frontend service.
  - Exposes port 8000 (backend) and port 3000 (frontend).
  - Uses container networking, with frontend communicating with the backend via `http://backend:8000/api` or proxying correctly.
  - Includes a readiness wrapper script (`wait-for-it` or simple curl-based health check) for the frontend container to wait until `http://backend:8000/api/products` is active before launching, preventing startup race conditions.

*Traceability: REQ-CON-1, REQ-CON-2, REQ-CON-3.*

### 7.4 Public API response Caching Design
To avoid heavy loads on static read data, we will implement a safe, bounded caching layer.
- **Data Structure** (`backend/app/cache.py`):
  - We will manage an in-memory cache dictionary:
    ```python
    CACHE = {
        # cache_key: { "data": response_payload, "expires_at": float_timestamp }
    }
    ```
- **Caching Rules**:
  - Only `GET /api/products` and `GET /api/products/{id}/reviews` will use caching.
  - Expiry is set to a default of 60 seconds (Time-To-Live).
  - Key format: `"products"` for catalog, `"reviews:{id}"` for product reviews.
- **Invalidation Strategy**:
  - When the moderation status of a review is changed (`POST /api/moderation/reviews/{id}/status`), or when a new review is submitted (for immediate updates once approved), the cache for `"reviews:{product_id}"` is cleared/invalidated immediately. This guarantees newly approved reviews appear instantly.
- **Safety / Isolation Constraints**:
  - Private and authenticated endpoints (`/api/login`, `/api/register`, `/api/checkout`, `/api/moderation/reviews`, `/api/logout`) are NEVER cached and bypass the caching layer entirely, ensuring that no sensitive user session data, moderation queues, or private checkout profiles are leaked.

*Traceability: REQ-CCH-1, REQ-CCH-2, REQ-CCH-3, REQ-CCH-4.*


