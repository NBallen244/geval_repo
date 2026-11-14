# Research Report: Tetris Stage 4 Option A Technical Specifications

## 1. Authoritative 90-Degree Tetromino Rotation & Wall-Kick Algorithm [ROT-01, ROT-02, ROT-03]

The rotation mechanism must be authoritatively computed on the backend server within the game engine. Each tetromino has orientations mapped relative to its pivot point (`origin`).

### 1.1 Tetromino Coordinate Definitions and Mapping
Tetrominoes spawn at specific positions with Orientation 0. Below is the mapping of each tetromino's relative offsets. All coordinates are indexed as `[row, col]` where `0 <= row <= 19` and `0 <= col <= 9`.

- **I Piece** (Pivot `[0, 4]` at spawn):
  - Orientation 0: `[[0, -1], [0, 0], [0, 1], [0, 2]]`  -> Spawn: `[[0, 3], [0, 4], [0, 5], [0, 6]]`
  - Orientation 1: `[[-1, 0], [0, 0], [1, 0], [2, 0]]`
  - Orientation 2: `[[0, -2], [0, -1], [0, 0], [0, 1]]`
  - Orientation 3: `[[-2, 0], [-1, 0], [0, 0], [1, 0]]`
- **O Piece** (Pivot `[0, 4]` at spawn, rotation is a strict no-op):
  - All orientations (0, 1, 2, 3) are identical: `[[0, 0], [0, 1], [1, 0], [1, 1]]` (Rotation is a strict, state-invariant no-op. Position, pivot, and orientation values remain unchanged). -> Spawn: `[[0, 4], [0, 5], [1, 4], [1, 5]]`
- **T Piece** (Pivot `[1, 4]` at spawn):
  - Orientation 0: `[[-1, 0], [0, -1], [0, 0], [0, 1]]` -> Spawn: `[[0, 4], [1, 3], [1, 4], [1, 5]]`
  - Orientation 1: `[[-1, 0], [0, 0], [0, 1], [1, 0]]`
  - Orientation 2: `[[0, -1], [0, 0], [0, 1], [1, 0]]`
  - Orientation 3: `[[-1, 0], [0, -1], [0, 0], [1, 0]]`
- **S Piece** (Pivot `[1, 4]` at spawn):
  - Orientation 0: `[[-1, 0], [-1, 1], [0, -1], [0, 0]]` -> Spawn: `[[0, 4], [0, 5], [1, 3], [1, 4]]`
  - Orientation 1: `[[-1, 0], [0, 0], [0, 1], [1, 1]]`
  - Orientation 2: `[[0, 0], [0, 1], [1, -1], [1, 0]]`
  - Orientation 3: `[[-1, -1], [0, -1], [0, 0], [1, 0]]`
- **Z Piece** (Pivot `[1, 4]` at spawn):
  - Orientation 0: `[[-1, -1], [-1, 0], [0, 0], [0, 1]]` -> Spawn: `[[0, 3], [0, 4], [1, 4], [1, 5]]`
  - Orientation 1: `[[-1, 1], [0, 0], [0, 1], [1, 0]]`
  - Orientation 2: `[[0, -1], [0, 0], [1, 0], [1, 1]]`
  - Orientation 3: `[[-1, 0], [0, -1], [0, 0], [1, -1]]`
- **J Piece** (Pivot `[1, 4]` at spawn):
  - Orientation 0: `[[-1, -1], [0, -1], [0, 0], [0, 1]]` -> Spawn: `[[0, 3], [1, 3], [1, 4], [1, 5]]`
  - Orientation 1: `[[-1, 0], [-1, 1], [0, 0], [1, 0]]`
  - Orientation 2: `[[0, -1], [0, 0], [0, 1], [1, 1]]`
  - Orientation 3: `[[-1, 0], [0, 0], [1, -1], [1, 0]]`
- **L Piece** (Pivot `[1, 4]` at spawn):
  - Orientation 0: `[[-1, 1], [0, -1], [0, 0], [0, 1]]` -> Spawn: `[[0, 5], [1, 3], [1, 4], [1, 5]]`
  - Orientation 1: `[[-1, 0], [0, 0], [1, 0], [1, 1]]`
  - Orientation 2: `[[0, -1], [0, 0], [0, 1], [1, -1]]`
  - Orientation 3: `[[-1, -1], [-1, 0], [0, 0], [1, 0]]`

### 1.2 Wall-Kick and Offset Application Order
When a rotation instruction (`"cw"` or `"ccw"`) is received:
1. Increment or decrement the orientation index modulo 4:
   - Clockwise (`cw`): `new_orientation = (current_orientation + 1) % 4`
   - Counterclockwise (`ccw`): `new_orientation = (current_orientation - 1) % 4`
2. Retrieve the relative offsets for `new_orientation` corresponding to the active tetromino type.
3. Test candidates using horizontal column offsets applied to the current pivot position in the strict order: `0, -1, +1, -2, +2`.
4. For each offset `dx` in `[0, -1, +1, -2, +2]`:
   - Compute proposed cells: `[[row_pivot + dr, col_pivot + dc + dx] for dr, dc in offsets]`
   - Verify that all cells lie within board bounds (row `[0, 19]`, column `[0, 9]`) and do not collide with settled cells in the board matrix.
   - The first candidate `dx` that satisfies this check is applied: the active piece cells are updated, the pivot column is shifted by `dx`, and the new orientation index is locked.
5. If none of the five horizontal candidates is valid, the entire rotation is rejected: position, pivot, and orientation remain completely unchanged.
6. Rotation is a pure positioning mutation: it must never trigger line locks, gravity updates, points, or hold transitions.

## 2. High-DPI Canvas 2D Board Rendering [CAN-01, CAN-02]

To transition board rendering from individual React DOM nodes to HTML5 Canvas 2D, the canvas drawing pipeline must scale matching the display density.

### 2.1 Display Density & Scaling Mechanics
Modern screens use a high device pixel ratio (`window.devicePixelRatio > 1`). Direct 1:1 pixel rendering on a standard canvas results in blurry images because CSS pixels do not align with physical device pixels.
- The canvas dimensions must be configured programmatically on component mount, screen resize, and DPR change:
  ```typescript
  const dpr = window.devicePixelRatio || 1;
  canvas.width = cssWidth * dpr;
  canvas.height = cssHeight * dpr;
  canvas.style.width = `${cssWidth}px`;
  canvas.style.height = `${cssHeight}px`;
  ```
- After resizing the backing store, the 2D drawing context must scale all coordinates up:
  ```typescript
  ctx.scale(dpr, dpr);
  ```
- Canvas redraws must occur programmatically on every state change (falling piece movement, locking, line clears, etc.).

### 2.2 Testing & Objective Verification Strategy
- Traditional React DOM tests checking for `.board-grid` or `div.cell` elements must be decommissioned.
- New unit and component tests will verify:
  - The `<canvas>` element mounts successfully.
  - A window resize or orientation event triggers the scaling function.
  - Programmatic checks verify that `canvas.width === cssWidth * window.devicePixelRatio`.
- Visual regression is verified through Playwright tests by capturing automated screenshots or verifying pixel structures tied directly to game states (using actual pixel/checksum checks).

## 3. Real-Time WebSockets Duel [NET-01, NET-02, NET-03, INF-01]

The two-player duel mode utilizes same-origin WebSockets to synchronize boards. It is built using FastAPI's standard WebSocket handler, running under a single-worker process to permit lightweight, thread-safe, in-memory room management.

### 3.1 Handshake Security & Room Management
- **Handshake Origin Check**: Server validates the `Origin` header during upgrade to prevent Cross-Site WebSocket Hijacking (CSWSH), matching configured permitted hosts exactly.
- **Deterministic Room Routing**:
  - Request with unknown or finished `room_id` parameter fails immediately, closing the socket with `4004 Room Invalid/Finished`.
  - Omitted `room_id` triggers the server to authoritatively allocate a fresh room ID.
  - Full room triggers standard close code `4001 Room Full`.
  - Handshake and payloads are strictly client-identity free.
- **Server and Room Capacity Boundaries**:
  - The server caps concurrent active rooms at exactly 100. Upgrade requests exceeding this capacity receive `4000 Bad Request`.
  - Frame Parsing Limit: Incoming WebSocket message sizes are authoritatively limited to exactly 1 KB. Sockets exceeding this are instantly terminated.

### 3.2 Sequence Deduplication & Generation-level Stale Rejection
- To prevent out-of-order or duplicate action processing (caused by network jitter or visual event loop queuing), the client must supply:
  - `seq_num`: Monotonic increasing bounded safe integer (`[1, 9007199254740991]`).
  - `generation`: Server-owned active piece generation count, echoed exactly.
- **Validation**:
  - If `seq_num` <= seat's stored `last_processed_seq_num`, reject action.
  - If `generation` != seat's current `active_piece_generation`, reject action.
- **Generation Advance**: The server increments `active_piece_generation` only when spawning a new piece or when a piece is retrieved/replaced via Hold, not on standard downward gravity movements or lateral manual shifts. This ensures actions meant for a previous piece can never be applied to a newly spawned piece.
- **Action Correlation**: State updates carry `last_action_seat`, `last_action_seq`, and `last_action_observable_change` top-level properties so Playwright can verify the precise outcome of client actions.

### 3.3 Server-Side Gravity Tick Draw Logic
- Each player seat has an independent gravity timer driven by `asyncio` background tasks on the server.
- **Double-Gravity Tie update logic**: If gravity timers for both seats expire within the same authoritative server loop iteration (the same single update tick), the server updates both boards sequentially.
- If both players top out in this single tick, the server declares a **DRAW** with outcome `"draw"`. If they top out in different ticks, the first to top out loses/forfeits, and the other instantly wins, preventing ties across separate tick periods.
- **Disconnection (Forfeit)**: Dropping a WebSocket instantly forfeits, transitioning room status to `"finished"` and broadcasting the result to the survivor.
- **Cleanup Policy**: Svc runs a background task every 60 seconds to sweep abandoned or terminal rooms (no connections or no inputs for 5 minutes). This sweeps the room ID dictionary and cancels background `asyncio` gravity loop futures, resolving resources gracefully.

## 4. Playwright Benchmarking & Testing Protocol [PERF-01]

Performance audits must be run on foreground production Chromium with a visible window of `1280x900` at DPR `1`.

### 4.1 Six-Trial Protocol & Foreground Window Constraint
- Because browsers aggressively throttle `requestAnimationFrame` and `setTimeout` intervals in background tabs or minimized windows to save power, both clients in a duel must be run in **visible, non-overlapping foreground windows** (e.g. side-by-side windows) or separate processes to ensure standard 60Hz loop execution on both ends.
- Focus/foreground status and active client modes must be recorded during the run.
- Runs a 6-trial protocol using a frozen piece sequence:
  - 3 trials of Solo Play (30s each, after 5s warmup)
  - 3 trials of Duel Play (30s each, after 5s warmup)

### 4.2 Repaint & Latency Captures
- Redraw evidence must be bound to state changes using screenshot pixel validation or `ctx.getImageData` checksum checks (drawing callback scheduling is not physical display presentation proof).
- Frame intervals are recorded chronologically via rAF timestamp lists.
- Captures:
  - Frame scheduling interval (target p95 <= 25 ms, mean rate >= 55 FPS)
  - Action-to-visible-update latency (local repaint time)
  - Remote action-to-opponent-visible latency (time from Client 1 input to Client 2 screen update representing Seat 1)
- Reports median, p95, p99, and logs any unavailable measures as "unavailable".

## 5. Bounded Control Recovery and Benchmark Correction (as17) [PERF-01]

Following a documented coordinator control incident where overlapping model instances were running, a bounded recovery is established. A clean own retained source boundary is preserved. The earlier benchmark (native16) has known smoke failures (e.g., rAFCount=0 and drawCount=0, actions falsely classified as blocked_noop). 

### 5.1 Remaining Measurement and Correction Requirements
To resolve these defects and ensure accurate, robust benchmark data:
1. **Explicitly Invoked IIFE for Trackers**: `injectInstrumentTrackers` must use an explicitly invoked raw IIFE (`(() => { ... })()`) when evaluating page closures to ensure the tracker runs, and assert that trackers exist and produce samples before claiming readiness. A smoke with zero scheduler samples or zero verified changes fails.
2. **Correct Active Piece HTTP State Field**: The matched HTTP response uses `activePiece` (GameSession alias), not `active_piece`. The instrument must be corrected to read the correct `activePiece` field to reflect falling tetrominoes correctly and verify pixel changes. State changes vs. before-state are correctly evaluated to avoid false "blocked_noop" classifications.
3. **Comprehensive RAW Per-run Data**: Every benchmark run must preserve raw tuples of rAF events, draw events, network/HTTP logs, declared driver start/end times, and duet action dispatch/response/ACK times with selected sequence/generation/revision numbers. Expected board state and actual pixel RGB arrays must be captured.
4. **Window Bounds and Calibrated Window Filters**: Apply exact calibrated range rules for rAF events and action latencies on both solo and duel modes.
5. **Robust Failure Handling and Partial Data Flushing**: Ensure raw partial run objects are retained outside the try-catch block and flushed/saved in a finally block even upon unexpected failure, preserving screenshots/traces when available.
6. **Explicit Browser Bounds and Visibility State Tracking**: Capture browser, version, launch args, requested viewport/DPR, actual window bounds (e.g., screenX, screenY, outerWidth, outerHeight), and visibility/focus snapshots at each keypress.
7. Canvas Color Classification with Bounded Tolerance**: Determine empty cells and active/locked cells using a documented bounded RGB distance tolerance, accounting for canvas alpha overlays.

## 6. Precise OS-Foreground Verification and Bounded Handshake [PERF-01]

While Playwright's `bringToFront` and `document.hasFocus` are useful for browser-level status, they are not proof of OS-level foreground focus. To ensure absolute physical OS-level foreground alignment without fabricating approvals, we implement an optional, bounded foreground-activation gate based on a file-system handshake:

1. **CLI Parsing**:
   - `--foreground-gate`: Optional boolean switch (default off).
   - `--foreground-gate-timeout-seconds`: Bounded timeout (default 120).
   Runs without `--foreground-gate` are marked explicitly as OS-foreground-unverified in metadata.

2. **Wait Hooks**:
   - Hook 1: Invoked on the solo page after tracker installation but before "Start New Game".
   - Hook 2: Invoked on the duel pages after tracker installation but before starting or joining any room.
   This ensures server gravity loops are not active during the external activation waiting phase.

3. **Temporary Title Instrumentation**:
   - Actor page title: `SDD S4 <output-dir-basename> <runId> INPUT`
   - Receiver page title: `SDD S4 <output-dir-basename> <runId> RECEIVER` (or null if solo)
   This temporary title serves strictly as test instrumentation and remains stable until the run completes.

4. **Handshake Protocol**:
   - Write `foreground-ready.json` in the current run's output directory with properties: `runId`, `scenario`, `actorTitle`, `receiverTitle`, `runsPerScenario`, `created UTC`, `requested channel/mode`, and `phase='before-game-setup'`.
   - Poll for `foreground-approved.json` every 100ms inside the configured timeout.
   - Parse `foreground-approved.json` strictly as data; require `approved: true` and matching `runId` and `actorTitle`.
   - On timeout/invalid approval, abort immediately with a partial record marking `errorStage='foreground-gate'`.
   - All gate delays are excluded from warmup and active measurement windows.

### 5.2 Positive Interval Aggregation Correction [PERF-01]

To address the issue of zero/nonpositive intervals (such as `[17867.20000000298, 17867.20000000298, 0]`) inflating callback interval counts and observed FPS, the measurement aggregation logic in `performance-benchmark.ts` must be updated as follows:
1. **Unchanged Raw Tuples**: All raw rAF samples and tuples collected from `window.__rafSamples` must remain completely unchanged and preserved for diagnostics inside the partial and final reports.
2. **Positive Interval Selection**:
   - A requestAnimationFrame interval (tuple `s`) is counted in the main measurement calculations (including `rAFCount`, `observedMeanFPS`, and `frameSchedulingIntervalMs` statistics) ONLY when both calibrated endpoints (previous frame timestamp `s[0] - offset` and current frame timestamp `s[1] - offset`) lie within the fixed measurement window (`[measureStartNode, measureEndNode]`) AND its delta `s[2]` is finite and strictly positive (`> 0`).
   - The same strict positive-interval inclusion rule must be applied to any warmup interval selection.
3. **Excluded Metric Tracking**:
   - Keep explicit counts of nonpositive/invalid raw rAF tuples for each client (`excludedNonpositiveRafCount`, and the subset of those that lie within the window `excludedNonpositiveRafInWindowCount`).
   - Reconcile the sum of retained vs. excluded tuples to verify that all raw samples are fully accounted for without modifying the raw arrays or the existing out-of-window/uncertainty counters.
4. **Denominator Preservation**:
   - The FPS calculation denominator must remain exactly `requestedMeasureSeconds` (measureSeconds), without substituting nominal or overrun elapsed durations.
5. All drawing, pixel, and action latency metrics remain completely unaffected.



