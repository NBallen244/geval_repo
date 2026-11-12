# Requirements - Stage 1 E-Commerce

This document establishes the atomic and verifiable functional and non-functional requirements for Stage 1, derived directly from the canonical seed specification.

## 1. Product Catalog (CAT)
- **REQ-CAT-1**: The application must provide a product catalog as the main entry point, accessible to visitors without authentication.
- **REQ-CAT-2**: Each product in the catalog must display its name, a representative image, a short description, its price, and its general availability.
- **REQ-CAT-3**: Demonstration data used in the catalog must remain consistent between the user interface and other application flows.
- **REQ-CAT-4 (Optional)**: The application may include an expanded product view. If included, it must complement the catalog and preserve the identical commercial information (name, image, description, price, and availability).
- **REQ-CAT-5 (Exclusion)**: The catalog must not implement text search, advanced filters, recommendations, or complex catalog classification.

## 2. Local Shopping Cart (CRT)
- **REQ-CRT-1**: A person must be able to add products from the catalog to a shopping cart managed locally by the application.
- **REQ-CRT-2**: The cart must display which products it contains, their quantities, their individual prices, and the accumulated total purchase amount.
- **REQ-CRT-3**: The cart must allow the user to adjust product quantities, remove products, and recognize an empty state.
- **REQ-CRT-4**: Changes to the cart must be reflected immediately in the interface and remain available throughout the active journey.
- **REQ-CRT-5 (Exclusion)**: Durable cart persistence across browser closures or separate sessions is not mandatory and is not required for this stage.

## 3. Basic Authentication (ATH)
- **REQ-ATH-1**: The application must provide a simple customer registration and sign-in mechanism using the minimum necessary data to identify a customer.
- **REQ-ATH-2**: The interface must visibly indicate whether a session is active (authenticated) or inactive.
- **REQ-ATH-3**: The interface must provide a way for the authenticated user to sign out.
- **REQ-ATH-4**: Registration and sign-in forms must explain the expected information, validate incomplete or invalid input, and communicate errors without exposing sensitive information.
- **REQ-ATH-5**: Passwords must be handled securely within the academic scope; they must not be displayed in plain text or stored as readable plain text.
- **REQ-ATH-6 (Exclusion)**: The authentication mechanism must not implement multi-factor authentication, external identity providers, password recovery, email verification, or advanced profile management.
- **REQ-ATH-7**: When an unauthenticated buyer must be identified to finish the purchase journey, the application must guide the buyer to sign in or register and then allow the journey to continue without losing the active cart. Visitors must still be able to browse the catalog and prepare the cart without authentication.

## 4. Simulated Checkout (CHK)
- **REQ-CHK-1**: A person with products in the cart must be allowed to proceed to a simulated checkout.
- **REQ-CHK-2**: Before checkout confirmation, the application must present a clear summary of the products, their quantities, and the total purchase amount.
- **REQ-CHK-3**: The checkout process may request only the minimum demonstration information necessary to complete the simulated journey.
- **REQ-CHK-4**: The payment confirmation must be fictitious. The system must clearly and explicitly state that no actual charge is made and no real payment gateway is contacted.
- **REQ-CHK-5**: After successful completion, the system must present an unambiguous purchase confirmation and a summary of the simulated purchase.
- **REQ-CHK-6**: If the shopping cart is empty, the application must prevent the user from proceeding to checkout.
- **REQ-CHK-7 (Exclusion)**: The checkout must not implement an address book, selection of saved addresses, advanced tax breakdowns, or real payment integrations.

## 5. Continuous Journey & User Experience (UX)
- **REQ-UX-1**: The catalog, cart, authentication, and checkout must operate as one continuous and cohesive journey.
- **REQ-UX-2**: Product information, quantities, and totals must remain consistent when moving across all views (catalog, cart, checkout summary, and confirmation).
- **REQ-UX-3**: User authentication (registration or sign-in) must not cause an unjustified loss of the active cart.
- **REQ-UX-4**: A successful checkout confirmation must leave the system in a comprehensible state from which a new purchase journey can be started.
- **REQ-UX-5**: The application must provide visible feedback for relevant actions, including adding or removing a product, signing in, encountering invalid data, and completing the simulated purchase.
- **REQ-UX-6**: The system must handle loading, empty, and error states sufficiently so the user understands what is happening and what action to take next.
- **REQ-UX-7**: The interface must be clear, consistent, and usable on both desktop and mobile screens.
- **REQ-UX-8**: Primary controls must have understandable names, forms must correctly associate labels and messages, and keyboard navigation must not prevent completion of the main journey.
- **REQ-UX-9**: Visual design must not hide or alter any behavior specified in the canonical seed.

## 6. Technical, Architecture & Language Constraints (TEC)
- **REQ-TEC-1**: The frontend must be implemented with React and TypeScript.
- **REQ-TEC-2**: The backend must be implemented with Python and FastAPI.
- **REQ-TEC-3**: The application must separate user interface logic (frontend) from server-side logic (backend) through a clear communication interface.
- **REQ-TEC-4**: The project structure must allow the frontend and the backend components to be run and reviewed separately.
- **REQ-TEC-5**: The catalog and account data may use a simple mechanism appropriate for a demonstration (e.g., in-memory storage).
- **REQ-TEC-6**: All specification artifacts, source-code identifiers, code comments, technical documentation, and user-facing interface text must be written in English.
- **REQ-TEC-7 (Exclusion)**: Do not implement production infrastructure, distributed services, asynchronous processing, real external integrations, real-time inventory, coupons, multi-criteria filtering, dynamic shipping calculations, multiple currencies, seller/admin functionality, containers, CI/CD, mandatory E2E tests, API caching, or advanced access controls.

## 7. Product Reviews & Moderation - Stage 2 Extension (REV)
- **REQ-REV-1**: The application must allow authenticated users to submit reviews for any product in the catalog.
- **REQ-REV-2**: Each review must contain: a rating (an integer between 1 and 5 stars), a title/comment (text), the reviewer's username, and optionally a single attached image.
- **REQ-REV-3**: Review images must be stored locally (e.g., in memory as Base64 encoded strings) without using any third-party or paid hosting services.
- **REQ-REV-4**: All submitted reviews must start in a `"pending"` state and are not visible to regular users browsing the product reviews.
- **REQ-REV-5**: A Moderation Dashboard/View must be accessible to users with the moderator role (user `moderator` or via a demonstrative UI toggle in testing).
- **REQ-REV-6**: From the Moderation Dashboard, a moderator can view all `"pending"` reviews (showing reviewer, rating, comment, and the attached image if any) and must be able to change their state to `"approved"` or `"rejected"`.
- **REQ-REV-7**: Reviews in the `"approved"` state must be visible on their respective product details view. Reviews in `"pending"` or `"rejected"` states must remain hidden from regular users.
- **REQ-REV-8**: Product pages must display a list of all approved reviews, showing the author name, rating (stars), review comment/text, and the attached image (if present).
- **REQ-REV-9**: The catalog or an expanded product detail modal/view must allow users to view product reviews. To keep things clean, we can implement an expandable review section or a detailed product modal view.
- **REQ-REV-10**: The user interface must provide clear, English-only feedback for review submission, image attachment limits (e.g. 2MB size limit, only images allowed), and moderation actions (approval/rejection).

## 8. Architecture & Automated Delivery Verification - Stage 3 (STG3)
*Note: Stage 3 requirements explicitly override the exclusions in REQ-TEC-7 regarding containers, CI/CD, mandatory E2E tests, and API caching.*

### 8.1 End-to-End Testing (E2E)
- **REQ-E2E-1**: The project must include an automated end-to-end (E2E) test suite using Playwright or Cypress running against the real, live running frontend and backend.
- **REQ-E2E-2**: The E2E tests must verify the entire purchasing journey: adding products to cart, registering a new user / logging in, checking out, and viewing the simulated purchase confirmation.
- **REQ-E2E-3**: The E2E tests must verify the full review submission and moderation lifecycle:
  1. A standard authenticated user submits a review with rating and comment.
  2. The review is initially hidden from the public product details view.
  3. The moderator logs in and accesses the Moderation Dashboard to approve the review.
  4. The review is verified as now visible to any catalog visitor on the product reviews list.
- **REQ-E2E-4**: The E2E tests must verify access control by asserting that a standard authenticated customer attempting to access the Moderation Dashboard/view or APIs is denied access (e.g., receives 403 Forbidden or is prevented in the UI).

### 8.2 Continuous Integration Pipeline (CI)
- **REQ-CI-1**: The application must include a local or automated CI configuration (such as GitHub Actions or a highly reproducible PowerShell/Bash pipeline script) that:
  1. Installs all backend and frontend dependencies.
  2. Runs backend unit/integration tests and collects coverage.
  3. Runs frontend tests and collects coverage.
  4. Performs a production build of the frontend.
  5. Launches both backend and frontend servers, and runs the entire E2E test suite against them.
- **REQ-CI-2**: The CI process must run locally without requiring external paid deployments, cloud environments, or external infrastructure.

### 8.3 Containerization & Local Orchestration (CON)
- **REQ-CON-1**: The project must provide reproducible multi-stage Dockerfiles for both backend and frontend.
  - The backend Dockerfile should use a lightweight Python base image and install requirements.
  - The frontend Dockerfile must use multi-stage builds (e.g., build in Node, serve with static file server/Nginx or Node preview).
- **REQ-CON-2**: A local orchestration solution (e.g., Docker Compose) must be provided to spin up both containers under appropriate container networking.
- **REQ-CON-3**: The containerized setup must document health check / readiness strategies to ensure the frontend only initiates or routes requests after the backend is ready.

### 8.4 Public API Response Caching (CCH)
- **REQ-CCH-1**: The backend must implement bounded response caching for suitable public read-only API endpoints:
  - `GET /api/products` (Catalog listing)
  - `GET /api/products/{id}/reviews` (Approved product reviews)
- **REQ-CCH-2**: The caching mechanism must implement documented TTL (Time-To-Live) expiration to avoid serving stale data indefinitely.
- **REQ-CCH-3**: The caching mechanism must implement explicit cache invalidation. Specifically, when a review is approved via the moderation API, the cache for that product's reviews (`GET /api/products/{id}/reviews`) must be invalidated immediately so the new review becomes visible.
- **REQ-CCH-4**: Safety & Isolation: Authentication-specific responses, checkout endpoints, and moderation queues must NEVER be cached or shared between users, preventing leakage of private or moderator-only data.

### 8.5 Automated Test Coverage Reporting (COV)
- **REQ-COV-1**: Backend tests must generate standard coverage outputs (e.g., a `coverage.xml` file) through standard commands.
- **REQ-COV-2**: Frontend tests must generate standard coverage outputs (e.g., an `lcov.info` file) through standard commands.
- **REQ-COV-3**: All test suites must be real; mocks must not be used to fake E2E success or substitute for actual end-to-end verification.


