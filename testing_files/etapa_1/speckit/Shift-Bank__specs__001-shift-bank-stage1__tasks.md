---

description: "Task list template for feature implementation"
---

# Tasks: Shift Bank Stage 1

**Input**: Design documents from `/specs/001-shift-bank-stage1/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/api.md

**Tests**: The tasks below include comprehensive unit and integration test tasks for both backend and frontend, as planned in the testing strategy.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Multi-project**: `backend/` and `frontend/` at repository root
- **Backend paths**: `backend/src/`, `backend/tests/`
- **Frontend paths**: `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directories `backend/src/`, `backend/tests/`, `frontend/src/`, and `frontend/tests/` to establish multi-project baseline structure
- [X] T002 Initialize backend Python 3.13 project with required dependencies in `backend/requirements.txt` (`fastapi`, `uvicorn`, `pytest`, `httpx`)
- [X] T003 [P] Initialize frontend React 18+ and TypeScript project configuration and web dependencies in `frontend/package.json` (`react`, `react-dom`, `vite`, `typescript`, `vitest`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup SQLite database schemas for `accounts` and `transfers` tables and write initialization seed data in `backend/src/database.py` (pre-seeding accounts Checking with balance exactly COP 5,000,000.00 and Savings with balance exactly COP 15,000,000.00; insert pre-seeded historical transfers representing past movements of COP 500,000.00 and COP 100,000.00 strictly as historical logs in the `transfers` table, ensuring they do NOT modify or trigger any mathematical adjustments to the initial account balances during seeding)
- [X] T005 [P] Configure development CORS middleware to allow requests from the frontend origin `http://localhost:5173` in `backend/src/main.py`
- [X] T006 Configure backend FastAPI application routing, base app startup, and Pydantic schemas utilizing exact string-decimal conversion in `backend/src/main.py` and `backend/src/models.py`
- [X] T007 [P] Create React application styling using strict Vanilla CSS layout and component constraints in `frontend/src/App.css` (no Tailwind or other external CSS frameworks)
- [X] T008 [P] Define TypeScript interfaces for accounts, transfers, API responses, and histories matching the backend Pydantic models in `frontend/src/types.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Account Overview & Balances (Priority: P1) 🎯 MVP

**Goal**: View Checking (COP 5,000,000) and Savings (COP 15,000,000) balances on a unified dashboard strictly using friendly names without showing database IDs or account numbers.

**Independent Test**: Load the mock dashboard session and verify that the Checking card displays a balance of COP 5,000,000 and the Savings card displays a balance of COP 15,000,000 with no internal IDs or keys visible.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Create unit tests for `GET /api/accounts` verifying response has exactly 2 accounts, friendly names, and exact string balances in `backend/tests/test_api.py`
- [X] T010 [P] [US1] Create frontend tests verifying render of the Checking and Savings cards with correct formatted balances and friendly names in `frontend/src/App.test.tsx`

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `GET /api/accounts` endpoint retrieving data from the `accounts` SQLite table and outputting exact decimal strings in `backend/src/api.py`
- [X] T012 [P] [US1] Implement accounts fetch API client function using standard browser fetch in `frontend/src/services.ts`
- [X] T013 [US1] Build Dashboard account overview layout in `frontend/src/App.tsx` displaying accounts strictly by friendly names "Checking" and "Savings", formatting balances properly, and completely hiding database IDs

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Transfer Between Own Accounts (Priority: P1)

**Goal**: Transfer money strictly between Checking and Savings accounts with immediate execution for transfers under COP 1,000,000.

**Independent Test**: Select Checking as source and Savings as destination, enter a transfer amount of COP 500,000, submit, and verify that Checking balance updates to COP 4,500,000 and Savings updates to COP 15,500,000 instantly without triggering MFA. Same-account transfers, negative amounts, and overdrafts are rejected with descriptive messages.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T014 [P] [US2] Create unit and integration tests for standard transfers, validating balance deduction/addition, overdraft rejection, non-positive amount rejection, and same-account rejection in `backend/tests/test_api.py`
- [X] T015 [P] [US2] Create frontend unit tests for validating input values, showing error messages, and submitting standard transfers in `frontend/src/App.test.tsx`

### Implementation for User Story 2

- [X] T016 [P] [US2] Create transfer initiation request validation Pydantic model with decimal string parsing in `backend/src/models.py`
- [X] T017 [US2] Implement `POST /api/transfers` endpoint executing Python `decimal.Decimal` math inside an atomic SQLite transaction block (using read, validate sufficiency, update, and commit with rollback on exceptions) for amounts under COP 1,000,000 in `backend/src/api.py`
- [X] T018 [P] [US2] Implement transfer initiation API client function in `frontend/src/services.ts`
- [X] T019 [US2] Build the Transfer Form component in `frontend/src/App.tsx` allowing users to select source, destination, enter amounts, showing errors (e.g., overdraft, same-account), and updating balances upon successful submission

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Transaction History & Pre-seeded Movements (Priority: P2)

**Goal**: Review past transfers for Checking and Savings accounts showing chronological movements, accurate incoming/outgoing direction, amount, date, and description, without displaying any "resulting balance".

**Independent Test**: Load the transaction history section for each account, verify that exactly two pre-seeded historical transfers display (Savings to Checking for COP 500,000; Checking to Savings for COP 100,000) with correct directions, and that any newly completed transfer immediately adds a history row without any resulting balance column.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US3] Create backend integration tests for `GET /api/accounts/{account_id}/history` endpoint verifying correct chronological sorting, pre-seeded elements, and accurate directions in `backend/tests/test_api.py`
- [X] T021 [P] [US3] Create frontend tests verifying the list layout, column values (date, direction, amount, description), and the absolute absence of a resulting balance column in `frontend/src/App.test.tsx`

### Implementation for User Story 3

- [X] T022 [US3] Implement `GET /api/accounts/{account_id}/history` in `backend/src/api.py` that queries completed transfers from SQLite where source or destination match `{account_id}` and formats incoming/outgoing directions accurately
- [X] T023 [P] [US3] Implement account history fetch API client function in `frontend/src/services.ts`
- [X] T024 [US3] Build the Transaction History UI list component in `frontend/src/App.tsx` displaying the transaction date, amount, description, and direction, ensuring no resulting balance column is rendered

**Checkpoint**: At this point, User Stories 1, 2, and 3 should all work together

---

## Phase 6: User Story 4 - Mock Multi-Factor Authentication (MFA) & State Machine (Priority: P2)

**Goal**: Implement step-up MFA verification for sensitive transfers (amount >= COP 1,000,000) with state machine tracking transaction states: `PENDING_MFA`, `COMPLETED`, `FAILED`, and `EXPIRED`.

**Independent Test**: Initiate a sensitive transfer (e.g. COP 1,500,000). Verify that:
1. It is saved in the database in `PENDING_MFA` status with a 5-minute `expires_at` timestamp, and balances remain unchanged.
2. Closing the modal leaves it `PENDING_MFA` allowing later completion.
3. Submitting incorrect codes allows infinite retries without state changes.
4. Submitting code `123456` after 5 minutes triggers an on-demand `EXPIRED` status write in SQLite and rejects the transfer.
5. Submitting code `123456` within 5 minutes executes an atomic transaction, re-validating the source balance, and updating the state to `COMPLETED` (or `FAILED` if balance became insufficient).

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US4] Create comprehensive backend unit tests for the sensitive transfers lifecycle: POST creating `PENDING_MFA` and `expires_at`, invalid code retries, on-demand expiration detection (mocking clock > 5 minutes), insufficient funds re-validation at confirmation, and successful confirmation with code `123456` in `backend/tests/test_api.py`
- [X] T026 [P] [US4] Create frontend tests verifying step-up modal visibility, invalid code input handling, closing/cancelling modal behavior, and success confirmation routing in `frontend/src/App.test.tsx`

### Implementation for User Story 4

- [X] T027 [US4] Update `POST /api/transfers` in `backend/src/api.py` to intercept transfers >= COP 1,000,000, write a `PENDING_MFA` record to SQLite with an `expires_at` timestamp (creation + 5 mins), and return `202 Accepted` without changing balances
- [X] T028 [US4] Implement `POST /api/transfers/{transfer_id}/mfa` endpoint in `backend/src/api.py` performing on-demand expiration check, code validation (`123456`), and source balance re-validation inside an explicit SQLite transaction block with Python `decimal.Decimal` calculations
- [X] T029 [P] [US4] Implement MFA confirmation API client function in `frontend/src/services.ts`
- [X] T030 [US4] Build the step-up MFA Overlay modal in `frontend/src/App.tsx` displaying the input field for the 6-digit verification code, validating inputs, showing incorrect code errors, and refreshing balances upon successful verification
- [X] T031 [US4] Implement the close/cancel modal logic and a "Pending Sensitive Transfers" resume widget in `frontend/src/App.tsx` enabling users to close the modal without deleting the transfer and resume it later during its active 5-minute window

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Run Python linting and formatting commands on backend files to ensure codebase standards
- [X] T033 [P] Verify that all frontend user-facing interface views strictly hide system UUIDs, primary keys, and internal account IDs per specification requirements
- [X] T034 Execute Pytest backend test suite to verify that all implemented backend tests pass successfully
- [X] T035 Execute Vitest frontend test suite to verify that all implemented frontend tests pass successfully
- [X] T036 Perform manual end-to-end walkthroughs of all verification scenarios in specs/001-shift-bank-stage1/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phases 3 to 6)**: All depend on Foundational phase completion.
  - User stories can then proceed in parallel (if staffed) or sequentially in priority order.
- **Polish (Phase 7)**: Depends on all user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 for balance updates but can be developed independently using the API contracts.
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Relies on completed transfers, but pre-seeded database data in T004 allows testing it independently from US2's transfer form.
- **User Story 4 (P2)**: Depends on standard transfer initiation logic from US2 (T017) to intercept sensitive amounts, but its MFA state machine and database validation flow run independently.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models and schemas before endpoint handlers.
- Endpoint handlers before frontend client integrations.
- UI views and state connection as the final step.

### Parallel Opportunities

- All Setup tasks marked `[P]` can run in parallel.
- All Foundational tasks marked `[P]` can run in parallel.
- Once Foundational phase is complete, US1, US2, US3, and US4 backend and frontend tasks marked `[P]` can be started in parallel.
- Test suites (backend vs frontend) can be developed and run in parallel.

---

## Parallel Example: User Story 1

```bash
# Launch backend accounts API tests:
Task: "T009 [P] [US1] Create unit tests for GET /api/accounts endpoint in backend/tests/test_api.py"

# Launch frontend accounts component tests:
Task: "T010 [P] [US1] Create frontend tests verifying render of the Checking and Savings cards in frontend/src/App.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories).
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: Verify User Story 1 independently in the browser and with tests.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!).
3. Add User Story 2 → Test independently → Deploy/Demo.
4. Add User Story 3 → Test independently → Deploy/Demo.
5. Add User Story 4 → Test independently → Deploy/Demo.
6. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
   - Developer A: User Story 1 (Account Overview)
   - Developer B: User Story 2 (Standard Transfer)
   - Developer C: User Story 3 (Transaction History)
   - Developer D: User Story 4 (Mock MFA and State Machine)
3. Stories complete and integrate independently.

---

## Notes

- `[P]` tasks = different files, no dependencies.
- `[Story]` label maps task to specific user story for traceability.
- Each user story is independently completable and testable.
- Verify tests fail before implementing.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.
