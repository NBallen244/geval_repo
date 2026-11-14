# Tasks: Tetris Stage 4 Option A - Rotation, Canvas 2D Board, and Real-Time WebSockets Duel

**Input**: Design documents from `/specs/004-tetris-stage4-option-a/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story / milestone to enable independent implementation and testing of each phase, traceably mapped to acceptance IDs `ROT-01`, `ROT-02`, `ROT-03`, `CAN-01`, `CAN-02`, `NET-01`, `NET-02`, `NET-03`, `INF-01`, and `PERF-01`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1: Rotation, US2: Canvas, US3: WebSocket Duel)
- Includes exact file paths and requirements in descriptions

## Path Conventions

- **Full-stack App**: `backend/app/`, `backend/tests/`, `frontend/src/`, `frontend/tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Environment and dependency initialization [INF-01]

- [X] T001 [US3/M3-Deferred] Pin standard backend dependencies in `backend/requirements.txt` and `backend/requirements-dev.txt` to include `websockets==12.0` and configure Python 3.11/3.12 compatibility.
- [X] T002 [US1/M1-Preserved] Verify existing frontend environment and build toolchain (keep inherited frontend lock, TS options and existing lint/toolchain; the seed does not require new lint tools or blanket frontend dependency updates).
- [X] T003 [US1/M1-Preserved] Verify existing backend code standards via pytest, coverage.py statement coverage, and pip-audit.
- [X] T004 [US1/M1-Preserved] Verify existing frontend code styles, TypeScript build options, and Vite configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared model extensions and infrastructure prep [INF-01]

- [X] T005 [US3/M3-Deferred] Extend core player and game schemas in `backend/app/models/schemas.py` to support `active_piece_generation` (starts at 0) and client-tracking fields (`last_processed_seq_num`, `last_action_seat`, `last_action_seq`, `last_action_observable_change`) in preparation for sequence validation.
- [X] T006 [US3/M3-Deferred] Configure same-origin reverse-proxy WebSocket upgrade rules (`/api/duel/ws`) routing to backend, and set up non-root containers in `docker-compose.yml` and `nginx.conf`.
- [X] T007 [US3/M3-Deferred] Ensure persistent solo high-score SQL structures in `backend/app/services/database.py` are isolated from duel modes (no writing duel results to solo SQLite volume).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel or sequence.

---

## Phase 3: User Story 1 - Authoritative Tetromino Rotation (Priority: P1) [ROT-01, ROT-02, ROT-03]

**Goal**: Implement authoritative 90-degree clockwise and counterclockwise tetromino rotation with column wall-kick offset logic in Python, exposed via REST endpoints and mapped keys in UI.

**Independent Test**: Run backend rotation tests `pytest tests/unit/test_game_engine_us1.py` and verify 100% pass on all rotation and kick states.

### Tests for User Story 1
> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Implement comprehensive tetromino rotation tests in `backend/tests/unit/test_game_engine_us1.py covering four unobstructed CW/CCW turns, O piece no-op, board wall-kicks, locked-cell rejections, hold reset, and gravity isolation.

### Implementation for User Story 1
- [X] T009 [US1] Define deterministic pivots and sorted coordinate cell offsets for tetrominoes (I, O, T, S, Z, J, L) in their four orientation states in `backend/app/services/game_engine.py`, ensuring O is a strict state-invariant no-op.
- [X] T010 [US1] Implement the horizontal wall-kick shift check order (`0, -1, +1, -2, +2` column offsets, with zero vertical kicks) applying the first legal candidate in `backend/app/services/game_engine.py`.
- [X] T011 [US1] Expose rotation instructions `"cw"` and `"ccw"` as accepted direction values under strict `MoveRequest` body validation in `backend/app/api/endpoints.py`.
- [X] T012 [US1] Ensure rotation is a pure position change and does NOT trigger line locks, gravity speedups, points, or hold transitions in `backend/app/services/game_engine.py`.
- [X] T013 [US1] Implement automatic orientation index reset (sets orientation to 0) whenever newly spawning a piece or retrieving a piece from Hold in `backend/app/services/game_engine.py`.
- [X] T014 [P] [US1] Update the frontend movement API trigger to send CW/CCW commands for the move endpoint in `frontend/src/hooks/useGame.ts`.
- [X] T015 [US1] Map keyboard controls `ArrowUp` to clockwise (`"cw"`) and `Z` / `z` to counterclockwise (`"ccw"`) in `frontend/src/components/GameControls.tsx` and the main keyboard listener in `frontend/src/App.tsx`.

**Checkpoint**: At this point, User Story 1 is fully functional and testable independently on the existing board.

---

## Phase 4: User Story 2 - High-DPI Canvas 2D Board Rendering (Priority: P2) [CAN-01, CAN-02]

**Goal**: Replace the DOM cell board with high-DPI Canvas 2D rendering scaling programmatically with `devicePixelRatio`, keeping outer stats, preview, hold, and leaderboard in React DOM.

**Independent Test**: Decommission `.board-grid` and `div.cell` assertions, verifying canvas mounting and resize triggers with frontend unit tests.

### Tests for User Story 2
- [X] T016 [P] [US2] Create unit and component tests verifying canvas mounting, resizing, and pixel scaling in `frontend/tests/App.test.tsx` while decommissioning traditional cell div selectors.

### Implementation for User Story 2
- [X] T017 [US2] Implement programmatic backing store scaling (`canvas.width = cssWidth * window.devicePixelRatio` and `ctx.scale(dpr, dpr)`) on mount and resize events in `frontend/src/components/Board.tsx`.
- [X] T018 [US2] Implement Canvas 2D rendering pipeline drawing the 10x20 cell board, locked cells, and the active falling piece using absolute coordinate cells in `frontend/src/components/Board.tsx`.
- [X] T019 [US2] Connect resize, rotation, movement, line-clears, locking, and restart event handlers to trigger immediate canvas repaints in `frontend/src/components/Board.tsx`.
- [X] T020 [US2] Decommission the DOM board div grid, preserving the surrounding React DOM overlays, stats panels, preview/hold containers, and leaderboard overlays in `frontend/src/App.tsx`.
- [X] T021 [P] [US2] Integrate the existing stale-response protection in the solo game update hook in `frontend/src/hooks/useGame.ts`.
- [X] T022 [US2] Verify that solo terminal games still trigger once-only persistent SQLite saves in `backend/app/services/database.py`.

**Checkpoint**: At this point, single-player mode has been successfully migrated to Canvas 2D, with all DOM tests updated.

---

## Phase 5: User Story 3 - Two-Player Real-Time Duel over WebSockets (Priority: P3) [NET-01, NET-02, NET-03, INF-01, PERF-01]

**Goal**: Add real-time same-origin WebSockets duel mode with side-by-side Canvas boards, server-driven gravity loops, same tetromino sequences, seat inputs validation, monotonic sequences, generation-level stale rejection, and 5-min sweeps.

**Independent Test**: Execute WebSocket connection, manager unit tests, and Playwright benchmark script, validating handshakes, start gating, synchronized play, forfeits, and latency.

### Tests for User Story 3
- [X] T023 [P] [US3] Create WebSocket upgrade handshake and CSWSH Origin validation tests in `backend/tests/integration/test_api_ws.py`.
- [X] T024 [P] [US3] Create comprehensive duel room manager tests covering start gating, seed piece sequences, seat controls isolation, duplicate sequence suppression, generation checks, DRAW results on same-tick top-out, disconnect forfeits, and inactivity garbage collection in `backend/tests/unit/test_duel_manager.py`.

### Implementation for User Story 3
- [X] T025 [US3] Implement WebSocket handshake origin verification against authorized domains, immediately returning `403 Forbidden` for invalid upgrade requests in `backend/app/main.py`.
- [X] T026 [US3] Implement the thread-safe `DuelRoom` manager enforcing capacity bounds (max 100 rooms, max 2 players per room), 1KB payload bounds, and deterministic room ID queries in `backend/app/services/duel_manager.py`.
- [X] T027 [US3] Implement server-side gravity loop tasks (driven independently per seat using asyncio background timers) and seed sequence distributions in `backend/app/services/duel_manager.py`.
- [X] T028 [US3] Implement seat action inputs validation and connection routing (restricting players from sending commands targeting the opponent's seat) in `backend/app/api/ws_duel.py`.
- [X] T029 [US3] Implement monotonic sequence `seq_num` validation and `active_piece_generation` stale action rejection rules (ignoring outdated commands without applying board mutations) in `backend/app/services/duel_manager.py`.
- [X] T030 [US3] Implement double-gravity tick DRAW evaluation logic (if both seats top out within the same authoritative server loop tick) and forfeit outcome handling in `backend/app/services/duel_manager.py`.
- [X] T031 [US3] Implement background sweeps task checking for room inactivity and cancelling associated server-side gravity futures after 5 minutes of inactivity in `backend/app/services/duel_manager.py`.
- [X] T032 [P] [US3] Build the side-by-side Canvas 2D duel board component and same-origin room creation / room ID typing controls in `frontend/src/components/DuelBoard.tsx` and `frontend/src/App.tsx`.
- [X] T033 [US3] Implement WebSocket bidirectional state machine synchronization matching JSON `"v": 1` envelopes and accepting action correlation attributes in `frontend/src/hooks/useDuel.ts`.
- [X] T034 [US3] Enforce isolation of duel results, ensuring no writes are sent to the SQLite high scores DB in `backend/app/services/database.py`.
- [X] T035 [US3] Create the six-trial Playwright browser performance benchmark script mapping frame intervals, local repaints, and remote latencies under a visible side-by-side window focus mode in `frontend/tests/performance-benchmark.ts` using a common monotonic clock or calibrated cross-context timing with explicit correlation ID and validated changed Canvas state. Keep raw source timestamps, reject ambiguous overlap, and document the measured boundary.
- [X] T035b [US3] Create a Playwright functional test verifying a WebSocket duel through two independent browser clients (isolated contexts) against the actual production proxy (Nginx), including start gating, movement and rotation synchronization, disconnect, room isolation, and result delivery.
- [X] T035c [US3] Add a separate M3 CI workflow trigger task for the 004 duel workflow trigger and run actual local CI/build checks (e.g., executing the pipeline in local Nginx/containers), with no hosted-run claim. (CI workflow trigger already has main/master and 003/004 branches, verified in `docs/validation/ci-config-12-01/report.json`. Local CI execution validated with 74 tests passing on backend, and 46 tests passing on frontend).

**Checkpoint**: At this point, real-time two-player WebSocket duels are fully functional, synchronized, secure, and isolated.

---

## Phase 5.5: Bounded Corrective Implementation (Milestone 3 Defects)

**Purpose**: Bounded corrective execution on Milestone 3 defects

- [X] T040 [US3] Preserve the assigned shared sequence prefix by appending a shared tail under the manager lock rather than regenerating all entries on demand, preserving original entries exactly.
- [X] T041 [US3] Deliver the terminal result once, making finalization/delivery idempotent across gravity, action, duplicate disconnect, shutdown, and cleanup, and never sending multiple game_over frames.
- [X] T042 [US3] Require configured browser Origin on WebSocket upgrade, rejecting missing or invalid Origin headers immediately before room allocation/upgrade.
- [X] T043 [US3] Finish explicit strict schema bounds: require "v": 1 explicitly (no default), sequence in [1, 9007199254740991], and generation in [0, 9007199254740991], excluding booleans and unknown fields.
- [X] T044 [US3] Resolve the action-induced game over non-reentrant lock deadlock in process_action by releasing self.lock before delivering state and game over events. Add the corresponding deadlock and idempotency regression tests.
- [X] T045 [US3] Ensure every post-join endpoint exit is routed through one unified disconnect/cleanup path (e.g. using a `finally` block), fixing the receive loop oversized-payload bug (where the loop broke but didn't trigger `handle_disconnect`), and adding corresponding integration regressions.
- [X] T046 [US3] Correct the native measurement instrument (performance-benchmark.ts) and repair the two native test gaps (test_api_ws.py policy close and duel-functional-test.ts enhancements) to ensure accurate, non-colliding pixel-by-pixel validation and robust connection policy close checks.
- [X] T046b [US3] Implement the headed launch correction in performance-benchmark.ts: pass `channel` option to all three Playwright launch calls, pass headed window-size/position options to the solo launch, implement a safe-launch wrapper to handle launch failures cleanly with empty arrays in runsReport to retain failure rows, and run verification.
- [X] T047 [US3] Implement the bounded file-system handshake as an optional foreground-activation gate before setup/warmup inside performance-benchmark.ts, adding command-line arguments, wait hooks for solo and duel clients, temporary title instrumentation, JSON ready/approved handshake protocol, and partial row failure handling.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, linting, audits, and performance capture

- [X] T036 Verify Nginx reverse-proxy routes (HTTP and WebSockets) and non-root Docker Compose execution through container verification. (Nginx proxy routing and non-root Docker runtime verified in `docs/final/docker/runtime-final-21-01/report.json`. Multi-container health, loopback 5513, and persistence checks all successfully completed).
- [X] T037 Run full test suites (`pytest` on backend and `npm run test` on frontend) to ensure zero regressions exist.
- [X] T038 [P] Record audited dependencies, SonarQube metrics, and verification logs in `specs/004-tetris-stage4-option-a/checklists/requirements.md`. (Audited 49 dependencies with 0 known direct packaging advisories verified in `docs/audit-inputs/final-reconciliation-21-01/report.json`. SonarQube metrics recorded: 50.9% new-code coverage, 40 violations, resulting in computation SUCCESS and dedicated study Quality Gate ERROR [global Sonar coverage 65.1% remains distinct]. Verified logs and hashes cataloged in checklists and native closure files).
- [X] T039 Execute the Playwright performance protocol script (`performance-benchmark.ts`) and document frame scheduling rates, local repaints, and remote latencies. (6 trials completed across 180 scenario seconds / 270 client seconds in headed Chrome. All 9 client rows met >= 55 scheduling events/s [164.67–164.93 observed] and p95 <= 25ms [~6.2ms observed]. 75 solo local, 62 duel local, and 61 duel remote latency samples collected and validated. Full telemetry logged in `docs/gate-performance-verified.json`).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
  - Recommended order: Phase 3 (Rotation) ➔ Phase 4 (Canvas) ➔ Phase 5 (WebSocket Duel) to establish the engine core before drawing, and drawing before multi-board duels.
- **Polish (Final Phase)**: Depends on all user stories being complete.

### Within Each User Story

- Tests MUST be written and fail before implementation.
- Models and schemas before services.
- Services before API/WS handlers.
- Handlers before frontend integrations.

### Parallel Opportunities

- All Setup tasks marked `[P]` (T002, T003, T004) can run in parallel.
- Setting up the reverse proxy (T006) can run in parallel with extending schemas (T005) inside Phase 2.
- Backend rotation tests (T008) and frontend hooks (T014) can be prepared in parallel with core engine work (T009) inside Phase 3.
- Unit testing canvas resize (T016) and stale protection (T021) can run in parallel with Board component work (T017) inside Phase 4.
- Handshake tests (T023) and Duel Board components (T032) can run in parallel with core Duel manager implementation inside Phase 5.

---

## Parallel Example: User Story 1

```bash
# Launch backend rotation tests and frontend hooks in parallel:
Task: "Implement comprehensive tetromino rotation tests in backend/tests/unit/test_game_engine_us1.py"
Task: "Update the frontend movement API trigger to send CW/CCW commands in frontend/src/hooks/useGame.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Implement Phase 3 (deterministic rotation, kick check offsets `0, -1, +1, -2, +2`, keys).
3. **STOP and VALIDATE**: Run `pytest tests/unit/test_game_engine_us1.py` and verify rotation is correct.

### Incremental Delivery

1. Setup + Foundation ready ➔ Base structures complete.
2. Add Rotation (US1) ➔ Test on existing board ➔ Deploy/Demo core mechanics.
3. Add Canvas 2D (US2) ➔ Test mounting/redraws/DPR ➔ Deploy/Demo visually polished board.
4. Add WebSockets Duel (US3) ➔ Test synchronization/CSWSH/Cleanups ➔ Deploy/Demo complete Duel.

---

## Notes

- `[P]` tasks have no file conflicts or logical dependencies and can be worked on concurrently.
- `[Story]` label maps tasks back to specific user stories for strict compliance and traceability.
- Verify tests fail first, and use automatic code formatters to format files after modifications.

---

## Supplemental Coverage Remediation Plan (Stage 4 Option A)

**Historical Baseline**: 50.9% New-Code Coverage (Quality Gate: ERROR / Failed)
**Remediation Goal**: Target >=80% Sonar NEW-CODE coverage by adding robust behavioral unit and component tests for `DuelBoard.tsx` and `useDuel.ts` inside `frontend/tests`. No modifications to production source are authorized.

### Phase 7: Supplemental Test Suite Implementation (Vitest)

- [X] T101 [P] [US3] Implement comprehensive behavioral unit tests for `frontend/src/hooks/useDuel.ts` in `frontend/tests/useDuel.test.ts`. Cover:
  - Controlled WebSocket fake simulating open, message, error, close, and send events.
  - Room creation and join lifecycle via `joined` WS messages.
  - State synchronization and rendering payload parsing on `state_update`.
  - Game over outcome validation on `game_over`.
  - Error rendering and propagation on `error`.
  - Sent action envelope payload checks (ensuring monotonic `seq_num` increments, correct `generation` mapping, and matched `action_type`).
  - Strict input gates (pre-OPEN send inhibition, seat validation).
  - Out-of-order and stale revision message rejection.
  - Stale/old socket callback protection (discarding callbacks from older, overridden sockets).
  - Socket unmounting, disconnect sweeps, and connection close code categorization (4001, 4004, 4008, non-1000).
- [X] T102 [P] [US3] Implement comprehensive component tests for `frontend/src/components/DuelBoard.tsx` in `frontend/tests/DuelBoard.test.tsx`. Cover:
  - Mocked global `ResizeObserver` and realistic Canvas 2D spy recording fillRect, strokeRect, clearRect, scale calls.
  - Board vacancy state rendering and active player states.
  - Occupied cell color-index merging, active falling piece merging, and absolute coordinate clipping bounds.
  - DPI backing store scaling (`window.devicePixelRatio` logic) and resize-triggered repaints.
  - React DOM stats rendering (Score, Lines, Level, Hold slots, and Next piece preview).
  - Main keyboard event handlers mapping (ArrowUp -> cw, Z/z -> ccw, ArrowLeft, ArrowRight, ArrowDown, C/c/Shift -> hold).
  - Game status listener gating (suppressing keyboard events when room status is not active).
  - Listener cleanup on unmount and exit button disconnect click handlers.
- [X] T103 Run existing local Vitest suite with coverage to measure intermediate coverage improvements and verify zero regressions.
- [X] T104 [P] [US3] Implement comprehensive backend unit tests in `backend/tests/unit/test_duel_lifecycle_coverage.py` targeting uncovered sections of `duel_manager.py` (including `sweep_inactive_rooms`, `close_all_rooms`, and `get_room_snapshot`). Validate the actual sweeper with synthetic ages/sockets, `close_all_rooms` with task/socket cleanup and exception handling, and snapshot retrieval under varying room validity.

