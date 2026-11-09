# Tasks: Reverse Polish Notation (RPN) Engine and UI Migration

**Input**: Design documents from `/specs/004-rpn-calculator-refactor/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Pytest backend tests and React component tests are included below to satisfy the strict $\ge 80\%$ statement and branch coverage requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Initialize feature branches and verify documentation paths in `specs/004-rpn-calculator-refactor/`
- [x] T002 [P] Configure backend dependencies for Decimal evaluation and custom exceptions in `backend/requirements.txt`
- [x] T003 [P] Configure frontend npm script bindings and dependencies for Vitest/Jest in `frontend/package.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core API schemas and error structures that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Define RPN-specific exception codes (such as `STACK_UNDERFLOW`) in `backend/src/api/v1/errors.py`
- [x] T005 [P] Define `CalculationRequest` and `CalculationResponse` schemas with `mode` and `stack` properties in `backend/src/api/v1/schemas.py`
- [x] T006 Update the primary `/evaluate` router handler to parse requested mode and branch execution path in `backend/src/api/v1/router.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - RPN Mode Stack Operations (Priority: P1) 🎯 MVP

**Goal**: Direct space-separated postfix evaluation on a backend-managed LIFO Decimal stack engine.

**Independent Test**: Verify by sending REST API calls or running backend unit tests with space-separated RPN strings (e.g. `12.5 3 *`) and confirming exact results and remaining stack levels.

### Tests for User Story 1

- [x] T007 [P] [US1] Create unit tests for stack-based postfix execution, scientific operations, and underflow error scenarios in `backend/tests/unit/test_rpn_evaluator.py`
- [x] T008 [P] [US1] Write API integration tests for `/evaluate` endpoint in RPN mode in `backend/tests/unit/test_router.py`

### Implementation for User Story 1

- [x] T009 [US1] Implement core `RPNEvaluator` stack execution engine using high-precision Decimal logic in `backend/src/core/evaluator.py`
- [x] T010 [US1] Support all memory register functions (`M+`, `M-`, `MR`, `MC`) and scientific functions within RPN stack evaluation in `backend/src/core/evaluator.py`
- [x] T011 [US1] Wire API router to call RPN evaluation path when `mode="rpn"`, returning both the top-of-stack result and the list of remaining stack levels in `backend/src/api/v1/router.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Standard Mode Infix-to-RPN Conversion (Priority: P1)

**Goal**: Parse infix mathematical formulas with parentheses and scientific functions, convert them to postfix (RPN) tokens, and evaluate on the stack engine.

**Independent Test**: Run Standard Mode infix calculations (e.g. `12.5 + 3 * (4 - 1.5) / 2`) and confirm exact results using the combined Shunting Yard + Stack engine.

### Tests for User Story 2

- [x] T012 [P] [US2] Create unit tests for the Shunting Yard Algorithm tokenizer and converter (handling parentheses, scientific functions, and custom binary functions like `root(x, y)`) in `backend/tests/unit/test_shunting_yard.py`
- [x] T013 [P] [US2] Write infix math regression tests to guarantee strict PEMDAS precedence compliance in `backend/tests/unit/test_evaluator.py`

### Implementation for User Story 2

- [x] T014 [US2] Implement Shunting Yard tokenizer and converter logic in `backend/src/core/evaluator.py`
- [x] T015 [US2] Refactor `evaluate_expression` entry point to route Standard Mode formulas through Shunting Yard conversion and evaluate the resulting tokens on the stack engine in `backend/src/core/evaluator.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently on the backend

---

## Phase 5: User Story 3 - Real-Time Stack Visualizer UI (Priority: P2)

**Goal**: Standard/RPN dual modes and real-time visual stack display in the React frontend.

**Independent Test**: Switch to RPN Mode on the UI, push numeric values via the ENTER key, and confirm that levels X, Y, Z, T update correctly on the screen in real-time (<100ms).

### Tests for User Story 3

- [x] T016 [P] [US3] Write frontend component tests to verify Standard/RPN dual-mode toggle, Enter key stack push, and real-time stack shifts in `frontend/src/tests/Calculator.test.tsx`

### Implementation for User Story 3

- [x] T017 [P] [US3] Define client-side TypeScript types for mode selections and backend-synchronized stack levels in `frontend/src/types/calculator.ts`
- [x] T018 [P] [US3] Implement `StackVisualizer` UI component showing stack levels X, Y, Z, T with proper focus outlines and ARIA labels in `frontend/src/components/StackVisualizer.tsx`
- [x] T019 [US3] Refactor main `Calculator` React component to manage active modes, RPN keystroke listeners (Enter key pushing to stack), and stack level synchronization in `frontend/src/components/Calculator.tsx`
- [x] T020 [US3] Update button grids and layouts to support the RPN `ENTER` button and standard operators in standard/RPN modes in `frontend/src/components/ButtonGrid.tsx`

**Checkpoint**: All user stories should now be independently functional across the entire full-stack application

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T021 [P] Update user documentation, setup instructions, and feature lists in `README.md`
- [x] T022 Clean up code formatting, imports, and run linter validation checks across all frontend and backend source files
- [x] T023 Run comprehensive end-to-end validation as specified in `specs/004-rpn-calculator-refactor/quickstart.md`
- [x] T024 Verify that Docker builds succeed cleanly for both backend and frontend images using `docker-compose.yml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
  - User stories can proceed in parallel once foundational tasks are complete.
  - Recommended order is priority order (US1 → US2 → US3).
- **Polish (Phase 6)**: Depends on all user stories being completed.

### Within Each User Story
- Test files MUST be created and verified as failing before starting implementation.
- Core math evaluation/state logic is built before routing API endpoints.
- Backend APIs are finalized before client UI integrations are wired.

### Parallel Opportunities
- All Setup tasks marked `[P]` can run in parallel.
- All Foundational tasks marked `[P]` can run in parallel.
- Once Foundational phase is complete, US1, US2, and US3 implementation can proceed in parallel (e.g. backend engineers working on US1/US2 math, frontend engineers preparing US3 UI components).
- Independent tests marked `[P]` within stories can be authored simultaneously.

---

## Parallel Example: User Story 1 & 2 Backend
```bash
# Launch writing of tests for US1 and US2 in parallel:
Task: "Create unit tests for stack-based postfix execution... backend/tests/unit/test_rpn_evaluator.py"
Task: "Create unit tests for the Shunting Yard Algorithm... backend/tests/unit/test_shunting_yard.py"

# Implement core features after test verification:
Task: "Implement core RPNEvaluator stack execution engine... backend/src/core/evaluator.py"
Task: "Implement Shunting Yard tokenizer and converter logic... backend/src/core/evaluator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete **Phase 1: Setup** and **Phase 2: Foundational** (blocking tasks).
2. Complete **Phase 3: User Story 1** (Backend direct RPN mode).
3. **STOP and VALIDATE**: Run `pytest backend/tests/unit/test_rpn_evaluator.py` to verify the direct RPN engine.

### Incremental Delivery
1. Start with core stack-based engine (US1 backend).
2. Layer on infix-to-postfix translation (US2 backend Shunting Yard).
3. Layer on frontend dual-mode switch and stack visualizer UI (US3 frontend).
4. Complete polish tasks, container check, and documentation updates.
