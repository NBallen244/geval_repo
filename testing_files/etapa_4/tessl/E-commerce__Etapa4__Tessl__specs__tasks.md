# Implementation Tasks - Stage 1 E-Commerce

This document lists the implementation tasks required to build the Stage 1 application. All tasks are mapped to their corresponding requirements and design elements.

## Phase 1: Workspace Setup (Pre-Implementation Plan)
*Note: No implementation or installation is to be performed in the current specification step.*
- **TSK-1.1**: Initialize the project directory structure separating `frontend/` and `backend/`. *(Traces to: REQ-TEC-4, Technical Design Section 2)*
- **TSK-1.2**: Set up the React + TypeScript frontend configuration template. *(Traces to: REQ-TEC-1, Technical Design Section 1)*
- **TSK-1.3**: Set up the FastAPI backend configuration template. *(Traces to: REQ-TEC-2, Technical Design Section 1)*
- **TSK-1.4**: Establish mechanisms to ensure that all specification artifacts, source-code identifiers, code comments, technical documentation, and user-facing interface text remain strictly in English. *(Traces to: REQ-TEC-6)*

## Phase 2: Backend Development (Python & FastAPI)
- **TSK-2.1**: Define the mock product catalog data structures containing Name, Representative Image, Description, Price, and Availability. *(Traces to: REQ-CAT-2, REQ-CAT-3, Technical Design Section 4)*
- **TSK-2.2**: Implement the endpoint to retrieve the list of products for the catalog. *(Traces to: REQ-CAT-1, Technical Design Section 3)*
- **TSK-2.3**: Implement user account registration, including validation of fields, error feedback, and password hashing. *(Traces to: REQ-ATH-1, REQ-ATH-4, REQ-ATH-5, Technical Design Section 4, 5)*
- **TSK-2.4**: Implement session management / authentication endpoints (sign-in, sign-out) with validation and secure error messages. *(Traces to: REQ-ATH-1, REQ-ATH-3, REQ-ATH-4, Technical Design Section 3, 5)*
- **TSK-2.5**: Implement a simulated checkout endpoint that validates the checkout payload and returns fictitious success confirmations. *(Traces to: REQ-CHK-3, REQ-CHK-4, REQ-CHK-5, Technical Design Section 3)*

## Phase 3: Frontend Development (React & TypeScript)
- **TSK-3.1**: Develop the main catalog interface displaying each product's name, image, description, price, and availability, including "Add to Cart" functionality. *(Traces to: REQ-CAT-1, REQ-CAT-2, REQ-CRT-1, REQ-UX-7)*
- **TSK-3.2**: Implement the local shopping cart state management to handle adding items, modifying quantities, removing items, and calculating the running total. *(Traces to: REQ-CRT-1, REQ-CRT-3, REQ-CRT-4)*
- **TSK-3.3**: Develop the shopping cart drawer or page view reflecting the products contained, their quantities, their individual prices, and the accumulated purchase total, including the empty state. *(Traces to: REQ-CRT-2, REQ-CRT-3, REQ-CRT-4)*
- **TSK-3.4**: Create registration and login forms with input validation, helper messages, error indicators, and active session visual feedback. *(Traces to: REQ-ATH-1, REQ-ATH-2, REQ-ATH-4, REQ-ATH-5)*
- **TSK-3.5**: Integrate checkout navigation to present the required checkout summary showing products, quantities, and total. If any demonstration information is collected to complete the simulated journey, it must be limited to the minimum necessary. Do not invent or require any specific checkout fields. *(Traces to: REQ-CHK-1, REQ-CHK-2, REQ-CHK-3)*
- **TSK-3.6**: Create the simulated checkout confirmation interface presenting fictitious payment warnings, unambiguous completion confirmation, and a purchase summary. This interface must implement a comprehensible post-confirmation state (such as a clear navigation option back to the catalog or a state-reset control) from which a new purchase journey can be started. *(Traces to: REQ-CHK-4, REQ-CHK-5, REQ-UX-4)*
- **TSK-3.7**: Apply UI styling to ensure responsiveness on desktop and mobile screens, legible typography, proper keyboard navigation, and explicit label associations. *(Traces to: REQ-UX-7, REQ-UX-8, REQ-UX-9)*
- **TSK-3.8**: Implement empty-cart checkout prevention by disabling checkout navigation buttons when the cart is empty and enforcing empty-state validation on the client and API level. *(Traces to: REQ-CHK-6)*
- **TSK-3.9**: Implement visible sign-out UI control and state updates, ensuring that clicking sign-out clears the client-side session state, triggers the sign-out API request, and updates the visible UI indicator to an inactive session state. *(Traces to: REQ-ATH-2, REQ-ATH-3, Technical Design Section 3)*
- **TSK-3.10**: Implement loading, empty, and error states across the catalog loading, empty cart view, registration/login form submissions, and simulated checkout processing to help the user understand what is happening and what action to take next. *(Traces to: REQ-ATH-4, REQ-UX-6)*
- **TSK-3.11**: Implement checkout authentication guard so that an unauthenticated buyer trying to checkout is guided to sign in or register, preserving the active cart contents, and allowing the purchase journey to proceed upon successful login. *(Traces to: REQ-ATH-7, REQ-UX-3)*

## Phase 4: Integration, UX, and Verification
- **TSK-4.1**: Integrate frontend API calls with the backend endpoints, ensuring the cart context is fully preserved during and after registration/sign-in. *(Traces to: REQ-UX-1, REQ-UX-3, Technical Design Section 3)*
- **TSK-4.2**: Verify consistency of product details, prices, quantities, and totals across catalog, cart, checkout, and confirmation views. *(Traces to: REQ-UX-2, REQ-CAT-3)*
- **TSK-4.3**: Add UI visual feedback for all key events (adding/removing items, session changes, validation errors, successful simulated purchase). *(Traces to: REQ-UX-5)*
- **TSK-4.4**: Verify the system handles empty cart checkout prevention. *(Traces to: REQ-CHK-6)*
- **TSK-4.5**: Verify that completing a purchase leaves the application in a state ready to start a new purchase. *(Traces to: REQ-UX-4)*

## Phase 5: Stage 2 - Backend Implementation
- **TSK-5.1**: Define the in-memory review storage in `database.py` and pre-populate with mock reviews. *(Traces to: REQ-REV-3, REQ-REV-7, Section 6 of Design)*
- **TSK-5.2**: Define Pydantic models for submitting reviews and updating status in `models.py`. *(Traces to: REQ-REV-2, Section 6 of Design)*
- **TSK-5.3**: Implement the `GET /api/products/{id}/reviews` endpoint in `main.py` to retrieve approved reviews. *(Traces to: REQ-REV-7, REQ-REV-8, Section 6 of Design)*
- **TSK-5.4**: Implement the `POST /api/products/{id}/reviews` endpoint in `main.py` for review submission, validating rating (1-5) and comment, automatically assigning user session details, and saving as `pending`. *(Traces to: REQ-REV-1, REQ-REV-2, REQ-REV-3, REQ-REV-4, Section 6 of Design)*
- **TSK-5.5**: Implement the `GET /api/moderation/reviews` and `POST /api/moderation/reviews/{id}/status` endpoints in `main.py`, restricting them to the moderator user. *(Traces to: REQ-REV-5, REQ-REV-6, Section 6 of Design)*
- **TSK-5.6**: Auto-populate the system with a default moderator user on startup with username `moderator` and hashed password `moderator`. *(Traces to: REQ-REV-5, Section 6 of Design)*

## Phase 6: Stage 2 - Frontend Implementation
- **TSK-6.1**: Update `AppContext.tsx` to handle reviews and moderation state/API calls (fetching product reviews, submitting reviews, fetching reviews for moderation, approving/rejecting reviews). *(Traces to: REQ-REV-1 to REQ-REV-10)*
- **TSK-6.2**: Design and implement the product reviews list and "Write a Review" form in a new modal or expandable panel in `Catalog.tsx`. *(Traces to: REQ-REV-1, REQ-REV-2, REQ-REV-3, REQ-REV-8, REQ-REV-9, REQ-REV-10)*
- **TSK-6.3**: Implement image file uploading in the "Write a Review" form with type and size checks (e.g. max 2MB) and local conversion to Base64 data-URL. *(Traces to: REQ-REV-2, REQ-REV-3, REQ-REV-10)*
- **TSK-6.4**: Build a "Moderator Dashboard" view/component visible only to the logged-in `moderator` user, showcasing all pending reviews with their details and images, with Approve and Reject buttons. *(Traces to: REQ-REV-5, REQ-REV-6, REQ-REV-7)*
- **TSK-6.5**: Integrate header/navigation updates to display a link to the "Moderation Dashboard" when the logged-in user is `moderator`. *(Traces to: REQ-REV-5)*

## Phase 7: Stage 3 - Architecture & Automated Delivery Verification
- **TSK-7.1**: Implement the backend bounded response caching layer in `backend/app/cache.py` with 60s default TTL for public endpoints. *(Traces to: REQ-CCH-1, REQ-CCH-2, REQ-CCH-4, Technical Design Section 7.4)*
- **TSK-7.2**: Integrate caching in `backend/app/main.py` and implement immediate cache invalidation for product reviews upon submission and approval/rejection. *(Traces to: REQ-CCH-3, Technical Design Section 7.4)*
- **TSK-7.3**: Create backend unit/integration tests (using pytest/unittest) to verify the endpoints, authentication, caching behavior, and cache invalidation, compiling a standard `coverage.xml`. *(Traces to: REQ-COV-1, REQ-COV-3, Technical Design Section 7.2)*
- **TSK-7.4**: Create frontend unit/integration tests (using Vitest/Jest) and configure coverage output to generate `lcov.info`. *(Traces to: REQ-COV-2, REQ-COV-3, Technical Design Section 7.2)*
- **TSK-7.5**: Configure Playwright in the frontend directory, installing the necessary library and creating `playwright.config.ts`. *(Traces to: REQ-E2E-1, Technical Design Section 7.1)*
- **TSK-7.6**: Implement comprehensive Playwright E2E tests covering:
  1. Complete purchasing journey (with dynamic user registration, cart totals consistency, and simulated checkout verification without order ID).
  2. Full reviews submission & moderation lifecycle (anonymous visitor -> authenticated user review submission (pending/hidden) -> moderator dashboard approval -> public visibility validation).
  3. Strict access-control check (anonymous/regular user receives access-denied or 403 when hitting moderation views/APIs).
  *(Traces to: REQ-E2E-1, REQ-E2E-2, REQ-E2E-3, REQ-E2E-4, Technical Design Section 7.1)*
- **TSK-7.7**: Create multi-stage Dockerfiles (`backend/Dockerfile` and `frontend/Dockerfile`) and a local orchestration setup (`docker-compose.yml`) with a health check readiness strategy. *(Traces to: REQ-CON-1, REQ-CON-2, REQ-CON-3, Technical Design Section 7.3)*
- **TSK-7.8**: Develop the CI orchestration script `run-ci.ps1` and `.github/workflows/ci.yml` that run all tests, collect coverage, build production assets, and run the E2E test suite automatically. Ensure `run-ci.ps1` fails immediately on any failed native command, tracks and stops started server processes and their child processes in `finally` to prevent orphaned Vite/Node or Python processes, restores the original working directory upon completion, and keeps startup hidden or in the existing console without killing unrelated servers. *(Traces to: REQ-CI-1, REQ-CI-2, Technical Design Section 7.2)*
- **TSK-7.9**: Update `README.md` with explicit, English-only setup, testing, Docker orchestration, and E2E verification commands, along with demo credentials. *(Traces to: REQ-TEC-6)*

## Phase 8: Stage 4 - Distributed Microservices Migration
- **TSK-8.1**: Partition the backend codebase into Identity, Commerce, Reviews, and Gateway service directories. *(Traces to: REQ-STG4-1)*
- **TSK-8.2**: Implement local SQLite database setups for each service, isolating state and storage. *(Traces to: REQ-STG4-2)*
- **TSK-8.3**: Implement internal token verification in Identity Service and call it from Commerce and Reviews. *(Traces to: REQ-STG4-6)*
- **TSK-8.4**: Implement the Transactional Outbox pattern inside Reviews Service, utilizing an SQLite outbox table and a background publisher loop. *(Traces to: REQ-STG4-4)*
- **TSK-8.5**: Implement RabbitMQ publisher confirmations in the outbox publisher daemon. *(Traces to: REQ-STG4-4)*
- **TSK-8.6**: Implement the RabbitMQ subscriber in Commerce Service to process approval events idempotently, update its public review projection table, and invalidate caching. *(Traces to: REQ-STG4-3, REQ-STG4-5)*
- **TSK-8.7**: Construct the thin HTTP Gateway Service to route incoming endpoints over HTTP to appropriate services. *(Traces to: REQ-STG4-1)*
- **TSK-8.8**: Build PowerShell launch and stop scripts (`Start-Services.ps1` and `Stop-Services.ps1`) for local processes. *(Traces to: REQ-STG4-7)*
- **TSK-8.9**: Update E2E test setup, Docker Compose stack, and CI pipeline (`run-ci.ps1` and `workflows/ci.yml`) for the distributed microservices architecture. *(Traces to: REQ-STG4-7)*

## Phase 9: Stage 4 - Reliability and Persistence Fixes
- **TSK-9.1**: Modify `Start-Services.ps1` and `Stop-Services.ps1` to avoid deleting databases on normal start, start background processes with output redirected to logs, run local Vite via node directly to allow clean shutdown, and cleanly kill only owned process trees instead of broad port-killing.
- **TSK-9.2**: Update Commerce and Reviews services to use stable absolute paths for databases and allow environment overrides for DB paths, exchanges, and queues.
- **TSK-9.3**: Implement durable RabbitMQ queues and a concise bounded retry with manual ack in Commerce, and configure Dead-Letter Queue (DLQ) topology.
- **TSK-9.4**: Implement versioned envelopes with `version`, `event_id`, `correlation_id`, `type`, `event_type`, `timestamp`, and `payload` in the Reviews Transactional Outbox, and use mandatory routing with confirmations.
- **TSK-9.5**: Support a Terminal-State Contract by publishing a `review.rejected` event when a review is rejected, and having Commerce process it by removing the public review projection and invalidating the cache.
- **TSK-9.6**: Implement and execute the isolated real-RabbitMQ subprocess acceptance test suite `backend/test_reliability_acceptance.py`.



