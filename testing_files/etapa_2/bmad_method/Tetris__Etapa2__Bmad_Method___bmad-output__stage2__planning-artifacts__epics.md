---
stepsCompleted: ["validate-prerequisites", "design-epics", "generate-epics-and-stories", "final-validation"]
inputDocuments: [
  "_bmad-output/stage2/planning-artifacts/prds/prd-stage2-option-a/prd.md",
  "_bmad-output/stage2/planning-artifacts/prds/prd-stage2-option-a/addendum.md",
  "_bmad-output/stage2/planning-artifacts/architecture/stage2-option-a/ARCHITECTURE-SPINE.md"
]
---

# Stage 2 Tetris Study (Option A) - Epic Breakdown

## Overview
This document provides the complete epic and story breakdown for Stage 2 (Option A) of the Tetris Study. It decomposes the requirements from the Stage 2 PRD, the PRD Addendum, and the Feature Architecture Spine into implementable and testable user stories. This backlog is strictly focused on the brownfield delta (progression, scoring, preview/hold API, client timer queue, HUD sidebars, and quality gates), avoiding redundant greenfield setup.

## Requirements Inventory

### Functional Requirements
- **FR-31: Initial State Counters**: A fresh game session starts with standard progression parameters: `score` set to 0, cumulative cleared lines `total_lines` set to 0, `level` set to 1, and `gravity_interval_ms` set to 500ms.
- **FR-32: Level Calculation**: The current level must be updated immediately after scoring is calculated, using the formula: `level = 1 + floor(total_lines / 10)`.
- **FR-33: Progressive Gravity Interval**: The gravity interval (in milliseconds) must be calculated on the backend from the current Level using the formula: `gravity_interval_ms = max(100, 500 - 50 * (level - 1))`.
- **FR-34: Frontend Gravity Scheduling and Concurrency**: The frontend client manages automatic tick intervals using exactly one active automatic timer, canceling it on mutations, queuing requests FIFO, rescheduling timer intervals, and verifying session generation tokens to prevent race conditions.
- **FR-35: Cleared Line Scoring Formulas**: Points are awarded immediately upon piece locking based on completed rows cleared: 1 row = 100 * level, 2 rows = 300 * level, 3 rows = 500 * level, 4 rows = 800 * level (multiplier is level immediately before that lock).
- **FR-36: Non-Clearing Lock Score**: If a locked piece clears zero rows, no points are awarded.
- **FR-37: Soft Drop Score Exclusion**: Manual soft drop inputs (downward movements) grant no additional points.
- **FR-38: Hold Endpoint**: Expose standard endpoint `POST /api/games/{id}/hold` that swaps the current active piece and the piece in the Hold slot.
- **FR-39: Hold Cooldown Lock**: Can hold at most once per active piece. `can_hold` set to false after swap, resets to true when a piece locks.
- **FR-40: Empty Hold Swap (First Hold)**: If `hold_piece` is empty, store active piece, spawn `next_piece` at its canonical coordinates, draw 1 new random piece for next preview, set `can_hold` to false.
- **FR-41: Occupied Hold Swap**: Swap active and hold piece, spawning retrieved piece at its canonical coordinates. Keeps preview unchanged and does not perform RNG draws. Set `can_hold` to false.
- **FR-42: Held Piece Standard Spawn Origin and Orientation**: Retrieved held piece spawns matching canonical template coordinates defined in `SHAPE_TEMPLATES` (e.g. `(0,4)` for O, `(0,3)` for others).
- **FR-43: Obstructed Hold Re-entry**: If retrieval results in immediate collision, set status to `game_over` and active_piece to `null`.
- **FR-44: Immutable Rejected Holds and No-Op Handling**: Hold requests when can_hold is false or status is game_over return 200 OK and unmodified state with 0 RNG draws. Missing ID returns 404.
- **FR-45: Next Piece State Representation**: All game state responses must expose the `next_piece` parameter.
- **FR-46: Next Preview Lifecycle**: Next piece preview is consumed only on standard spawn or empty-hold swap. Occupied hold swap does not consume next preview.
- **FR-47: State Peek Invariance**: Peeking state (GET) never consumes or alters preview.
- **FR-48: Clean Game-Over Spawn Transition**: On obstructed spawn, set status to `game_over` and `active_piece` to `null` to avoid rendering illegal overlapping cells.
- **FR-49: Unified State Payload Composition**: All responses must carry all seven new fields.
- **FR-50: Progression Order of Operations**: Score computed first, then lines updated, then level updated, then gravity updated.
- **FR-51: New Game and Restart Initialization**: Resets score=0, lines=0, level=1, gravity_interval_ms=500, hold_piece=null, can_hold=true. Performs exactly two random draws.
- **FR-52: Terminal State Immutability and Draw-Free Invariance**: Once game over, all actions, rejected actions, and GETs are immutable and perform 0 RNG draws.
- **FR-53: Normal Locking Draw Dynamics**: Normal piece lock consumes preview and draws exactly 1.
- **FR-54: Occupied Hold Draw Invariance**: Swapping with occupied Hold slot performs exactly 0 RNG draws.

### NonFunctional Requirements
- **NFR-3: Timer Concurrency Prevention**: Client's gravity scheduler must handle latency or keyboard queues gracefully. Concurrent manual moves must not overlap or double-fire.
- **NFR-4: Stale Request Suppression**: Client must discard out-of-order/obsolete responses to prevent state reversal.

### Additional Requirements
- **AD-7**: Both frontend and backend strictly conform to the 11-field schema. GETs are immutable with 0 draws.
- **AD-8**: Canonical RNG draw accounting rules.
- **AD-9**: Single active timer, immediate cancellation, FIFO mutation queue, timer rescheduling, and Restart queue preemption.
- **AD-10**: Monotonically unique generation ID tokens checked after fetch, after JSON, in catch/finally, and in timer callbacks. Discard mismatched callbacks.
- **AD-11**: UI renders score, lines, level, hold, and preview. `C` key and button are queueable and usable. Skip active piece render if null.
- **AD-12**: REST endpoints backward compatibility. Cooldown/gameover hold no-ops return 200 with 0 draws. Missing ID returns 404. Invalid moves return 422.
- **AD-13**: Test strategy using canonical `"O"` piece above N=3 and N=4 precompleted bottom rows. Achieve >= 80% coverage with 0 violations. Keep original 13 tests intact.

### FR Coverage Map
- **FR-31 (Initial State):** Epic 1 - Story 1.1 (Progression Initialization and Unified State Response)
- **FR-32 (Level Calc):** Epic 1 - Story 1.2 (Multi-Line Scoring, Level Progression, and Gravity Intervals)
- **FR-33 (Gravity Formula):** Epic 1 - Story 1.2 (Multi-Line Scoring, Level Progression, and Gravity Intervals)
- **FR-34 (Timer Scheduling):** Epic 3 - Story 3.2 (Single Active Timer, FIFO Mutation Queue, and Timing Coordination) & Story 3.3 (Component Lifecycle, Token Validation, and Preemption)
- **FR-35 (Scoring Formulas):** Epic 1 - Story 1.2 (Multi-Line Scoring, Level Progression, and Gravity Intervals)
- **FR-36 (Non-Clearing lock):** Epic 1 - Story 1.2 (Multi-Line Scoring, Level Progression, and Gravity Intervals)
- **FR-37 (Soft Drop score):** Epic 1 - Story 1.3 (Soft Drop Score Exclusion and Terminal Immutability)
- **FR-38 (Hold Endpoint):** Epic 2 - Story 2.1 (Hold Slot Creation and Empty Hold Swap Endpoint)
- **FR-39 (Hold Cooldown):** Epic 2 - Story 2.3 (Hold Cooldown, Cooldown Rejections, and Clean Game Over)
- **FR-40 (Empty Hold swap):** Epic 2 - Story 2.1 (Hold Slot Creation and Empty Hold Swap Endpoint)
- **FR-41 (Occupied Hold swap):** Epic 2 - Story 2.2 (Occupied Hold Swap Execution)
- **FR-42 (Held Piece spawn coordinates):** Epic 2 - Story 2.1 (Hold Slot Creation and Empty Hold Swap Endpoint) & Story 2.2 (Occupied Hold Swap Execution)
- **FR-43 (Obstructed hold):** Epic 2 - Story 2.3 (Hold Cooldown, Cooldown Rejections, and Clean Game Over)
- **FR-44 (No-Op Hold handling):** Epic 2 - Story 2.3 (Hold Cooldown, Cooldown Rejections, and Clean Game Over)
- **FR-45 (Next piece state):** Epic 1 - Story 1.1 (Progression Initialization and Unified State Response) & Epic 2 - Story 2.1 (Hold Slot Creation and Empty Hold Swap Endpoint)
- **FR-46 (Next preview lifecycle):** Epic 2 - Story 2.1 (Hold Slot Creation and Empty Hold Swap Endpoint) & Story 2.2 (Occupied Hold Swap Execution)
- **FR-47 (State Peek):** Epic 1 - Story 1.1 (Progression Initialization and Unified State Response)
- **FR-48 (Clean Game Over):** Epic 2 - Story 2.3 (Hold Cooldown, Cooldown Rejections, and Clean Game Over)
- **FR-49 (Unified State Payload):** Epic 1 - Story 1.1 (Progression Initialization and Unified State Response)
- **FR-50 (Progression Order of Ops):** Epic 1 - Story 1.2 (Multi-Line Scoring, Level Progression, and Gravity Intervals)
- **FR-51 (New Game / Restart reset):** Epic 1 - Story 1.1 (Progression Initialization and Unified State Response)
- **FR-52 (Terminal Immutability):** Epic 1 - Story 1.3 (Soft Drop Score Exclusion and Terminal Immutability)
- **FR-53 (Normal locking draws):** Epic 1 - Story 1.2 (Multi-Line Scoring, Level Progression, and Gravity Intervals)
- **FR-54 (Occupied hold draw-free):** Epic 2 - Story 2.2 (Occupied Hold Swap Execution)

---

## Epic List

### Epic 1: Authoritative Progression, Multi-Line Scoring, and Difficulty System (Backend)
**Epic Goal:** Implement server-side score, total cleared lines, current level, and progressive gravity calculations to drive difficulty dynamically based on gameplay.
**FRs Covered:** FR-31, FR-32, FR-33, FR-35, FR-36, FR-49, FR-50, FR-51, FR-53

### Epic 2: Next Piece Preview, Hold Slot, and API Route Extension (Backend)
**Epic Goal:** Implement server-side Hold piece swapping, Next piece preview tracking, and obstructed spawn game-over transitions to complete the stateful mechanics.
**FRs Covered:** FR-38, FR-39, FR-40, FR-41, FR-42, FR-43, FR-44, FR-45, FR-46, FR-47, FR-48, FR-54

### Epic 3: Responsive Client HUD, Queue Mutation, and StrictMode Timer Coordination (Frontend)
**Epic Goal:** Implement the frontend UI sidebar layout, a FIFO mutation request queue, monotonically increasing session tokens, and strict-mode resilient automatic timer scheduling.
**FRs Covered:** FR-34, NFR-3, NFR-4

### Epic 4: Non-Rotational 3/4 Row Clear and End-to-End Quality Validation (Verification)
**Epic Goal:** Implement non-rotational O-piece test fixtures for 3-row and 4-row clears, write comprehensive tests, configure code coverage, and execute Sonar Quality Gate audits.
**FRs Covered:** AD-13

---

## Epic 1: Authoritative Progression, Multi-Line Scoring, and Difficulty System (Backend)

### Story 1.1: Progression Initialization and Unified State Response
As a Software Architect,
I want the game session to initialize and return all 7 progression fields,
So that both client and server have a single authoritative starting state.

**Acceptance Criteria:**
- **Given** no active game session,
- **When** `POST /api/games` is executed,
- **Then** a new game session is created with standard board, status `"playing"`, active_piece, and preview next_piece.
- **And** the 7 new fields are returned: `score` is 0, `total_lines` is 0, `level` is 1, `gravity_interval_ms` is 500, `next_piece` is drawn, `hold_piece` is `null`, and `can_hold` is `true`.
- **And** the creation performs exactly 2 random draws (one for active_piece, one for next_piece).
- **And** any standard state read via `GET /api/games/{id}` returns the same 11 fields with zero (0) RNG draws.

### Story 1.2: Multi-Line Scoring, Level Progression, and Gravity Intervals
As a Developer,
I want the game engine to calculate scores and speed up gravity automatically when completed rows are cleared upon a piece lock,
So that difficulty increases progressively as the player clears lines.

**Acceptance Criteria:**
- **Given** an active game session at level $L$,
- **When** a piece locks and clears $R$ rows (where $1 \leq R \leq 4$),
- **Then** the engine awards points to `score` immediately using the pre-lock level $L$ multiplier: 100 points for $R=1$, 300 points for $R=2$, 500 points for $R=3$, or 800 points for $R=4$ (multiplied by $L$).
- **And** the cleared rows are added to the cumulative count: `total_lines = total_lines + R`.
- **And** the current level is updated: `level = 1 + floor(total_lines / 10)`.
- **And** the gravity interval is updated: `gravity_interval_ms = max(100, 500 - 50 * (level - 1))`.
- **And** locking with 0 rows cleared awards 0 points and makes no state adjustments.
- **And** normal piece lock consumes the previewed `next_piece` and draws exactly one (1) new preview piece.

### Story 1.3: Soft Drop Score Exclusion and Terminal Immutability
As a Security Reviewer,
I want downward movements to grant no score and terminal states to be completely immutable,
So that scoring integrity is maintained and no post-gameover mutations occur.

**Acceptance Criteria:**
- **Given** an active game session,
- **When** a `POST /api/games/{id}/move` with direction `"down"` is processed,
- **Then** the active piece advances rows, but the score is NOT incremented (remains unchanged).
- **Given** a game session with status `"game_over"`,
- **When** any `POST` move/tick/hold request or `GET` request is received,
- **Then** the endpoint returns the exact current state unmodified and performs exactly zero (0) RNG draws.

---

## Epic 2: Next Piece Preview, Hold Slot, and API Route Extension (Backend)

### Story 2.1: Hold Slot Creation and Empty Hold Swap Endpoint
As a Player,
I want to hold my current piece in an empty slot to save it for later,
So that I can adapt my strategy based on the upcoming board layout.

**Acceptance Criteria:**
- **Given** a game with status `"playing"` and `hold_piece` set to `null` and `can_hold` set to `true`,
- **When** a `POST /api/games/{id}/hold` is executed,
- **Then** the current `active_piece.shape` is stored in the `hold_piece` slot.
- **And** the previewed `next_piece` is consumed to spawn as the new `active_piece` at its canonical template coordinates (e.g. `(0,4)` for O, `(0,3)` for other shapes).
- **And** exactly one (1) new random piece is drawn to populate the `next_piece` queue.
- **And** `can_hold` is set to `false` (locking the hold slot until the next piece locks).
- **And** the backend returns `200 OK` and the updated GameState payload.

### Story 2.2: Occupied Hold Swap Execution
As a Player,
I want to swap my current active piece with a previously held piece,
So that I can deploy my held piece strategically.

**Acceptance Criteria:**
- **Given** a game with status `"playing"`, `hold_piece` set to a shape code (e.g., `"J"`), and `can_hold` set to `true`,
- **When** a `POST /api/games/{id}/hold` is executed,
- **Then** the current `active_piece.shape` is stored in the `hold_piece` slot.
- **And** the former held shape `"J"` is spawned as the new `active_piece` at its canonical template coordinates (origin `(0,3)`).
- **And** the `next_piece` queue remains completely unchanged.
- **And** exactly zero (0) RNG draws are performed.
- **And** `can_hold` is set to `false`.
- **And** the backend returns `200 OK` and the updated GameState payload.

### Story 2.3: Hold Cooldown, Cooldown Rejections, and Clean Game Over
As a Developer,
I want hold swaps to be locked until a piece locks, and spawn obstructions to trigger clean game-overs,
So that players cannot double-hold, and game over leaves the board settled without illegal overlaps.

**Acceptance Criteria:**
- **Given** a game where `can_hold` is `false`,
- **When** a `POST /api/games/{id}/hold` is executed,
- **Then** the backend treats it as a valid no-op, returning `200 OK` and the unmodified current `GameState` with zero (0) RNG draws.
- **Given** a piece locks into the board normally,
- **Then** the backend resets `can_hold` to `true`.
- **Given** a normal piece spawn or retrieval from Hold is obstructed at its standard spawning coordinates,
- **When** the spawn is evaluated,
- **Then** the game status is immediately set to `"game_over"`.
- **And** the `active_piece` field is set to `null` (rather than returning illegal overlapping coordinates).

---

## Epic 3: Responsive Client HUD, Queue Mutation, and StrictMode Timer Coordination (Frontend)

### Story 3.1: Sidebar HUD Layout, Panels, and Hold Triggers
As a Player,
I want to see my Score, Lines, Level, Hold Slot, and Next Preview in real-time sidebars,
So that I can track my progress and plan my hold strategy during gameplay.

**Acceptance Criteria:**
- **Given** a running game session,
- **When** the game starts or receives a state update,
- **Then** the React UI displays panels for Score, Lines, Level, Hold Slot, and Next Preview.
- **And** the Hold Slot renders the held piece shape (or displays "Empty" if `null`).
- **And** the Hold Slot includes a visible "Hold" button which is disabled when `can_hold` is `false` or when `status === "game_over"`.
- **And** pressing the `C` key or clicking the "Hold" button enqueues a Hold mutation request.

### Story 3.2: Single Active Timer, FIFO Mutation Queue, and Timing Coordination
As a Developer,
I want all manual moves and ticks to be dispatched sequentially via a FIFO queue and schedule exactly one automatic timer at idle,
So that timer race conditions and double-tick intervals are prevented.

**Acceptance Criteria:**
- **Given** an active game session at idle,
- **Then** there is exactly one automatic timer running at `gravity_interval_ms`.
- **When** any mutation request is enqueued (manual move, hold, tick, restart),
- **Then** the active automatic timer is immediately canceled.
- **And** the mutation is processed in a strict FIFO queue without overlapping concurrent fetch requests.
- **And** after the very last queued response completes, the client schedules exactly one full current `gravity_interval_ms` timer.
- **And** if the final returned state is `"game_over"`, the timer is completely cleared and no timer remains.

### Story 3.3: Component Lifecycle, Token Validation, and Preemption
As a Developer,
I want components to track monotonically unique generation tokens and Restart to preempt the queue,
So that React StrictMode double effect runs or component unmounts do not cause stale state updates or timer double fires.

**Acceptance Criteria:**
- **Given** any component mount or session start under React StrictMode,
- **Then** the client generates a monotonically unique generation ID.
- **When** a fetch request, JSON parsing, or timer callback executes,
- **Then** it validates the active session token before updating state.
- **And** if the token does not match (due to unmount or obsolete session), the callback is ignored and does not mutate any variables. Falsy rejected values are ignored.
- **When** the "Restart" button is clicked,
- **Then** the client immediately preempts and discards the old mutation queue and clears any active timers, without waiting for pending fetch requests.

---

## Epic 4: Non-Rotational 3/4 Row Clear and End-to-End Quality Validation (Verification)

### Story 4.1: Non-Rotational O-Piece 3/4 Row Clear Domain Tests
As a Quality Assurance Engineer,
I want to verify 3-row and 4-row clears without implementing piece rotation by using canonical `"O"` pieces above precompleted bottom rows,
So that progression score calculations are verified with high integrity and minimal code footprint.

**Acceptance Criteria:**
- **Given** the standard `SHAPE_TEMPLATES` configuration (where O origin is `(0,4)`),
- **When** running a 3-row clear test (N=3), the backend precompletes rows 17, 18, and 19 as full rows, and leaves row 16 empty.
- **And** the O piece is locked at origin `(15,4)` with cells `(15,4), (15,5), (16,4), (16,5)` via downward move/tick.
- **Then** the engine clears exactly 3 rows, increments cumulative line count by 3, and awards 500 * level points.
- **When** running a 4-row clear test (N=4), the backend precompletes rows 16, 17, 18, and 19 as full rows, and leaves row 15 empty.
- **And** the O piece is locked at origin `(14,4)` with cells `(14,4), (14,5), (15,4), (15,5)` via downward move/tick.
- **Then** the engine clears exactly 4 rows, increments cumulative line count by 4, and awards 800 * level points.
- **And** all 13 original regression tests continue to pass completely unchanged.

### Story 4.2: Automated Coverage Instrumentation and Audit Compliance
As a Tech Lead,
I want automated coverage reports (FastAPI pytest XML and frontend LCOV) and production dependency audits to be fully clean,
So that code quality is verified and production vulnerabilities are resolved.

**Acceptance Criteria:**
- **Given** the backend codebase,
- **When** running backend tests with coverage,
- **Then** a `coverage.xml` file is generated, omitting test and application scaffolding files, and verifying >= 80% coverage on new backend code.
- **Given** the frontend React codebase,
- **When** running frontend tests,
- **Then** an all-source frontend LCOV report is generated including `main.tsx`.
- **When** running `npm audit`,
- **Then** all production dependencies are audited and resolved without critical vulnerabilities.

### Story 4.3: Sonar Quality Gate Compliance Integration
As a Release Manager,
I want the project to pass the dedicated Sonar Quality Gate checks under `tetris-stage2-bmad`,
So that the final 2.0 release is validated against the 1.0 baseline.

**Acceptance Criteria:**
- **Given** the Sonar scanner config,
- **When** the Sonar gate runs on `tetris-stage2-bmad`,
- **Then** it verifies that new code coverage is >= 80%, new duplication density is <= 3%, and new violations are exactly 0.
