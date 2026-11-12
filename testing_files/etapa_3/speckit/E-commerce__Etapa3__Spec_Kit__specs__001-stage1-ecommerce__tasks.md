# Tasks: Stage 1 E-Commerce Application

**Input**: Design documents from `/specs/001-stage1-ecommerce/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/api.md

**Tests**: Includes backend and frontend component test tasks to measure coverage and validate seed-approved behavior, derived only from approved requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story, following a clean MVP first approach.

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Parallelizable task (independent files, no conflicting modifications)
- **[Story]**: Identifies the user story this task belongs to (e.g., [US1], [US2], [US3], [US4])
- Detailed repository-relative file paths are specified for every task description.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repository initialization and environment structure setup.

- [X] T001 Create project directories at `backend/` and `frontend/` (ATC-003, ATC-006, ATC-007)
- [X] T002 Initialize frontend React and TypeScript project with `frontend/package.json`, configuring ESLint and style guidelines (ATC-001, ATC-005)
- [X] T003 Initialize backend Python and FastAPI project with `backend/requirements.txt`, configuring local development environment constraints (ATC-002, ATC-005)
- [X] T004 Create local static JSON catalog data file at `backend/src/data/catalog.json` initialized with non-normative sample products (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, ATC-008)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core application infrastructure that MUST be completed before any User Story work begins.

**⚠️ CRITICAL**: All tasks in this phase must be completed before starting Phase 3.

- [X] T005 Implement central FastAPI application in `backend/src/main.py` with basic router routing, CORS permissions, and non-sensitive error handling middleware (ATC-003, ATC-004, ATC-005)
- [X] T006 [P] Implement in-memory data store in `backend/src/storage.py` to handle accounts and session state maps (FR-024, FR-040, ATC-008)
- [X] T007 [P] Implement PBKDF2 secure password hashing utility using `hashlib.pbkdf2_hmac` in `backend/src/security.py`, ensuring passwords are never stored in plain text (FR-039, FR-040)
- [X] T008 [P] Implement frontend REST API service client in `frontend/src/services/api.ts` to consume local HTTP interface endpoints (ATC-003, ATC-004, ATC-005)
- [X] T009 [P] Create backend testing conftest configuration in `backend/tests/conftest.py` and frontend test setups in `frontend/src/setupTests.ts` (ATC-007)

**Checkpoint**: Foundation ready - User Story implementation can now begin.

---

## Phase 3: User Story 1 - Product Browsing & Shopping Cart Management (Priority: P1) 🎯 MVP

**Goal**: Allow unauthenticated visitors to browse product catalog items and manage a local shopping cart in React state.

**Independent Test**: Start backend on port `8000` and frontend on port `3000` separately. Verify products load in catalog, adding products updates cart total immediately, adjust quantities, remove products, and verify empty cart state displays correctly.

### Tests for User Story 1

- [X] T010 [P] [US1] Create catalog endpoint integration tests in `backend/tests/test_catalog.py` (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008)
- [X] T011 [P] [US1] Create cart state and visual component tests in `frontend/src/tests/CatalogCart.test.tsx` (FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021)

### Implementation for User Story 1

- [X] T012 [US1] Implement catalog endpoint `GET /api/products` in `backend/src/main.py` loading catalog list data from the local JSON static file (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, ATC-008)
- [X] T013 [P] [US1] Implement catalog display component in `frontend/src/components/Catalog.tsx` rendering name, representative image, short description, price, and general availability (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008)
- [X] T014 [P] [US1] Implement shopping cart React context state manager in `frontend/src/context/CartContext.tsx` handling local state additions, quantity modifications (selected count in cart), and removals (FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018)
- [X] T015 [P] [US1] Implement cart item list and summary display component in `frontend/src/components/Cart.tsx` communicating products, quantities, prices, accumulated totals, and empty state (FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021)
- [X] T016 [US1] Integrate catalog and cart components in `frontend/src/pages/CatalogPage.tsx` to handle catalog browsing and cart state updates (FR-011, FR-019, FR-020, FR-021, FR-056)

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Basic Authentication & Cart Preservation (Priority: P2)

**Goal**: Provide distinct user registration and sign-in interfaces using a technology-neutral identifier plus password, visibly indicating the session status and preserving the active local cart throughout.

**Independent Test**: Register an account, verifying that registration results in successful account creation, while leaving post-registration session behavior completely unspecified. Successfully sign in to activate the session, confirm the session indicator updates, sign out to end the session and verify that the local cart is preserved throughout.

### Tests for User Story 2

- [X] T017 [P] [US2] Create backend authentication endpoints unit tests in `backend/tests/test_auth.py` verifying registration and sign-in endpoints behavior (FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-033, FR-039, FR-040)
- [X] T018 [P] [US2] Create user session state, form validation, and control component verification tests in `frontend/src/tests/Auth.test.tsx` (FR-023, FR-026, FR-028, FR-029, FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, FR-038, FR-063, FR-064)

### Implementation for User Story 2

- [X] T019 [US2] Implement user registration endpoint `POST /api/register` in `backend/src/main.py` using secure salt PBKDF2 hashing, creating accounts in memory with a technology-neutral identifier. Post-registration session behavior is left completely unspecified (FR-022, FR-023, FR-024, FR-039, FR-040)
- [X] T020 [US2] Implement sign-in endpoint `POST /api/signin` in `backend/src/main.py` verifying identifier and password, returning session token, and activating session (FR-025, FR-026, FR-027, FR-033, FR-039, FR-040)
- [X] T021 [US2] Implement sign-out endpoint `POST /api/signout` in `backend/src/main.py` invalidating the session token in backend storage (FR-029)
- [X] T022 [P] [US2] Create client auth context state manager in `frontend/src/context/AuthContext.tsx` to handle register requests, sign-in token storage in memory, session sign-out, and active session visual state (FR-024, FR-025, FR-027, FR-028, FR-029)
- [X] T023 [P] [US2] Create user registration form component in `frontend/src/components/RegisterForm.tsx` explaining expected info, validating incomplete and invalid input, and showing non-sensitive error messages (FR-023, FR-030, FR-031, FR-032, FR-033, FR-038, FR-040)
- [X] T024 [P] [US2] Create user sign-in form component in `frontend/src/components/SignInForm.tsx` explaining expected info, validating incomplete and invalid input, and showing non-sensitive error messages (FR-026, FR-030, FR-031, FR-032, FR-033, FR-038, FR-040)
- [X] T025 [P] [US2] Create visible session status indicators and a clear sign-out control in `frontend/src/components/AuthStatus.tsx` that calls the sign-out flow endpoint, visibly returns the UI to a non-authenticated state, and preserves the active local cart on sign-out (FR-028, FR-029)
- [X] T026 [US2] Integrate authentication flows with Cart context in `frontend/src/App.tsx`, preserving local cart on registration/sign-in, and guiding buyers to register or sign-in when checkout requires identification (FR-034, FR-035, FR-036, FR-037)

**Checkpoint**: User Stories 1 and 2 work seamlessly together, and the local cart is preserved across authentication boundaries.

---

## Phase 5: User Story 3 - Simulated Checkout & Purchase Confirmation (Priority: P3)

**Goal**: Allow authenticated customers with items in their cart to proceed to a simulated checkout, presenting a summary, requesting minimum opaque details, displaying fictitious payment warnings, and completing the journey.

**Independent Test**: Verify empty cart blocks checkout. Verify checkout page presents cart summary and totals, accepts opaque details, returns fictitious confirmation with disclaimer, and leaves the system in a comprehensible state to start a new purchase.

### Tests for User Story 3

- [X] T027 [P] [US3] Create simulated checkout integration tests in `backend/tests/test_checkout.py` (FR-041, FR-044, FR-045, FR-046, FR-047, FR-049, FR-050, FR-054)
- [X] T028 [P] [US3] Create checkout form and confirmation components verification tests in `frontend/src/tests/Checkout.test.tsx` (FR-042, FR-043, FR-044, FR-045, FR-046, FR-047, FR-048, FR-049, FR-050, FR-051, FR-052, FR-053, FR-054)

### Implementation for User Story 3

- [X] T029 [US3] Implement backend checkout endpoint `POST /api/checkout` in `backend/src/main.py` requiring active authenticated session, validating request structure, authentication, non-empty cart, and generic demonstration data only. No real inventory validation is performed (FR-041, FR-044, FR-045, FR-046, FR-047, FR-048, FR-049, FR-050, FR-054)
- [X] T030 [P] [US3] Create checkout summary component in `frontend/src/components/CheckoutSummary.tsx` rendering products, quantities, prices, and totals before confirmation (FR-042, FR-043, FR-044)
- [X] T031 [P] [US3] Create checkout form component in `frontend/src/components/CheckoutForm.tsx` to collect minimum opaque demonstration information, without implementing an address book or saved addresses (FR-045, FR-046, FR-047)
- [X] T032 [P] [US3] Create purchase confirmation panel in `frontend/src/components/ConfirmationScreen.tsx` displaying unambiguous confirmation, simulated purchase summary, and a clear disclaimer that no real gateway is contacted (FR-048, FR-049, FR-050, FR-051, FR-052)
- [X] T033 [US3] Integrate simulated checkout flow in `frontend/src/pages/CheckoutPage.tsx` blocking empty carts, managing submission states, and leaving the system in a comprehensible state from which a new purchase can start (FR-041, FR-048, FR-049, FR-050, FR-051, FR-052, FR-053, FR-054)

**Checkpoint**: End-to-end simulated purchasing journey is fully functional and ready for integrated UI testing.

---

## Phase 6: User Story 4 - Overall System Behavior, Feedback, & Accessibility (Priority: P4)

**Goal**: Ensure the application behaves as one integrated, usable system on desktop and mobile screens, presenting loading/empty/error states, associated form labels/messages, visible action feedback, and complete keyboard completion.

**Independent Test**: Run the frontend across multiple viewport screen sizes. Test catalog adding/removals, registration, and sign-in. Verify that visible feedback triggers for each key action, empty and error states are clearly handled, control names are understandable, and keyboard navigation allows completing the full purchase journey.

### Tests for User Story 4

- [X] T034 [P] [US4] Create integrated journey tests in `frontend/src/tests/JourneyIntegration.test.tsx` verifying product catalog, shopping cart, authentication, and simulated checkout continuous integration flows (FR-055, FR-056, FR-057, FR-058, FR-059, FR-060)
- [X] T035 [P] [US4] Create frontend integration and accessibility verification tests in `frontend/src/tests/IntegrationUX.test.tsx` focused on feedback, layout states, labels, and usability (FR-061, FR-062, FR-063, FR-064, FR-065, FR-066, FR-067, FR-068, FR-069, FR-070, FR-071, FR-072, FR-073, FR-074, FR-075, FR-076, FR-077)

### Implementation for User Story 4

- [X] T036 [US4] Implement feedback notifications in `frontend/src/components/FeedbackToast.tsx` providing visible feedback for actions, and wire the toast trigger into adding and removing products, signing in, encountering invalid data, and completing simulated purchase across `frontend/src/components/Catalog.tsx`, `frontend/src/components/Cart.tsx`, `frontend/src/components/SignInForm.tsx`, and `frontend/src/components/ConfirmationScreen.tsx` (FR-061, FR-062, FR-063, FR-064, FR-065)
- [X] T037 [US4] Implement shared loading, empty, and error fallback UI states in `frontend/src/components/StateFallbacks.tsx` and wire the presentations into the catalog, cart, registration, sign-in, and checkout views across `frontend/src/components/Catalog.tsx`, `frontend/src/components/Cart.tsx`, `frontend/src/components/RegisterForm.tsx`, `frontend/src/components/SignInForm.tsx`, and `frontend/src/pages/CheckoutPage.tsx` (FR-066, FR-067, FR-068, FR-069, FR-070, FR-071, FR-072, FR-073)
- [X] T038 [P] [US4] Adjust responsive layouts and CSS styling in `frontend/src/index.css` to guarantee usable viewports on desktop and mobile screens (FR-073, FR-074)
- [X] T039 [P] [US4] Audit and adjust all interactive HTML elements in frontend forms and controls to ensure they use understandable primary control names and correctly associate labels and messages (FR-075, FR-076)
- [X] T040 [US4] Implement and verify semantic, focusable, and keyboard-operable controls and navigation across all views in `frontend/src/App.tsx` (FR-077)

**Checkpoint**: Core usability, accessibility, and feedback coverage verified and integrated across components.

---

## Phase 7: Polish & Quality Validation

**Purpose**: English-only validations, automated test coverage reporting, and manual validation matching `quickstart.md`.

- [X] T041 Conduct complete manual end-to-end validation journey matching `quickstart.md`, running frontend and backend components separately (FR-007, FR-055, FR-058, FR-059, FR-060, ATC-004, ATC-006, ATC-007)
- [X] T042 [P] Conduct English language verification audit on all specifications, source-code identifiers, comments, technical documentation, and user-facing interface text (ATC-009, ATC-010, ATC-011, ATC-012, ATC-013)
- [X] T043 Run backend pytest suite with test coverage enabled (`pytest --cov`) and expose the resulting metric for external evidence capture without inventing thresholds (ATC-002, ATC-007)
- [X] T044 Run frontend npm test suite with test coverage enabled (`npm test -- --coverage`) and expose the resulting metric for external evidence capture without inventing thresholds (ATC-001, ATC-007)

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 Setup completion. BLOCKS all subsequent phases.
- **User Stories (Phases 3 to 6)**: All depend on Phase 2 Foundational completion.
  - Can proceed sequentially in priority order: US1 → US2 → US3 → US4.
- **Polish (Phase 7)**: Depends on all user stories being completed.

### User Story Dependencies
- **User Story 1 (P1)**: Starts after Phase 2 is complete. Has no dependencies on other stories.
- **User Story 2 (P2)**: Starts after Phase 2 is complete. Operates on separate endpoints and views; integrates with US1 cart preservation but is independently testable.
- **User Story 3 (P3)**: Starts after Phase 2 is complete. Integrates with US1 cart context and US2 user session but is independently testable.
- **User Story 4 (P4)**: Depends on completion of US1, US2, and US3 to validate unified layout states, feedback, and keyboard traversals.

### Parallel Opportunities
- All Foundational tasks marked `[P]` can run in parallel (`T006`, `T007`, `T008`, `T009`).
- Once Foundational phase is complete, US1 and US2 implementation can be worked on in parallel:
  - Backend endpoints (`GET /api/products` vs `POST /api/register` & `POST /api/signin`) are separate; backend task modifications to `backend/src/main.py` (T012, T019, T020, T021) do not have parallel markers to prevent git merge conflicts on that file.
  - Frontend components (`Catalog.tsx` vs `RegisterForm.tsx` / `SignInForm.tsx`) are separate independent files and can safely be developed in parallel.
- All testing tasks marked `[P]` within each story can run in parallel.
- All final Polish and validation tasks marked `[P]` can run in parallel (`T038`, `T039`, `T042`).
- There are an exact safe count of **24** `[P]` task-line parallel markers in this list.

---

## Parallel Example: User Story 1

```bash
# Developer A implements frontend catalog list component:
Task: "Implement catalog display component in frontend/src/components/Catalog.tsx"

# Developer B implements local shopping cart state manager context:
Task: "Implement shopping cart React context state manager in frontend/src/context/CartContext.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories).
3. Complete Phase 3: User Story 1 (Product Browsing & Shopping Cart).
4. **STOP and VALIDATE**: Test User Story 1 independently in browser.

### Incremental Delivery
1. Setup + Foundational → Core structures ready.
2. Add User Story 1 → Test independently → Deliver (P1 MVP).
3. Add User Story 2 → Test independently → Deliver (Preserved Shopping cart + Identification).
4. Add User Story 3 → Test independently → Deliver (Simulated Checkout Confirmation).
5. Add User Story 4 → Test integrated usability, desktop/mobile responsive style views, feedback notifications, and keyboard completion.
6. Add Phase 7 Polish → Deliver (Final audits and metrics exposure).

---

## Traceability Index

| ID | Description | Mapped Task IDs | Notes |
|:---|:---|:---|:---|
| **FR-001** | Display product catalog at entry point | `T010`, `T012`, `T013` | Fully Covered |
| **FR-002** | Display product name | `T010`, `T013` | Fully Covered |
| **FR-003** | Display product representative image | `T010`, `T013` | Fully Covered |
| **FR-004** | Display product short description | `T010`, `T013` | Fully Covered |
| **FR-005** | Display product price | `T010`, `T013` | Fully Covered |
| **FR-006** | Display product general availability | `T010`, `T013` | Fully Covered |
| **FR-007** | Catalog consistency across app flow | `T004`, `T010`, `T012`, `T013`, `T041` | Fully Covered |
| **FR-008** | Catalog available without auth | `T010`, `T012`, `T013` | Fully Covered |
| **FR-009** | Optional expanded product view | *Not Activated* | Conditional requirement - not in scope |
| **FR-010** | Optional expanded view consistency | *Not Activated* | Conditional requirement - not in scope |
| **FR-011** | Shopping cart managed locally | `T011`, `T014`, `T016` | Fully Covered |
| **FR-012** | Durable cart persistence not mandatory | `T011`, `T014` | Fully Covered |
| **FR-013** | Cart lists products | `T011`, `T014`, `T015` | Fully Covered |
| **FR-014** | Cart lists quantities | `T011`, `T014`, `T015` | Fully Covered |
| **FR-015** | Cart lists prices | `T011`, `T014`, `T015` | Fully Covered |
| **FR-016** | Cart lists accumulated purchase total | `T011`, `T014`, `T015` | Fully Covered |
| **FR-017** | Adjust cart quantities | `T011`, `T014`, `T015` | Fully Covered |
| **FR-018** | Remove cart products | `T011`, `T014`, `T015` | Fully Covered |
| **FR-019** | Cart changes reflected immediately | `T011`, `T015`, `T016` | Fully Covered |
| **FR-020** | Cart changes remain available | `T011`, `T016` | Fully Covered |
| **FR-021** | Cart empty state recognition | `T011`, `T015`, `T016` | Fully Covered |
| **FR-022** | Simple registration mechanism | `T017`, `T019` | Fully Covered |
| **FR-023** | Registration minimum identifying data | `T017`, `T018`, `T019`, `T023` | Fully Covered |
| **FR-024** | Registration creates an account | `T006`, `T017`, `T019`, `T022` | Fully Covered |
| **FR-025** | Simple sign-in mechanism | `T017`, `T020`, `T022` | Fully Covered |
| **FR-026** | Sign-in minimum identifying data | `T017`, `T018`, `T020`, `T024` | Fully Covered |
| **FR-027** | Successful sign-in session activation | `T017`, `T020`, `T022` | Fully Covered |
| **FR-028** | Active session indicated visibly | `T018`, `T022`, `T025` | Fully Covered |
| **FR-029** | Session clear sign-out control | `T018`, `T021`, `T022`, `T025` | Fully Covered |
| **FR-030** | Forms explain expected info | `T018`, `T023`, `T024` | Fully Covered |
| **FR-031** | Forms validate incomplete input | `T018`, `T023`, `T024` | Fully Covered |
| **FR-032** | Forms validate invalid input | `T018`, `T023`, `T024` | Fully Covered |
| **FR-033** | Forms communicate errors safely | `T017`, `T018`, `T020`, `T023`, `T024` | Fully Covered |
| **FR-034** | Registration preserves active cart | `T018`, `T026` | Fully Covered |
| **FR-035** | Sign-in preserves active cart | `T018`, `T026` | Fully Covered |
| **FR-036** | Guide buyer to register/sign-in | `T026` | Fully Covered |
| **FR-037** | Preserve cart during identification | `T026` | Fully Covered |
| **FR-038** | Passwords not displayed in UI | `T018`, `T023`, `T024` | Fully Covered |
| **FR-039** | Passwords not stored in plain text | `T007`, `T017`, `T019`, `T020` | Fully Covered |
| **FR-040** | Authentication data secure within academic scope | `T006`, `T007`, `T017`, `T019`, `T020`, `T023`, `T024` | Fully Covered |
| **FR-041** | Simulated checkout proceed | `T027`, `T029`, `T033` | Fully Covered |
| **FR-042** | Checkout pre-confirmation summary products | `T028`, `T030` | Fully Covered |
| **FR-043** | Checkout pre-confirmation summary quantities | `T028`, `T030` | Fully Covered |
| **FR-044** | Checkout pre-confirmation summary totals | `T027`, `T028`, `T029`, `T030` | Fully Covered |
| **FR-045** | Request minimum checkout demo info | `T027`, `T028`, `T029`, `T031` | Fully Covered |
| **FR-046** | Do NOT implement address book | `T027`, `T028`, `T029`, `T031` | Fully Covered |
| **FR-047** | Do NOT implement selection of saved addresses | `T027`, `T028`, `T029`, `T031` | Fully Covered |
| **FR-048** | Fictitious payment confirmation | `T028`, `T029`, `T032`, `T033` | Fully Covered |
| **FR-049** | Explicit disclaimer no charge made | `T027`, `T028`, `T029`, `T032`, `T033` | Fully Covered |
| **FR-050** | Explicit disclaimer no payment gateway contacted | `T027`, `T028`, `T029`, `T032`, `T033` | Fully Covered |
| **FR-051** | Unambiguous checkout confirmation | `T028`, `T032`, `T033` | Fully Covered |
| **FR-052** | Simulated purchase summary | `T028`, `T032`, `T033` | Fully Covered |
| **FR-053** | Comprehensible post-checkout state | `T028`, `T033` | Fully Covered |
| **FR-054** | Empty cart blocks checkout | `T027`, `T028`, `T029`, `T033` | Fully Covered |
| **FR-055** | Application acts as integrated system | `T034`, `T035`, `T041` | Fully Covered |
| **FR-056** | Catalog actions reflected in cart | `T016`, `T034`, `T035` | Fully Covered |
| **FR-057** | Catalog actions lead to checkout confirmation | `T034`, `T035` | Fully Covered |
| **FR-058** | Product info consistent across views | `T034`, `T035`, `T041` | Fully Covered |
| **FR-059** | Quantities consistent across views | `T034`, `T035`, `T041` | Fully Covered |
| **FR-060** | Totals consistent across views | `T034`, `T035`, `T041` | Fully Covered |
| **FR-061** | Visible feedback for adding product | `T035`, `T036` | Fully Covered |
| **FR-062** | Visible feedback for removing product | `T035`, `T036` | Fully Covered |
| **FR-063** | Visible feedback for signing in | `T035`, `T036` | Fully Covered |
| **FR-064** | Visible feedback for encountering invalid data | `T018`, `T035`, `T036` | Fully Covered |
| **FR-065** | Visible feedback for simulated purchase confirmation | `T035`, `T036` | Fully Covered |
| **FR-066** | Loading state handled sufficiently | `T035`, `T037` | Fully Covered |
| **FR-067** | Loading state instructions | `T035`, `T037` | Fully Covered |
| **FR-068** | Empty state handled sufficiently | `T035`, `T037` | Fully Covered |
| **FR-069** | Empty state instructions | `T035`, `T037` | Fully Covered |
| **FR-070** | Error state handled sufficiently | `T035`, `T037` | Fully Covered |
| **FR-071** | Error state instructions | `T035`, `T037` | Fully Covered |
| **FR-072** | Error messages useful & non-sensitive | `T035`, `T037` | Fully Covered |
| **FR-073** | Clear/consistent UI | `T035`, `T037`, `T038` | Fully Covered |
| **FR-074** | Usable on desktop/mobile viewports | `T035`, `T038` | Fully Covered |
| **FR-075** | Primary controls have understandable names | `T035`, `T039` | Fully Covered |
| **FR-076** | Associated labels/messages | `T035`, `T039` | Fully Covered |
| **FR-077** | Keyboard completion of main journey | `T035`, `T040` | Fully Covered |
| **ATC-001** | React & TypeScript frontend | `T002`, `T044` | Fully Covered |
| **ATC-002** | Python & FastAPI backend | `T003`, `T043` | Fully Covered |
| **ATC-003** | Interface separates presentation from logic | `T001`, `T005`, `T008` | Fully Covered |
| **ATC-004** | Frontend/backend clear communication interface | `T005`, `T008`, `T041` | Fully Covered |
| **ATC-005** | Separation of concerns (no mixing) | `T002`, `T003`, `T005`, `T008` | Fully Covered |
| **ATC-006** | Frontend runs separately | `T001`, `T041` | Fully Covered |
| **ATC-007** | Frontend & Backend reviewed separately | `T001`, `T009`, `T041`, `T043`, `T044` | Fully Covered |
| **ATC-008** | Simple storage appropriate for demo | `T004`, `T006`, `T012` | Fully Covered |
| **ATC-009** | English specification artifacts | `T042` | Fully Covered |
| **ATC-010** | English source-code identifiers | `T042` | Fully Covered |
| **ATC-011** | English code comments | `T042` | Fully Covered |
| **ATC-012** | English technical documentation | `T042` | Fully Covered |
| **ATC-013** | English user-facing interface text | `T042` | Fully Covered |
| **SC-001** | Navigatable continuous integrated journey | `T034`, `T035`, `T041` | Fully Covered |
| **SC-002** | Product information consistency | `T034`, `T035`, `T041` | Fully Covered |
| **SC-003** | Quantities and totals consistency | `T034`, `T035`, `T041` | Fully Covered |
| **SC-004** | Authentication preserves active cart | `T018`, `T026` | Fully Covered |
| **SC-005** | Post-checkout comprehensible starting state | `T028`, `T033`, `T041` | Fully Covered |

---

## Implementation Approval Status

**CRITICAL CHECKPOINT**: This task list represents the native implementation planning checkpoint. **Actual coding, directory scaffolding, dependency installations, and implementation tasks execution must NOT begin until separate, explicit human approval is granted.**
