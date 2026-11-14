# Design

## Context

The system is a brownfield Tetris application consisting of a FastAPI Python backend (using SQLite for solo persistence) and a React/TypeScript frontend (currently rendering a 10x20 cell grid using standard DOM nodes). Stage 3 successfully added game hold mechanisms, levels, dynamic gravity intervals, and solo leaderboards. See `proposal.md` for the Stage 4 motivation.

## Goals / Non-Goals

**Goals:**
- Implement deterministic active piece 90-degree clockwise and counterclockwise rotations with horizontal wall-kicks in the authoritative Python engine.
- Replace the DOM-based 10x20 cell grid on the frontend with an HTML5 Canvas 2D element utilizing browser high-DPI scaling (`window.devicePixelRatio`).
- Implement real-time two-player WebSocket-based dueling rooms using a single FastAPI worker process, same-origin handshake validation, in-memory state synchronization, and server-side gravity timers.
- Guarantee strict validation of client-supplied actions, seat boundaries, input freshness, and secure WebSocket origins.
- Preserve all Stage 3 solo play behaviors, CORS restrictions, and SQLite leaderboards.

**Non-Goals:**
- Do not persist multiplayer duel scores or outcomes to the SQLite solo leaderboard database.
- Do not implement vertical wall-kicks (kicks that adjust the row position).
- Do not use external database/cache systems (like Redis) for match rooms; use in-memory Python structures matching the single worker process limit.

## Decisions

### Decision 1: Deterministic Tetromino Orientations (Milestone 1)
To support 90-degree rotations, each of the standard tetromino types (I, O, T, S, Z, J, L) will have its occupied coordinate cells explicitly mapped for all four possible orientations (`0`, `1`, `2`, `3`).

- **Orientation Mapping**:
  ```python
  TETROMINO_ORIENTATIONS = {
      "I": {
          0: [[1, 0], [1, 1], [1, 2], [1, 3]],
          1: [[0, 2], [1, 2], [2, 2], [3, 2]],
          2: [[2, 0], [2, 1], [2, 2], [2, 3]],
          3: [[0, 1], [1, 1], [2, 1], [3, 1]]
      },
      "O": {
          0: [[1, 1], [1, 2], [2, 1], [2, 2]],
          1: [[1, 1], [1, 2], [2, 1], [2, 2]],
          2: [[1, 1], [1, 2], [2, 1], [2, 2]],
          3: [[1, 1], [1, 2], [2, 1], [2, 2]]
      },
      "T": {
          0: [[1, 1], [2, 0], [2, 1], [2, 2]],
          1: [[1, 1], [2, 1], [2, 2], [3, 1]],
          2: [[2, 0], [2, 1], [2, 2], [3, 1]],
          3: [[1, 1], [2, 0], [2, 1], [3, 1]]
      },
      "J": {
          0: [[1, 0], [2, 0], [2, 1], [2, 2]],
          1: [[1, 1], [1, 2], [2, 1], [3, 1]],
          2: [[2, 0], [2, 1], [2, 2], [3, 2]],
          3: [[1, 1], [2, 1], [3, 0], [3, 1]]
      },
      "L": {
          0: [[1, 2], [2, 0], [2, 1], [2, 2]],
          1: [[1, 1], [2, 1], [3, 1], [3, 2]],
          2: [[2, 0], [2, 1], [2, 2], [3, 0]],
          3: [[1, 0], [1, 1], [2, 1], [3, 1]]
      },
      "S": {
          0: [[1, 1], [1, 2], [2, 0], [2, 1]],
          1: [[1, 1], [2, 1], [2, 2], [3, 2]],
          2: [[2, 1], [2, 2], [3, 0], [3, 1]],
          3: [[1, 0], [2, 0], [2, 1], [3, 1]]
      },
      "Z": {
          0: [[1, 0], [1, 1], [2, 1], [2, 2]],
          1: [[1, 2], [2, 1], [2, 2], [3, 1]],
          2: [[2, 0], [2, 1], [3, 1], [3, 2]],
          3: [[1, 1], [2, 0], [2, 1], [3, 0]]
      }
  }
  ```
- **Clockwise transition**: `next_orientation = (current_orientation + 1) % 4`
- **Counterclockwise transition**: `next_orientation = (current_orientation - 1) % 4`
- **O piece behavior**: All orientations point to the identical block layout, and rotation requests behave as logical no-ops.
- **Derivation and Closure**: All coordinate entries are audited relative to a fixed pivot `[2, 1]` for 3-row shapes, and `[1.5, 1.5]` for the 4x4 "I" shape. This guarantees unobstructed four-turn closure and exact CW/CCW inverse mappings. Spawning and Hold retrieves enter orientation 0.
- **Alternative considered**: Implementing a general rotation matrix multiplier `[r, c] -> [-c, r]`. However, floating-point coordinates or mathematical shifts can introduce rounding errors and misalignments across complex pieces like I or S. Explicit cell coordinates at each orientation provide absolute deterministic pivots.

### Decision 2: Horizontal Wall-Kick Sequence (Milestone 1)
During rotation, if the calculated absolute cell positions collide with a boundary or an existing locked cell, the engine will attempt to "kick" the piece horizontally.
- **Offset sequence**: `0, -1, +1, -2, +2`.
- **Algorithm**:
  ```python
  for col_offset in [0, -1, +1, -2, +2]:
      candidate_origin = [origin_row, origin_col + col_offset]
      candidate_cells = calculate_cells(piece_type, target_orientation, candidate_origin)
      if is_valid_position(board, candidate_cells):
          apply_rotation(candidate_origin, target_orientation, candidate_cells)
          return success
  return reject_rotation
  ```
- **Alternative considered**: Standard SRS (Super Rotation System) which includes complex vertical kicks and floor-kicks. However, SRS can cause pieces to jump upward or skip over obstacles. Horizontal-only kicks match the exact requested Stage 4 option A mechanics, keeping gameplay predictable and avoiding vertical skipping bugs.

### Decision 3: HTML5 Canvas 2D Sizing and Sharp Scale (Milestone 2)
To replace `GridBoard.tsx` and maintain high-fidelity aesthetics under high-DPI (Retina) monitors, we will render the grid using Canvas 2D.
- **High-DPI Alignment**:
  - We read `window.devicePixelRatio || 1`.
  - Set the canvas's physical backing width/height attributes: `canvas.width = rect.width * dpr`, `canvas.height = rect.height * dpr`.
  - Set the canvas's CSS display width/height attributes: `canvas.style.width = "${rect.width}px"`, `canvas.style.height = "${rect.height}px"`.
  - Call `ctx.scale(dpr, dpr)` on the 2D context.
- **Rendering sequence**:
  1. Clear Rect (full canvas).
  2. Draw grid lines (subtle border paths).
  3. Draw settled blocks cell-by-cell (from the 20x10 matrix).
  4. Draw the active piece's cells overlaying the board.
- **Colors**: Keep matching tetromino thematic colors for occupied blocks (e.g., cyan for "I", yellow for "O", purple for "T", etc.).
- **Alternative considered**: Sticking to DOM-based grid elements. However, DOM elements are heavy, trigger browser layout reflows during rapid block updates, and fail to scale smoothly. HTML5 Canvas scales natively and processes pixel matrices instantly as a robust rendering optimization design choice.

### Decision 4: Real-time Duel Matchmaking & WebSockets Room Protocol (Milestone 3)
Matchmaking and live dueling are managed entirely in-memory within the single FastAPI worker.
- **Data Models**:
  ```python
  class DuelPlayer:
      def __init__(self, player_id: str, ws: WebSocket, seat: int):
          self.player_id = player_id
          self.ws = ws
          self.seat = seat # 1 or 2
          self.session = GameSession(session_id=player_id)
          self.seq_number = 0
          self.generation = 0

  class DuelRoom:
      def __init__(self, room_id: str, seed: int):
          self.id = room_id
          self.seed = seed
          self.players: Dict[str, DuelPlayer] = {} # player_id -> DuelPlayer
          self.status = "waiting" # "waiting", "playing", "finished"
          self.gravity_tasks: Dict[str, asyncio.Task] = {} # player_id -> task
          self.winner_id: Optional[str] = None
          self.loser_id: Optional[str] = None
          self.is_draw = False
          self.last_input_time = time.time()
          self.finished_at: Optional[float] = None
  ```
- **Same-Update Draw and Room Lock Grouping**:
  - The server serializes board ticks and state updates using a room-level `asyncio.Lock()`.
  - During gravity ticks or action evaluations, if both players top out in the same update cycle, the server sets `self.is_draw = True`, cancels both gravity loops, and broadcasts a single definitive `"outcome"` message. Outcomes are committed exactly once.
- **Deterministic Infinite Piece Sequence**:
  - A shared room seed is generated at start. We use a pseudo-random generator `get_piece_at_index(index, seed)` to retrieve pieces deterministically by index.
  - Each board session tracks its own `piece_index` (starts at 0). When a new piece spawns, it fetches the piece type at its active `piece_index`, avoiding finite queue exhaustion.
- **Versioned WebSockets Message Envelope**:
  - Envelopes use a strict `v: 1` structure. Extra fields are forbidden (`extra="forbid"` rule). UTF-8 frame size limit is 4096 bytes.
- **Validation Boundaries & Handshake Validation**:
  - The WebSocket handshake validates the `Origin` header. Connections with missing, null, or foreign origins are rejected (HTTP 403 Forbidden).
  - Incoming messages can only control the sender's assigned seat.
  - Stale and duplicate messages are discarded via sequence and generation gates:
    - `seq` must be strictly monotonic (`seq > last_processed_seq`).
    - The client sends the board's `generation` counter. If it does not match the active server-side board's `generation` (which increments on every spawn or hold swap), the action is rejected as stale.
- **Alternative considered**: REST polling. REST polling is heavy, introduces lag, and makes live peer boards choppy. WebSockets provide low-latency bi-directional message dispatch as our chosen real-time transport.

## Risks / Trade-offs

- **[Risk] WebSockets Memory Leaks** → If clients open rooms and disconnect, stale rooms might sit in memory.
  - *Mitigation*: Implement a background task in `main.py` that sweeps `DuelRoom` storage every 60 seconds, releasing rooms that have been finished for 60s, or inactive (no actions received) for more than 240 seconds. This guarantees room release within 5 minutes of inactivity. Heartbeats and gravity updates do NOT reset active input timers.
- **[Risk] WebSocket Connection Interruption** → If a player disconnects mid-duel, the room could hang.
  - *Mitigation*: The `WebSocketDisconnect` handler automatically marks the disconnected player as having forfeited the game under the room lock, reports the immediate forfeit result to the survivor, halts gravity tasks, and moves the room to the "finished" state.

## Migration Plan

1. **Phase 1: Backend Rotation Integration**: Extend `models.py` and `engine.py` with orientations, rotation, and kick priority. Add unit tests for engine rotation and API endpoints. Expose keyboard controls on the frontend in Milestone 1 (while keeping DOM rendering).
2. **Phase 2: Canvas Board Implementation**: Refactor `GridBoard.tsx` into an HTML5 Canvas 2D element, integrating responsive sizing, device pixel ratio scaling, drawing routines, and custom styling. Verify layout and input bindings.
3. **Phase 3: WebSockets Duel Matchmaking & Lifecycle**: Add WebSocket endpoints, state synchronized rooms, seat protection, same-update draw grouping, and side-by-side rendering in the client.
4. **Phase 4: Docker & Reverse Proxy Updates**: Ensure Nginx handles WebSocket Upgrade and Host proxy headers properly. Run containers as non-root with no internal backend port exposure.

## Bounded Apply Scope and Future Isolation Constraints (Milestone 1)

- **Bounded Apply Scope**: Implement ONLY Milestone 1 (tasks 1.1–1.7) of this reviewed native Stage 4 change. Do not implement Canvas conversion, duel implementation, benchmark edits, infrastructure or dependency-declaration changes now.
- **Future Isolation Constraints**: Stage 4 must use its own isolated Compose project `tetris-stage4-openspec`, its own test SQLite volume, and loopback production proxy port `5514` (not inherited `5183`, which belongs to historical runs). Do NOT implement these Docker/CI changes during M1; this is the future isolation constraint only.

### Milestone 1 Correction Note: Missing Frontend Wire Type (ActivePiece Orientation)

During final validation of Milestone 1, a TypeScript contract defect was discovered. 
The backend serializes `orientation` in the `ActivePiece` model, but `frontend/src/api.ts` omitted this field from the `ActivePiece` TypeScript interface. This caused type errors in frontend tests (e.g., `src/App.test.tsx`) when compiling under strict TypeScript checks.
- **Correction**: Add `orientation: number;` to the `ActivePiece` interface in `frontend/src/api.ts` to reflect the actual wire payload, ensuring the frontend type definitions match the backend serialization structure.
- **Verification**: Reopen verification for frontend key capturing (Task 1.5) and tests (Task 1.7) by updating tasks.md and verifying with full frontend TypeScript compilation and tests.

### Milestone 3 Static Analysis Findings (S8980 & S6819) & Warnings Rationale

During Milestone 2 review, SonarQube reported 2 static findings (code smells):
- **S8980 (GridBoard.test.tsx: redundant act around unmount)**:
  - *Rationale/Analysis*: In `GridBoard.test.tsx` (around line 179), calling `unmountFn()` inside an `act` block is flagged as redundant since `unmount` from `@testing-library/react` is already wrapped in `act()` under modern React testing environments. This is a valid lint observation. We will remove the redundant outer `act` wrapper.
- **S6819 (GridBoard.tsx: role="img" on Canvas)**:
  - *Rationale/Analysis*: The canvas element is used to render the game board visually, which is an interactive graphical presentation. Declaring `role="img"` is appropriate to describe this component's role to assistive technologies, accompanied by an `aria-label` and accessible fallback description. Removing `role="img"` or replacing the Canvas with a static image would break the real-time canvas rendering functionality or weaken accessibility. Therefore, we retain the `role="img"` attribute with this documented rationale.
- Node 24 Warnings:
  - `no-this-alias` (in test observer) and `set-state-in-effect` (in `App.tsx`) were observed under Node 24. These represent inherited behaviors. They are documented here and will only be resolved if naturally necessary and tested.

## Milestone 4 Correction Note: Stage 10 Continuation, Test Remediation, and Playwright Benchmark Instrument Plan

### 1. Context and Partial 09 Fact Recording
The previous execution run (PARTIAL09) was paused due to `providerRESOURCE_EXHAUSTED429` (Quota Limit Exhaustion) after 898.781s.
- **Added Files**: It added exactly `backend/test_duel_remediation.py`, `backend/test_main_remediation.py`, and `backend/test_models.py`.
- **Invariance**: No native planning artifacts (proposal, design, tasks, or specs) were modified during the 09 run; all native 08 artifacts remained completely identical.
- **Application Code & Config**: Production code, configuration, dependencies, and infrastructure remained byte-identical to the independently accepted 08 run.
- **Continuation Goal**: Fix the 4 failing WebSocket tests in `backend/test_main_remediation.py` and the `App.test.tsx` side-effect, and then implement the new Playwright benchmark instrument in `playwright-benchmark.js`. No retroactive claims are made.

### 2. Native 10 Test Remediation Plan
We will fix the 4 failing WebSocket tests under `backend/test_main_remediation.py`:
- `test_websocket_binary_message_rejection`
- `test_websocket_oversized_frame_rejection`
- `test_websocket_invalid_envelope_json_rejection`
- `test_websocket_forbidden_message_type`

**Root Cause & Solution**:
- **Issue**: After sending start signals, both seats have initial state frames queued in the TestClient's receive buffer. Sending an invalid/binary message causes the server to close/reject, but calling `ws.receive_text()` immediately returns the previously queued old `state` message instead of throwing `WebSocketDisconnect`.
- **Draining Helper**: We will implement an actual bounded sync draining helper in the test file. It will use Starlette TestClient's underlying portal to receive messages asynchronously and wrap them with `anyio.fail_after` to enforce a strict deadline. It will drain state/error frames until a `WebSocketDisconnect` is caught, asserting the precise rejection code (e.g., `1003` for binary, `1008` for oversized/invalid json/forbidden messages). This avoids modifying server behavior or introducing arbitrary thread sleeps.
- **App.test.tsx S8985 Side Effect Fix**: In `App.test.tsx` (around line 463), we will fix the side-effect inside `waitFor` by dispatching `fireEvent` outside `waitFor` and only asserting inside `waitFor` (test-only change, preserving correct behavior).
- **Lifespan Task Cancellation S7497**: We will handle the expected child sweeper task cancellation cleanly during lifespan shutdown without propagating it as a new lifespan failure, documenting appropriate rationale.

### 3. Playwright Benchmark Instrument Plan
We will implement the complete Chromium-based benchmark inside `playwright-benchmark.js` utilizing our existing devDependencies:
- **Environment**: Headful Chromium channel, 1280x900 viewport, DPR 1. No silent headless fallback.
- **Active Window Verification**: Ensure the browser input window has a title ending in "INPUT", a ready marker, and an explicit activation gate. We will track focus/visibilityState via periodic checks throughout the run.
- **Sizing & Visibility**: Prior to the 5s warm-up, use `scrollIntoViewIfNeeded()` to fit both local and remote boards completely within the 1280x900 viewport. Record layout bounds and verify that action-effect cells are within the viewport bounds.
- ** rAF and Canvas Draw Separation**: Separate browser-level requestAnimationFrame (rAF) scheduling timestamps from actual Canvas 2D draw operations (such as `clearRect`, `fillRect`, `strokeRect`, `drawImage`, `putImageData`). Canvas draw wrapper hooks will preserve arguments, context, return values, and record accurate performance.now timestamps.
- **Causal Action-to-Visible Latency**: Keyboard events will be dispatched with precise keydown timestamps. We will track outgoing HTTP requests/WebSocket actions (with message sequences/generations), await the authoritative ACK/state update, and verify that 200 cells / color changes are rendered on the local canvas.
- **Remote Latency Clock Domains**: Calibrate clocks across the foreground actor and background opponent context using raw anchors with recorded uncertainty to calculate remote input-to-opponent-visible latency. Mark background scheduling limits as unavailable/excluded where appropriate rather than fabricating measurements.
- **Execution**: Provide a gated trial option for `solo|duel` with a trial label, a 5-second warm-up, and 30-second measurement window. All raw samples, percentile calculations (median, p95, p99), exclusions, and trace images will be written to a unique output directory. No final trials are executed during the inference turn itself.

## Milestone 4: Benchmark Semantic Correction and Fixture Design

To resolve the 9 critical semantic readiness failures observed in the benchmark instrument and fixtures, we implement the following strict corrections:

1. **Strict Port and Output Directory Control**:
   - The target URL is restricted exclusively to `http://127.0.0.1:5514`. All other ports (`5183`, `5513`, `9000`) and arbitrary navigation are explicitly rejected.
   - Output directory management is made immutable: the benchmark must fail closed and refuse to overwrite or execute if the output directory already contains existing files or subdirectories, ensuring retention and trace integrity.

2. **Transparent WebSocket/Fetch Prototype Instrumentation**:
   - Instead of overriding `window.WebSocket` with a simple function (which destroys the `OPEN` static constant, prototype properties, and breaks client checks like `readyState === WebSocket.OPEN`), we transparently extend the native `WebSocket` constructor, preserving its prototype, static constants, `this` binding, arguments, return values, and errors.
   - The `fetch` wrapper is corrected so it does not await the `.json()` resolution of responses before returning, which delayed app fetch availability and caused async deadlocks. Response cloning and JSON checking are done asynchronously in a separate non-blocking microtask or using native Playwright network responses.

3. **Accurate rAF and Canvas Draw Counting**:
   - The `requestAnimationFrame` hook is updated to use exactly ONE dedicated original rAF sampler per page with one entry per actor frame, avoiding double-counting or merging of multiple callbacks.
   - Canvas draw call counting is strictly isolated to actual rendering methods (`clearRect`, `fillRect`, `strokeRect`, `drawImage`, `putImageData`) and uniquely identified per canvas/context/role (e.g., local vs opponent canvas across both pages). Coordinate reads and state transforms are excluded.

4. **Actual Pixel Sampling and Verification using `getImageData`**:
   - The use of `CanvasRenderingContext2D.getImageData` is strictly required and permitted. We implement a robust, synchronous pixel sampler Page function / RPC that reads actual pixel values directly from the canvas 2D context.
   - The sampler targets the exact canvas based on the page's role (local-seat canvas for Page 1, opponent-seat canvas for Page 2). It loops 20 rows by 10 columns, reading the center of each cell: `ctx.getImageData(Math.floor((c + 0.5) * canvas.width / 10), Math.floor((r + 0.5) * canvas.height / 20), 1, 1).data`.
   - The sampler captures all 200 RGBA values, canvas dimensions, DPR, paint counter, and observation start/end timestamps in the exact same JavaScript execution turn.
   - Verification matches these 200 actual RGBA pixels against an expected mask that merges the authoritative `state.board` and `state.active_piece.cells` (if playing). Palette colors are matched with a small rounding tolerance, while empty cells match the background color `[16, 18, 36, 153]`. Mismatches never qualify for a successful latency sample. Old draw-only success paths are fully deleted.

5. **Precise Causal Latency & Input Matching**:
   - Input causal matching for duels matches the exact room, player, action sequence number (`seq`), and active generation. For solo HTTP, we match the actual request ID, game ID, and move direction.
   - Solo `Z` rotations are correctly evaluated with their actual CCW effects (checking that valid CCW counts, and O shape remains a no-op).

6. **Monotonic Clock Domain Calibration**:
   - Dispatched keys are recorded with a precise causal label at the actual DOM event dispatch.
   - Remote input-to-opponent latency calculates clocks across the actor and opponent using paired anchor offset calibration (recording before/after timestamps and estimating uncertainty), with no negative-latency clamps.

7. **Fail-Closed Foreground Focus Gating**:
   - The benchmark gates on OS foreground focus and fails closed if focus is lost. It writes a `foreground-ready.json` file and waits up to 120s for an external `foreground-approved.json` file, aborting if `foreground-abort.json` is detected.

8. Pre-Setup Gating and Logical Measurement Windows:
   - All focus gates and approval loops run BEFORE setting up any fresh games or active rooms to prevent human wait times from spoiling active room/game states.
   - Logical measurement windows are strictly bounded to `[start, end)` timestamps. No mid-measurement restarts are allowed.

9. Truthful Metrics Reporting:
   - If zero valid samples are captured, metrics report `null` and count `0` instead of fabricating fake values.
   - Disclose Playwright default flags and hardware profiles without adding performance boost parameters.

## Independent Source Review Benchmark Corrections (November 2026)

To resolve critical executable defects identified during the independent source review before any live probe, the following corrections are applied to `playwright-benchmark.js`:

1. **Resolution of ReferenceError on lastStateReceivedPage1**:
   Instead of accessing `lastStateReceivedPage1` as a top-level global let variable inside `runBenchmark` (which triggers a `ReferenceError` during `executeAndVerifyAction`), we pass an explicit, unified `sessionState` context object representing the tracking state of the observers to `executeAndVerifyAction`. The self-test is updated to invoke the actual live `executeAndVerifyAction` function using a fake page, fake network event listeners, and simulated pixel sampling.

2. **Unified Clock Domains & Timestamp Alignment**:
   Browser/Page event timestamps (`keydownMono`) are precisely mapped to Node's `performance.now()` clock using high-precision paired anchor offsets obtained from clock calibration. We do away with imprecise +/-150ms guessed searches. The `keydown` timestamp is retrieved from actual event capture timestamps registered at the browser level (`window.keydownEvents`), not estimated evaluate timestamps.

3. **Multiplayer State Overwrite Isolation**:
   To prevent states from being overwritten by concurrent multiplayer updates, WebSocket and HTTP state parsing filters authoritative frames strictly by `room_id`, `player_id`, action sequence number (`seq`), and active piece spawn generation. Action frame mapping is based on precise payload keys (`action, seq, room_id, player_id, generation`) and mapped to actual action names from `App.tsx` (`left`, `right`, `down`, `clockwise`, `counterclockwise`).

4. **Strict Measurement Bounding**:
   A strictly fixed logical window limit of `end = start + measurementTimeMs` is enforced. The `isInWindow` utility applies the strict `[start, end)` interval to all action dispatches, ACKs, and observations. If the deadline is near, the benchmark ceases dispatching new actions to prevent window overflow. Page-level raw rAF and DRAW events are mapped to the Node clock domain prior to window filtering.

5. **Precise Verification & Exclusions**:
   Pixel polling is verified against the expected state mask while explicitly excluding no-ops, blocked rotations, or O-piece rotations (which are marked as excluded/no-op and not counted towards latency). We compare before/after states and save the 200-RGBA canvas state, canvas identity, clock bounds, maskhash, and paintcounter (batch count) for both local and remote contexts. All raw network/input/scheduler/draw/calibration anchors are fully written to `raw-metrics.json`.

6. **Drift-Compensated Calibration**:
   Clock calibration is performed both before the warm-up and after the measurement window, capturing at least 5 paired anchors `(NodeBefore, PageNow, NodeAfter)` each. We calculate the mid-point and half-RTT uncertainty, choose the anchor with the minimum RTT, and report the drift between the two calibration phases.

7. **Atomic Phase & Focus Monitoring**:
   We emit a dedicated `phase-timing.json` file on transitions (`warmup`, `measure`, `finished`). If the game tops out or reaches a terminal state, the run is invalidated. Focus and visibility of both actor and peer browser context sessions are continuously monitored and recorded, keeping the headful Chromium HWND in the foreground without OS focus hacks.

8. **Output Cleanup & Integrity**:
   Mirroring to the repository root directory `docs/benchmark-evidence.md` is removed; all output files remain isolated to the designated `outdir`. Tracing contexts are stopped and finalized (`trace.stop`) prior to computing `traceHash`. Proper cleanup is executed on any errors, while retaining invalid raw files for diagnosis.

## Stage 4 Final Documentary Scope and Accepted Facts/Limits

### 1. Chronology of Corrections
- **Native 15 Chronology**: The first correction note was recorded as a Javascript header modification before the later tasks note was registered.
- **Native 16 Chronology**: The tasks note was appended and finalized preceding the final metadata fix.

### 2. Accepted Milestone 1 (Rotation) Facts
- Active piece 90-degree clockwise and counterclockwise rotations are fully integrated and verified via 86 public HTTP checks and 39 engine tests, alongside the 4 physical keyboard controls.
- Keyboard layout uses `ArrowUp` for clockwise, and `Z` for counterclockwise rotation. "O" piece rotation is a deterministic no-op. Spawns and retrieval from Hold enter in orientation 0.
- Rotation does not advance gravity, trigger lockdown, change scores, level, or lines, nor does it affect hold/next piece queues.
- Horizontal column offsets sequence: `0, -1, +1, -2, +2`. No vertical or floor kicks. Preserves position and orientation if none fit.

### 3. Accepted Milestone 2 (Canvas 2D) Facts
- Replaced 10x20 cell DOM grid with sharp HTML5 Canvas 2D rendering.
- Fully validated across 14 cases (4 real HTTP and 10 renderer fixtures). High-DPI scaling handles DPR 1 and 2 seamlessly.
- Accessible DOM panels for game status, score, level, lines, hold, and preview remain intact.

### 4. Accepted Milestone 3 (WebSockets Duel) Facts
- Live two-player same-origin WebSockets dueling with a single FastAPI worker process and in-memory rooms.
- Fully validated via 18 independent server core fixtures (handling room lifecycles, state synchronization, and 625 pieces per player), 42 public WS checks, and 19 dual Chromium checks (covering start gating, seat ownership, movement/rotation synchronization, disconnect forfeit, room isolation, and outcome delivery).
- Concurrent top-out draws are evaluated strictly as deterministic server-side gravity update draw fixtures, not as public browser board injections.
- Own loopback socket runs on `127.0.0.1:5514` with internal backend on `8000`. Docker Compose image and volume configurations use `stage4openspec`.

### 5. Code Quality, Coverage & Audits
- Passes all 83 backend and 22 frontend tests cleanly, alongside zero linter/build warnings.
- SonarQube results: New code coverage of `86.3%` and Global code quality score of `88.9%` with new duplications at `0%` (analysis: `e6b3d8f3-0038-4cad-ab4a-b27cadc7cf60`). Quality gate error remains due to 39 open static findings (1 bug, 38 code smells). Stage 3 baseline was `91.3%` with `0` issues.
- Backend dependency audit resolved 47 selected packages (23 aggregate + 24 direct OSV HTTP 200, all 0 advisories, no version mismatches), which represents a verified sub-segment of the OS environment.

### 6. Playwright Benchmark & Performance Trials
- Platform profile: Windows NT 10.0.26200 x64, AMD Ryzen 7 5700X 8-core, 24GB RAM. Chromium channel `chrome 156.0.8078.80` with window `1280x900` at DPR = 1.
- Trials recorded: `final16-solo-01`, `final16-solo-02`, `final16-solo-03` and `final16-duel-01-r02`, `final16-duel-02`, `final16-duel-03`.
- Scheduler rate means: `164.9333`, `164.8667`, `164.9` intervals/sec for solo, and `164.9`, `164.9`, `164.9` intervals/sec for duel. p95 intervals: `6.5, 6.5, 6.3, 6.4, 6.4, 6.3` ms. All trials meet the scheduling targets of >=55 FPS and <=25ms p95 intervals. Direct physical display presentation rate and server-side loop intervals are unavailable/null.
- Verification samples: Local draw paint operations (200-RGBA changed mask count on accepted inputs) are `75, 44, 52, 68, 67, 62` (total `368` frames). Duel remote verified opponent draws are `68, 66, 61` (total `195` frames).
- Latency samples: Observed p95 controller-to-canvas readback times are `33.7099, 33.7616, 32.3149, 26.6791, 28.5219, 31.1511` ms for local and `36.1047, 37.1772, 38.3465` ms for remote. Peer DOM focus history is incomplete due to background context limits; manual focus reactivation is required after peer opens.
- Trial `final16-duel-01` was aborted during warm-up due to peer window taking foreground before measurement (excluded, and replaced by `r02` with manual focus instructions). Probe `14-solo-01` was a NOOP 0.297s, preserving historical failed/empty runs.
- Metrology: Clock calibration uses paired anchor drift adjustments with no negative clamps. Metrology maps event IDs by raw timestamp/array ordinal. Mock event IDs are not used as native IDs.




