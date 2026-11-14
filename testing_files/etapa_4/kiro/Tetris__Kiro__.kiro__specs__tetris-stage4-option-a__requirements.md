# Requirements Document

## Introduction

This document defines the functional scope for Stage 4, Option A, of a browser-based Tetris study. It is a brownfield extension of this tool's own final Stage 3, Option A implementation (the `backend/` FastAPI service and `frontend/` React + TypeScript client in this workspace), whose native specification lives under `.kiro/specs/tetris-stage3-option-a/`, which in turn extended Stage 2 under `.kiro/specs/tetris-stage2-option-a/` and Stage 1 under `.kiro/specs/tetris-stage1-option-a/`. All Stage 1, Stage 2, and Stage 3 behavior and contracts are the baseline and must be preserved; Stage 4 only adds the features described below and only supersedes an inherited behavior where this document says so explicitly.

Stage 4 adds three ordered milestones:

- **M1 (Rotation):** authoritative server-side 90-degree rotation of the active piece, clockwise and counter-clockwise, with deterministic pivots, exactly four orientations per piece, a horizontal-only wall-kick search, and single-player UI controls, exposed through the existing API conventions.
- **M2 (Canvas):** replacement of the main 10x20 React DOM cell board with a Canvas 2D rendering surface for the active and settled blocks, while keeping the React + TypeScript application and all accessible DOM controls, status, and panels.
- **M3 (WebSocket duel):** a two-player real-time duel over same-origin WebSockets, served by the same single FastAPI worker, with in-memory rooms holding independent private board states, kept fully separate from the inherited solo HTTP game stores and the solo SQLite leaderboard.

Stage 4 also plans, as specification-only statements of WHAT must hold, the testing, coverage, container, continuous-integration, performance-benchmark, and process-guardrail obligations described below.

This document describes WHAT must hold. It does **not** claim that any build, test, lint, audit, container run, container build, CI run, benchmark, approval, screenshot, token, cost, coverage number, duplication number, or any other metric has been executed, produced, measured, or approved. Any such value is produced only by an actual execution during a later phase, and this document asserts no such execution or result.

The inherited specifications under `.kiro/specs/tetris-stage1-option-a/`, `.kiro/specs/tetris-stage2-option-a/`, and `.kiro/specs/tetris-stage3-option-a/` must be preserved byte-for-byte and must not be edited by this stage.

### Relationship to Stage 3 (preserved baseline)

The following Stage 1, Stage 2, and Stage 3 facts are inputs and must not be changed by Stage 4 unless a Stage 4 requirement explicitly supersedes them. They are reproduced here so Stage 4 acceptance criteria can reference them precisely.

- **Stack:** a Python FastAPI backend that holds authoritative in-memory game state and rules, and a React + TypeScript frontend that renders backend state and forwards controls.
- **Board:** 20 rows by 10 columns. Row `0` is the top, row `19` is the bottom; column `0` is leftmost, column `9` is rightmost.
- **Pieces:** the seven standard tetrominoes `I`, `O`, `T`, `S`, `Z`, `J`, `L`.
- **Spawn origin and spawn geometry (`spawn0`):** every piece spawns at origin `(row 0, column 3)` with `SPAWN_ROW = 0` and `SPAWN_COLUMN = 3` in its initial orientation. Shapes are expressed as top-left-bounding-box-relative `(row, column)` offsets added to the origin. The `I` piece spawns on **row 0**: offsets `[(0,0),(0,1),(0,2),(0,3)]`. The other spawn offsets are `O = [(0,0),(0,1),(1,0),(1,1)]`, `T = [(0,1),(1,0),(1,1),(1,2)]`, `S = [(0,1),(0,2),(1,0),(1,1)]`, `Z = [(0,0),(0,1),(1,1),(1,2)]`, `J = [(0,0),(1,0),(1,1),(1,2)]`, `L = [(0,2),(1,0),(1,1),(1,2)]`. This `spawn0` geometry is authoritative and must be preserved; Stage 4 must not import a rotation table that assumes the `I` piece spawns on row 1.
- **Piece generator:** a seeded deterministic shuffled 7-bag; the same seed produces the same type sequence; exactly one preview piece is exposed.
- **Board serialization:** JSON `board` is a 20x10 array of integer codes, `0` = empty and `1..7` = settled block type codes (`I=1, O=2, T=3, S=4, Z=5, J=6, L=7`).
- **Active piece key:** the active piece is exposed under the key `active_piece` with `type`, `origin`, and `cells`.
- **Endpoints:** `POST /api/games` (returns HTTP 200, not 201), `GET /api/games/{id}`, `POST /api/games/{id}/tick`, `POST /api/games/{id}/move`, and `POST /api/games/{id}/hold` keep their existing request/response compatibility.
- **Status values:** `playing` and `game_over`.
- **State fields:** every solo state response includes `score`, `total_lines`, `level`, `gravity_interval_ms`, `next_piece`, `hold_piece`, and `can_hold` in addition to `id`, `status`, `board`, and `active_piece`.
- **Scoring and progression:** line-clear scoring is `100 / 300 / 500 / 800` multiplied by the pre-lock level for `1 / 2 / 3 / 4` cleared lines; `level = 1 + floor(total_lines / 10)`; gravity interval is `gravity_interval_ms = max(100, 500 - 50 * (level - 1))`; soft drop grants no points.
- **Hold:** a one-piece Hold with once-per-active-piece availability and a one-piece next preview.
- **Lock / clear / spawn ordering:** on a lock, the active piece settles into the board, completed lines are cleared, then scoring, level, and gravity are applied using the pre-lock level, then Hold is re-enabled for the next active piece, and only then is the next piece spawned.
- **Persistence:** completed-game high scores persist once-only to SQLite via the Python standard-library `sqlite3` module, keyed by `game_id` with a UNIQUE constraint, with error-retry on a later mutating request and HTTP 503 on storage failure; the leaderboard is `GET /api/high-scores` returning at most ten entries.
- **CORS:** a restrictive, configurable CORS policy that fails closed when a wildcard origin is combined with credentials.
- **Process model:** a single in-memory game worker; exactly one backend process owns in-memory games.
- **Frontend lifecycle safety:** generation tokens, per-generation FIFO serialization of mutating requests, a coalesced per-generation automatic-tick scheduler, dynamic gravity scheduling from `gravity_interval_ms`, and stale-response discarding after both `fetch` and `response.json()` resolve are preserved.

## Glossary

- **Backend / System:** the authoritative FastAPI service that owns all solo game state and rules, high-score persistence, and now the Stage 4 rotation engine and the duel rooms.
- **Frontend:** the React + TypeScript client that renders backend state and forwards controls, now rendering the main board on a Canvas surface and hosting a duel client.
- **Rotation_Engine:** the authoritative Python component that computes a new orientation and occupied cell set for the active piece on a clockwise or counter-clockwise rotation request.
- **Orientation:** one of the four discrete rotation states of a piece, indexed `0`, `1`, `2`, `3`, where `0` is the spawn orientation, `1` is one clockwise quarter-turn from spawn, `2` is a half-turn, and `3` is one counter-clockwise quarter-turn from spawn (equivalently three clockwise quarter-turns).
- **CW:** a clockwise 90-degree rotation, advancing the orientation index by one modulo four.
- **CCW:** a counter-clockwise 90-degree rotation, decreasing the orientation index by one modulo four.
- **Pivot:** the declared fixed reference cell about which a piece's four orientations are defined, such that each orientation is a rigid 90-degree turn of the previous one about that pivot.
- **Occupied cell set:** the exact set of four board cells a piece occupies in a given orientation at a given origin.
- **Wall kick:** the horizontal-only offset search applied after a raw rotation collides, testing candidate column offsets in the exact order `0, -1, +1, -2, +2` and accepting the first candidate whose occupied cell set fits the legal board and locked cells.
- **Locked cells:** the settled (non-active) blocks already recorded in the board.
- **Rejected rotation:** a rotation request for which the raw rotation and every wall-kick candidate collide, so the active piece's position and orientation are both left unchanged.
- **Canvas_Board:** the Stage 4 Canvas 2D rendering surface that draws the active and settled blocks of the main 10x20 board.
- **DPR:** the browser `devicePixelRatio`, the ratio of physical device pixels to CSS pixels.
- **Accessible DOM controls:** the non-canvas DOM elements for controls, score, level, lines, Hold, preview, leaderboard/ranking, restart, and game status that remain available to assistive technology.
- **Duel:** a two-player real-time match played over WebSockets in a single in-memory room, separate from solo HTTP games.
- **Room:** an in-memory duel container holding up to two seats and their independent private board states, with a bounded lifecycle.
- **Seat:** one of the two player positions in a room, each owning an independent private board state.
- **Board state (duel):** the per-seat authoritative duel game state, including that seat's board, active piece, queue, Hold, level, and gravity timing, never shared with the other seat except through broadcast state frames.
- **Wire contract:** the single, versioned, machine-readable message contract governing all duel WebSocket frames for handshake, action, state, acknowledgement, rejection, error, and terminal outcome.
- **Revision:** a monotonically increasing integer identifying an authoritative state version, used so a client can declare the exact revision an action targets.
- **Action ID:** a per-seat identifier a client assigns to an action so the server can acknowledge, reject, or report that exact action.
- **Monotonic clock:** a non-decreasing time source used for gravity scheduling and lifecycle timeouts, injectable in tests so time can be advanced deterministically.
- **Benchmark_Harness:** the performance measurement tool that drives the production Frontend in a real headful production Chrome channel, following this tool's own `perf/` convention.
- **Native spec/task note:** a dated file written on disk under this workspace that records a defect and the intended correction before any later code, test, configuration, or benchmark change is made.

## Requirements

<!-- =====================  MILESTONE M1: ROTATION  ===================== -->

### Requirement 1: Authoritative rotation action and API surface (M1)

**User Story:** As a player, I want to rotate the active piece clockwise and counter-clockwise, so that I can orient pieces to clear lines.

#### Acceptance Criteria

1. WHEN a client requests a clockwise rotation of a solo game whose status is `playing` and that has an active piece THEN the Rotation_Engine SHALL set the new orientation index to `(current_orientation_index + 1) mod 4`.
2. WHEN a client requests a counter-clockwise rotation of a solo game whose status is `playing` and that has an active piece THEN the Rotation_Engine SHALL set the new orientation index to `(current_orientation_index - 1) mod 4`.
3. WHEN a rotation request is accepted for a solo game THEN the System SHALL respond with HTTP 200, consistent with the inherited `POST /api/games/{id}/move` success convention.
4. WHEN a rotation request is accepted for a solo game THEN the response body SHALL be the same state shape as the inherited `POST /api/games/{id}/move` response, containing exactly the keys `id`, `status`, `board`, `active_piece`, `score`, `total_lines`, `level`, `gravity_interval_ms`, `next_piece`, `hold_piece`, and `can_hold`.
5. WHEN a rotation request names a direction THEN the System SHALL accept exactly two documented case-sensitive string values, one identifying clockwise rotation and one identifying counter-clockwise rotation, and SHALL reject any other string value.
6. IF a rotation request body omits the direction field, provides a string direction value other than the two documented values, provides a non-string direction value (a boolean, a number, an array, an object, or null), or includes any field beyond the documented rotation contract THEN the System SHALL respond with HTTP 422 and SHALL leave every authoritative game-state field unchanged.
7. IF a rotation request targets a game id that does not exist in the authoritative store THEN the System SHALL respond with HTTP 404 and SHALL leave every authoritative game-state field unchanged.
8. IF a rotation request targets a game whose status is `game_over` THEN the System SHALL leave the board, the active piece, the orientation, the score, the level, the line count, the queue, and the Hold availability unchanged and SHALL return the current terminal state with status `game_over`.
9. IF a rotation request targets a game whose `active_piece` is absent (null) at the moment the request is served THEN the System SHALL leave every authoritative game-state field unchanged and SHALL return the current state.
10. WHEN a rotation request is served THEN the visible text of any rotation-related label, status, or message SHALL be in English.

### Requirement 2: Four orientations with exact occupied cell sets (M1)

**User Story:** As a researcher, I want every piece's four orientations defined by exact occupied cells around a declared pivot, so that rotation is deterministic and independently verifiable.

#### Acceptance Criteria

1. WHEN the Rotation_Engine defines a piece type THEN it SHALL define exactly four orientations indexed `0`, `1`, `2`, and `3`, where orientation `0` equals that piece's inherited `spawn0` occupied cell set at the spawn origin `(row 0, column 3)`.
2. WHEN the Rotation_Engine defines each orientation of a non-`O` piece THEN each orientation SHALL be a rigid 90-degree turn of the adjacent orientation about that piece's single declared fixed pivot point (a fixed reference point that may be fractional, declared in the design as I = (1.5, 1.5), O = (0.5, 0.5), and T, S, Z, J, L = (1, 1)), preserving the four-cell shape without reflection or scaling.
3. WHEN the Rotation_Engine applies four successive clockwise quarter-turns to a non-`O` piece with no intervening collision, movement, or lock THEN the resulting orientation index SHALL equal the starting orientation index and the resulting occupied cell set SHALL equal the starting occupied cell set.
4. WHEN the Rotation_Engine rotates the `O` piece clockwise or counter-clockwise THEN the resulting occupied cell set SHALL be identical to the `O` piece's occupied cell set immediately before the request, so that `O` rotation is a no-op in both directions.
5. WHEN the Rotation_Engine defines the four orientations of the `I` piece THEN each orientation SHALL be derived explicitly from the inherited `spawn0` geometry in which the `I` piece occupies row `0` with offsets `[(0,0),(0,1),(0,2),(0,3)]`, and the Rotation_Engine SHALL NOT substitute any rotation table that assumes the `I` piece spawns on row `1`.
6. WHEN the Rotation_Engine computes an occupied cell set for any orientation at any origin THEN the result SHALL contain exactly four cells, all distinct, and each within rows `0` through `19` and columns `0` through `9` when the origin places the piece inside the board.
7. WHEN the Rotation_Engine applies a clockwise rotation immediately followed by a counter-clockwise rotation with no intervening collision, movement, or lock THEN the resulting orientation index and occupied cell set SHALL equal the pre-rotation orientation index and occupied cell set.
8. WHEN the Rotation_Engine defines each orientation THEN the definition SHALL be recorded as a declared data table of occupied cells or of offsets from the declared pivot, so that each orientation's expected cells can be asserted independently of the rotation algorithm under test.

### Requirement 3: Horizontal wall-kick search (M1)

**User Story:** As a player, I want rotation near walls, the floor, and settled blocks to try small horizontal nudges, so that rotation succeeds when a simple shift makes room.

#### Acceptance Criteria

1. WHEN a raw rotation's occupied cell set lies fully within columns `0` through `9` and rows `0` through `19` and overlaps no locked cell THEN the Rotation_Engine SHALL accept that rotation with a column offset of `0` and SHALL apply no further kick offset.
2. IF a raw rotation's occupied cell set lies partly outside columns `0` through `9` or rows `0` through `19`, or overlaps any locked cell THEN the Rotation_Engine SHALL evaluate candidate column offsets in the exact order `0, -1, +1, -2, +2`.
3. WHEN the Rotation_Engine evaluates a wall-kick candidate THEN it SHALL offset the rotated occupied cell set only along columns and SHALL apply no row offset.
4. WHEN the Rotation_Engine evaluates the candidate offsets in the order `0, -1, +1, -2, +2` THEN it SHALL accept the first candidate whose occupied cell set lies fully within columns `0` through `9` and rows `0` through `19` and overlaps no locked cell, and SHALL NOT evaluate or select any later candidate once one is accepted.
5. IF the raw rotation and every candidate offset in the order `0, -1, +1, -2, +2` lie partly outside the board or overlap a locked cell THEN the rotation SHALL be a rejected rotation.
6. WHEN a wall-kick candidate is accepted THEN the Rotation_Engine SHALL set the active piece's orientation index to the rotated orientation and set its origin to the accepted kicked origin, so that subsequent movement and locking proceed from the accepted rotated geometry.

### Requirement 4: Rejected rotation immutability (M1)

**User Story:** As a researcher, I want a fully rejected rotation to change nothing, so that a blocked rotation never leaks side effects.

#### Acceptance Criteria

1. WHEN a rotation is a rejected rotation THEN the System SHALL leave the active piece's origin and orientation index equal to their pre-request values.
2. WHEN a rotation is a rejected rotation THEN the System SHALL NOT lock the active piece and SHALL NOT advance gravity or settle the active piece downward.
3. WHEN a rotation is a rejected rotation THEN the System SHALL leave the `gravity_interval_ms` value and the automatic-tick schedule unchanged.
4. WHEN a rotation is a rejected rotation THEN the System SHALL leave the `score`, `level`, `total_lines`, `next_piece`, `hold_piece`, and `can_hold` values equal to their pre-request values.
5. WHEN a rotation is a rejected rotation THEN the System SHALL return the pre-request state with its `status` unchanged.

### Requirement 5: Rotation side-effect isolation (M1)

**User Story:** As a researcher, I want even a successful rotation to change only orientation and position, so that rotation is cleanly separated from gravity, locking, scoring, and queue management.

#### Acceptance Criteria

1. WHEN a rotation is accepted THEN the System SHALL NOT lock the active piece as a result of the rotation alone.
2. WHEN a rotation is accepted THEN the System SHALL NOT advance gravity or settle the active piece downward as a result of the rotation alone.
3. WHEN a rotation is accepted THEN the System SHALL leave the `score`, `level`, `total_lines`, `next_piece`, `hold_piece`, and `can_hold` values equal to their pre-request values.
4. WHEN a rotation is accepted THEN the only authoritative fields the System SHALL change are the active piece's orientation index and, where a wall kick was applied, its origin.

### Requirement 6: Spawn orientation and Hold interaction (M1)

**User Story:** As a player, I want pieces to enter play in their spawn orientation, including from Hold, so that orientation is predictable.

#### Acceptance Criteria

1. WHEN a piece enters play from the piece queue THEN it SHALL enter with orientation index `0` at the inherited spawn origin `(row 0, column 3)`.
2. WHEN a piece enters play because it is retrieved from Hold THEN it SHALL enter with orientation index `0` at the inherited spawn origin `(row 0, column 3)`, regardless of the orientation index it held before being placed into Hold.
3. WHEN a piece is placed into Hold through the first-Hold path (no piece previously held) THEN the piece that enters play SHALL enter with orientation index `0`.
4. WHEN a piece is placed into Hold through the swap-Hold path (a piece was previously held) THEN the piece swapped into play SHALL enter with orientation index `0`.
5. WHEN a piece is retrieved from Hold THEN the inherited once-per-active-piece Hold availability rule SHALL continue to apply unchanged, so that `can_hold` becomes false for the entering active piece until the next active piece.

### Requirement 7: Rotated geometry under movement and locking (M1)

**User Story:** As a player, I want a rotated piece to keep its shape as it moves and locks, so that rotation integrates correctly with gameplay.

#### Acceptance Criteria

1. WHEN a rotated active piece moves left, right, or down THEN the System SHALL leave the orientation index unchanged and SHALL translate every cell of the rotated occupied cell set by the move delta.
2. WHEN a rotated active piece locks THEN the System SHALL settle the rotated occupied cell set into the board and SHALL then apply the inherited lock, line-clear, scoring, level, gravity, Hold-re-enable, and spawn ordering unchanged.
3. WHEN an automatic gravity tick applies to a rotated active piece whose downward step is blocked THEN the System SHALL lock the active piece and SHALL NOT change the orientation index.
4. WHEN a soft drop is applied to a rotated active piece THEN the System SHALL grant exactly zero points, consistent with the inherited soft-drop scoring rule.

### Requirement 8: Single-player rotation controls in the UI (M1)

**User Story:** As a player, I want keyboard and on-screen rotation controls, so that I can rotate pieces in the single-player view.

#### Acceptance Criteria

1. WHEN the player presses the `ArrowUp` key while the solo game status is `playing` THEN the Frontend SHALL issue exactly one clockwise rotation request bound to the current game generation per key-down event.
2. WHEN the player presses the `Z` key or the `z` key while the solo game status is `playing` THEN the Frontend SHALL issue exactly one counter-clockwise rotation request bound to the current game generation per key-down event.
3. WHEN the Frontend renders on-screen controls THEN it SHALL provide one accessible clockwise rotation control and one accessible counter-clockwise rotation control, each reachable by assistive technology.
4. WHEN an accessible rotation control is activated THEN the Frontend SHALL issue exactly one corresponding rotation request bound to the current game generation per activation.
5. WHEN a rotation request is issued THEN the Frontend SHALL enqueue it on the inherited per-generation FIFO queue and SHALL discard any rotation response whose generation does not match the current generation, applying the inherited stale-response protection.
6. IF the solo game status is not `playing` THEN the Frontend SHALL NOT issue a rotation request from the `ArrowUp` key, the `Z` or `z` key, or either on-screen rotation control.
7. WHEN the rotation controls are present THEN the Frontend SHALL preserve the inherited left, right, soft-drop, Hold, and restart controls unchanged, SHALL NOT create a competing scheduler or a second queue but instead reuse the inherited manual-action timeout ownership and reconciliation by cancelling the exact current-generation pending automatic tick at dispatch and scheduling at most one replacement automatic tick from the authoritative `gravity_interval_ms` (or none on a terminal result), and SHALL NOT itself tick, lock, change `gravity_interval_ms`, or consume RNG while preserving the inherited stale-response, generation, and coalescing protection.

### Requirement 9: Independently-expected rotation tests (M1)

**User Story:** As a researcher, I want rotation covered by tests whose expectations are independent of the implementation, so that rotation correctness is trustworthy.

#### Acceptance Criteria

1. WHEN Stage 4 rotation tests are authored THEN they SHALL assert the exact occupied cell set of every orientation index `0` through `3` of every piece type using independently-declared expected cells rather than values produced by the rotation algorithm under test.
2. WHEN Stage 4 rotation tests are authored THEN they SHALL assert that four successive clockwise quarter-turns and, separately, four successive counter-clockwise quarter-turns each return every piece type to its orientation `0` occupied cell set.
3. WHEN Stage 4 rotation tests are authored THEN they SHALL assert that the `O` piece rotation is a no-op in both directions and that the `I` piece uses the `spawn0` row-`0` geometry in all four orientations.
4. WHEN Stage 4 rotation tests are authored THEN they SHALL cover a wall kick against the left wall, against the right wall, against the floor, and against locked cells, including a case where the first fitting candidate in the order `0, -1, +1, -2, +2` is selected over a later fitting candidate.
5. WHEN Stage 4 rotation tests are authored THEN they SHALL cover a fully rejected rotation and SHALL assert that the origin, orientation index, `gravity_interval_ms`, `score`, `level`, `total_lines`, `next_piece`, `hold_piece`, and `can_hold` are each unchanged.
6. WHEN Stage 4 rotation tests are authored THEN they SHALL cover a rotation request against a `game_over` game and a rotation request against a game whose `active_piece` is absent, asserting that no authoritative state field changes.
7. WHEN Stage 4 rotation tests are authored THEN they SHALL assert HTTP 422 rejection for a missing-direction payload, a non-string-direction payload, and an extra-field payload.
8. WHEN Stage 4 frontend rotation tests are authored THEN they SHALL exercise a real `ArrowUp` key event, a real `Z` key event, and activation of each on-screen rotation control, and SHALL NOT assert rotation solely through internal function calls.

<!-- =====================  MILESTONE M2: CANVAS  ===================== -->

### Requirement 10: Canvas board rendering (M2)

**User Story:** As a player, I want the main board drawn on a Canvas, so that rendering is efficient while gameplay looks the same.

#### Acceptance Criteria

1. WHEN the Frontend renders the main 10x20 board THEN it SHALL render the board on a Canvas 2D surface and SHALL NOT render the main board as a grid of per-cell React DOM elements.
2. WHEN the Canvas_Board draws the board THEN it SHALL draw the settled blocks using the inherited per-type colors and SHALL draw the active piece using its type color so that active and settled blocks are visually distinguishable.
3. WHEN the Canvas_Board draws the active piece THEN it SHALL draw the active piece's rotated occupied cell set at its current origin, consistent with the authoritative `active_piece` returned by the backend.
4. WHEN the backend reports a board state THEN the Canvas_Board SHALL draw exactly the 200 cells described by that state, mapping board code `0` to empty and codes `1..7` to the corresponding type colors.
5. WHEN the Stage 4 Frontend is built THEN it SHALL remain a React + TypeScript application.

### Requirement 11: Canvas redraw triggers and device pixel ratio (M2)

**User Story:** As a player, I want the Canvas to stay correct after every state change and on resize, so that the view never shows a stale or blurry board.

#### Acceptance Criteria

1. WHEN the active piece rotates, moves, or the board changes through a gravity tick THEN the Canvas_Board SHALL redraw to reflect the new authoritative state.
2. WHEN the active piece locks, a line clears, or the game restarts THEN the Canvas_Board SHALL redraw to reflect the new authoritative state.
3. WHEN the pixel width or the pixel height of the Canvas_Board's layout box changes from its previously measured value THEN the Canvas_Board SHALL recompute its backing-store size and redraw so that the board is neither stretched nor clipped.
4. WHEN the Canvas_Board sizes its backing store THEN it SHALL account for the device pixel ratio so that the board renders crisply at `DPR` `1` and at `DPR` `2`.
5. WHEN the device pixel ratio is `1` or `2` THEN the Canvas_Board SHALL render the full 10x20 board within its layout box without clipping any of the 200 cells.
6. WHEN the Canvas_Board redraws THEN it SHALL draw from the current authoritative state and SHALL NOT leave residual pixels from a prior state within the board area.

### Requirement 12: Preserved accessible controls and panels (M2)

**User Story:** As a player using assistive technology, I want the controls and information panels to remain accessible DOM, so that the Canvas does not remove accessibility.

#### Acceptance Criteria

1. WHEN the Canvas_Board replaces the DOM cell grid THEN the Frontend SHALL keep accessible DOM controls for left, right, soft drop, clockwise rotation, counter-clockwise rotation, Hold, and restart.
2. WHEN the Frontend renders status information THEN it SHALL keep accessible DOM elements for the score, the level, the line count, the Hold piece, the next-piece preview, the leaderboard or ranking, and the game status.
3. WHEN the Canvas_Board is present THEN the Frontend SHALL provide an accessible text alternative or status region so that the game status does not depend solely on the Canvas pixels.
4. WHEN the Frontend keyboard controls are used THEN they SHALL behave exactly as in the inherited stage for left, right, soft drop, Hold, and restart, plus the Stage 4 rotation keys.
5. WHEN the Canvas_Board is added THEN the Frontend SHALL preserve the inherited per-generation FIFO serialization and the inherited stale-response protection.

### Requirement 13: Preserved solo contract and persistence under Canvas (M2)

**User Story:** As a researcher, I want the Canvas change to be a rendering change only, so that the solo HTTP contract and persistence are unaffected.

#### Acceptance Criteria

1. WHEN the Canvas_Board is introduced THEN the solo HTTP contract (`POST /api/games`, `GET /api/games/{id}`, `POST /api/games/{id}/tick`, `POST /api/games/{id}/move`, `POST /api/games/{id}/hold`, and the rotation action) SHALL remain unchanged.
2. WHEN the Canvas_Board is introduced THEN the SQLite high-score persistence and the once-only terminal finalization SHALL remain unchanged.
3. WHEN the Canvas_Board is introduced THEN the leaderboard endpoint `GET /api/high-scores` and its ordering and shape SHALL remain unchanged.
4. WHEN the Canvas_Board is introduced THEN the backend SHALL remain the single authoritative owner of all game state and rules, and the Canvas SHALL render only backend-reported state.

### Requirement 14: Canvas rendering tests and pixel evidence (M2)

**User Story:** As a researcher, I want Canvas rendering verified by real pixels and honest fixtures, so that rendering claims are evidence-based.

#### Acceptance Criteria

1. WHEN Stage 4 native unit fixtures verify the Canvas_Board THEN they MAY verify renderer draw calls, context setup and cleanup, and safe behavior when the 2D context is absent.
2. WHEN Stage 4 asserts that the Canvas displays a state correctly THEN mock draw-call records and DOM data attributes SHALL NOT be treated as pixel evidence.
3. WHEN Stage 4 provides pixel evidence THEN it SHALL capture actual rendered pixel masks or screenshots from the unmodified production bundle tied to meaningful authoritative states, including a spawned piece, a rotated piece, a moved piece, a locked piece, and a cleared-line state.
4. WHERE an authoritative state such as a multi-line clear is hard to reach through ordinary play THEN Stage 4 SHALL drive the production clear path with an explicitly-declared isolated fixture and SHALL NOT claim that the fixture API is the production backend.
5. WHEN Stage 4 documents the Canvas migration THEN it SHALL identify which inherited DOM-cell assertions are superseded by the Canvas rendering and SHALL replace their semantic coverage with Canvas rendering evidence.
6. WHEN Stage 4 captures pixel evidence THEN it SHALL NOT introduce production debug hooks, backend-state injection hooks, or network interception into the production bundle.

### Requirement 15: Solo layout usability and relationship to duel (M2)

**User Story:** As a player, I want the solo view usable at the benchmark viewport, so that the board is fully visible without clipping or overlap.

#### Acceptance Criteria

1. WHEN the solo view is displayed at a `1280x900` viewport THEN every part of the 10x20 board SHALL lie within the viewport and no control or panel element SHALL overlap another control or panel element.
2. WHEN a duel is active THEN the solo view SHALL remain reachable, and the layout SHALL NOT require that three boards render simultaneously.
3. WHEN the solo and duel views coexist in the application THEN the Frontend SHALL present the solo single-player view as a distinct, independently usable view.

<!-- =====================  MILESTONE M3: WEBSOCKET DUEL  ===================== -->

### Requirement 16: Duel transport, rooms, and worker model (M3)

**User Story:** As a player, I want a two-player real-time duel over WebSockets, so that two people can play at the same time against each other.

#### Acceptance Criteria

1. WHEN two players start a duel THEN the System SHALL connect them over same-origin WebSockets served by the same single FastAPI worker that serves the solo HTTP API.
2. WHEN a duel is created THEN the System SHALL hold the match in an in-memory Room with up to two Seats, each owning an independent private Board state.
3. WHEN a duel Board state exists THEN the System SHALL keep each Seat's Board state private, sharing another Seat's state only through broadcast state frames defined by the wire contract.
4. WHEN a duel is played THEN the System SHALL NOT register the duel game in the solo HTTP game stores and SHALL NOT expose a duel game through the solo `GET /api/games/{id}` endpoint.
5. WHEN a duel is played THEN the System SHALL NOT persist any duel game, Seat, or outcome in the solo SQLite database and SHALL NOT add a duel entry to the solo leaderboard.
6. WHILE a duel is in progress, THE System SHALL preserve solo play so that solo HTTP games continue to work independently of the duel.

### Requirement 17: Duel seat seeding and independent progression (M3)

**User Story:** As a player, I want both duel boards to start fairly and then progress independently, so that each player controls their own game.

#### Acceptance Criteria

1. WHEN a Room has fewer than two connected Seats THEN the System SHALL NOT start the duel and SHALL hold the Room in a waiting state.
2. WHEN both Seats are connected THEN the System SHALL start exactly two distinct Seats, each beginning with this tool's same initial seeded 7-bag sequence.
3. WHEN the duel has started THEN each Seat SHALL advance its piece queue, its first-Hold availability, its Hold swap, and its lock consumption independently of the other Seat.
4. WHEN the duel uses seeded sequences THEN the System SHALL NOT share a global random generator in a way that alters the solo seeded sequence or couples the two Seats' advancement.
5. WHEN a Seat performs a move, rotation, soft drop, Hold, or lock THEN that action SHALL affect only that Seat's private Board state.

### Requirement 18: Per-board server-side gravity (M3)

**User Story:** As a player, I want each board's gravity to run on the server independently, so that neither player's timing depends on the other.

#### Acceptance Criteria

1. WHEN the duel runs THEN the System SHALL apply gravity on the server independently per Board, using a per-Board due time derived from that Board's level and the inherited gravity formula `gravity_interval_ms = max(100, 500 - 50 * (level - 1))`.
2. WHEN the System evaluates gravity THEN it SHALL advance only Boards whose per-Board due time has elapsed on the Monotonic clock.
3. WHEN the System evaluates an outcome after advancing gravity THEN it SHALL evaluate ALL due Boards before deciding a single outcome, so that a simultaneous top-out of both Boards within the same evaluation is a DRAW.
4. WHEN exactly one Board remains playable after an evaluation THEN the System SHALL declare the surviving Seat the winner.
5. WHEN an active Seat disconnects while the duel is in progress THEN the System SHALL treat that disconnect as a forfeit that resolves the duel exactly once and SHALL NOT resolve the same duel a second time on a later event.
6. WHEN the duel reaches a terminal outcome THEN the System SHALL emit the terminal outcome through the wire contract and SHALL stop advancing that Room's gravity.

### Requirement 19: Room lifecycle, cleanup, and concurrency (M3)

**User Story:** As an operator, I want rooms cleaned up safely and concurrency bounded, so that the single worker stays responsive and memory is bounded.

#### Acceptance Criteria

1. WHEN the System manages Rooms THEN it SHALL run a bounded lifecycle and idle-cleanup process periodically, and that cleanup SHALL run even when no new traffic arrives.
2. WHEN the System defines retention THEN it SHALL define a finished-Room retention policy distinct from a waiting or inactive-Room retention policy, each with a bounded maximum lifetime.
3. WHEN a Room is cancelled, has a slow peer, has a failed send, or the server shuts down THEN the System SHALL release that Room's resources and SHALL NOT leak a Room, a task, or a socket.
4. WHEN the System schedules gravity or lifecycle timeouts THEN it SHALL use the Monotonic clock, and that clock SHALL be injectable so tests can advance time deterministically.
5. WHEN the System mutates a Room's state THEN it SHALL hold a short per-Room state lock to take a consistent snapshot, and it SHALL perform bounded, ordered outbound I/O OUTSIDE that lock.
6. WHEN the System performs outbound I/O THEN it SHALL NOT hold a global lock that a slow or blocked peer can stall, so that one peer cannot block the whole worker.
7. WHEN a player restarts after a duel THEN the System SHALL treat the restart as a fresh Room or a fresh solo game and SHALL NOT reuse the finished Room's state.

### Requirement 20: Versioned duel wire contract (M3)

**User Story:** As a client developer, I want a single consistent versioned wire contract, so that handshake, actions, state, acknowledgements, errors, and outcomes are unambiguous.

#### Acceptance Criteria

1. WHEN the duel defines its message protocol THEN it SHALL define a SINGLE consistent wire contract carrying an explicit protocol version and covering handshake, action, state, acknowledgement, rejection, error, and terminal-outcome messages.
2. WHEN the wire contract defines revisions THEN it SHALL resolve how a Room-level or event-level revision relates to a per-Board revision, so that a client can tell which revision a state or acknowledgement refers to.
3. WHEN a client sends an action THEN the action SHALL carry a per-Seat Action ID that is independent of the revision, and the server SHALL reference that exact Action ID in the corresponding acknowledgement or rejection.
4. WHEN a client sends an action with an expected revision THEN the server SHALL require strict EQUALITY between the expected revision and the authoritative target-Board revision, and SHALL reject an action whose expected revision does not exactly equal the authoritative revision.
5. WHEN the server receives a duplicate action (an Action ID already processed) THEN it SHALL NOT apply the action twice and SHALL acknowledge or reject it idempotently, using a bounded per-Seat idempotency structure consisting of a monotonic high-water mark of the highest accepted Action ordinal plus a bounded reply cache of at most the 256 most-recent Action IDs and their replies: a duplicate Action ID still in the reply cache SHALL return its cached reply unchanged; a duplicate Action ID whose ordinal is at or below the high-water mark but has been evicted from the reply cache SHALL be rejected (never re-applied and never accepted as a new Action); and an Action ID whose ordinal is strictly greater than the high-water mark SHALL be treated as a new Action, so that losing a reply-cache entry can never cause a second application of an already-processed Action nor silently accept a changed-content reused Action ID as new.
6. WHEN the server receives an action whose expected revision is lower than the authoritative revision (a stale input) THEN it SHALL reject the action as stale without mutating the Board.
7. WHEN the server receives an action whose expected revision is higher than the authoritative revision (a future input) THEN it SHALL reject the action as not-yet-valid without mutating the Board.
8. WHEN the server applies an action that produces no legal change (a no-op, such as a fully rejected rotation) THEN it SHALL acknowledge the action and SHALL report that it produced no state change rather than inventing a change.
9. WHEN a state frame or an acknowledgement is emitted THEN it SHALL identify the authoritative revision and the target Board (Seat) it refers to, so that a later input-to-Canvas effect and the opponent-Canvas timing can be correlated.
10. WHEN the server receives an action for a Seat the sender does not own THEN it SHALL reject the action and SHALL NOT mutate the targeted Board.
11. IF a received message has a field of the wrong type (a boolean, string, or float where another type is required), is missing a required field, or carries an extra undocumented field THEN the server SHALL reject the message and SHALL NOT mutate any Board.
12. IF the server receives an APPLICATION-VISIBLE malformed message (invalid JSON, a missing / wrong-typed / non-canonical uncorrelatable `action_id`, or an in-band BINARY payload such as a browser `Uint8Array` binary frame) THEN the server SHALL answer with a schema-valid error message carrying the `malformed_message` reason (which carries no `action_id` and leaks no filesystem path, SQL text, exception or class name, or stack trace) and SHALL NOT mutate any Board; a wire-level invalid-UTF8 TEXT frame rejected by the WebSocket transport BEFORE the application receives a decoded message is NOT this application-visible case and is instead governed by Requirement 22 item 5 (standard close code 1007).

### Requirement 21: Wire contract field definitions and schema validity (M3)

**User Story:** As a client developer, I want every wire field precisely defined and the schema machine-readable, so that both clients and the server agree on the contract.

#### Acceptance Criteria

1. WHEN the wire contract defines a message THEN it SHALL define every required field with its name, type, allowed range, and nullability for handshake, action, state, acknowledgement, rejection, error, and terminal-outcome messages, including explicit SAFE integer upper bounds so that no JS-imprecise magnitude is accepted: `revision`, `expected_revision`, `score`, `total_lines`, and each `final_revision` Seat value SHALL range 0 through 9007199254740991 (2^53 - 1, the largest integer exactly representable as an IEEE-754 double); `level` SHALL range 1 through 100000; and `gravity_interval_ms` SHALL range 100 through 500 inclusive, consistent with the inherited formula `max(100, 500 - 50 * (level - 1))`.
2. WHEN the wire contract defines a Board state frame THEN the `board`, active-piece, queue or preview, and Hold fields SHALL be consistent with the existing solo wire schema, using the same board code mapping (`0` empty, `1..7` type codes) and the same active-piece `type`, `origin`, and `cells` shape, WHERE the active-piece `origin` is an anchor coordinate whose row ranges -4 through 19 and column ranges -3 through 9 (so that a valid negative anchor is expressible) AND each occupied `cells` entry is an absolute on-Board cell whose row ranges 0 through 19 and column ranges 0 through 9, AND `cells` SHALL contain exactly four DISTINCT cells; FURTHERMORE the state frame SHALL carry a non-null active-piece exactly when `status` is `playing` and a null active-piece when `status` is `game_over`.
3. WHEN the wire contract publishes schemas or examples THEN they SHALL be valid machine-readable JSON with no placeholders, no ellipsis, and no pipe-delimited enum strings standing in for real values.
4. WHEN the wire contract defines an enumerated field THEN it SHALL enumerate the allowed values explicitly as valid JSON values.
5. WHEN the wire contract defines a terminal-outcome message THEN it SHALL define the win, loss, draw, and forfeit outcomes explicitly with the fields that identify the winning or forfeiting Seat, enforcing that a `win` names two DISTINCT Seats as winner and loser with a null forfeiter, a `draw` leaves winner, loser, and forfeiter all null, and a `forfeit` sets the loser equal to the forfeiter and the winner to the other surviving Seat distinct from the forfeiter.
6. WHEN the wire contract defines an error or rejection message THEN it SHALL define a stable set of machine-readable reason codes and SHALL NOT leak a filesystem path, SQL text, an exception or class name, or a stack trace.
7. WHEN an APPLICATION-VISIBLE malformed inbound message is received (invalid JSON, a missing / wrong-typed / non-canonical uncorrelatable `action_id`, or an in-band BINARY payload) THEN the server SHALL answer with a schema-valid error message carrying the `malformed_message` reason; WHERE a TEXT frame's payload is not valid UTF-8 and is rejected by the WebSocket transport BEFORE the application receives a decoded message, THE server SHALL instead fail the connection at the transport layer per Requirement 22 item 5 (standard close code 1007) and SHALL NOT be required to emit an application-controlled error message or an exact application-controlled reason string for that transport-level case.

### Requirement 22: Duel origin, bounds, close codes, and WS engine (M3)

**User Story:** As an operator, I want the duel socket origin-checked, bounded, and backed by a real WebSocket engine, so that it is safe and actually works behind the proxy.

#### Acceptance Criteria

1. WHEN the server receives a WebSocket upgrade request THEN it SHALL validate the request Origin against an exact allow-list bound to the actual proxy host and port (`http://localhost:5517` and `http://127.0.0.1:5517` by default, configurable and fail-closed like the inherited restrictive CORS posture), and SHALL deny a disallowed Origin at the HTTP upgrade before any WebSocket is established, so that a denied Origin never becomes a WebSocket connection and receives no WebSocket CLOSE frame.
2. WHEN the duel is served behind the reverse proxy THEN the Nginx configuration SHALL preserve the proxy host AND the proxy port (`5517`) through to the backend worker so that the same-origin WebSocket URL reaches it.
3. WHEN the server defines limits THEN it SHALL bound these to exact values: Room ID length 1..64 characters, maximum inbound UTF-8 message size 4096 bytes, inbound action rate 20 actions per second per Seat, maximum concurrent Rooms 100, per-Seat outbound queue depth 64 frames, handshake timeout 10 seconds, idle timeout 60 seconds, finished-Room retention 15 seconds, and waiting/inactive-Room retention 120 seconds.
4. IF an inbound message exceeds the maximum size, violates the rate limit, or the Room count is at its maximum THEN the System SHALL reject the message or connection using a defined close code or rejection reason and SHALL NOT exhaust worker memory; WHERE the malformed input is an APPLICATION-VISIBLE malformed JSON message, an uncorrelatable / missing / wrong-typed / non-canonical `action_id`, or an in-band BINARY payload, THE server SHALL answer with a schema-valid error message carrying the `malformed_message` reason, WHEREAS a wire-level invalid-UTF8 TEXT frame rejected by the WebSocket transport BEFORE the application receives a decoded message SHALL be failed at the transport layer with standard close code 1007 (per item 5) and SHALL NOT require an application-controlled JSON reply.
5. WHEN the server closes a WebSocket THEN it SHALL use a defined standard close code for each close reason, mapping normal completion to 1000, policy or Origin violation to 1008, an oversize (message-too-big) message to 1009, a rate-limit violation to 1008 with a `rate_limited` reason, and idle timeout, handshake timeout, and server shutdown each to 1001 (going away); two reasons MAY deliberately share the standard going-away code provided they remain distinguished by their accompanying close reason semantics; FURTHERMORE WHERE a TEXT frame's payload is not valid UTF-8, THE server SHALL fail the WebSocket connection with the standard close code 1007 (invalid payload data for the message type) and a library-managed BOUNDED reason, consistent with RFC 6455 §8.1 (fail the connection on invalid UTF-8) and §7.4.1 (code 1007), and SHALL NOT be required to supply an exact application-controlled reason string for that library-generated close; WHERE such a 1007 transport close occurs in a STARTED Room, THE server SHALL apply the ordinary disconnect / forfeit / once-only cleanup to the remaining peer, and WHERE it occurs in a waiting Room with a single occupant, THE server SHALL fabricate no gameplay winner.
6. WHEN duel tests assert a close THEN they SHALL drain the queued handshake, state, and error frames before asserting that the socket reached a CLOSE state, so that a close assertion does not race ahead of deliverable frames.
7. WHEN the production server runs under uvicorn THEN the deployment SHALL include an actual WebSocket protocol engine dependency that implements uvicorn's WebSocket upgrade, and the specification SHALL NOT treat `anyio` alone as satisfying the WebSocket upgrade requirement.
8. WHEN later M3 duel tests exercise invalid-UTF8 handling THEN they SHALL include a PUBLIC test that sends a raw masked TEXT frame carrying byte `0xFF` and expects a transport close with standard close code 1007, DISTINCT from a browser binary `Uint8Array` `0xFF` frame (an application-visible BINARY payload) which expects the `malformed_message` error path.

### Requirement 23: Duel separation and preserved solo posture (M3)

**User Story:** As a researcher, I want duel results isolated from solo, so that the inherited leaderboard and CORS posture stay intact.

#### Acceptance Criteria

1. WHEN a duel finishes THEN its result SHALL remain separate from the inherited solo leaderboard and SHALL NOT appear in `GET /api/high-scores`.
2. WHEN the duel feature is added THEN the inherited restrictive HTTP CORS policy SHALL be retained unchanged for the solo HTTP API.
3. WHEN the duel feature is added THEN the System SHALL NOT delete, move, or clear solo SQLite data outside its own declared temporary test fixtures.
4. WHEN the duel feature is added THEN the solo SQLite persistence and the once-only terminal finalization SHALL remain unchanged.

<!-- =====================  TESTING, COVERAGE, AND INFRASTRUCTURE  ===================== -->

### Requirement 24: Regression preservation and coverage reporting

**User Story:** As a researcher, I want inherited tests preserved and new code covered, so that Stage 4 does not regress and its hard paths are exercised.

#### Acceptance Criteria

1. WHEN Stage 4 is implemented THEN all inherited Stage 1, Stage 2, and Stage 3 backend and frontend regression assertions SHALL continue to pass unchanged, including the inherited request-ordering, lifecycle, persistence, and leaderboard assertions.
2. WHEN Stage 4 reports backend coverage THEN it SHALL produce a backend coverage report in XML form covering all executable backend modules, including the rotation, duel-room, gravity, cleanup, wire-contract, and error branches.
3. WHEN Stage 4 reports frontend coverage THEN it SHALL produce a frontend coverage report in LCOV form covering all executable frontend modules, including the Canvas rendering, resize, rotation-control, duel-client, and API branches.
4. WHEN Stage 4 reports coverage THEN the reports SHALL exercise error, race, cleanup, resize, and API branches rather than only the happy path.
5. WHEN Stage 4 evaluates its independent Sonar analysis THEN NEW-code coverage of at least `80` percent, code duplication of at most `3` percent, and `0` new static-analysis findings SHALL each be a SEPARATE outcome, and passing the coverage outcome SHALL NOT be treated as proof that the overall quality gate passed.
6. WHEN a milestone completes THEN Stage 4 SHALL check coverage after that milestone and SHALL NOT weaken thresholds, add production-code coverage exclusions, or reset the coverage baseline to pass a gate.

### Requirement 25: Containerization and CI planning

**User Story:** As an operator, I want reproducible Stage 4 containers and CI that never disturb inherited stacks, so that Stage 4 runs in isolation.

#### Acceptance Criteria

1. WHEN Stage 4 provides containers THEN it SHALL provide reproducible Docker and CI configuration using its own isolated Stage 4 resources, including an isolated project name, an isolated network, and an isolated named volume.
2. WHEN the Stage 4 Compose stack publishes ports THEN it SHALL publish only the frontend on host port `5517` and SHALL keep the backend reachable only inside the internal container network.
3. WHEN the Stage 4 containers run THEN the backend and frontend SHALL each run as a non-root user, and the backend SHALL run exactly one worker.
4. WHEN Stage 4 runs its containers or CI THEN it SHALL NOT start, stop, modify, or remove the inherited Stage 3 resources or any other tool's containers, volumes, or networks.
5. WHEN Stage 4 describes CI THEN it SHALL treat a local workflow file and local clean-equivalent checks as configuration artifacts only and SHALL NOT claim they are evidence of a hosted Actions run.
6. WHEN Stage 4 runs tests or fixtures THEN it SHALL NOT delete data outside its own declared temporary fixtures, and it SHALL preserve the solo SQLite data and the inherited restrictive HTTP CORS policy.

<!-- =====================  BENCHMARK HARNESS IMPLEMENTATION (AUTHORIZED) + MEASURED TRIALS (SEPARATELY AUTHORIZED, UNEXECUTED)  ===================== -->
<!-- Amended per native-checks/21-stage4-benchmark-harness-authorization/NOTE.md (2026-11-06): the former "DESIGN ONLY; no execution" posture is amended to AUTHORIZE actual benchmark harness implementation plus the harness's own semantic self-checks. The six measured production trials (two short headful probes, three solo, three duel 35s) remain separately-authorized, still-unexecuted work. Every pre-existing measurement-honesty, exclusion, and calibration requirement below is preserved unchanged. -->

### Requirement 26: Benchmark environment, scenario design, and authorized harness implementation

**User Story:** As a researcher, I want a rigorous benchmark design that follows the tool's own convention and an authorized harness implementation, so that the harness can be built and self-checked now while any future measured run produces trustworthy evidence.

#### Acceptance Criteria

1. WHEN the Benchmark_Harness is designed THEN it SHALL follow this tool's own `perf/` convention and SHALL drive the production Frontend in a real headful production Chrome channel with the sandbox enabled.
2. WHEN the Benchmark_Harness is designed THEN it SHALL use a `1280x900` viewport at device pixel ratio `1` and SHALL record the exact operating system, browser, browser version, channel, hardware, configuration, and source metadata.
3. WHEN the Benchmark_Harness defines a trial THEN it SHALL use a fresh session, at least `5` seconds of warm-up excluded from measurement, and a fixed `30`-second measured window.
4. WHEN the Benchmark_Harness defines its final trials THEN it SHALL define exactly three solo trials and three duel trials, each exercising real left, right, soft-drop, clockwise, and counter-clockwise actions.
5. WHEN the Benchmark_Harness runs a duel trial THEN it SHALL open both duel clients before approving actual-actor input foreground, SHALL identify the actual process identifier, window title, and window handle of the actor, and SHALL observe the operating-system foreground state plus native focus throughout the measured window.
6. WHEN the Benchmark_Harness drives input THEN it SHALL NOT use a hidden or headless fallback and SHALL NOT steal focus during the measured window.
7. WHEN the Benchmark_Harness defines its clocks THEN it SHALL keep true monotonic start, warm-up, measured, and end bounds, and SHALL include paired Node and browser calibration and drift measurement.
8. WHEN Stage 4 benchmark work is authorized THEN the actual IMPLEMENTATION of the Benchmark_Harness and the harness's OWN semantic self-checks SHALL be authorized now, amending the former design-only prohibition, WHILE the SIX measured production trials (two short headful probes, three solo trials, and three duel trials of `35` seconds each) SHALL remain separately-authorized work that SHALL NOT be executed under this authorization.
9. WHEN the Benchmark_Harness is implemented and self-checked THEN it SHALL NOT launch any production timing run, probe, trial, or measured window, so that implementation and self-checking never constitute a measured production run.
10. WHEN the Benchmark_Harness is implemented THEN it SHALL target the production URL `http://127.0.0.1:5517`, SHALL pin the existing Playwright `1.56.0` lock, SHALL use the installed production Chrome channel with the sandbox enabled, SHALL run HEADFUL only with no hidden or headless fallback, and SHALL use a `1280x900` viewport at device pixel ratio `1`.
11. WHEN the Benchmark_Harness is implemented THEN the accepted application source, tests, dependency locks, infrastructure, and the canonical duel wire contract SHALL remain frozen and unchanged.
12. WHEN the Benchmark_Harness exposes a command-line entrypoint THEN that entrypoint SHALL actually invoke the trial driver and SHALL exit with a non-zero status if no trial executed, so that a vacuous entrypoint cannot be reported as a successful run.
13. WHEN the Benchmark_Harness runs THEN it SHALL use only this tool's own `tetris-stage4-kiro` containers, named volume, and network on host port `5517`, SHALL NOT restart the backend during a measured trial, SHALL preserve solo FIFO, the solo HTTP API, and solo SQLite persistence, SHALL keep duel state non-persistent, and SHALL NOT claim a hosted CI run from local workflow files.

### Requirement 27: Benchmark evidence, correlation, and honest limits

**User Story:** As a researcher, I want benchmark evidence to prove action-caused pixels and keep targets honest, so that no scheduling number is mistaken for a presentation guarantee.

#### Acceptance Criteria

1. WHEN the Benchmark_Harness records rendering evidence THEN it SHALL separate the `requestAnimationFrame` scheduler stream from the actual CHANGED 200-cell RGBA masks and the verified draws, and SHALL NOT treat `requestAnimationFrame` frequency as proof of rendering throughput.
2. WHEN the Benchmark_Harness associates an action with a visible update THEN it SHALL correlate the actual source input identity, key, and timestamp with the authorized acknowledgement or HTTP result, the authoritative Board and revision effect, and the real target pixels, in the actor and peer clock domains.
3. WHEN a visible change is caused by ordinary gravity or by a scalar-only change THEN the Benchmark_Harness SHALL NOT treat that change as action-visible proof.
4. WHEN the Benchmark_Harness records a trial THEN it SHALL retain all samples, counts, exclusions, median, p95, p99, screenshots, and traces, and SHALL report excluded samples with their reasons.
5. WHEN the Benchmark_Harness reports results THEN it SHALL NOT pool samples across trials, SHALL NOT make statistical-significance claims, SHALL NOT make scalability claims, and SHALL NOT make physical-presentation claims.
6. WHEN the Benchmark_Harness states a target THEN a scheduler mean of at least `55` FPS and a p95 frame interval of at most `25` ms SHALL be stated as scheduling targets only, kept separate from measurement qualification.
7. WHEN the Benchmark_Harness runs a measured window THEN it SHALL NOT auto-restart the game inside that measured window.
8. WHEN this document describes the benchmark THEN it SHALL authorize harness implementation and the harness's own semantic self-checks, and it SHALL NOT assert that any benchmark timing run, measured trial, probe, screenshot, trace, or measured metric has been executed or produced.
9. WHEN the Benchmark_Harness measures a trial THEN it SHALL exclude at least `5` seconds of warm-up from measurement, SHALL use a fixed `30`-second measured window on a monotonic clock, SHALL use a fresh session per trial, and SHALL NOT perform any hidden restart or timer reset inside the measured window.
10. WHEN the Benchmark_Harness correlates clock domains THEN it SHALL use paired Node `hrtime` and browser `performance` pre-measurement and post-measurement calibration with drift and uncertainty, and SHALL NOT subtract timestamps from uncalibrated clock domains.
11. WHEN the Benchmark_Harness records scheduling and rendering evidence THEN it SHALL keep `requestAnimationFrame` scheduling samples separate from the verified action-visible 200-cell Canvas RGBA masks, and the scheduler mean of at least `55` FPS and the p95 `requestAnimationFrame` interval of at most `25` ms SHALL be scheduling targets only, never display or throughput guarantees, and physical presentation latency SHALL remain UNKNOWN.
12. WHEN the Benchmark_Harness drives input THEN it SHALL send real left, right, soft-drop, clockwise (`ArrowUp`), and counter-clockwise (`z` or `Z`) input, SHALL NOT place input inside any polling predicate, and SHALL distinguish the source input identity from the protocol `action_id` and from the authoritative acknowledgement, HTTP result, or revision.
13. WHEN the Benchmark_Harness observes the system THEN it SHALL use passive network and WebSocket observation plus read-only Canvas, DOM, and input recorders only, and SHALL NOT monkeypatch or intercept `fetch` or `WebSocket`, read React internals or debug state, or inject authority.
14. WHEN the Benchmark_Harness qualifies samples THEN it SHALL exclude, each with an explicit recorded reason, every unchanged `O`-rotation or no-op sample, every gravity-only sample, every scalar-only sample, every stale or rate-rejected sample, every superseded sample, every out-of-window sample, and every unqualified-focus sample, and it SHALL NOT clamp a negative interval.
15. WHEN the Benchmark_Harness records a trial THEN it SHALL retain all inputs, all replies, and all exclusions with their exact counts, and any unknown field SHALL be recorded as null and never as zero.

<!-- =====================  PROCESS GUARDRAIL  ===================== -->

### Requirement 28: On-disk process guardrail before corrective changes

**User Story:** As a maintainer, I want a dated on-disk note to precede any corrective change, so that corrections are never silent and are always traceable.

#### Acceptance Criteria

1. WHEN a later code, test, configuration, or benchmark correction is to be made in response to a failed or defective check THEN a NEW dated native spec or task note SHALL be written ON DISK in this workspace BEFORE that correction is made.
2. WHEN the guardrail requires an on-disk note THEN chat narration and a pre-existing broad note SHALL NOT be sufficient to satisfy the guardrail.
3. IF a check fails AND the required dated on-disk note cannot be written first THEN the implementer SHALL report the failure and stop rather than silently applying the correction.
4. WHEN a dated note is written THEN it SHALL identify the observed defect and the intended correction before the corresponding change is applied.

<!-- =====================  PRESERVATION AND EXCLUSIONS  ===================== -->

### Requirement 29: Preserved boundaries and retained exclusions

**User Story:** As a researcher, I want scope controlled, so that Stage 4 adds only rotation, Canvas, and the WebSocket duel.

#### Acceptance Criteria

1. WHEN Stage 4 is implemented THEN the inherited specifications under `.kiro/specs/tetris-stage1-option-a/`, `.kiro/specs/tetris-stage2-option-a/`, and `.kiro/specs/tetris-stage3-option-a/` SHALL remain unchanged and SHALL be preserved byte-for-byte in their original directories.
2. WHEN Stage 4 is implemented THEN the inherited solo gameplay, scoring, leveling, gravity, Hold, lock-ordering, persistence, leaderboard, and CORS behaviors SHALL be preserved except where a Stage 4 requirement explicitly supersedes them.
3. WHEN Stage 4 is implemented THEN the only inherited behaviors it supersedes SHALL be: adding server-side rotation of the active piece, replacing the main board's DOM-cell rendering with a Canvas surface, and adding the WebSocket duel; every other inherited behavior SHALL be preserved.
4. WHEN Stage 4 is implemented THEN it SHALL NOT add a ghost piece, T-Spin scoring, hard drop scoring changes, time attack, achievements, saved or resumable games, a non-SQLite database, authentication, player-name collection, a global or networked leaderboard, or cloud deployment.
5. WHEN Stage 4 is implemented THEN duel games SHALL remain in memory only, and the only persisted data SHALL remain the inherited completed solo-game `High_Score_Record` rows.
6. WHEN Stage 4 is implemented THEN the System SHALL NOT perform commits, pushes, container image publishing, or external deployment on its own.
7. WHEN Stage 4 reports status THEN it SHALL NOT fabricate completed approvals, checks, metrics, CI runs, tokens, costs, screenshots, Docker successes, coverage numbers, duplication numbers, or performance results.

## Material Ambiguities and Assumptions

These are recorded for transparency.

1. **Spawn geometry is authoritative.** Stage 4 rotation is defined from this tool's own `spawn0` geometry, in which the `I` piece spawns on row `0`. Standard rotation tables that assume the `I` piece spawns on row `1` are explicitly not imported; the four orientations of every piece are declared as independent data around a fixed pivot.
2. **Wall-kick scope.** The wall-kick search is horizontal-only with the exact candidate order `0, -1, +1, -2, +2`. There are no vertical kicks. A rotation for which no candidate fits is fully rejected and immutable.
3. **Rotation is a pure orientation change.** A rotation alone never locks, advances gravity, awards points, or mutates the next, preview, or Hold pieces. This keeps rotation cleanly separated from the inherited lock / clear / score / spawn ordering.
4. **Canvas is a rendering change only.** The Canvas migration changes how the main board is drawn, not the authoritative state, the solo HTTP contract, the persistence, or the leaderboard. Mock draw-call records and DOM data attributes are not accepted as pixel evidence; only real pixels from the unmodified production bundle are.
5. **Duel isolation.** Duel rooms are in-memory, private per Seat, never registered in the solo HTTP stores, and never persisted in the solo SQLite leaderboard. Solo play and the solo leaderboard are preserved during a duel.
6. **Simultaneous top-out is a DRAW.** Gravity is evaluated per Board, but all due Boards are evaluated before a single outcome is decided, so two boards topping out in the same evaluation produce a draw; otherwise the last survivor wins and an active disconnect forfeits exactly once.
7. **One versioned wire contract.** The duel uses a single versioned, machine-readable wire contract with strict expected-revision equality, independent action IDs, explicit handling of duplicate, stale, future, no-op, and seat-ownership cases, and no placeholders or ellipsis in its schemas or examples.
8. **Real WebSocket engine.** A production uvicorn deployment must include an actual WebSocket protocol engine dependency; `anyio` alone does not implement the uvicorn WebSocket upgrade.
9. **Measurement honesty.** Any coverage, duplication, static-analysis, container, CI, or benchmark MEASURED value is produced only by an actual execution in a later phase. Per `native-checks/21-stage4-benchmark-harness-authorization/NOTE.md` (2026-11-06), benchmark HARNESS implementation and the harness's own semantic self-checks are now authorized, but the six measured production trials (two short headful probes, three solo, three duel 35s) remain separately-authorized and unexecuted; this specification still asserts no measured timing run, trial, probe, screenshot, trace, or metric. The three Sonar outcomes (coverage, duplication, new static findings) remain separate from one another and from the overall gate, which is not claimed to pass.
10. **Process guardrail precedes corrections.** A dated on-disk note must be written before any corrective code, test, configuration, or benchmark change; if such a note cannot be written first after a failed check, the implementer reports the failure and stops rather than silently correcting.
