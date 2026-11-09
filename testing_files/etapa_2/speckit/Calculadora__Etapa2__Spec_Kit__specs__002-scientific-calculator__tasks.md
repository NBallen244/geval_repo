# Tasks: Scientific Web Calculator & Extended State Management

**Input**: Design documents from `/specs/002-scientific-calculator/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included as requested and recommended by the Test-Driven Validation Principle of the project Constitution.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Paths below utilize explicit, relative directory paths starting from the repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Configure updated TypeScript and FastAPI development environments in `frontend/` and `backend/`
- [X] T002 Configure linter rules and prettier setups in `frontend/.eslintrc.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Extend backend API schemas in `backend/src/api/v1/schemas.py` to support `CalculationRequest` with `angle_unit`
- [X] T004 Define TypeScript interfaces for request and response structures in `frontend/src/types/index.ts`
- [X] T005 [P] Register custom exception handler or update error responses in `backend/src/api/v1/errors.py` to support standard `ErrorResponse` format

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Advanced Mathematical Evaluation with Angle Toggle (Priority: P1) 🎯 MVP

**Goal**: Expand the backend evaluator to parse and compute scientific operations (trig, powers, roots, logs, constants) with precision and support Degrees vs. Radians toggle.

**Independent Test**: Run `pytest tests/unit/test_evaluator.py` and `pytest tests/contract/test_evaluate.py` to verify scientific calculations and angle toggles return correct precision results and descriptive errors.

### Tests for User Story 1 (TDD - Write first and ensure they fail)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T006 [P] [US1] Write unit tests in `backend/tests/unit/test_evaluator.py` verifying precision and correctness for scientific operations
- [X] T007 [P] [US1] Write contract integration tests in `backend/tests/contract/test_evaluate.py` targeting `POST /api/v1/evaluate` with the `angle_unit` field

### Implementation for User Story 1

- [X] T008 [US1] Refactor AST parser/evaluator in `backend/src/core/evaluator.py` to replace caret with power operator
- [X] T009 [US1] Extend evaluator node traversal in `backend/src/core/evaluator.py` to support whitelisted constants
- [X] T010 [US1] Implement function call traversal for whitelisted mathematical functions in `backend/src/core/evaluator.py`
- [X] T011 [US1] Add angle-unit unit conversion logic for trigonometric functions inside function call evaluation in `backend/src/core/evaluator.py`
- [X] T012 [US1] Add strict mathematical domain checks inside evaluation traversal in `backend/src/core/evaluator.py`
- [X] T013 [US1] Update router POST handler in `backend/src/api/v1/router.py` to pass the payload's `angle_unit` parameter
- [X] T014 [US1] Update API service in `frontend/src/services/api.ts` to include `angle_unit` parameter in payload calls
- [X] T015 [US1] Implement responsive layout expansion with scientific button grid layout in `frontend/src/components/Calculator.tsx`
- [X] T016 [US1] Add angle toggle state button to UI layout in `frontend/src/components/Calculator.tsx`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Memory Register System (Priority: P2)

**Goal**: Implement client-side memory controls (`M+`, `M-`, `MR`, `MC`) and display an active "M" badge when the memory is non-zero.

**Independent Test**: Perform addition/subtraction to memory in UI, recall the value to the input expression, and clear memory to ensure the visual memory badge disappears.

### Tests for User Story 2

- [X] T017 [P] [US2] Create memory-specific component unit tests in `frontend/src/tests/Calculator.test.tsx` verifying memory buttons

### Implementation for User Story 2

- [X] T018 [US2] Add `memory_register` state variable to Calculator component in `frontend/src/components/Calculator.tsx`
- [X] T019 [US2] Implement memory button actions in `frontend/src/components/Calculator.tsx`
- [X] T020 [US2] Render visual memory badge above the display in `frontend/src/components/Calculator.tsx`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interactive Session Calculation History (Priority: P3)

**Goal**: Build a side-drawer or collapsible section displaying calculation logs of the current session, enabling reloading formulas/results or clearing logs.

**Independent Test**: Add several calculations, confirm they populate the history panel, click them to restore formula/result, and clear list via "Clear History" button.

### Tests for User Story 3

- [X] T021 [P] [US3] Create history-specific component unit tests in `frontend/src/tests/Calculator.test.tsx` verifying history operations

### Implementation for User Story 3

- [X] T022 [US3] Declare in-memory history log state array of `HistoryItem` type in `frontend/src/components/Calculator.tsx`
- [X] T023 [US3] Build a side-drawer panel or collapsible section in `frontend/src/components/Calculator.tsx`
- [X] T024 [US3] Integrate log insertion trigger in `frontend/src/components/Calculator.tsx`
- [X] T025 [US3] Add interactive onClick events on history log elements in `frontend/src/components/Calculator.tsx`
- [X] T026 [US3] Add "Clear History" button to drawer in `frontend/src/components/Calculator.tsx`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T027 [P] Enhance screen reader accessibility bindings across updated elements in `frontend/src/components/Calculator.tsx`
- [X] T028 Add keyboard shortcut key handlers in `frontend/src/components/Calculator.tsx` for scientific operations
- [X] T029 Run `quickstart.md` validation checklist end-to-end to verify manual and automated testing scenarios
- [X] T030 [P] Run frontend build and lint commands and python code checks in `frontend/` and `backend/`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Write unit tests in backend/tests/unit/test_evaluator.py verifying precision and correctness for scientific operations"
Task: "Write contract integration tests in backend/tests/contract/test_evaluate.py targeting POST /api/v1/evaluate with the angle_unit field"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
