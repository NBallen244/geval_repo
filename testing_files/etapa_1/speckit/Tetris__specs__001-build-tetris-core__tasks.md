---
description: "Task list for build-tetris-core feature implementation"
---

# Tasks: build-tetris-core

**Input**: Design documents from `/specs/001-build-tetris-core/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are requested and will be written first (TDD approach) as part of the core deliverables.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/app/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create backend directory structure with files `backend/app/__init__.py`, `backend/app/main.py`, `backend/app/api/__init__.py`, `backend/app/api/endpoints.py`, `backend/app/models/__init__.py`, `backend/app/models/schemas.py`, `backend/app/services/__init__.py`, `backend/app/services/game_engine.py`
- [X] T002 [P] Create frontend directory structure for React Vite with components/hooks structure in `frontend/`
- [X] T003 Configure Python environment, installing dependencies and writing `backend/requirements.txt` (FastAPI, Uvicorn, Pydantic, pytest, requests)
- [X] T004 [P] Configure React frontend environment, installing dependencies and writing `frontend/package.json`, `frontend/tsconfig.json`, and `frontend/vite.config.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement Pydantic schemas in `backend/app/models/schemas.py` with verbatim constraints from data-model.md: `board` count exactly 20 rows of 10 cells containing 0-7, `TetrominoSchema.type` enum of "I", "O", "T", "S", "Z", "J", "L", and `cells`/`origin` bounded between 0 and 19 for rows and 0 and 9 for columns
- [X] T006 [P] Implement TypeScript interfaces in `frontend/src/types.ts` matching GameSession, Tetromino, and MoveRequest schemas
- [X] T007 Setup base FastAPI server and CORS middleware in `backend/app/main.py` allowing frontend origin (e.g., `http://localhost:5173`)
- [X] T008 Setup initial empty API endpoints in `backend/app/api/endpoints.py` mapping to `/api/games`, `/api/games/{id}`, `/api/games/{id}/tick`, and `/api/games/{id}/move` to return mock or empty states
- [X] T009 Create the in-memory active session store dictionary in `backend/app/services/game_engine.py` to hold games by UUID string keys

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Falling Block Gameplay (Priority: P1) 🎯 MVP

**Goal**: Start a new game and see a 10x20 grid with a random tetromino starting at the top, descending automatically every 500 ms, controlling its movement (left, right, down) and locking at the bottom.

**Independent Test**: Verify that a new game session is created with a 10x20 board, a random piece spawns at the top, shifts down via `/tick`, accepts movement, and locks when resting on the bottom.

### Tests for User Story 1
> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Write contract tests in `backend/tests/integration/test_api_us1.py` for `/api/games` creation, `/api/games/{id}` retrieval, `/api/games/{id}/tick` shift, and `/api/games/{id}/move` (left, right, down) and ensure they fail
- [X] T011 [P] [US1] Write unit tests in `backend/tests/unit/test_game_engine_us1.py` verifying core falling, boundary collisions (row 0-19, col 0-9), spawning, movement (left, right, down), and lock transition on tick collision, ensuring they fail
- [X] T012 [P] [US1] Write frontend unit tests in `frontend/tests/useGame.test.ts` for the game hook to verify the 500 ms tick interval triggers state updates and keyboard events trigger move requests, and ensure they fail

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement tetromino definition, coordinates, and initial spawn states in `backend/app/services/game_engine.py` for all 7 standard shapes (I, O, T, S, Z, J, L) using verbatim coordinates from research.md
- [X] T014 [US1] Implement the collision check logic `has_collision(board, cells)` in `backend/app/services/game_engine.py` to validate grid boundaries (rows 0-19, cols 0-9) and settled block overlap
- [X] T015 [US1] Implement game session initialization logic and `/api/games` endpoint in `backend/app/services/game_engine.py` and `backend/app/api/endpoints.py` to create a 20x10 empty grid, choose a random tetromino (14.28% equal probability), spawn it at top-center, and generate a unique UUID
- [X] T016 [US1] Implement horizontal movement (left/right) logic in `backend/app/services/game_engine.py` and `/api/games/{id}/move` endpoint in `backend/app/api/endpoints.py` that shifts piece cells and origin, and collision-reverts on fail
- [X] T017 [US1] Implement manual down move (soft drop) logic in `backend/app/services/game_engine.py` and endpoints in `backend/app/api/endpoints.py` that shifts piece cells and origin down but does NOT lock yet on collision
- [X] T018 [US1] Implement the automatic gravity tick logic in `backend/app/services/game_engine.py` and `/api/games/{id}/tick` endpoint in `backend/app/api/endpoints.py` to shift active piece down by 1 row, and lock it (writing active cells to the board and spawning next piece) if a downward collision is detected
- [X] T019 [P] [US1] Implement the React custom hook `frontend/src/hooks/useGame.ts` to manage the game state, start the 500 ms tick interval (drift <10 ms) using `POST /api/games/{id}/tick`, and handle movement API calls
- [X] T020 [P] [US1] Create the visual grid component `frontend/src/components/Board.tsx` that renders the 10x20 board using Vanilla CSS Grid, superimposes the active falling tetromino in its distinct shape color, and handles empty vs settled block rendering
- [X] T021 [US1] Create the control keys listener in `frontend/src/App.tsx` and `frontend/src/hooks/useGame.ts` that captures ArrowLeft, ArrowRight, and ArrowDown keyboard events, maps them to "left", "right", and "down" directions, and triggers movement requests to the backend via `useGame.ts`
- [X] T022 [US1] Assemble the initial gameplay container in `frontend/src/App.tsx` including the Board component and verified 500 ms gravity ticks

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Clearing Completed Horizontal Lines (Priority: P2)

**Goal**: Automatically clear completed horizontal rows of blocks from the grid and shift the rows above down.

**Independent Test**: Verify line clearing by loading a state with row 19 filled except col 0, locking a block there, and ensuring row 19 is cleared and upper blocks shift down.

### Tests for User Story 2

- [X] T023 [P] [US2] Write unit tests in `backend/tests/unit/test_game_engine_us2.py` verifying detection of complete rows, removal of completed rows, downward shifting of all rows above, and inserting empty row placeholders at index 0, ensuring they fail
- [X] T024 [P] [US2] Write integration test in `backend/tests/integration/test_api_us2.py` verifying that locking a piece that completes a line clears the line and shifts the board in the returned API response, ensuring it fails

### Implementation for User Story 2

- [X] T025 [US2] Implement full line clear detection logic in `backend/app/services/game_engine.py` checking all 20 rows of the board for fully completed horizontal lines (all 10 cells filled with non-zero color values) upon piece lock
- [X] T026 [US2] Implement row clearing and row shifting in `backend/app/services/game_engine.py` that deletes completed rows, shifts settled blocks above them down by the exact number of cleared lines, and prepends new empty rows filled with 0s at the top
- [X] T027 [US2] Update `/api/games/{id}/tick` endpoint in `backend/app/api/endpoints.py` to return the updated game board state with any completed lines cleared and blocks shifted down

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Game Over & Replayability (Priority: P3)

**Goal**: Detect when the stack of blocks reaches the top, transition status to `"game_over"`, disable movement controls, render a game-over screen, and support restarting the game.

**Independent Test**: Verify game status changes to `"game_over"` when spawning piece overlaps settled blocks, controls are ignored, and pressing restart clears the board and resets.

### Tests for User Story 3

- [X] T028 [P] [US3] Write unit tests in `backend/tests/unit/test_game_engine_us3.py` for game over detection (when newly spawned piece overlaps settled block), ensuring status transitions to `"game_over"`, and all subsequent ticks/moves are ignored, ensuring they fail
- [X] T029 [P] [US3] Write integration tests in `backend/tests/integration/test_api_us3.py` verifying `/api/games` restart behavior, and that a game over state rejects further tick/move requests, ensuring they fail
- [X] T030 [P] [US3] Write frontend tests in `frontend/tests/GameOverModal.test.tsx` verifying the GameOverModal renders correctly in English and the restart button triggers game reset, ensuring they fail

### Implementation for User Story 3

- [X] T031 [US3] Implement spawn overlap check in `backend/app/services/game_engine.py` during piece spawning; if overlap with settled block is found, set status to `"game_over"` and `active_piece` to None
- [X] T032 [US3] Update tick and move endpoints in `backend/app/api/endpoints.py` to immediately reject or ignore operations with no state changes if the game status is `"game_over"`
- [X] T033 [US3] Implement the restart state reset in `backend/app/services/game_engine.py` and the `POST /api/games` endpoint in `backend/app/api/endpoints.py` to clear settled board blocks to 0, reset status to `"playing"`, and spawn a new random piece
- [X] T034 [P] [US3] Create the game over rendering component `frontend/src/components/GameOverModal.tsx` in English that pops up as a modal or overlay when the game status transitions to `"game_over"`
- [X] T035 [P] [US3] Create the game controls panel component `frontend/src/components/GameControls.tsx` featuring a prominent "Restart" button that triggers a fresh session request
- [X] T036 [US3] Update custom hook `frontend/src/hooks/useGame.ts` to support game restart requests and disable the gravity interval once status is `"game_over"`
- [X] T037 [US3] Integrate `GameOverModal` and `GameControls` in `frontend/src/App.tsx`, verifying controls are disabled when the game is over and the restart button correctly restarts the session

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 Add global styling polish, spacing, cell block design with custom color themes per tetromino type (I, O, T, S, Z, J, L) using CSS variables in `frontend/src/index.css`
- [X] T039 [P] Set up automatic testing workflow or execution target for frontend (build with `cd frontend; npm run build`) and backend tests (`cd backend; pytest` or `python -m pytest backend/tests`) and root test script
- [X] T040 Implement Swagger-compliant documentation annotations for the backend in `backend/app/main.py`
- [X] T041 Run quickstart.md validation script `validate_engine.py` to confirm and verify E2E backend state machine compliance
- [X] T042 [P] Create documentation files inside `docs/` summarizing architectural details and API endpoints usage
- [X] T043 Perform final lint, typescript compilation check (`cd frontend; npm run build`), and format checking on all backend and frontend files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3, 4, 5)**: All depend on Foundational phase completion
  - User stories should proceed sequentially in priority order (US1 -> US2 -> US3) to maintain strict incremental focus
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) is complete. Has no dependencies on other stories.
- **User Story 2 (P2)**: Depends on User Story 1 (requires active block falling and locking engine in order to clear lines).
- **User Story 3 (P3)**: Depends on User Story 1 (requires block stack and spawning engine in order to trigger game over on overlap).

### Within Each User Story

- Tests MUST be written and fail before implementation.
- Models and schemas before core services and mechanics.
- Services before controller endpoints.
- Integration and rendering validation.

### Parallel Opportunities

- Phase 1 Setup tasks T002 and T004 marked [P] can run in parallel with T001 and T003.
- Phase 2 Foundational task T006 can run in parallel with database/schema/backend models setup tasks.
- For each User Story, tests (T010, T011, T012) can be designed in parallel.
- Piece coordinate definition (T013) can run in parallel with other backend tasks.
- React components Board.tsx (T020) and App.tsx controls (T021) can be developed in parallel as long as the useGame hooks interfaces are defined.
- Game Over components (T034, T035) can be developed in parallel while the backend overlap detection is being worked on.

---

## Parallel Example: User Story 1

```bash
# Writing and preparing test files in parallel:
Task: "Write contract tests in backend/tests/integration/test_api_us1.py"
Task: "Write frontend unit tests in frontend/tests/useGame.test.ts"

# Designing frontend presentation blocks in parallel with engine:
Task: "Create the visual grid component frontend/src/components/Board.tsx"
Task: "Implement tetromino definition, coordinates in backend/app/services/game_engine.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Complete Phase 3 (User Story 1).
3. **STOP and VALIDATE**: Use unit tests and run the manual game interface to verify a piece descends at 500 ms, moves left/right/down, and locks on the bottom.

### Incremental Delivery

1. Complete Setup + Foundational -> Project backbone is ready.
2. Complete US1 -> Playable engine is ready (MVP).
3. Complete US2 -> Line clear capability is ready.
4. Complete US3 -> Full game lifecycle (game over/restart) is ready.
5. Apply Phase 6 (Polish) -> Visual and code enhancements.

### Parallel Team Strategy

With multiple developers:
1. Team completes Setup + Foundational together.
2. Once Foundational is done:
   - Developer A: Implements backend game engine physics and endpoints for US1 -> US2 -> US3.
   - Developer B: Implements frontend components, keyboard listeners, and React hooks.
3. Validate independent endpoints and UI bindings progressively.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
