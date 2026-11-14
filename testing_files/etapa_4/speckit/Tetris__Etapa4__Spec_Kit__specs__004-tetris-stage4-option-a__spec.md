# Feature Specification: Tetris Stage 4 Option A - Rotation, Canvas 2D Board, and Real-Time WebSockets Duel

**Feature Branch**: `004-tetris-stage4-option-a`
**Created**: Tuesday, November 3, 2026
**Status**: Revised

---

## 1. User Stories & Testing

### User Story 1 - Deterministic 90-Degree Tetromino Rotation (Priority: P1) [ROT-01, ROT-02, ROT-03]
As a Tetris player, I want to rotate the active tetromino clockwise (using `ArrowUp`) and counterclockwise (using `Z` or `z`) with realistic, deterministic wall-kick behavior so that I can fit pieces into tight gaps on the board.

**Why this priority**: Rotation is the core missing mechanic of the game's piece interaction, and must be implemented authoritatively in the backend game engine to enable proper single-player and multi-player gaming.

**Independent Test (Milestone 1 Gate)**: Verify that:
1. All pieces (except O) cycle through their orientations deterministic relative to pivot.
2. O piece rotation operates as a strict, state-invariant no-op.
3. Horizontal offsets are evaluated in the strict order `0, -1, +1, -2, +2`.
4. If no horizontal offset fits, the rotation is rejected (no position or orientation change).
5. Rotation does not trigger score updates, gravity advancement, locks, or hold queue mutations.
6. Rotation reset to spawn orientation (Orientation 0) occurs on spawn and Hold retrieval.

---

### User Story 2 - High-DPI Canvas 2D Board Rendering & DOM Assertions Replacement (Priority: P2) [CAN-01, CAN-02]
As a Tetris player, I want the primary 10x20 cell board rendered smoothly using HTML5 Canvas 2D rather than DOM divs, while keeping crisp high-DPI resolution and the surrounding DOM layout, so that the game looks modern and scales sharply with my display.

**Why this priority**: Transitioning to Canvas 2D provides high-performance rendering and a cleaner structure, paving the way for multi-board rendering in real-time duel play.

**Independent Test (Milestone 2 Gate)**: Verify that the board displays inside a `<canvas>` element.
1. The canvas adapts dynamically to high `window.devicePixelRatio` (DPR) to ensure razor-sharp borders.
2. Existing DOM-based components (stats, preview, hold, leaderboard) update correctly.
3. Traditional React DOM cell unit tests asserting `.board-grid` or `div.cell` are successfully decommissioned and replaced by assertions verifying the canvas element, resizing behavior, and redraw events.
4. Existing SQLite-backed single-player score finalization works exactly once per session.

---

### User Story 3 - Two-Player Real-Time Duel over WebSockets (Priority: P3) [NET-01, NET-02, NET-03]
As a competitive Tetris player, I want to participate in a real-time, two-player duel over WebSockets with same-seed pieces, side-by-side board visibility, server-side gravity, and strict cheating protections, so that I can test my skills fairly against an opponent.

**Why this priority**: Real-time multi-player duel is the crown-jewel feature of Stage 4, requiring bidirectional WebSocket syncing and robust room/seat lifecycle management.

**Independent Test (Milestone 3 Gate)**: Connect two clients to the `/api/duel/ws` endpoint.
1. The game starts only when both players have joined (start gating).
2. Both boards receive the exact same tetromino sequences.
3. Server-side gravity advances both boards independently.
4. Disconnecting immediately forfeits the match, awarding victory to the active player.
5. Inactive, finished, or abandoned rooms are cleaned up within 5 minutes, releasing their event loops.
6. Handshake enforces strict origin checks to prevent CSWSH.

---

## 2. Requirements

### Functional Requirements

#### Milestone 1: Authoritative Tetromino Rotation Requirements [ROT-01, ROT-02, ROT-03]
- **FR-001**: The authoritative Python backend game engine MUST support 90-degree clockwise and counterclockwise piece rotation.
- **FR-002**: Expose rotation to the API via the existing `/api/games/{id}/move` endpoint by accepting `"cw"` (clockwise) and `"ccw"` (counterclockwise) as valid values in the `MoveRequest` `direction` parameter.
- **FR-003**: The keyboard controls MUST map `ArrowUp` to clockwise rotation (`"cw"`) and `Z` (or lowercase `z`) to counterclockwise rotation (`"ccw"`) in the single-player and duel UI.
- **FR-004**: Each tetromino type (except O) MUST have deterministic pivots (`origin`) and four distinct orientations (indices 0, 1, 2, 3), represented by explicit, sorted cell offsets relative to the pivot:
  - **I Piece** (Pivot `[0, 4]` at spawn):
    - Orientation 0: `[[0, -1], [0, 0], [0, 1], [0, 2]]`
    - Orientation 1: `[[-1, 0], [0, 0], [1, 0], [2, 0]]`
    - Orientation 2: `[[0, -2], [0, -1], [0, 0], [0, 1]]`
    - Orientation 3: `[[-2, 0], [-1, 0], [0, 0], [1, 0]]`
  - **O Piece** (Pivot `[0, 4]` at spawn, rotation is a no-op):
    - All Orientations (0, 1, 2, 3) are identical: `[[0, 0], [0, 1], [1, 0], [1, 1]]` (Rotation is a strict, state-invariant no-op).
  - **T Piece** (Pivot `[1, 4]` at spawn):
    - Orientation 0: `[[-1, 0], [0, -1], [0, 0], [0, 1]]`
    - Orientation 1: `[[-1, 0], [0, 0], [0, 1], [1, 0]]`
    - Orientation 2: `[[0, -1], [0, 0], [0, 1], [1, 0]]`
    - Orientation 3: `[[-1, 0], [0, -1], [0, 0], [1, 0]]`
  - **S Piece** (Pivot `[1, 4]` at spawn):
    - Orientation 0: `[[-1, 0], [-1, 1], [0, -1], [0, 0]]`
    - Orientation 1: `[[-1, 0], [0, 0], [0, 1], [1, 1]]`
    - Orientation 2: `[[0, 0], [0, 1], [1, -1], [1, 0]]`
    - Orientation 3: `[[-1, -1], [0, -1], [0, 0], [1, 0]]`
  - **Z Piece** (Pivot `[1, 4]` at spawn):
    - Orientation 0: `[[-1, -1], [-1, 0], [0, 0], [0, 1]]`
    - Orientation 1: `[[-1, 1], [0, 0], [0, 1], [1, 0]]`
    - Orientation 2: `[[0, -1], [0, 0], [1, 0], [1, 1]]`
    - Orientation 3: `[[-1, 0], [0, -1], [0, 0], [1, -1]]`
  - **J Piece** (Pivot `[1, 4]` at spawn):
    - Orientation 0: `[[-1, -1], [0, -1], [0, 0], [0, 1]]`
    - Orientation 1: `[[-1, 0], [-1, 1], [0, 0], [1, 0]]`
    - Orientation 2: `[[0, -1], [0, 0], [0, 1], [1, 1]]`
    - Orientation 3: `[[-1, 0], [0, 0], [1, -1], [1, 0]]`
  - **L Piece** (Pivot `[1, 4]` at spawn):
    - Orientation 0: `[[-1, 1], [0, -1], [0, 0], [0, 1]]`
    - Orientation 1: `[[-1, 0], [0, 0], [1, 0], [1, 1]]`
    - Orientation 2: `[[0, -1], [0, 0], [0, 1], [1, -1]]`
    - Orientation 3: `[[-1, -1], [-1, 0], [0, 0], [1, 0]]`
- **FR-005**: Rotation wall-kicks MUST be evaluated by trying horizontal offsets (shifts in board columns) in the exact order: `0, -1, +1, -2, +2` relative to the current column coordinate. Vertical kicks are NOT supported (vertical offset is strictly 0).
- **FR-006**: The engine MUST apply the first horizontal offset candidate that fits the board boundaries (row `[0, 19]`, col `[0, 9]`) and does not collide with any locked cells. If none of the five candidates fit, the engine MUST reject the rotation, leaving position and orientation unmodified.
- **FR-007**: Active piece rotation MUST NOT by itself lock the piece, trigger line clears, advance progressive gravity, award points, or modify the hold/preview queues.
- **FR-008**: Pieces MUST always enter play in their spawn orientation (Orientation 0). This includes newly spawned pieces and pieces retrieved/swapped from the Hold slot.
- **FR-009**: The backend MUST preserve all inherited Stage 3 gameplay behavior, including progressive gravity speedups, soft-drop mechanics, SQLite scores DB integration, and blocked-gravity terminal rules.

#### Milestone 2: Canvas 2D Board Replacement Requirements [CAN-01, CAN-02]
- **FR-010**: The frontend MUST replace the 10x20 cell grid made of individual React DOM div elements with a single HTML5 Canvas 2D element for board rendering.
- **FR-011**: React/TypeScript MUST remain the container for surrounding controls, statistics (score, lines, level), Hold piece slot, Next piece preview, high scores panel, and game state overlays.
- **FR-012**: The Canvas rendering pipeline MUST draw the 10x20 cell grid, drawing occupied cells on the board and the currently active falling piece with appropriate visually matching colors and grid borders.
- **FR-013**: The Canvas MUST redraw correctly and immediately after any piece rotation, movement, locking, line-clears, restart, or screen resize event.
- **FR-014**: High-DPI Support: The Canvas dimensions and rendering scale MUST adapt to the device pixel ratio (`window.devicePixelRatio`) to ensure sharp, crisp lines on Retina or high-DPI monitors.
- **FR-015**: Preserve Stage 3 stale-response protection, ensuring out-of-order API packets do not cause visual glitches or board state regression.
- **FR-016**: Preserve the solo REST HTTP contract, including body validation, same-origin `/api` proxy routing, CORS rules, and database-backed terminal game finalization. Specifically:
  - **Manual Down No-Op**: Under the inherited Stage 1 mechanics, a manual downward movement request (`"down"`) made when a piece is at the bottom (colliding) MUST be treated as a no-op (leaves the state completely unchanged and does NOT lock the piece or trigger game over).
  - **Gravity Lock**: Only progressive gravity ticks (or an obstructed Hold) can lock a piece to the board and transition the game to `"game_over"`.
  - **Terminal Retry**: If SQLite persistence fails on the initial finalization after game over, a subsequent mutating API request on that terminal game must safely retry database persistence, whereas GET requests never trigger a retry.
  - **CORS & HTTP Status**: Preserve the Stage 3 configurable REST HTTP CORS policy, the valid bodyless game creation endpoint (`POST /api/games` with empty body), and returning `422 Unprocessable Entity` on invalid movement directions (including any non-supported direction strings) and `404 Not Found` for unknown games.
  - **No Response Shape Expansion**: Do NOT expand the solo API response schemas (`GameSessionSchema` or `TetrominoSchema`) to expose internal engine rotation index or orientation, as the client renders the board and active piece correctly using absolute coordinate cells.
- **FR-017**: Front-end tests MUST decommission assertions that rely on finding individual cell divs in the board DOM tree and instead assert the canvas element mounts, handles resize events, and triggers redraws.

#### Milestone 3: Real-Time WebSockets Duel Requirements [NET-01, NET-02, NET-03, INF-01]
- **FR-018**: Provide real-time two-player duel rooms over bidirectional WebSocket connections mounted on the same origin.
- **FR-019**: Room management MUST run on a single FastAPI worker process using thread-safe, in-memory rooms. No multi-worker or external message broker (such as Redis) is required.
- **FR-020**: Dual Boards: Both boards MUST be 10x20 grids, rendered side-by-side on each client using separate Canvas 2D elements. Both players see both authoritative board states in real-time.
- **FR-021**: Start Gating: A duel game session MUST remain in a waiting state until two distinct players have connected and joined the room. No inputs or gravity loop updates occur while waiting.
- **FR-022**: Deterministic Seed: Both players MUST receive the exact same sequence of tetrominoes generated on the server, ensuring absolute mechanical fairness.
- **FR-023**: Server-driven Gravity: Progressive gravity ticks for each board MUST be driven independently by server-side timers and event loops (background `asyncio` tasks), rather than client-side browser clocks, preventing speed cheating.
- **FR-024**: Seat Ownership & Validation: The server MUST validate all inputs, rejecting any movement or rotation messages that target the opponent's seat or submit forged scores or board layouts. Payloads MUST remain completely free of any client-provided player identity (identities are server-assigned based on connection).
- **FR-025**: Room Isolation: WebSocket communication (inputs and state broadcasts) MUST be strictly scoped and isolated to the assigned room.
- **FR-026**: Monotonic State Revisions: State updates broadcasted by the server MUST contain monotonic increasing revision numbers, and clients MUST reject any out-of-order or late messages to protect against stale state.
- **FR-027**: Bounded Room Retention: The server MUST clean up and release inactive, abandoned, or finished rooms and their associated server gravity timers after 5 minutes of inactivity to prevent memory leaks.
- **FR-028**: Outcomes & Terminal States:
  - Last surviving player wins.
  - **Room Scheduler**: The server MUST use one room scheduler with independent per-seat due times. Apply all seats due in one authoritative batch before evaluating the winner.
  - **Double-Gravity Tick Draw Logic**: If both players' gravity timers independently expire and trigger a gravity tick within the same authoritative server update loop (the same clock cycle), the server processes both moves sequentially before evaluating top-out. If both seats transition to `game_over` as a result of this single loop update, the server declares a **DRAW**.
  - If one player tops out first in a previous server tick, the other player instantly wins, and the room status transitions to `"finished"`.
  - **WebSocket Disconnection Forfeit & Waiting Release**: If a player disconnects or closes their connection during an active duel, the server MUST record an immediate forfeit, transition room status to `"finished"`, and broadcast a win to the surviving player, without waiting for reconnection. Keep active-forfeit and terminal retention separate. If the sole player disconnects while waiting (before the second player joins), the server MUST release the room immediately and produce no forfeit result.
- **FR-029**: Separation of Leaderboards: Duel game results and metrics MUST remain completely separate from the solo SQLite leaderboard; high scores database inserts are strictly restricted to solo terminal games.
- **FR-030**: Solo Coexistence: Players MUST be able to run standard solo games while other players participate in real-time duels, without any resource leakage or interference.
- **FR-031**: Handshake Origin Verification: The server MUST perform explicit WebSocket handshake origin validation, verifying the `Origin` header against configured allowed domains to protect against Cross-Site WebSocket Hijacking (CSWSH), separately from HTTP CORS.
- **FR-032**: Versioned JSON Messages: All WebSocket messages exchanged between browser and server MUST conform to explicit versioned schemas (e.g., `"v": 1` in JSON structures).
- **FR-033**: Server-owned Room and Seat Assignment: The server MUST authoritatively assign and own room IDs and seats (Seat 1 and Seat 2), preventing any client-side override or seat selection.
- **FR-034**: Bounded Payloads & Limits: All incoming WebSocket payloads MUST have bounded size (maximum message size limit of 1KB) to prevent denial-of-service, and room sizes are strictly bounded to exactly 2 players. Server capacity is bounded at a maximum of 100 concurrent active rooms.
- **FR-035**: Monotonic Sequence and Deduplication: State updates and commands MUST use monotonic increasing sequence numbers, and the server MUST deterministically deduplicate client action messages and reject any stale actions.
- **FR-036**: Stale Action Semantics:
  - The client action payload MUST carry a sequence number `seq_num` and echo the last received `active_piece_generation` value for its seat.
  - The server advances `active_piece_generation` ONLY on piece spawn or Hold replacement, NOT on gravity-driven downward movements or lateral shifts of the same piece.
  - If the incoming action carries a `generation` mismatched with the current server-owned generation, or if its `seq_num` is <= `last_processed_seq_num` for that seat, the server MUST reject it as stale/duplicate, with no state or board mutations.
- **FR-037**: Deterministic Room Joining: A supplied room ID that is unknown, full, or finished MUST fail connection deterministically, returning standard close codes (such as `4004 Room Invalid/Finished` or `4001 Room Full`). An omitted room ID creates a fresh room.
- **FR-038**: Accepted Snapshot Ordering: State updates broadcasted by the server must be strictly ordered. Clients must process and render incoming snapshots chronologically, ignoring any older updates received out of order.
- **FR-039**: Fresh Room Restart: Restarting a duel game MUST allocate a fresh room ID with all resources and event loops fully re-initialized, rather than recycling the existing terminal room. No database writes to the solo leaderboard are performed for duel matches.
- **FR-040**: Same-Origin UI Controls: The client UI MUST expose an explicit way to create a room (creates a room via empty query parameter WS handshake) and to join an existing room by typing or copying a room ID.

---

## 3. Success Criteria & Verification Gates [PERF-01]

### 3.1 Milestone Implement Gates & Verification Requirements
- **Milestone 1 (Rotation) Gate**: 
  - **Prerequisites**: Python engine updated with the 90-degree CW/CCW rotation and column wall-kick offset logic.
  - **Evidence**: 100% pass on backend unit tests (`pytest tests/unit/test_game_engine_us1.py`) with full coverage of unobstructed turns, boundary/locked cell kicks, and Hold orientations.
- **Milestone 2 (Canvas 2D) Gate**:
  - **Prerequisites**: DOM grid removed, Canvas element integrated with `devicePixelRatio` logic.
  - **Evidence**: Vitest unit/component tests updated to decommission DOM cell queries and instead assert canvas mount/resize events. Production build completes successfully. Scoring finalization validated.
- **Milestone 3 (Duel) Gate**:
  - **Prerequisites**: WebSocket connection handshakes, room manager, and background server gravity loops fully implemented.
  - **Evidence**: Integration and unit tests pass (`test_duel_manager.py` and `test_api_ws.py`). Handshake origin validation rejects unauthorized origins.
- **Docker/Proxy/CI (Infrastructure) Gate [INF-01]**:
  - **Prerequisites**: Docker Compose fully functional, Nginx reverse proxy routes REST and WebSockets appropriately, Python 3.11 (inherited CI and containers baseline) / Python 3.12.4 (independent Windows verification runtime) and Node 24 majors pinned.
  - **Evidence**: Healthy containers from non-root Compose setup. CI runs successfully.

---

### 3.2 Playwright Browser Performance Benchmark Protocol [PERF-01]
Performance audits must be verified through the actual production browser bundle using the following strict guidelines:
1. **Environment**: Foreground production Chromium browser window sized at exactly `1280x900` with `deviceScaleFactor: 1`.
2. **Procedure**: Employs a frozen piece seed (same random seed) across a six-trial protocol:
   - **3 trials of Solo Play** (30 seconds each, after a 5-second warm-up)
   - **3 trials of Duel Play** (30 seconds each, after a 5-second warm-up)
3. **Player Inputs**: Exercise real movements (left, right) and rotations.
4. **Captured Distributions**:
   - **Frame-scheduling rate**: Programmatic interval tracking between successive `requestAnimationFrame` callbacks, reporting median, p95, and p99. Mean scheduling rate >= 55 FPS and p95 interval <= 25 ms serve strictly as numerical targets, not pass/fail gates.
   - **Action-to-visible-update latency**: Time elapsed between client-emitted keyboard events and the subsequent Canvas pixel repaint (not just draw callback invocation, must use actual canvas repaint timing).
   - **Remote action-to-opponent-visible latency**: Time elapsed between Client 1 action emission and the subsequent Canvas redraw representing Seat 1 on Client 2's screen.
5. **Foreground Constraint & Client Modes**: Since Chromium throttles background tabs, both duel clients must be run in visible, non-overlapping windows or side-by-side to guarantee both receive foreground scheduling, and the focus/foreground mode of each client must be recorded.
6. **Draw Evidence**: Use browser screenshots or actual pixel captures (not just dimensions or container asserts) to bind drawing evidence objectively to committed states.
7. **Reporting**: Report counts, raw samples, median/p95/p99, exclusions, and failures. Report unavailable measures as "unavailable".

---

## 4. Assumptions

- **ASM-001**: Duel rooms are hosted in-memory, assuming no multi-process load balancing or Redis stores are required, consistent with the single-process, one-worker FastAPI Docker configuration.
- **ASM-002**: Players have stable WebSocket-compatible connections to maintain responsive inputs during real-time duels.
- **ASM-003**: Web browsers used for play support the HTML5 Canvas 2D API and the WebSocket API.
- **ASM-004**: User identification in the WebSocket duel is managed transiently via session or room-specific UUIDs generated on connection, without requiring a permanent persistent user database.

---

## 5. Recorded Workflow Clarifications & Repair Cases

As part of independent verification, several critical defects and architectural requirements were identified. The following repair cases are canonically integrated into this Stage 4 specification:

### 5.1 Terminal Atomicity (Repair Case 1)
- **Finding**: In a deterministic duel fixture, when automatic gravity is canceled and both spawn areas are obstructed while current pieces are at row 8, calling Hold(seq=1,generation=0) on seat 1, then separately on seat 2, causes the room to remain active. After 50ms, a draw is evaluated. Distinct actions should NOT produce a draw.
- **Correction**: Replace per-seat gravity tasks and the 10ms grace window with a single room scheduler that independently tracks due times per seat. Evaluate all seats due in one authoritative batch before outcome evaluation. A same-batch double top-out draws. Distinct actions or distinct batches cannot draw; the first terminal action must immediately decide the winner (e.g., seat_2 wins if seat_1 tops out on a distinct action). Ensure only one terminal result is recorded and proper cancellation/lifespan cleanup of the room's event loop.

### 5.2 Continued Sequence (Repair Case 2)
- **Finding**: A fixture setting `next_piece_index` to `len(piece_sequence)`, then triggering a Hold action, raises an `IndexError`.
- **Correction**: Extend or deterministically generate the shared piece sequence on demand (by appending new pieces deterministically, e.g., via seed-based generator or repeating batches of 1000) for arbitrary continued play. This preserves equal piece order and independent indices across both seats.

### 5.3 Waiting Disconnect (Repair Case 3)
- **Finding**: When the sole waiting player disconnects from a room before any other player joins, the room remains allocated.
- **Correction**: Release the room immediately on waiting-player disconnect. Preserve bounded terminal retention (retaining finished rooms for a brief grace period before sweep), active disconnect forfeit, and robust app shutdown/restart cleanup for every owned task and socket. No background tasks may be created during module import.

### 5.4 Frontend Stale Protection (Repair Case 4)
- **Finding**: The production bundle accepts state revision 10 at row 8 but then renders revision 9 at row 2. Additionally, after creating a second room, the closed first socket's callback can overwrite the new room's Canvas with its old snapshot.
- **Correction**: Add explicit socket/session identity generation guards (e.g., unique socket ID or timestamp) for every socket message callback. Enforce monotonic accepted room revisions on the client. Perform a clean fresh-room reset and ensure proper cleanup of callbacks. Check terminal/late error/close frames to discard outdated snapshots. Add regression tests through the hooks and verify on the real Canvas UI.

### 5.5 Contract Synchronization (Repair Case 5)
- **Finding**: The native WS contract specifies `room_status`, while the actual server and frontend use `status` in the JSON payload.
- **Correction**: Align the WS contract, data models, and tests to use `status` as the canonical payload property. Preserve the original failed contract evidence if needed but ensure the 004 contract is synchronized.

### 5.6 Strict Payload Validation (Repair Case 6)
- **Finding**: Sending valid move left, duplicate seq, mismatched generation, or extra payload fields (e.g., `seat="seat_2"` forged on a seat_1 action) moves seat_1 instead of being rejected.
- **Correction**: Strictly validate all incoming payloads. Reject:
  - Unknown envelope/payload fields.
  - Client-submitted scores, board, seat, or player identity.
  - Boolean integers (e.g., true/false represented as 1/0 where integers are expected).
  - Non-object JSON/payloads.
  - Out-of-safe-range sequence and generation values.
  - Malformed messages or invalid actions.
  Enforce a strict 1024 UTF-8 byte cap (not codepoint length) on incoming messages. Validate the browser `Origin` header against the configured allowlist during the WebSocket handshake. Ensure errors are controlled and bounded without corrupting the board state.

### 5.7 Serialization and Delivery (Repair Case 7)
- **Finding**: Ordered broadcasts must remain identifiable when actions and gravity overlap.
- **Correction**: Preserve the authoritative seat/seq/generation/revision action correlation. Ensure ordered broadcasts remain identifiable. Do not use 'same event loop iteration' as an unmeasured proxy for one authoritative batch.

### 5.8 Production Isolation (Repair Case 8)
- **Finding**: The native Docker Compose uses a fixed historical SQLite volume name, leading to volume collision.
- **Correction**: Remove the fixed volume name from native Compose so a normal Stage 4 project has a project-scoped volume. Preserve default frontend port 5183, backend internal, and one worker. The researcher still tests only the isolated project on 5513, because the old Kiro stack owns 5183.

### 5.9 Non-reentrant Lock Deadlock during Action-Induced Game Over (Repair Case 9)
- **Finding**: When a player action triggers a game over (e.g. via Hold/Spawn obstruction), `process_action` is executed while holding `self.lock`. Under the lock, it awaits `broadcast_game_over`, which also attempts to acquire the same non-reentrant `self.lock` for its `game_over_sent` guard. This results in a deadlock, causing the task to stall indefinitely.
- **Correction**: Release `self.lock` in `process_action` before awaiting `broadcast_state` and `broadcast_game_over`. Compute and commit all terminal state transitions and cancel room tasks atomically under the lock, then release the lock before state and game-over result delivery.

### 5.10 Oversized Receive Loop Cleanup / Policy Close Path (Repair Case 10)
- **Finding**: When a player sends a message exceeding the 1024 UTF-8 byte payload limit, the receiver loop closes the connection and breaks, but does not trigger `handle_disconnect` because the loop ends normally. This leaves the opponent without a `game_over` broadcast and the room active.
- **Correction**: Route all post-join endpoint exits through a single, unified cleanup path using a `finally` block, ensuring `handle_disconnect` is called once for any post-join exit (including intentional policy close, transport disconnect, and exceptions), while keeping room/seat ownership guarded if the handshake did not finish.

### 5.11 Measurement Instrument Repairs (Repair Case 11)
- **Finding**: The performance benchmark script (performance-benchmark.ts) had significant instrument flaws (headless hardcoding, simple red-channel sampling leading to false positives/collisions, missing raw timestamp retention, overlong execution, and duel observer clock differences).
- **Correction**: Implement a robust executable performance measurement instrument that satisfies these criteria:
  - Accepts standard command-line options: `--base-url`, `--output`, `--runs`, `--warmup-seconds`, `--measure-seconds`, `--smoke` / `--headless`. Fails with a non-zero status if the output directory already exists to prevent overwriting.
  - Injects trackers using an explicitly invoked IIFE string (`(() => { ... })()`) to avoid functions not executing and transpilation issues. Asserts trackers exist and produce samples before claiming readiness.
  - Matches the real REST API camelCase response shape (reading `activePiece` instead of `active_piece`) to accurately draw and verify pixels. Classifies mismatched states as instrument mismatches/unresolved observations rather than blocked no-ops.
  - Binds "before" states to the preceding actual mutation response rather than relying on stale variables.
  - Records a raw record containing original network/state data, action and pixel acknowledgments, timestamps, calibration probes, and visibility events.
  - Filters requestAnimationFrame and draw events within both previous and current calibrated endpoints to the exact measurement window, retaining exclusions.
  - Persists partial raw run data and state on failures in a guarded `finally` block to prevent dropping telemetry on crash.
  - Queries actual browser window outer/inner bounds and visibility events dynamically.
  - Employs bounded Euclidean distance color classification with a maximum tolerance (e.g. distance <= 30) and a source-derived expected empty-cell RGB (`[19, 19, 23]`) accounting for alpha overlay blending.




