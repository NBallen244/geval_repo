# Requirements Specification: Browser-Based Tetris Study - Stage 4, Option A (Tetromino Rotation, Canvas 2D & Real-time Duel WebSockets)

## 1. Superseding Statement & Scope Boundaries
All legacy exclusions regarding tetromino piece rotation and multiplayer/real-time play from Stage 1, Stage 2, and Stage 3 are **explicitly and fully superseded** by this Stage 4 Option A specification.

Specifically:
1. **Rotation:** Counterclockwise (CCW) and clockwise (CW) 90-degree active tetromino rotations with horizontal wall-kicks are now fully required.
2. **Canvas 2D Rendering:** The 10x20 React DOM board grid must be replaced with a high-performance `<canvas>` element.
3. **Real-time Duel WebSockets:** A same-origin, server-authoritative, real-time two-player WebSocket duel mode must be implemented using in-memory rooms in a single FastAPI worker.

All other legacy exclusions—specifically, ghost piece rendering, T-Spins, gameplay achievements, time attack/specialized modes, PostgreSQL/external multi-user databases, and player authentication—remain strictly in effect and MUST NOT be implemented.

The in-memory single-player games, SQLite high scores persistence (for solo mode), level/score progression, and strict FIFO promise queuing remain fully active and must be preserved without regressions.

---

## 2. Atomic Requirements (Req-S4-1 to Req-S4-50)

### Group S4-A: Server-Authoritative 90-Degree Tetromino Rotation (Milestone 1)
- **Req-S4-1 (Rotation Direction Actions):** The Python engine MUST support two discrete rotation operations:
  - **Clockwise (CW):** Increments the piece's orientation index.
  - **Counterclockwise (CCW):** Decrements the piece's orientation index.
- **Req-S4-2 (Deterministic Orientations):** Each of the 7 Tetromino types MUST support exactly 4 predefined orientations (`[0, 1, 2, 3]`), represented as lists of relative `(row, col)` cell coordinates. The orientation cycle is strictly cyclic (wrapping around `3 -> 0` and `0 -> 3`), not monotonic.
- **Req-S4-3 (Deterministic Pivots & Coordinate Sets):** The precise fixed pivots and relative coordinates `(row, col)` for each orientation of each piece MUST be:
  - **'I' piece:** Fixed Pivot `(row 1.5, col 1.5)`.
    - Orientation 0 (Spawn): `[(0, 0), (0, 1), (0, 2), (0, 3)]`
    - Orientation 1 (CW 90°): `[(0, 3), (1, 3), (2, 3), (3, 3)]`
    - Orientation 2 (CW 180°): `[(3, 0), (3, 1), (3, 2), (3, 3)]`
    - Orientation 3 (CW 270°): `[(0, 0), (1, 0), (2, 0), (3, 0)]`
  - **'O' piece:** No-rotation / Pivot None.
    - Orientations 0, 1, 2, 3: `[(0, 0), (0, 1), (1, 0), (1, 1)]` (strict no-op)
  - **'T' piece:** Fixed Pivot `(1, 1)`.
    - Orientation 0: `[(0, 1), (1, 0), (1, 1), (1, 2)]`
    - Orientation 1: `[(0, 1), (1, 1), (1, 2), (2, 1)]`
    - Orientation 2: `[(1, 0), (1, 1), (1, 2), (2, 1)]`
    - Orientation 3: `[(0, 1), (1, 0), (1, 1), (2, 1)]`
  - **'S' piece:** Fixed Pivot `(1, 1)`.
    - Orientation 0: `[(0, 1), (0, 2), (1, 0), (1, 1)]`
    - Orientation 1: `[(0, 1), (1, 1), (1, 2), (2, 2)]`
    - Orientation 2: `[(1, 1), (1, 2), (2, 0), (2, 1)]`
    - Orientation 3: `[(0, 0), (1, 0), (1, 1), (2, 1)]`
  - **'Z' piece:** Fixed Pivot `(1, 1)`.
    - Orientation 0: `[(0, 0), (0, 1), (1, 1), (1, 2)]`
    - Orientation 1: `[(0, 2), (1, 1), (1, 2), (2, 1)]`
    - Orientation 2: `[(1, 0), (1, 1), (2, 1), (2, 2)]`
    - Orientation 3: `[(0, 1), (1, 0), (1, 1), (2, 0)]`
  - **'J' piece:** Fixed Pivot `(1, 1)`.
    - Orientation 0: `[(0, 0), (1, 0), (1, 1), (1, 2)]`
    - Orientation 1: `[(0, 1), (0, 2), (1, 1), (2, 1)]`
    - Orientation 2: `[(1, 0), (1, 1), (1, 2), (2, 2)]`
    - Orientation 3: `[(0, 1), (1, 1), (2, 0), (2, 1)]`
  - **'L' piece:** Fixed Pivot `(1, 1)`.
    - Orientation 0: `[(0, 2), (1, 0), (1, 1), (1, 2)]`
    - Orientation 1: `[(0, 1), (1, 1), (2, 1), (2, 2)]`
    - Orientation 2: `[(1, 0), (1, 1), (1, 2), (2, 0)]`
    - Orientation 3: `[(0, 0), (0, 1), (1, 1), (2, 1)]`
- **Req-S4-4 (O Piece Excluded):** Any rotation command on the 'O' piece MUST return immediately without checking kicks, changing orientation, or altering the active piece state (strict no-op).
- **Req-S4-5 (Horizontal Kick Offsets):** When checking rotation validity, the engine MUST try column offsets in the exact horizontal order `dc = [0, -1, +1, -2, +2]`. No vertical offsets (row offsets) or vertical kicks are allowed.
- **Req-S4-6 (Valid Positions Gating):** The engine MUST apply the first column offset `dc` that produces a legal, unobstructed position on the 10x20 board (within column bounds `[0, 9]`, row bounds `[0, 19]`, and not overlapping any locked cells).
- **Req-S4-7 (Rotation Rejection Immutability):** If none of the 5 offsets produce a legal position, the rotation command MUST be fully rejected and the active piece's position, cells, orientation, board cells, score, lines, next, hold, and timers MUST remain completely unchanged (immutable on failure).
- **Req-S4-8 (Lifecycle Isolation):** Rotation does NOT by itself lock the piece, trigger gravity ticks, award points, change the level/lines count, or mutate the next/hold pieces.
- **Req-S4-9 (Spawn Orientation):** A piece MUST always enter play in its spawn orientation (Orientation 0), both when spawning from the top and when retrieved from the Hold container.
- **Req-S4-10 (Block Down & Gravity Semantics):** The inherited behavior where a manual "down" input or a gravity tick triggers immediate locking if the piece cannot move further down MUST be preserved exactly.
- **Req-S4-11 (API Contract Expansion):** The single-player game controllers MUST expose a new endpoint `POST /api/games/{id}/rotate` taking a JSON payload `{"direction": "cw" | "ccw"}` with `extra = "forbid"` configuration, or support rotation via direction parameters.

### Group S4-B: React Canvas 2D Board Rendering (Milestone 2)
- **Req-S4-12 (Canvas 2D Grid Board):** The 10-column by 20-row React DOM cells grid in `TetrisBoard` MUST be replaced with a single HTML `<canvas>` element.
- **Req-S4-13 (Board Coordinates Drawing):** The `<canvas>` element MUST render:
  - Every occupied/settled block on the 10x20 board with colors representing their Tetromino type.
  - The current active piece blocks on top with colors representing its type.
- **Req-S4-14 (Redraw Correctness):** The canvas MUST clear and redraw the updated grid and active piece correctly upon any state update (including movement, rotation, locking, line clears, game restarts, and window resizing).
- **Req-S4-15 (Device Pixel Ratio Scaling):** The canvas size and drawing context MUST scale based on the browser's device pixel ratio (`window.devicePixelRatio` or default to 1) to ensure crisp, high-resolution block edges at both DPR 1 and DPR 2, without blurring or stretching.
- **Req-S4-16 (UI Elements Retention):** All other game UI panels—specifically, Next Piece Preview, Hold Piece, Level, Score, Lines, Game Status, and Leaderboard—MUST remain React HTML DOM components.
- **Req-S4-17 (Keyboard Inputs Mapping):** The UI key handler MUST map the following keys:
  - `ArrowLeft` / `ArrowRight`: Move horizontal left / right.
  - `ArrowDown`: Move down (soft drop).
  - `ArrowUp`: Rotate Clockwise (CW).
  - `Z` / `z`: Rotate Counterclockwise (CCW).
  - `C` / `c`: Hold Piece.
- **Req-S4-18 (Double Board Visibility):** At a resolution of 1280x900, both the single-player board and the WebSocket duel boards MUST be completely visible on screen simultaneously without overlapping or requiring vertical scrolling.
- **Req-S4-19 (Accessible DOM Controls):** Accessible buttons/DOM panels for restart, hold, and other actions MUST remain operational.
- **Req-S4-20 (State Testability via Data Attributes):** To provide state diagnostics (not replacing visual checks but assisting Vitest), the `TetrisBoard` component MUST expose test-friendly data attributes on the canvas or wrapper elements:
  - `data-status`: Current game status (`"playing"`, `"game_over"`, etc.).
  - `data-active-piece-type`: Active piece type or `"none"`.
  - `data-active-piece-orientation`: Current active piece orientation (`0-3`) or `"none"`.
  - `data-board-hash`: A serialized representation of the board state to allow Vitest assertions to verify virtual state model changes.

### Group S4-C: WebSocket Real-time Duel Mode (Milestone 3)
- **Req-S4-21 (In-Memory Duel Rooms):** The backend MUST manage real-time duel rooms in memory. Multi-worker, distributed, or persistent duel storage is explicitly out-of-scope.
- **Req-S4-22 (WebSocket Route & Origin/Host Check):** The backend MUST expose a WebSocket endpoint `WS /api/ws/duel/{room_id}` that validates the `Origin` header against the Stage 4 restrictive origins policy to block CSWSH attacks and checks valid `Host` bindings.
- **Req-S4-23 (Client Handshake & Seat Authorization):** When a WebSocket client connects:
  - The first connection to `room_id` is assigned to `"player1"` (Left Board).
  - The second connection is assigned to `"player2"` (Right Board).
  - Subsequent connections to the same `room_id` MUST be immediately closed with code `4001` (Room Full).
  - The server MUST send an immediate handshake message confirming their assigned seat, room, and status.
- **Req-S4-24 (Start Gating & Shared Infinite Sequence):** The game MUST remain in `"waiting"` status until both `"player1"` and `"player2"` connections are active.
  - Upon starting, both players MUST receive the exact same deterministic sequence of tetrominoes.
  - To prevent sequence exhaustion, piece generation MUST use an infinite, O(1) random-access, seed-based mathematical function (e.g. hash of room seed + index) rather than a finite cache.
  - Both players advance through this sequence independently using their own piece index pointer.
- **Req-S4-25 (Independent Server-Side Gravity):** Server-side gravity timers MUST drive both players' boards independently of the client.
  - Each board has its own independent gravity tick timer derived from its own level.
  - Ticks are executed on the server, modifying state and broadcasting updates immediately.
- **Req-S4-26 (Versioned JSON Envelopes):** Client and server communication MUST follow complete, versioned JSON envelopes without any schema ellipsis or structural ambiguity.
- **Req-S4-27 (Revision Equality & Action Sequence Deduplication):** The action and revision lifecycles, duplicate filtering, stale/future revision rejection, and start gating behaviors MUST strictly follow the exact monotonic highwater and ACK rules specified in **`protocol-policy.md` Section 1**.
- **Req-S4-28 (Simultaneous Topout Evaluation):** The server-side gravity update and simultaneous topout evaluation MUST follow the single-tick assessment rules specified in **`protocol-policy.md` Section 5**.
- **Req-S4-29 (Forfeit and Win Outcomes):** Outcomes, forfeits, disconnections, and wait-state aborts MUST follow the precise win/forfeit/draw state transition rules specified in **`protocol-policy.md` Section 3.4**.
- **Req-S4-30 (Bounded Memory & Active Sweeping):** Finished room retention, waiting peer timeouts, playing idle timeouts, and background sweeping tasks MUST follow the exact timelines and sweeper behaviors specified in **`protocol-policy.md` Section 3.2**.
- **Req-S4-31 (No Solo Persistence Integration):** Duel scores, state, and outcomes MUST NOT be saved to the SQLite solo high scores database as specified in **`protocol-policy.md` Section 3.1**.
- **Req-S4-32 (Locking Strategy):** Room serialization, in-lock snapshots, and asynchronous out-of-lock broadcasts MUST follow the concurrency rules specified in **`protocol-policy.md` Section 5**.

### Group S4-D: Boundary & Error Mitigation Requirements
- **Req-S4-33 (Malformed/Oversized Message Rejection):** The WebSocket handler MUST reject malformed JSON (closing with code `1008`), binary messages (`1003` is binary ONLY), or UTF-8 messages exceeding 4KB in size (closing with code `1009` Message Too Big). Invalid text/UTF-8 transport data before ASGI closes with code `1007`.
- **Req-S4-34 (Message Rate Limiting):** The WebSocket server MUST rate-limit incoming client messages to at most 50 messages per second per client. Excess messages MUST cause the socket to close with code `1008` (Policy Violation).
- **Req-S4-35 (Seat Guard Authorization):** The server MUST reject any action message where the sender attempts to control the opponent's seat or manipulate scores directly, closing with code `1008` (Policy Violation).
- **Req-S4-36 (Graceful Network Failures):** Disconnections, write errors, or connection resets during game updates MUST NOT crash the FastAPI server. Exceptions MUST be caught gracefully, logging internal traces while preserving the remaining player's session.
- **Req-S4-37 (CORS Isolation):** Dual WebSockets and HTTP endpoints must retain Stage 3 CORS constraints. Only documented exact local Stage 4 origins (`http://localhost:5515` and `http://127.0.0.1:5515`) are allowed credentials access. Wildcards (`"*"`) are strictly forbidden.

### Group S4-E: Testing, Benchmarking & Infrastructure Controls
- **Req-S4-38 (Real-Browser Visual occupied-cell checks):** Visual testing MUST require actual production-browser occupied-cell/color checks at DPR 1 and DPR 2 after move, CW, CCW, lock, clear, restart, and resize events. Same-count moved-cell tests and unchanged-board no-op checks must be run to detect stale drawing.
- **Req-S4-39 (Traceable Task Gating):** All tasks inside the development checklist remain OPEN until executed. No milestones may be marked complete before actual execution.
- **Req-S4-40 (Dated Native Notes Directive):** A dated native note MUST be written in `session_notes.md` or `requirements.md` BEFORE every generated code, test, infrastructure, or benchmark correction, not after.
- **Req-S4-41 (Deterministic Mockable Clocks):** The backend MUST support injectable monotonic clocks to allow fast-forwarding of time in tests, preventing test suites from having to sleep or wait minutes for room sweepers or timeouts.
- **Req-S4-42 (CORS Origin Matching):** Standard HTTP endpoints and WebSocket connection checks must strictly validate exact matching of the `Origin` header.
- **Req-S4-43 (Solo Game Creation Heritage):** Single-player game creation must remain a standard HTTP POST returning status `200 OK` as inherited from Stage 3.
- **Req-S4-44 (No Double Outcomes):** Outcome delivery for a finished duel must occur exactly once, tolerating subsequent socket retries or no-op/resend requests by returning the cached finished room state.
- **Req-S4-45 (Sonar Quality Gates):** New or modified files must meet strict quality metrics: Sonar NEW Line Coverage >= 80%, duplication rate <= 3%, and new static analysis findings = 0.
- **Req-S4-46 (CI Execution & Non-Root Docker):** The Docker environment must execute backend and proxy processes under non-root users (UID 10001 for backend, 101 for frontend) and persist solo high scores on a named volume.
- **Req-S4-47 (Playground/Benchmark Control):** The benchmark suite must be executed with a real Chromium browser in the foreground with sandbox enabled, at viewport 1280x900 and DPR 1, using foreground active focus gating.
- **Req-S4-48 (rAF and Frame Recording separation):** In benchmarks, frame scheduling via `requestAnimationFrame` must be recorded separately from verified Canvas visual draws.
- **Req-S4-49 (Visual Frame Latency Correlation):** Benchmarks must correlate input event keys/timestamps and ACK/revision/target cell changes to an actual changed rendered 200-cell RGBA pixel mask, not merely state value updates.
- **Req-S4-50 (Outcome Truthfulness):** Unachievable stable/100% test or latency targets must not be claimed as guaranteed; all measurements must be reported truthfully.

---

## 3. Mathematical Rotation Specifications & Hand-Authored Assertions

To guarantee absolute rigid 90-degree turning around a single fixed pivot, the Python core engine and the JSDOM/production-browser unit tests must comply with the following deterministic mathematical specifications:

### 3.1 Pivot Formulas
1. **For 'I' Tetromino (Fixed Pivot `(1.5, 1.5)`):**
   - Let `(r, c)` be the coordinates of a block relative to the piece's bounding box.
   - Clockwise (CW) Rotation:
     $$r' = 1.5 + (c - 1.5) = c$$
     $$c' = 1.5 - (r - 1.5) = 3 - r$$
   - Counterclockwise (CCW) Rotation:
     $$r' = 1.5 - (c - 1.5) = 3 - c$$
     $$c' = 1.5 + (r - 1.5) = r$$

2. **For non-I, non-O Tetrominoes (Fixed Pivot `(1, 1)`):**
   - Clockwise (CW) Rotation:
     $$r' = 1 + (c - 1) = c$$
     $$c' = 1 - (r - 1) = 2 - r$$
   - Counterclockwise (CCW) Rotation:
     $$r' = 1 - (c - 1) = 2 - c$$
     $$c' = 1 + (r - 1) = r$$

3. **For 'O' Tetromino (No Pivot):**
   - Rotation commands are a strict no-op. Coordinate set is permanently `[(0, 0), (0, 1), (1, 0), (1, 1)]`.

---

### 3.2 Hand-Authored Exact-Cell Assertions Table (Open Space)

The following tables define the exact relative coordinate sets `[(row, col)]` (sorted lexicographically) for all 7 tetrominoes in open space across all 4 cyclic orientations:

| Piece | Orientation 0 (Spawn) | Orientation 1 (CW 90°) | Orientation 2 (CW 180°) | Orientation 3 (CW 270°) |
|---|---|---|---|---|
| **I** | `[(0,0), (0,1), (0,2), (0,3)]` | `[(0,3), (1,3), (2,3), (3,3)]` | `[(3,0), (3,1), (3,2), (3,3)]` | `[(0,0), (1,0), (2,0), (3,0)]` |
| **O** | `[(0,0), (0,1), (1,0), (1,1)]` | `[(0,0), (0,1), (1,0), (1,1)]` | `[(0,0), (0,1), (1,0), (1,1)]` | `[(0,0), (0,1), (1,0), (1,1)]` |
| **T** | `[(0,1), (1,0), (1,1), (1,2)]` | `[(0,1), (1,1), (1,2), (2,1)]` | `[(1,0), (1,1), (1,2), (2,1)]` | `[(0,1), (1,0), (1,1), (2,1)]` |
| **S** | `[(0,1), (0,2), (1,0), (1,1)]` | `[(0,1), (1,1), (1,2), (2,2)]` | `[(1,1), (1,2), (2,0), (2,1)]` | `[(0,0), (1,0), (1,1), (2,1)]` |
| **Z** | `[(0,0), (0,1), (1,1), (1,2)]` | `[(0,2), (1,1), (1,2), (2,1)]` | `[(1,0), (1,1), (2,1), (2,2)]` | `[(0,1), (1,0), (1,1), (2,0)]` |
| **J** | `[(0,0), (1,0), (1,1), (1,2)]` | `[(0,1), (0,2), (1,1), (2,1)]` | `[(1,0), (1,1), (1,2), (2,2)]` | `[(0,1), (1,1), (2,0), (2,1)]` |
| **L** | `[(0,2), (1,0), (1,1), (1,2)]` | `[(0,1), (1,1), (2,1), (2,2)]` | `[(1,0), (1,1), (1,2), (2,0)]` | `[(0,0), (0,1), (1,1), (2,1)]` |

---

### 3.3 Hand-Authored Specific Verification Assertions

1. **Four-Cycle Verification in Open Space:**
   - **CW Cycle:** Starting in Orientation 0, executing CW 4 times MUST yield Orientations `[1, 2, 3, 0]` sequentially. The active cells at index 4 MUST exactly match those at index 0.
   - **CCW Cycle:** Starting in Orientation 0, executing CCW 4 times MUST yield Orientations `[3, 2, 1, 0]` sequentially. The active cells at index 4 MUST exactly match those at index 0.
   - Verified for all 7 pieces.
2. **O Piece Isolation:**
   - Any CW or CCW command on 'O' must immediately succeed but leave orientation at 0 and coordinates at `[(0, 0), (0, 1), (1, 0), (1, 1)]`. No collision or kick checks are performed.
3. **Kick Priority Resolvers:**
   - **Right Wall Kick:** Given 'I' piece at `(0, 7)` (relative col offset `col = 7`), attempting CW rotation:
     - Kick 0 (`dc = 0`): Coordinates would be `[(0, 10), (1, 10), (2, 10), (3, 10)]` -> Exceeds right wall boundary `col = 9` (FAILED).
     - Kick 1 (`dc = -1`): Coordinates would be `[(0, 9), (1, 9), (2, 9), (3, 9)]` -> Inside bounds, succeeds!
     - Result: Orientation changes to 1, column offset shifts left by 1.
   - **Left Wall Kick:** Given 'I' piece at `(0, -1)` (relative col offset `col = -1`), attempting CW rotation:
     - Kick 0 (`dc = 0`): Col 3 would be `-1 + 3 = 2`. Wait, Col 0 is `-1 + 0 = -1` -> Exceeds left wall boundary `col = 0` (FAILED).
     - Kick 1 (`dc = -1`): Shift left -> Exceeds further (FAILED).
     - Kick 2 (`dc = +1`): Coordinates would be `[(0, 3), (1, 3), (2, 3), (3, 3)]` -> Col 0 is `-1 + 1 + 0 = 0`, inside bounds! Succeeds!
     - Result: Orientation changes to 1, column offset shifts right by 1.
4. **Floor & Obstacle Full Rejection:**
   - **Floor Rejection:** Given 'I' piece at `row = 18`, relative coordinates of Orientation 1 would place a block at `18 + 3 = 21` (which is > 19 floor bound). If trying to rotate CCW/CW, and no horizontal kick `dc` in `[0, -1, +1, -2, +2]` can move all blocks inside the `[0, 19]` row bounds, the rotation is fully rejected.
   - **Obstacle Rejection:** Given 'I' piece at `row = 5, col = 3` surrounded by locked cells on both sides. Attempting rotation: all 5 horizontal kicks `dc = [0, -1, +1, -2, +2]` overlap with a locked cell.
   - **Immutability verification:** On full rejection, the engine MUST assert that the active piece's row, col, orientation, board cells, score, lines, level, next, hold, and gravity timers are unchanged.
5. **Spawn, Hold & Terminal State Interactions:**
   - **Spawn:** Newly spawned tetrominoes MUST have `orientation = 0` and be centered.
   - **Hold Retrieve:** Retrieving a tetromino from Hold (even if it was held while rotated) MUST place it at `(0, 3)` with `orientation = 0`.
   - **Terminal Game Rejection:** If the game is in `game_over` state, rotation requests MUST return a `400 Bad Request` or a rejected ACK.
6. **Rotated Movement, Gravity, and Lock:**
   - **Movement:** A rotated piece (e.g. 'I' in Orientation 1) MUST move left/right correctly based on its rotated cells.
   - **Gravity & Lock:** If a rotated piece cannot move further down, the next gravity tick or manual soft-drop MUST lock it into the board in its exact rotated configuration, clearing lines if applicable.

---

## 4. Real-time WebSocket Protocol & Canonical JSON Schemas (No Ellipsis)

All real-time communications MUST comply strictly with the canonical JSON schemas defined in `specs/stage4/duel-protocol.schema.json`. Any earlier conflicting drafts or legacy message patterns in this specification are **fully and explicitly superseded**.

### 4.1 Canonical Protocol Definition
Our real-time duel mode uses a strict JSON-enveloped messaging convention under version `"1.0"`. Every message exchanged between clients and the server contains top-level properties `"version"`, `"type"`, and `"payload"`.

- **Strict Type Validation:** Standard integers MUST NOT be passed as floats or quoted string representations (such as `"12"`); float, string, or boolean coercion for revision fields is strictly rejected.
- **Seat Authorization Guard:** Client messages targeting or attempting to control the opponent's seat or forge authoritative state will result in immediate connection closure with code `1008` (Policy Violation).
- **Graceful Unjoined Seat Representation:** A seat without a connected player is represented as `null` in player boards and client ID fields, avoiding dummy or fake placeholder objects.

### 4.2 Message Wire Format Examples
The following fenced JSON blocks illustrate exact compliant structures that parse completely as valid JSON.

#### 4.2.1 Client Handshake Message
Sent by the client upon connecting to authenticate and request a seat in a room.
```json
{
  "version": "1.0",
  "type": "handshake",
  "payload": {
    "room_id": "room_abc123",
    "client_id": "client_99xyz"
  }
}
```

#### 4.2.2 Server Handshake Response
Sent immediately by the server to the connected client to assign their seat. This shows player 1 connected and player 2 absent (unjoined seat represented as `null`).
```json
{
  "version": "1.0",
  "type": "handshake",
  "payload": {
    "room_id": "room_abc123",
    "seat": "player1",
    "status": "waiting",
    "player1_id": "client_99xyz",
    "player2_id": null
  }
}
```

#### 4.2.3 Client Action Message
Sent by a player's client to perform a board mutation (move, rotate, or hold). It carries a client-monotonic integer `action_id` and the client's `expected_revision`.
```json
{
  "version": "1.0",
  "type": "action",
  "payload": {
    "action_id": 1,
    "action_type": "rotate",
    "direction": "cw",
    "expected_revision": 0
  }
}
```

#### 4.2.4 Server ACK Message
Sent by the server to acknowledge a specific player action. The `authoritative_board` contains the exact 20x10 cell arrays of the state of the player's board.
```json
{
  "version": "1.0",
  "type": "ack",
  "payload": {
    "action_id": 1,
    "status": "accepted",
    "reason": "Successfully rotated active tetromino clockwise",
    "board_revision": 1,
    "room_revision": 1,
    "authoritative_board": {
      "id": "board_player1_uuid",
      "board": [
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null]
      ],
      "active_piece": {
        "type": "T",
        "origin": [0, 3],
        "cells": [
          [0, 4],
          [1, 4],
          [1, 5],
          [2, 4]
        ],
        "orientation": 1
      },
      "status": "playing",
      "score": 0,
      "total_lines": 0,
      "level": 1,
      "gravity_interval_ms": 500,
      "next_piece": "I",
      "hold_piece": null,
      "can_hold": true,
      "board_revision": 1
    }
  }
}
```

#### 4.2.5 Server State Update Message
Broadcast to both clients upon any room-wide state change (gravity tick, player action, game over, or player disconnect forfeit). It includes the detailed 20x10 boards of both seats.
```json
{
  "version": "1.0",
  "type": "state_update",
  "payload": {
    "room_id": "room_abc123",
    "room_revision": 24,
    "status": "playing",
    "player1_board": {
      "id": "board_player1_uuid",
      "board": [
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        ["I", "I", "I", "I", null, null, "O", "O", "O", "O"]
      ],
      "active_piece": {
        "type": "T",
        "origin": [0, 3],
        "cells": [
          [0, 4],
          [1, 4],
          [1, 5],
          [2, 4]
        ],
        "orientation": 1
      },
      "status": "playing",
      "score": 100,
      "total_lines": 1,
      "level": 1,
      "gravity_interval_ms": 500,
      "next_piece": "I",
      "hold_piece": null,
      "can_hold": true,
      "board_revision": 12
    },
    "player2_board": {
      "id": "board_player2_uuid",
      "board": [
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, "S", "S", "Z", "Z"]
      ],
      "active_piece": {
        "type": "O",
        "origin": [0, 3],
        "cells": [
          [0, 3],
          [0, 4],
          [1, 3],
          [1, 4]
        ],
        "orientation": 0
      },
      "status": "playing",
      "score": 0,
      "total_lines": 0,
      "level": 1,
      "gravity_interval_ms": 500,
      "next_piece": "J",
      "hold_piece": null,
      "can_hold": true,
      "board_revision": 12
    },
    "winner_seat": null,
    "outcome_reason": null
  }
}
```

#### 4.2.6 Server Error Message
Sent by the server to a client to signal a validation failure or protocol error before socket termination.
```json
{
  "version": "1.0",
  "type": "error",
  "payload": {
    "error_code": 1008,
    "message": "Policy Violation: Seat Ownership Validation Failed"
  }
}
```

---

## 5. Bounded Resources & Concurrency Logic

To prevent denial-of-service and thread starvation under heavy load, the real-time websocket server MUST implement strict boundaries:

1. **Room Boundaries:**
   - Room IDs MUST be alphanumeric strings, length `[1, 64]`.

---

## 5. Bounded Resources & Concurrency Logic

To prevent denial-of-service and thread starvation under heavy load, the real-time websocket server MUST implement strict boundaries:

1. **Room Boundaries:**
   - Room IDs MUST be alphanumeric strings, length `[1, 64]`.
   - Globally active room count MUST NOT exceed 100 in-memory rooms. Connection requests to create or join beyond 100 active rooms must be immediately closed with code `1008` (Policy Violation).
2. **Bandwidth & Rate Boundaries:**
   - Message size limit: any UTF-8 text message exceeding 4096 bytes MUST be immediately rejected, closing the socket with code `1009` (Message Too Big).
   - Inbound rate limit: at most 50 messages per second per client socket. If a client exceeds this, the socket must be immediately closed with code `1008` (Policy Violation).
3. **Pending Outbound Buffer Boundaries:**
   - The outbound broadcast queue per client must be bounded to a maximum of 100 messages. If a slow client lags and causes this buffer to overflow, the server must close the connection to prevent memory leak accumulation.
4. **Timeouts:**
   - Handshake Hello Deadline: Exactly 10 seconds. The first valid handshake message (client_handshake) must be received within 10 seconds of establishing the socket connection. Failure to do so results in connection termination. This is not a deadline for the second player to arrive.
   - Waiting Peer Timeout: Exactly 120 seconds. If a room remains in "waiting" status with only one player for more than 120 seconds, the room is aborted with outcome reason "waiting-peer-timeout" and winner seat null.
   - Playing Idle Timeout: Exactly 120 seconds. If no action is received from either player in "playing" status for more than 120 seconds, the room is aborted with outcome reason "operational-abort" and winner "draw".
   - Finished Room Retention: Exactly 300 seconds of inactivity taking precedence. Once a game finishes, the final state is preserved for exactly 300 seconds of inactivity before deletion.
5. **Infinite Piece Generation Sequence:**
   - Rather than allocating a fixed-length array, the server and clients MUST compute the `i`-th piece type on demand.
   - The pseudo-random O(1) piece selection function is defined as:
     $$piece\_index = \text{index of piece requested}$$
     $$hash\_val = \text{hash}(room\_seed + \text{"\_"} + str(piece\_index))$$
     $$piece\_type = PIECES[hash\_val \pmod 7]$$
     where $PIECES = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']$.
     This ensures infinite continuation with zero array memory overhead.
6. **Short Lock Snapshotting Pattern:**
   - Any state modification (e.g. client actions or gravity tick evaluations) MUST run inside an `asyncio.Lock` specific to that room.
   - Once the mutation is done, a deep-copy/snapshot of the room state is generated, and the lock is released.
   - The actual sending of the JSON state updates to the player sockets is performed OUTSIDE of the room lock, avoiding any network socket delay blocking the main engine loop or other rooms.
7. **Injectable Monotonic Clocks:**
   - The cleanup background pruner and game loop must query time through an injectable clock class or mockable method (e.g. `Clock.get_time()`). This allows unit tests to instantly fast-forward 2 or 5 minutes, verifying sweeper cleanup of finished and idle rooms without any real-time waiting.

---

## 6. Canvas Rendering & Real-Browser Visual Assertions

The 10x20 cell-grid board must render via a high-performance `<canvas>` element. The visual rendering system is subject to the following rules:

### 6.1 Layout & Sizing
- Both single-player and dual-player canvas boards must fit completely within a 1280x900 viewport without overlapping.
- Back-buffer dimensions of the `<canvas>` MUST scale by `window.devicePixelRatio` (supporting DPR 1 and DPR 2), while CSS sizing matches container boundaries, guaranteeing perfectly sharp block borders on high-DPI screens.

### 6.2 Real-Browser Visual Verification (No Diagnostic Substitutions)
- **State diagnostics only:** While `data-` attributes (e.g. `data-board-hash`) are exposed for Vitest virtual DOM checking, they are only diagnostic tools. They NEVER guarantee that physical pixels are drawn correctly or that the browser isn't showing a stale/blank frame.
- **Mandatory Browser Checks:** Real-browser visual pixel color tests (using automated Chromium Playwright tests) are required at both DPR 1 and DPR 2.
- **Specific Visual Assertion Cases:**
  1. **Draw occupied cells:** After a block locks into the board, verify that the coordinate center of that cell on the canvas contains the exact RGBA color matching its Tetromino type.
  2. **Move/Rotate pixel shift:** After a left/right shift or rotation, verify that the previous coordinate pixels are now empty/background color, and the new target coordinates are filled with the correct piece color.
  3. **Same-count verification:** Verify that the number of occupied-color pixel centers on the canvas is exactly identical before and after rotation (confirming no block was lost or duplicated during rendering).
  4. **Unchanged-board no-op check:** If a rotation is rejected, or a move hits a wall, verify that the canvas does not repaint or change any pixel values (detecting and preventing redundant drawing cycles).
- **Historical Evidence Preservation:** Legacy React DOM cell class-name assertions are preserved as historical evidence of Stage 3 behavior. JSDOM virtual tests do not replace the Chromium pixel checks but run alongside them.

---

## 7. Quality Gates & Multi-Tier Verification Matrix

All development modifications must be checked against the following quality gates:

### 7.1 SonarQube & Coverage Targets
- **Sonar NEW Line Coverage:** >= 80% on all newly introduced code (backend and frontend).
- **Sonar Duplication Gate:** <= 3% across modified files.
- **Sonar New Static Findings:** Exactly 0 new bugs, security vulnerabilities, or code smells.
- **Disclose errors:** Any static analysis finding or coverage deficit must fail the build automatically.

### 7.2 Traceable Tasks Checklist
The following traceability checklist remains strictly OPEN until the execution phase is reached:

- [ ] **Req-S4-1 to S4-11 (M1 Python Rotation Core):** Implement rigid 90-degree CW/CCW rotations, pivots, horizontal wall-kicks, and isolated API endpoints. [OPEN]
- [x] **Req-S4-12 to S4-20 (M2 Canvas 2D Rendering):** Replace DOM with sharp DPR 1/2 scaled Canvas drawing, preserving UI panels and exposing JSDOM state attributes. [COMPLETE]
- [ ] **Req-S4-21 to S4-32 (M3 WebSocket Real-time Duel):** Build room-locked, seat-authorized, server-gravity WebSocket duel rooms with sequence hashing and short-lock sends. [OPEN]
- [ ] **Req-S4-33 to S4-37 (Error Mitigation & CORS):** Implement rate limiting, oversized/binary UTF-8 rejection, and restrictive localhost Stage 4 CORS policies. [OPEN]
- [ ] **Req-S4-38 (Real-Browser Visual Suite):** Automated Chromium visual color-checks at DPR 1 and 2 for moves, rotations, rejections, locks, and resets. [OPEN]
- [ ] **Req-S4-39 (Servercore / Wire Race tests):** Test suite evaluating concurrent WebSocket messages, race conditions, and out-of-order action discards. [OPEN]
- [ ] **Req-S4-40 (Active Room Sweeper test):** Unit tests verifying idle/finished room sweepers using injectable monotonic clocks. [OPEN]
- [ ] **Req-S4-41 (Non-root Docker Compose):** Deploy non-root Compose container network (backend 10001, frontend 101) with persistent SQLite database volume. [OPEN]
- [ ] **Req-S4-42 (Chromium Benchmark Suite):** Execute 6 timed trials (3 solo, 3 duel) in foreground Chrome 1280x900 with active focus gating, logging frame rate and latencies. [OPEN]

---

## 8. Dated Notes Requirement
For any future implementation phase: a dated native note MUST be written in the specifications/session_notes files BEFORE any code, test, infrastructure, or benchmark correction is generated.
This requirement is mandatory and takes absolute precedence over any automatic workflow.

---

## 9. Milestone 3 Detailed Forward Contract Specifications & Wire Formats
To ensure robust, real-time, two-player real-time WebSocket duels under Milestone 3 without any architectural gaps, the design must comply with the following forward contracts:

### 9.1 Deterministic Shared Tetromino Sequence Generator
- **Hash Algorithm:** To ensure a portable, identical sequence of piece types across players, the piece generator uses the SHA256 algorithm with UTF-8 encoding.
- **Formula:** `digest = SHA256(room_seed + "_" + piece_index)`
- **Piece Type Resolution:** The piece type is derived by converting the digest bytes into an unsigned integer (take the first 4 bytes of the digest big-endian) and applying modulo 7:
  `piece_type = PIECES[unsigned_digest_integer % 7]`
  Where PIECES is defined in the fixed ordering: `['I', 'O', 'T', 'S', 'Z', 'J', 'L']`.
- **Server Ownership:** The sequence and indices are fully calculated and stored on the server. The client piece list or local RNG is never trusted.
- **Index Management & Piece Consumption Flow:**
  - Piece indexes are infinite and independent per board.
  - A board starts with piece index 0 as its active piece (`active0`) and index 1 as its next piece (`next1`).
  - Upon a piece lock event:
    - The `next` piece index becomes the `active` piece.
    - The player's piece index pointer increments by 1.
    - The new `next` piece is fetched from `piece_index`.
  - Upon first Hold command:
    - The active piece is stored in the hold slot.
    - The `next` piece becomes active.
    - The piece index pointer increments by 1 to retrieve a new `next` piece.
  - Upon swap Hold command:
    - The active piece is swapped with the held piece.
    - The piece index pointer does NOT increment, and the `next` piece remains unchanged.
  - Lifecycle isolation: The piece provider is isolated per board (per-board piece provider instance) and is NOT shared with the global single-player solo RNG.

### 9.2 Unified Monolithic Authoritative Server Board Schema
To prevent any structural inconsistencies between single-player and multiplayer renderings, the server maintains and sends ONE consistent exact board schema for each player's board.
The JSON schema of a board (for a single seat) MUST contain exactly:
```json
{
  "id": "board_player1_uuid",
  "board": [
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null, null, null]
  ],
  "active_piece": {
    "type": "T",
    "origin": [0, 3],
    "cells": [
      [0, 4],
      [1, 4],
      [1, 5],
      [2, 4]
    ],
    "orientation": 1
  },
  "status": "playing",
  "score": 0,
  "total_lines": 0,
  "level": 1,
  "gravity_interval_ms": 500,
  "next_piece": "I",
  "hold_piece": null,
  "can_hold": true,
  "board_revision": 1
}
```
*Note: Board revision is a monotonic integer starting at 0, incremented with every successful state mutation on that board.*

### 9.3 Monotonic Room/Event Revision and Concurrency Control
- **Monotonic Revisions:** The duel room itself maintains a monotonic integer `room_revision` (or event sequence number) starting at 0. Any event (player joins, action ACK, outcome broadcast, gravity tick) increment the room revision.
- **Strict Data Types:** All message identifiers, action IDs, and room revisions must be strict integers (type `int` in Python, standard integer numbers in JSON). Boolean values, float representation, or coerced string-formatted numbers (e.g. `"123"`) MUST be rejected on receipt.
- **ACK Message Schema:**
  - Every valid client action receives a formal ACK.
  - The ACK message JSON shape is:
    ```json
    {
      "version": "1.0",
      "type": "ack",
      "payload": {
        "action_id": 1,
        "status": "accepted",
        "reason": "Successfully rotated active tetromino clockwise",
        "board_revision": 1,
        "room_revision": 1,
        "authoritative_board": {
          "id": "board_player1_uuid",
          "board": [
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null, null, null]
          ],
          "active_piece": {
            "type": "T",
            "origin": [0, 3],
            "cells": [
              [0, 4],
              [1, 4],
              [1, 5],
              [2, 4]
            ],
            "orientation": 1
          },
          "status": "playing",
          "score": 0,
          "total_lines": 0,
          "level": 1,
          "gravity_interval_ms": 500,
          "next_piece": "I",
          "hold_piece": null,
          "can_hold": true,
          "board_revision": 1
        }
      }
    }
    ```
- **Sender Sockets Non-blocking Architecture:**
  - Broadcast queues per player MUST be bounded (e.g. maximum 100 queued events).
  - Outgoing writes to a player's socket MUST enforce a short write timeout (e.g., 200ms) outside any room-wide state locks, so that a slow or lagging client socket does not stall the gravity ticker or block the other player.
  - Active room tasks must support clean shutdown/draining and immediate task cancellation upon room deletion.

### 9.4 Duel Room Retention Policy
- **Retention Rules:**
  - **Finished Room:** A room that has ended (status `"finished"`) is retained in memory for exactly 5 minutes of inactivity before deletion, allowing clients to query final outcome results. This takes absolute precedence over the idle deletion policy.
  - **Idle Room:** A room that has been inactive or waiting for players without any state mutations for more than 2 minutes is automatically cleaned up and purged from memory.
  - **Active Sweeper:** An active background sweeper task runs once every 60 seconds on the server.
  - **Injectable Monotonic Clock:** To ensure fast, deterministic tests without arbitrary sleep delays, the sweeper and room tasks must utilize an injectable clock provider (interface `Clock`) instead of calling `time.time()` or `asyncio.sleep()` directly.
  - **No Resurrection:** Once a room is cleaned up or transitioned to `"finished"`, it is permanently locked; players cannot rejoin a finished room as active or resurrect it.

### 9.5 WebSocket Host, Origin, and Dependency Policy
- **Host & Origin Check:** The real-time server strictly validates the `Origin` header.
  - Allowed origins list: `http://localhost:5515`, `http://127.0.0.1:5515`, `http://localhost:3000`, `http://127.0.0.1:3000`.
  - Same-host/port validation must be enforced. If Nginx is proxying WebSockets, the proxy configuration MUST pass `$http_host` (retaining the port 5515) rather than `$host` (which strips the port).
- **Required Runtime Engine:** The backend MUST utilize `websockets` or `anyio` as the native WebSocket engine.
- **draining-draining handshakes:** Test cases verifying WebSocket handshake/handshake and disconnection behavior using `TestClient` MUST support close draining, validating that initial state frames or handshakes are successfully popped from the client receiver queue before closing the socket.
