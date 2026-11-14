---
description: "Authoritative task list for Stage 2 Tetris implementation"
---

# Tasks: Extend Tetris to Stage 2 - Score, Level, Hold, Next Preview

**Input**: Design documents from `/specs/002-extend-tetris-stage2/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included as requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (i.e., [US1], [US2], [US3])
- Include exact file paths in descriptions

## Path Conventions

- **Backend app**: `backend/app/`
- **Frontend app**: `frontend/src/`
- **Backend tests**: `backend/tests/`
- **Frontend tests**: `frontend/tests/`

---

## Phase 1: Setup & Initial Verification (Shared Infrastructure)

**Purpose**: Project initialization, baseline verification, and security audits.

- [X] T001 [P] Verify current Stage 1 baseline by running existing backend tests via `pytest` in `backend/` and frontend tests via `npm run test` in `frontend/`
- [X] T002 Run dependency security audits (`pip-audit` or `safety` for `backend/requirements.txt` and `npm audit` for `frontend/package.json`) and apply remediation fixes to lockfiles without changing application code

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, state models, and SonarQube baseline schema updates.

**⚠️ CRITICAL**: This phase must be completed before starting any user story tasks.

- [X] T003 [P] Document 404 HTTPException responses in the OpenAPI schema/endpoints in `backend/app/api/endpoints.py` to fix SonarQube baseline code smell `python:S8415` by adding `responses={404: {"description": "Game not found"}}` to all game-retrieval and mutation endpoints
- [X] T004 Extend `GameSessionSchema` model in `backend/app/models/schemas.py` to include Stage 2 fields with strict validation: `score` (int, >= 0), `total_lines` (int, >= 0), `level` (int, >= 1), `gravity_interval_ms` (int, range [100, 500]), `next_piece` (str, one of the standard 7 shapes), `hold_piece` (Optional[str], nullable standard 7 shapes), and `can_hold` (bool, default True)
- [X] T005 [P] Extend `GameSession` TypeScript interface in `frontend/src/types.ts` to mirror Stage 2 schema properties: `score`, `total_lines`, `level`, `gravity_interval_ms`, `next_piece`, `hold_piece` (nullable string), and `can_hold`

**Checkpoint**: Foundation ready - user story implementation can now begin in priority order

---

## Phase 3: User Story 1 - Scoring, Leveling, and Progressive Gravity (Priority: P1) 🎯 MVP

**Goal**: Implement score tracking, cumulative line-clearing accounting, pre-lock level boundary checks, a minimum gravity floor (100 ms), dynamic timer rescheduling, and secure random piece queue generation.

**Independent Test**: Verify scoring formula, cumulative line counts, pre-lock levels, gravity intervals, and random choice queue count assertions using unit and integration tests.

### Tests for User Story 1

> **NOTE: Write these tests FIRST and ensure they FAIL before changing implementation**

- [X] T006 [P] [US1] Create unit tests in `backend/tests/unit/test_game_engine_us1.py` to verify:
  - Isolated 1, 2, 3, and 4-row scoring scoring rules (`100 * level`, `300 * level`, `500 * level`, `800 * level` respectively) using mock matrices
  - Level boundary calculation `1 + floor(total_lines / 10)` based on cumulative lines cleared
  - Pre-lock level scoring where score multiplier is evaluated using the level *immediately before* the lock
  - Progressive gravity calculations and the minimum gravity interval floor of 100 ms: `gravity_interval_ms = max(100, 500 - 50 * (level - 1))`
  - Next piece queue generation where normal spawning consumes the queue piece and generates exactly one new preview piece
- [X] T007 [P] [US1] Create integration tests in `backend/tests/integration/test_api_us1.py` targeting `/api/games`, `/api/games/{id}`, `/api/games/{id}/tick`, and `/api/games/{id}/move` to verify that GET state responses read state immutably (no consumption of queued next piece) and endpoints return the correct Stage 2 schemas

### Implementation for User Story 1

- [X] T008 [US1] Refactor `create_session` and initialization in `backend/app/services/game_engine.py` to populate initial Stage 2 variables: `score=0`, `total_lines=0`, `level=1`, `gravity_interval_ms=500`, `hold_piece=None`, `can_hold=True`, and populate a secure `next_piece` randomly
- [X] T009 [US1] Update piece selection and spawning in `backend/app/services/game_engine.py` to use Python's cryptographically secure choice generator (e.g. `secrets.choice` or `random.SystemRandom`) to avoid SonarQube baseline vulnerability `python:S2245` (without suppressions) for spawning both `active_piece` and `next_piece`
- [X] T010 [US1] Refactor the row locking phase of `tick_session` in `backend/app/services/game_engine.py` to calculate score using the level *prior* to line clearing, update `total_lines` with cumulative row clears, recalculate level using `1 + floor(total_lines / 10)`, and compute `gravity_interval_ms` using `max(100, 500 - 50 * (level - 1))`
- [X] T011 [US1] Update `tick_session` spawning logic in `backend/app/services/game_engine.py` to spawn the next active piece from `next_piece`, and generate exactly one new random tetromino type for `next_piece`
- [X] T012 [US1] Refactor frontend ticking logic in `frontend/src/hooks/useGame.ts` to reschedule its automatic gravity tick timer immediately upon receiving an updated `gravity_interval_ms` from backend state responses

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Holding and Swapping Tetrominoes (Priority: P2)

**Goal**: Implement the Hold piece mechanic, enabling players to temporarily save their active piece or swap it, restricted to one use per spawned piece, with immediate collision checks and obstructed Hold spawning game overs.

**Independent Test**: Trigger hold via `/hold` endpoint or button, verifying piece swaps, immutable next previews on swaps, ignored holds, reset on lock, and immediate collision game over.

### Tests for User Story 2

> **NOTE: Write these tests FIRST and ensure they FAIL before changing implementation**

- [X] T013 [P] [US2] Create unit tests in `backend/tests/unit/test_game_engine_us2.py` verifying:
  - Hold operations: first hold consumes preview and generates exactly one new preview, storing current active piece in empty Hold slot
  - Hold swaps: swapping with an occupied Hold slot does NOT consume the next preview, but swaps the active piece type with `hold_piece` and spawns the held piece at normal spawn origin in initial orientation
  - Immutable actions: rejected holds (when `can_hold` is false), actions after game-over, and repeated state reads never mutate the game state
  - Obstructed Hold spawn: spawning a piece from Hold that overlaps with settled blocks on the board immediately transitions `status` to `"game_over"` and sets `active_piece` to null
  - Reset on lock: `can_hold` is reset to true ONLY after a piece locks into the board
- [X] T014 [P] [US2] Create integration tests in `backend/tests/integration/test_api_us2.py` to verify the `POST /api/games/{id}/hold` endpoint returns 404 for invalid game IDs, returns the same state shape on success, and returns unmodified state on rejected holds (when `can_hold` is false or status is game_over)

### Implementation for User Story 2

- [X] T015 [US2] Implement `hold_session_piece` function in `backend/app/services/game_engine.py` to handle the hold/swap rules, check spawning collisions, and transition status to `"game_over"` and `active_piece` to null if blocked
- [X] T016 [US2] Add route and handler for `POST /api/games/{id}/hold` in `backend/app/api/endpoints.py` to expose the backend Hold action
- [X] T017 [US2] Update `tick_session` locking phase in `backend/app/services/game_engine.py` to reset `can_hold` to `True` whenever a piece settles/locks onto the board
- [X] T018 [US2] Update `create_session` and restart in `backend/app/services/game_engine.py` to reset `hold_piece` to `None` and `can_hold` to `True`, while generating a fresh random `active_piece` and `next_piece`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently on the backend

---

## Phase 5: User Story 3 - Stage 2 UI Display and Sync (Priority: P3)

**Goal**: Display all Stage 2 statistics, the Next preview queue, and the Hold slot on the UI; handle keyboard 'C' / 'c' key and click triggers; implement transaction sequencing to prevent out-of-order API race conditions (especially across restarts); and visually disable the Hold button when unavailable.

**Independent Test**: Verify UI rendering, C/c keybind triggers, unclickable Hold button when `can_hold` is false or status is `"game_over"`, and out-of-order request discarding across a restart.

### Tests for User Story 3

> **NOTE: Write these tests FIRST and ensure they FAIL before changing implementation**

- [X] T019 [P] [US3] Create frontend tests in `frontend/tests/useGame.test.ts` to verify:
  - 'C' and 'c' keyboard triggers and Hold button clicks dispatch `POST /api/games/{id}/hold`
  - Stale responses are discarded to prevent out-of-order state regression (e.g. sequence tracking)
  - Stale responses across restarts are properly invalidated so that pre-restart responses never override the reset state
  - Hold button is visually disabled and unclickable when `can_hold` is false or game status is `"game_over"`
- [X] T020 [P] [US3] Create frontend tests in `frontend/tests/GameOverModal.test.tsx` verifying that restarting reset-clears the Stage 2 visual panels correctly

### Implementation for User Story 3

- [X] T021 [US3] Refactor frontend `Board.tsx` in `frontend/src/components/Board.tsx` to fix SonarQube baseline code smell `typescript:S6479` by using stable React keys (e.g., combining row/col index with cell value or a stable coordinate ID string) instead of array indices
- [X] T022 [US3] Apply optional chaining in `frontend/src/App.tsx` and `frontend/src/hooks/useGame.ts` to fix SonarQube baseline code smells `typescript:S6582` by preferring `?.` for state access (e.g., `game?.score`, `game?.activePiece`)
- [X] T023 [US3] Implement client-side transaction request sequence tracking or locking in `frontend/src/hooks/useGame.ts` to filter out stale, out-of-order responses, specifically invalidating pending responses across restart so they cannot overwrite the reset state
- [X] T024 [US3] Add `hold` API fetch function in `frontend/src/hooks/useGame.ts` to dispatch `POST /api/games/{id}/hold` requests
- [X] T025 [US3] Bind `C` and `c` keys in keydown event listener in `frontend/src/hooks/useGame.ts` to trigger the `hold` function
- [X] T026 [US3] Design and build the Stage 2 dashboard panels in `frontend/src/App.tsx`, adding styled UI panels for Score, level, total_lines statistics, Hold Piece preview rendering, Next Piece preview rendering, and a clickable Hold button that is disabled when `can_hold` is false or status is `"game_over"`

**Checkpoint**: All user stories should now be independently functional and integrated!

---

## Phase 6: Polish & Quality/Remediation (Polish)

**Purpose**: Execute code cleaning, compile production builds, run coverage outputs, and verify complete SonarQube baseline remediation.

- [X] T027 Fix SonarQube baseline code smell `css:S7924` in `frontend/src/index.css` by updating text styles to ensure foreground text has a highly readable and contrast-compliant color with its background
- [X] T028 Run backend test suite with coverage, producing a `backend/coverage.xml` XML coverage file and verify all backend assertions pass 100%
- [X] T029 Run frontend test suite with coverage, producing a frontend LCOV coverage report (`frontend/coverage/lcov.info`) and verify all frontend assertions pass 100%
- [X] T030 Build the frontend for production via `npm run build` in `frontend/` to verify absence of typescript compilation or bundling errors
- [X] T031 Execute the local SonarQube scanning/verification tool to confirm all 9 baseline issues from `docs/sonar-baseline/sonar-issues.json` are completely remediated and no new code smells or vulnerabilities are introduced
- [X] T032 Perform quickstart manual validation scenarios in `specs/002-extend-tetris-stage2/quickstart.md` to guarantee perfect game-play and input responsiveness

---

## Phase 7: Post-Generation QA Iteration 1

**Purpose**: Systematically implement all corrections and post-generation QA requirements specified in QA-01 to QA-12.

- [X] T033 [US1] Replace backend tests with production path verification, removing duplicated scoring formulas (QA-01).
- [X] T034 [US1] Patch production random choice source with deterministic sequences and assert exact draw counts (QA-02).
- [X] T035 [US2/US3] Compare deep serialized full-state snapshots for repeated GET, rejected Hold, and after game-over actions, and verify dirty-state cleanup on restart (QA-03 / QA-04).
- [X] T036 [US1] Correct mislabeled bent pieces in scoring fixtures to be real horizontal I templates (QA-05).
- [X] T037 [US3] Implement frontend restart isolation using monotonically increasing generation counter to prevent state overwrites (QA-06 / QA-09).
- [X] T038 [US3] Implement mutation request serialization via a synchronous in-flight guard / queue (QA-06).
- [X] T039 [US3] Add deferred promise tests to verify concurrency, overlap, and race condition handling (QA-06 / QA-09).
- [X] T040 [US3] Verify timer scheduling, rescheduling, and cancellation paths via fake-timer tests (QA-09).
- [X] T041 [US3] Correct T preview cell orientation and verify all 7 shapes against template coordinates in App tests (QA-07).
- [X] T042 [US3] Fix npm vulnerability dependencies in frontend package-lock.json with compatible patched versions (QA-10).
- [X] T043 Produce backend/frontend coverage reports (XML, LCOV, text summary) and execute Sonar Qube scanner and save output with qa-iteration-1 labels (QA-11 / QA-12).

---

## Phase 8: Post-Generation QA Iteration 2

**Purpose**: Fix remaining production defects and resolve all verification gaps identified in QA Iteration 2.

- [X] T044 [US3] Fix startGame delayed JSON-body race (R1) by checking generation ownership after every asynchronous boundary, keeping requestSeqRef monotonically increasing, and synchronizing gameRef.
- [X] T045 [US3] Isolate mutation scheduling by generation (R2) by providing generation-specific queues or cancelling stale generation queues.
- [X] T046 [US3] Bound automatic gravity scheduling to prevent burst replay of queued gravity ticks, and handle timer cancellation on game over, restart, or unmount.
- [X] T047 [US3] Add deferred-promise tests exposing the detailed races, including A.json vs B wins, A.json reject vs B, mutation isolation by generation, old queue discarding, and bounded automatic ticks.
- [X] T048 [US3] Repair C/c key test evidence by creating separate fresh cases for lowercase 'c' and uppercase 'C' without direct state mutation, asserting call counts, and verifying blocked holds.
- [X] T049 [US3] Verify canonical geometry of all seven preview shapes (I, O, T, S, Z, J, L) in App tests against backend template coordinates.
- [X] T050 [US1] Replace tautological GET checks in backend/tests/unit/test_qa_iteration1.py with real FastAPI TestClient GET calls with secrets.choice spying, state comparisons, and zero random draws checks.
- [X] T051 [US3] Re-run and save backend and frontend tests, coverage reports, and Sonar Qube scans with qa-iteration-2 labels.

---

## Phase 9: Post-Generation QA Iteration 3

**Purpose**: Fix automatic tick coalescing ownership defect and complete rigorous verification evidence in QA Iteration 3.

- [ ] T052 [US3] Refactor automatic tick coalescing in `useGame.ts` to use a generation-owned token/Map so completion/cleanup clears only its own pending flag, and older timers verify their captured generation.
- [ ] T053 [US3] Add deferred A/B automatic-tick regression test in `useGame.test.ts` to assert A's tick fetch has begun before restart, B's tick fetch has begun before A settles, and no extra ticks or bursts are admitted when A settles.
- [ ] T054 [US3] Make existing delayed-body and old-queue tests in `useGame.test.ts` exercise their claimed windows by asserting that A.json or A's mutation is unresolved and in flight before starting B.
- [ ] T055 [US3] Complete meaningful timer/disposal verification in `useGame.test.ts`, including 499+1 ms, 449+1 ms, and 99+1 ms interval cancellation checks, game-over/unmount cancellation, and actual React.StrictMode wrapper testing with assertions.
- [ ] T056 [US1] Fix complete GET-state evidence in `test_qa_iteration1.py` by comparing the entire real HTTP JSON state (including activePiece and board) with a serialized snapshot across repeated successful GET calls.
- [ ] T057 [US3] Re-run and save backend and frontend tests, XML/LCOV coverage reports, and Sonar Qube scans with qa-iteration-3 labels.

---

## Phase 10: Post-Generation QA Iteration 4 (Sonar Remediation)

**Purpose**: Remediate the 5 minor code smell issues identified by Sonar (S6582 and S5906) while preserving tick ownership and meaningful assertions.

- [X] T058 [US3] Refactor `useGame.ts` to use optional chain expressions for `activeToken?.gen === intervalGen` and `pendingTickTokenRef.current?.gen === myToken.gen` to satisfy `typescript:S6582`, preserving generation and request-token identity guards exactly.
- [X] T059 [US3] Refactor `useGame.test.ts` to use `toHaveLength(1)` on `mutationUrls` assertions to satisfy `typescript:S5906`, keeping equivalent meaningful assertions.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup & Audit (Phase 1)**: No dependencies - can start immediately
- **Foundational Models (Phase 2)**: Depends on Phase 1 completion - BLOCKS all subsequent user stories
- **User Stories (Phases 3 to 5)**: All depend on Foundational (Phase 2) completion
  - **User Story 1 (P1)**: Establish core gameplay MVP first
  - **User Story 2 (P2)**: Integrates with the backend state after User Story 1
  - **User Story 3 (P3)**: Integrates UI statistics, previews, and key listeners; depends on US1/US2 APIs and schemas
- **Polish & Remediation (Phase 6)**: Depends on all user stories being complete

### Parallel Opportunities

- Verification and audits (`T001` and `T002`) can run in parallel
- Model extensions (`T003` and `T005`) can run in parallel
- Test suite preparation tasks (`T006`, `T007`, `T013`, `T014`, `T019`, `T020`) can be drafted in parallel
- Once Phase 2 is complete, US1 and US2 backend implementation can be worked on in parallel by different developers:
  - Developer A: scoring, leveling, and progressive gravity timer in `game_engine.py` (`T008` to `T011`)
  - Developer B: hold/swap backend actions and hold endpoints in `game_engine.py` and `endpoints.py` (`T015` to `T018`)
- Polish tasks, LCOV reports, XML coverage reports, and production builds (`T027` to `T030`) can run in parallel once code is complete

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup & Audit
2. Complete Phase 2: Foundational (schemas and interface setups, 404 documentation)
3. Complete Phase 3: User Story 1 (Scoring, Leveling, and Gravity)
4. **STOP and VALIDATE**: Verify that rows cleared via unit tests or manual console ticks accurately level-up, score, and increase gravity tick speed
5. Deliver the first MVP increment!

### Incremental Delivery

1. Complete Setup + Foundational → Core Stage 2 structures ready
2. Add User Story 1 → Test independently → Deliver (MVP: scoring and speed)
3. Add User Story 2 → Test independently → Deliver (tactical hold option)
4. Add User Story 3 → Test independently → Deliver (full visual HUD and race-proof play)
5. Polish & Verification → Final fully-featured release

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group (upon user request in follow-up sessions)
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
