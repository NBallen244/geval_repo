# Tasks: Web Calculator Application

**Input**: Design documents from `/specs/001-init-calculator-app/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/openapi.json, quickstart.md

**Tests**: Tests are requested and required per constitution (Test-Driven Validation). They are written first.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/src/`, `frontend/src/`
- Explicit workspace paths apply per planning design.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project folders for backend/ and frontend/ per project structure plan
- [X] T002 Initialize Python 3.11+ virtual environment in backend/ and configure pyproject.toml or requirements.txt
- [X] T003 Initialize React TypeScript project in frontend/ using Vite
- [X] T004 [P] Configure global gitignore and linting tools in backend/ and frontend/ (e.g., ruff, eslint, prettier)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Setup FastAPI boilerplate routing and main application entrypoint in backend/src/main.py
- [X] T006 Setup base layout and Vite build configuration in frontend/vite.config.ts and frontend/index.html
- [X] T007 [P] Implement CORS and security headers middleware in backend/src/main.py
- [X] T008 [P] Configure global environment configuration handlers in backend/src/core/config.py
- [X] T009 Configure global error response handlers and custom exceptions in backend/src/api/v1/errors.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Exact Decimal PEMDAS Calculation (Priority: P1) 🎯 MVP

**Goal**: Implement backend mathematical expression evaluation engine and FastAPI endpoint with absolute decimal accuracy.

**Independent Test**: Execute `pytest backend/tests/unit/test_evaluator.py` and verify standard JSON payloads and error returns.

### Tests for User Story 1

- [X] T010 [P] [US1] Create FastAPI contract test for POST /api/v1/evaluate in backend/tests/contract/test_evaluate.py
- [X] T011 [P] [US1] Create unit tests covering PEMDAS precedence, decimals, division-by-zero, and syntax errors in backend/tests/unit/test_evaluator.py

### Implementation for User Story 1

- [X] T012 [P] [US1] Define request and response schemas matching data-model.md in backend/src/api/v1/schemas.py
- [X] T013 [P] [US1] Implement AST-based high-precision mathematical evaluation engine using Python decimal in backend/src/core/evaluator.py
- [X] T014 [US1] Create FastAPI POST endpoint `/api/v1/evaluate` invoking AST engine in backend/src/api/v1/router.py
- [X] T015 [US1] Register api v1 router within backend/src/main.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Accessibility-First Calculator Interface (Priority: P2)

**Goal**: Deliver a desktop-like responsive React interface with keyboard bindings and screen reader features.

**Independent Test**: Run `npm run test` on the frontend and manually verify layout and key bindings in browser.

### Tests for User Story 2

- [X] T016 [P] [US2] Create React event test validating mouse clicks and keyboard mappings in frontend/src/tests/Calculator.test.tsx
- [X] T017 [P] [US2] Create testing suite validating ARIA attributes and focus behaviors in frontend/src/tests/Accessibility.test.tsx

### Implementation for User Story 2

- [X] T018 [P] [US2] Define strict TypeScript request/response types matching backend contract in frontend/src/types/calculator.ts
- [X] T019 [P] [US2] Implement API service client to invoke FastAPI endpoint in frontend/src/services/api.ts
- [X] T020 [US2] Create responsive Display component showing formula and results in frontend/src/components/Display.tsx
- [X] T021 [US2] Create ButtonGrid component with full click event hooks and screen reader labels in frontend/src/components/ButtonGrid.tsx
- [X] T022 [US2] Implement main Calculator shell with global React keydown listeners in frontend/src/components/Calculator.tsx
- [X] T023 [US2] Integrate components within frontend/src/App.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Responsive Desktop and Mobile Layout (Priority: P3)

**Goal**: Adjust CSS grids and viewports to prevent horizontal overflow or overlapping targets.

**Independent Test**: Use browser responsive viewer (widths down to 320px) to verify correct scaling.

### Implementation for User Story 3

- [X] T024 [P] [US3] Implement mobile-first CSS styles and flex alignments in frontend/src/App.css
- [X] T025 [P] [US3] Configure high-contrast color scheme, outlines, and standard typography in frontend/src/index.css

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T026 Documentation updates in docs/ and project README.md
- [X] T027 Code cleanup, linting, and minor visual optimizations
- [X] T028 Run e2e verification scenarios detailed in specs/001-init-calculator-app/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 via API service
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Pure styles

### Within Each User Story
- Tests MUST be written first and fail before implementation
- Models/types before services
- Services before UI views/endpoints
- Core implementation before integration

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 backend work and US2 components setup can proceed in parallel
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Execute independent unit and contract tests:
Task: "FastAPI contract test for POST /api/v1/evaluate in backend/tests/contract/test_evaluate.py"
Task: "Unit tests covering PEMDAS precedence, decimals, division-by-zero, and syntax errors in backend/tests/unit/test_evaluator.py"

# Write schema definitions and core mathematical logic in parallel:
Task: "Define request and response schemas matching data-model.md in backend/src/api/v1/schemas.py"
Task: "Implement AST-based high-precision mathematical evaluation engine using Python decimal in backend/src/core/evaluator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently with unit/contract tests and manual cURL calls
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories
