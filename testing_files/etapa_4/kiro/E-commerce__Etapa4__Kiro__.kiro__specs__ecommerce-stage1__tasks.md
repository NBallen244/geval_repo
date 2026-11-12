# Implementation Plan: E-Commerce Stage 1

## Overview

This plan converts the approved design into an ordered set of incremental coding steps for a demonstration e-commerce web application. Work is split across a Python + FastAPI backend (`/backend`) and a React + TypeScript frontend (`/frontend`), which run and are reviewed separately and communicate over HTTP/JSON. Foundational setup (project structure, data models, API scaffolding) precedes feature implementation, and each feature is paired with its tests. Property-based tests implement the 19 correctness properties (`hypothesis` on the Python backend, `fast-check` on the TypeScript frontend); unit, example, integration, and smoke tests cover the remaining Testing Strategy items. All identifiers, comments, and user-facing text are in English.

The backend endpoints are exactly: `GET /products`, `GET /products/{id}`, `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `POST /checkout/confirm`. The data store is a simple in-process demonstration mechanism (fixed in-memory catalog data, in-process account data, no stored orders). Checkout confirmation is non-persistent (no stored order, no order ID, no creation timestamp). The cart is managed client-side in in-memory state with no durable persistence. The credential contract is `identifier` + `password` only (password accepted as input, stored only as a hash, never returned).

## Tasks

- [x] 1. Set up separate frontend and backend project structure
  - Create `/frontend` (React + TypeScript) and `/backend` (Python + FastAPI) as independently runnable, separately reviewable parts, each with its own entry point, dependencies, and run command.
  - Scaffold the backend FastAPI application with its API, service, and data-access layer folders so presentation, business logic, and data access are not mixed.
  - Scaffold the frontend React + TypeScript application with a view layer, in-memory journey state, and an HTTP/JSON API client module.
  - Keep all identifiers, comments, and text in English.
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.7_

- [x] 2. Backend data layer and demonstration data store
  - [x] 2.1 Define backend data models and in-process demonstration store
    - Implement the `Product` model (`id`, `name`, `imageUrl`, `description`, `price`, `available`), the `Customer` model (`id`, `identifier`, `passwordHash`), and the `Session` representation (`active`, `customerId`).
    - Implement the data-access layer: fixed in-memory catalog product data and in-process account storage (read/write), storing no order records.
    - _Requirements: 1.3, 1.5, 5.1, 6.9, 7.3, 14.6_

  - [x] 2.2 Write unit tests for the data-access layer
    - Test catalog data retrieval and account create/read against the in-memory store.
    - _Requirements: 1.5, 5.6_

- [x] 3. Catalog API and service
  - [x] 3.1 Implement catalog retrieval service and endpoints
    - Implement the catalog service that returns the shared demonstration product data.
    - Implement `GET /products` (no authentication required) returning the product list and `GET /products/{id}` returning a single product for the expanded view, with structured JSON errors and appropriate status codes.
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 11.1_

  - [x] 3.2 Write unit tests for catalog endpoints
    - Test the product list and single-product responses and the not-found error shape.
    - _Requirements: 1.3, 1.4_

- [x] 4. Authentication API and service (credential contract: identifier + password)
  - [x] 4.1 Implement registration service and `POST /auth/register`
    - Validate that all required items are present and conform to their expected format; on success create a `Customer` account; store the password only as `passwordHash` and never return it.
    - On failure return a structured error that identifies each empty required item and each non-conforming item, and never echoes submitted credential values.
    - _Requirements: 5.1, 5.3, 5.4, 5.5, 5.6, 7.3_

  - [x] 4.2 Write property test for registration validation
    - **Property 5: Registration validation rejects and identifies all offending fields** — the reported set of offending items equals exactly the set of empty or non-conforming items.
    - **Validates: Requirements 5.3, 5.4**
    - Tag: `Feature: ecommerce-stage1, Property 5: Registration validation rejects and identifies all offending fields` (hypothesis).

  - [x] 4.3 Write property test for registration error message safety
    - **Property 6: Registration error messages exclude submitted credential values** — a rejected registration's error message contains none of the submitted credential values.
    - **Validates: Requirements 5.5**
    - Tag: `Feature: ecommerce-stage1, Property 6: Registration error messages exclude submitted credential values` (hypothesis).

  - [x] 4.4 Write property test for valid registration creating an account
    - **Property 7: Valid, conforming registration creates an account** — any fully present, conforming submission creates an account.
    - **Validates: Requirements 5.6**
    - Tag: `Feature: ecommerce-stage1, Property 7: Valid, conforming registration creates an account` (hypothesis, in-memory store).

  - [x] 4.5 Write property test for passwords not stored as plain text
    - **Property 12: Passwords are not stored as readable plain text** — the stored credential representation is never the readable plain-text password.
    - **Validates: Requirements 7.3**
    - Tag: `Feature: ecommerce-stage1, Property 12: Passwords are not stored as readable plain text` (hypothesis, in-memory store).

  - [x] 4.6 Implement sign-in/sign-out service and `POST /auth/login`, `POST /auth/logout`
    - `POST /auth/login` accepts `identifier` and `password`, establishes an active `Session` on complete, valid input, and returns an authentication error indicating failure without unnecessary internal detail on invalid/incomplete input; never returns the password.
    - `POST /auth/logout` ends the active `Session`.
    - _Requirements: 6.1, 6.3, 6.6, 6.9, 7.2, 7.4_

  - [x] 4.7 Write property test for sign-in validation
    - **Property 8: Sign-in validation rejects incomplete or invalid input** — incomplete/invalid sign-in input is rejected with a problem indicating the incomplete or invalid input.
    - **Validates: Requirements 6.3**
    - Tag: `Feature: ecommerce-stage1, Property 8: Sign-in validation rejects incomplete or invalid input` (hypothesis).

  - [x] 4.8 Write property test for sign-out ending the session
    - **Property 9: Sign-out ends the active session** — performing sign-out on any active session results in no active session.
    - **Validates: Requirements 6.6**
    - Tag: `Feature: ecommerce-stage1, Property 9: Sign-out ends the active session` (hypothesis).

  - [x] 4.9 Write property test for register-then-sign-in round trip
    - **Property 10: Register-then-sign-in establishes a session** — registering with valid credentials then signing in with the same credentials establishes an active session for that customer.
    - **Validates: Requirements 6.9**
    - Tag: `Feature: ecommerce-stage1, Property 10: Register-then-sign-in establishes a session (round trip)` (hypothesis, in-memory store).

  - [x] 4.10 Write unit tests for authentication error message content
    - Test that authentication error responses indicate failure without exposing internal details, hashes, or submitted credential values.
    - _Requirements: 7.4_

- [x] 5. Checkout confirmation API and service (non-persistent)
  - [x] 5.1 Implement checkout confirmation service and `POST /checkout/confirm`
    - Define `CheckoutRequest` (`items: [{ productId, quantity }]`) and `CheckoutConfirmation` (`items: [{ productId, name, unitPrice, quantity, lineTotal }]`, `total`, `simulated: true`).
    - Build the confirmation summary and total from the submitted cart contents and catalog data, with `total` equal to the sum of line totals; store no order record and return no order ID and no creation timestamp.
    - Reject an empty submission as the server-side re-check of the empty-cart guard.
    - _Requirements: 10.1, 10.2, 9.5_

  - [x] 5.2 Write property test for confirmation derivation
    - **Property 16: Confirmation summary and total are derived from the submitted cart and catalog data** — for any non-empty cart, the confirmation's items (identity, name, unit price, quantity, line total) and total derive from submitted cart and catalog data, with total equal to the sum of line totals.
    - **Validates: Requirements 10.2**
    - Tag: `Feature: ecommerce-stage1, Property 16: Confirmation summary and total are derived from the submitted cart and catalog data` (hypothesis).

  - [x] 5.3 Write unit tests for the fictitious-payment notice and non-persistence
    - Test that no order record is stored and the response contains no order ID or creation timestamp, and that an empty submission is rejected.
    - _Requirements: 10.1, 9.5_

- [x] 6. Checkpoint - backend complete
  - Ensure all backend tests pass, ask the user if questions arise.

- [x] 7. Frontend API client and shared journey state
  - [x] 7.1 Implement the HTTP/JSON API client
    - Implement typed client methods for `GET /products`, `GET /products/{id}`, `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, and `POST /checkout/confirm`, exposing loading/error outcomes for the UI.
    - _Requirements: 14.3, 14.4, 12.2, 12.4_

  - [x] 7.2 Implement in-memory cart state and session state
    - Implement cart state as the authoritative client-side list of `CartItem` (`{ productId, quantity }`) managed locally with no durable persistence across browser closures or separate sessions, resolving product details from loaded catalog data.
    - Implement derived `CartView` values: per-item `unitPrice`, `lineTotal = price * quantity`, and `total = sum(lineTotal)` as the single source used by Cart and Checkout.
    - Implement in-memory session state (active flag and display identity) holding no password or credential value.
    - _Requirements: 4.1, 4.2, 4.3, 3.1, 3.2, 11.4, 11.5, 7.3_

  - [x] 7.3 Write property test for cart total equals the sum of line totals
    - **Property 2: Cart total equals the sum of line totals** — the accumulated total equals the sum of `unitPrice * quantity`, and each item's unit price is unchanged by quantity changes.
    - **Validates: Requirements 3.1, 3.2**
    - Tag: `Feature: ecommerce-stage1, Property 2: Cart total equals the sum of line totals` (fast-check).

  - [x] 7.4 Write property test for cart contents preserved across navigation
    - **Property 4: Cart contents are preserved across journey navigation** — any sequence of non-mutating view navigations leaves cart contents unchanged.
    - **Validates: Requirements 3.5**
    - Tag: `Feature: ecommerce-stage1, Property 4: Cart contents are preserved across journey navigation` (fast-check).

- [x] 8. Catalog view
  - [x] 8.1 Implement the Catalog component
    - Present the product list as the initial view, reachable without authentication; for each product show name, one representative image, short description, price, and general availability.
    - Include the optional expanded product view showing the same commercial information as the list entry, and provide an add action per product using the shared catalog data.
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 11.1_

  - [x] 8.2 Write property test for catalog-cart product identity consistency
    - **Property 18: Catalog and cart show consistent product identity** — identity, name, and price resolved in the cart equal those shown in the catalog from the same demonstration data.
    - **Validates: Requirements 1.5, 11.2**
    - Tag: `Feature: ecommerce-stage1, Property 18: Catalog and cart show consistent product identity` (fast-check).

- [x] 9. Cart view and cart operations
  - [x] 9.1 Implement the Cart component with add, adjust, remove, and empty state
    - Add a product to the cart and update displayed contents without further user action, with a visible add confirmation.
    - Display each product, quantity, unit price, and accumulated total; update quantity and total immediately on adjustment while keeping unit price consistent; remove a product with a visible removal confirmation; show an empty-state indication when no products are present; retain contents throughout the Active_Journey.
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 11.6_

  - [x] 9.2 Write property test for adding a product makes it present
    - **Property 1: Adding a product makes it present in the cart** — performing the add action results in a cart whose contents include that product.
    - **Validates: Requirements 2.1, 11.6**
    - Tag: `Feature: ecommerce-stage1, Property 1: Adding a product makes it present in the cart` (fast-check).

  - [x] 9.3 Write property test for removing a product makes it absent
    - **Property 3: Removing a product makes it absent from the cart** — removing a contained product results in a cart that no longer includes it.
    - **Validates: Requirements 3.3**
    - Tag: `Feature: ecommerce-stage1, Property 3: Removing a product makes it absent from the cart` (fast-check).

  - [x] 9.4 Write unit tests for cart feedback and empty state
    - Test the add confirmation, the removal confirmation, and the empty-state indication.
    - _Requirements: 2.2, 3.3, 3.4_

- [x] 10. Checkpoint - catalog and cart complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Authentication view
  - [x] 11.1 Implement the Authentication component (registration, sign-in, sign-out, session indicator)
    - Provide registration and sign-in forms using the `identifier` + `password` contract, with labels describing expected input; render password fields obscured and never display passwords as readable text.
    - Validate required/format rules and surface errors that exclude submitted credential values and omit unnecessary internal detail; show visible confirmations for sign-in and sign-out; display the active/inactive session indicator.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 7.1, 7.2, 7.4_

  - [x] 11.2 Write property test for passwords never appearing as plain text in outputs
    - **Property 11: Passwords never appear as readable plain text in outputs** — no rendered view and no API response contains the entered password as readable plain text.
    - **Validates: Requirements 7.2**
    - Tag: `Feature: ecommerce-stage1, Property 11: Passwords never appear as readable plain text in outputs` (fast-check).

  - [x] 11.3 Write unit tests for auth form fields, labels, masking, indicators, and confirmations
    - Test registration/sign-in field sets and labels (R5.1, R5.2, R6.1, R6.2), password field masking (R7.1), authentication error message content (R7.4), active/inactive session indicators (R6.4, R6.5), and sign-in/sign-out confirmations (R6.7, R6.8).
    - _Requirements: 5.1, 5.2, 6.1, 6.2, 6.4, 6.5, 6.7, 6.8, 7.1, 7.4_

- [x] 12. Checkout view and identification gate
  - [x] 12.1 Implement the Checkout component with identification gate and completion
    - Present the pre-confirmation summary of products, quantities, and total; request only minimum demonstration information, if any; provide no address book or saved-address selection; prevent proceeding when the cart is empty.
    - Enforce identification before completion: when the person is not identified, offer sign-in and register options and block completion until identified, preserving cart items across sign-in and registration.
    - Display the fictitious-payment notice; on success show an unambiguous confirmation with a purchased-items summary and visible finish feedback, and return to a comprehensible state from which a new purchase can start.
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.4_

  - [x] 12.2 Write property test for completion blocked while not identified
    - **Property 13: Completion is blocked while the person is not identified** — for any non-empty cart with an unidentified person, the journey cannot complete.
    - **Validates: Requirements 8.2**
    - Tag: `Feature: ecommerce-stage1, Property 13: Completion is blocked while the person is not identified` (fast-check).

  - [x] 12.3 Write property test for authentication preserving the active cart
    - **Property 14: Authentication preserves the active cart** — sign-in or registration during the Active_Journey leaves cart items equal to those before the authentication action.
    - **Validates: Requirements 8.3, 8.4**
    - Tag: `Feature: ecommerce-stage1, Property 14: Authentication preserves the active cart` (fast-check).

  - [x] 12.4 Write property test for checkout reachable only when cart is non-empty
    - **Property 15: Checkout is reachable only when the cart is non-empty** — proceeding to checkout as a valid purchase is permitted iff the cart is non-empty.
    - **Validates: Requirements 9.5**
    - Tag: `Feature: ecommerce-stage1, Property 15: Checkout is reachable only when the cart is non-empty` (fast-check).

  - [x] 12.5 Write property test for completion resetting to a new-purchase state
    - **Property 17: Completion resets to a state that allows a new purchase** — after a successful simulated purchase, the state permits starting a new purchase.
    - **Validates: Requirements 10.3**
    - Tag: `Feature: ecommerce-stage1, Property 17: Completion resets to a state that allows a new purchase` (fast-check).

  - [x] 12.6 Write property test for cart-checkout consistency
    - **Property 19: Cart and checkout are consistent** — for any non-empty cart, the checkout summary lists the same product identities, names, prices, per-product quantities, and total as the cart.
    - **Validates: Requirements 9.1, 11.3, 11.4, 11.5**
    - Tag: `Feature: ecommerce-stage1, Property 19: Cart and checkout are consistent` (fast-check).

  - [x] 12.7 Write unit tests for checkout notice, gate options, and minimum information
    - Test the fictitious-payment notice (R10.1), the identification gate offering sign-in and register options (R8.1), the minimum checkout information with no address book/saved-address selection (R9.2, R9.3, R9.4), and the completion feedback (R10.4).
    - _Requirements: 8.1, 9.2, 9.3, 9.4, 10.1, 10.4_

- [x] 13. Checkpoint - all views complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Cross-cutting states, accessibility, and journey wiring
  - [x] 14.1 Implement shared feedback and system states
    - Implement visible invalid-data messages, loading indicators while requests are in flight, empty-state indications describing the next step, and request-failure indications across catalog, authentication, cart, and checkout.
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [x] 14.2 Implement responsive and accessible interface
    - Provide a clear, consistent, usable layout on desktop and mobile; give each primary control an understandable accessible name; associate each form input with its visible label and messages; ensure keyboard navigation does not prevent completing the main journey.
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [x] 14.3 Wire the integrated journey end to end
    - Connect catalog → cart → authentication → checkout so actions in any component are reflected in the others and product identity, quantities, and totals stay consistent across views, ending in a reset-to-new-purchase state.
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

  - [x] 14.4 Write integration and smoke tests
    - Integration examples for the journey wiring: add from catalog → cart reflects it → checkout summary matches → simulated completion returns a confirmation and resets state, including a keyboard-only pass through the main journey (R11.1, R13.4).
    - Representative responsive-usability example checks at desktop and mobile breakpoints (R13.1).
    - Smoke/structural checks confirming React + TypeScript frontend and Python + FastAPI backend run separately over HTTP/JSON with UI separated from server-side logic, the cart held client-side with no durable persistence wired, no address book or saved-address selection, and English artifacts/interface text (R14.1–R14.5, R14.7, R4.1–R4.3, R9.3, R9.4).
    - _Requirements: 11.1, 13.1, 13.4, 14.1, 14.2, 14.3, 14.4, 14.5, 14.7, 4.1, 4.2, 4.3, 9.3, 9.4_

- [x] 15. Final checkpoint - ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Remove prescribed iteration counts and the custom property-test timeout
  - Correct the property tests so no numerical quality target or iteration count is prescribed, restoring conformance with the approved design (which deliberately prescribes no iteration count or other numeric quality target). This corrects a deviation found in human validation of the first implementation: property tests introduced explicit iteration counts and a custom test timeout.
  - Remove every explicit Hypothesis `max_examples` setting from the backend property tests (and from any shared Hypothesis `settings`/profile), so the unmodified Hypothesis default controls the number of generated cases. Do not replace it with any other iteration-count or quality-target setting.
  - Remove every explicit fast-check `numRuns` setting from the frontend property tests (and from any shared fast-check parameters/configuration), so the unmodified fast-check default controls the number of generated cases. Do not replace it with any other iteration-count or quality-target setting.
  - Remove the custom numeric Vitest timeout from the password-output property test (Property 11 — passwords never appear as readable plain text in outputs) so it runs under the test runner's unmodified default timeout. If the test previously relied on that timeout, restructure the test so it completes within the default timeout without weakening its assertions or reducing functional coverage (for example, by relying on the restored default generated-case count rather than a raised limit).
  - Retain `deadline=None` only where real bcrypt hashing makes Hypothesis's per-example timing deadline inappropriate. This disables a per-example timing threshold and does not prescribe an iteration count, so it is permitted; do not add it anywhere it is not justified by bcrypt hashing.
  - Preserve all 19 correctness properties and their single tagged property tests (`hypothesis` on the backend, `fast-check` on the frontend, using the `Feature: ecommerce-stage1, Property N: ...` tag format) without weakening any assertion or reducing functional coverage.
  - After the correction, run the complete backend test suite, the complete frontend test suite, and the frontend production build, and confirm all pass.
  - _Design traceability: `design.md` > Testing Strategy > Property-Based Tests — property tests use the established libraries (`hypothesis`, `fast-check`) as single tagged tests, and the Testing Strategy prescribes no iteration count or numerical quality target. This is a design-conformance correction, not the implementation of a functional requirement._

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP; core implementation sub-tasks are never optional.
- Each task references specific requirements for traceability, and each of the 19 correctness properties maps to exactly one tagged property-based test (`hypothesis` on the backend, `fast-check` on the frontend) using the format `Feature: ecommerce-stage1, Property N: ...`.
- No iteration count or numeric quality target is prescribed, matching the approved design.
- Checkpoints provide incremental validation at natural breaks.
- Scope is held exactly to the approved artifacts: non-persistent checkout confirmation (no stored order, no order ID, no creation timestamp), client-side in-memory cart with no durable persistence, the `identifier` + `password` credential contract (password only as input, stored only as a hash, never returned), the six fixed endpoints, and the simple in-process demonstration data store. No deployment, infrastructure, containers, CI/CD, or excluded capabilities are included.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "3.1", "4.1", "4.6", "5.1"] },
    { "id": 3, "tasks": ["3.2", "4.2", "4.3", "4.4", "4.5", "4.7", "4.8", "4.9", "4.10", "5.2", "5.3"] },
    { "id": 4, "tasks": ["7.1", "7.2"] },
    { "id": 5, "tasks": ["7.3", "7.4", "8.1", "9.1", "11.1", "12.1"] },
    { "id": 6, "tasks": ["8.2", "9.2", "9.3", "9.4", "11.2", "11.3", "12.2", "12.3", "12.4", "12.5", "12.6", "12.7"] },
    { "id": 7, "tasks": ["14.1", "14.2", "14.3"] },
    { "id": 8, "tasks": ["14.4"] },
    { "id": 9, "tasks": ["16"] }
  ]
}
```
