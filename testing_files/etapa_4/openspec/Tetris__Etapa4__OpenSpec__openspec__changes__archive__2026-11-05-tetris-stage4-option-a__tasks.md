# Tasks

> [!NOTE]
> **Bounded Apply Scope**: Apply ONLY Milestone 1 (tasks 1.1–1.7) of this reviewed native Stage 4 change. Do not implement Canvas conversion, duel implementation, benchmark edits, infrastructure or dependency-declaration changes now.
> **Future Isolation Constraints**: Stage 4 must use its own isolated Compose project `tetris-stage4-openspec`, its own test SQLite volume, and loopback production proxy port `5514` (not inherited `5183`). Do NOT implement these Docker/CI changes during M1.

## 1. Milestone 1 - Active Piece Rotation in Python Engine & API

> [!NOTE]
> **M1 Correction Note: Missing Frontend Wire Type**
> A TypeScript contract discrepancy was identified where `orientation` on `ActivePiece` was serialized by the backend but omitted in the frontend's `ActivePiece` interface in `frontend/src/api.ts`. This caused frontend compilation failures in `src/App.test.tsx`.
> - Reopen Task 1.5 and Task 1.7 to verify the correction, ensuring that a full typescript compile (`npm run build`) and test execution (`npm run test`) pass.

- [x] 1.1 Extend `ActivePiece` and `GameState` models in `backend/models.py` with an optional `orientation: int = 0` field. Verify using pytest that standard serialization of game state payloads compiles and executes cleanly.
- [x] 1.2 Define the audited, deterministic `TETROMINO_ORIENTATIONS` coordinate matrix inside `backend/engine.py` specifying exact local blocks for orientations `0, 1, 2, 3` across all standard shapes (correcting T orientation 2 and L orientation 2 relative to pivot `[2, 1]`, and "I" relative to half-cell pivot `[1.5, 1.5]`). Verify that spawning or hold Swaps reset active piece orientation to `0`.
- [x] 1.3 Implement clockwise and counterclockwise coordinate calculation methods in `TetrisEngine` with horizontal-only column offsets in priority order `0, -1, +1, -2, +2` relative to the piece's current origin, without any vertical offsets or floor kicks. Verify that the engine applies the first candidate that fits without board boundary or locked block collisions.
- [x] 1.4 Integrate rotation actions in `GameSession.move`. Ensure that active piece rotation never triggers automatic lock-down, advances gravity, changes score, level, lines, or modifies hold/next piece queues. Preserve inherited blocked-down versus gravity-lock semantics. Verify that "O" piece rotation acts as a no-op, and rotation is a terminal no-op on game-over.
- [x] 1.5 Bind frontend keyboard event capturing in `frontend/src/App.tsx` for `ArrowUp` (clockwise rotation) and `Z` (counterclockwise rotation) using the existing REST API. Connect these keys directly to single-player UI actions while retaining the React DOM-based cell board rendering for Milestone 1.
- [x] 1.6 Extend `MoveRequest` and the POST `/api/games/{game_id}/move` API route in `backend/main.py` to allow `"clockwise"` and `"counterclockwise"` directions. Verify using an HTTP test client that rotation updates the board orientation and coordinate responses.
- [x] 1.7 Create a new comprehensive engine rotation test file `backend/test_rotation.py` with deterministic fixtures covering unobstructed clockwise/counterclockwise turns (four unobstructed turns closure), I and O shapes, boundary walls, floor limits, locked block collisions, kick priority, and full rejection, and Hold swaps. Create corresponding frontend keyboard event tests. Verify that engine coverage remains >=80%.

## 2. Milestone 2 - High-Performance HTML5 Canvas 2D Rendering

> [!NOTE]
> **M2 Task Notes: Accessible Canvas Behavior, Tests, and Expected Verification Boundaries**
> - **Accessible Canvas Behavior**:
>   - The HTML5 Canvas element must have an accessible fallback description inside it (e.g., `<canvas aria-label="Tetris Game Board" role="img">Your browser does not support HTML5 Canvas. Tetris board showing 20 rows by 10 columns.</canvas>`) to ensure screen readers understand its role.
>   - If the Canvas 2D context cannot be created (e.g., `getContext('2d')` returns `null`), the board must fail gracefully by displaying an accessible fallback text/alert in the DOM rather than crashing the interface.
>   - Score, level, lines, Hold, preview, leaderboard, and game status must remain in the accessible DOM as structural elements.
> - **Canvas Tests & Mocks**:
>   - Canvas tests will mock the HTMLCanvasElement and its 2D context to track and assert rendering invocations (`clearRect`, `fillRect`, `scale`, etc.).
>   - Assert correct canvas dimensions and scaling on DPR 1 and DPR 2.
>   - Assert clipping and coordinate bounds rendering (10 columns by 20 rows).
>   - Verify `ResizeObserver` setup, callback execution, and proper cleanup (disconnecting on unmount) to prevent memory leaks.
>   - Verify update propagation on prop changes, reset, and game-over transitions.
> - **Verification Boundaries**:
>   - Verify that DOM cell assertions from Stage 3 are superseded. The Canvas component is validated by asserting the mock context call sequences instead of counting DOM cell elements.
>   - Maintain verification evidence for existing keyboard controls, Hold, and stale-response protection in `App.test.tsx` alongside Canvas mocking.
> - **Test Readiness & Determinism Note**:
>   - Resolve the flaky "keeps the newer response when move requests complete out of order" test by deterministically awaiting the committed initial state/effect/listener readiness using a controlled promise returned by api.createGame wrapped in act().
>   - Repeat this specific test a small bounded number of times (e.g., 20 times) within a loop to prove that it is 100% deterministic and that older responses cannot replace newer state, confirming that the stale-response assertion remains robust and unweakened.

- [x] 2.1 Refactor the frontend DOM-based board grid in `frontend/src/components/GridBoard.tsx` to render using an HTML5 Canvas element instead of individual React DOM cells. Verify that the canvas element mounts successfully with correct responsive width and height.
- [x] 2.2 Implement Canvas drawing procedures to clear the canvas, draw a coordinate grid, draw settled blocks from the state matrix using distinct colors per block type, and overlay the active piece blocks. Verify that board updates render in real-time on Canvas.
- [x] 2.3 Integrate browser high-DPI display adjustments in the drawing routine by scaling the canvas width and height attributes by `window.devicePixelRatio`, adjusting CSS widths/heights, and calling `ctx.scale(dpr, dpr)`. Verify that blocks remain sharp.
- [x] 2.4 Ensure `ResizeObserver` bindings dynamically trigger Canvas resize and redraw, and verify that keyboard event listeners and callbacks cleanly unmount to prevent leaks or stale UI states.
- [x] 2.5 Document any intentionally superseded DOM test assertions in `frontend/src/App.test.tsx`. Replace them with canvas state-based mock checks and Canvas 2D Context mock drawing operations (e.g., verifying `clearRect`, `fillRect`, `scale` calls). Verify that `npm run test` and `npm run build` execute successfully without compile warnings.

> [!NOTE]
> **Static Analysis Findings (S8980 & S6819) & Node 24 Warnings Notes**:
> - **S8980**: In `GridBoard.test.tsx`, calling `unmountFn()` inside `act()` is flagged as a redundant act call. This is noted for cleanup during implementation.
> - **S6819**: In `GridBoard.tsx`, `role="img"` is declared on the `<canvas>` element for accessibility compliance. This finding is semantically inapplicable to be removed as the canvas functions as a graphics display, so we document this rationale and retain the finding rather than replacing canvas with an image or weakening accessibility.
> - **Node 24 Warnings**: Linting on Node 24 observed `no-this-alias` (in test observer) and `set-state-in-effect` (in App.tsx). These will be reported truthfully and fixed only if naturally necessary during the bounded call.

## 3. Milestone 3 - WebSockets Two-Player Matchmaking and Duel Mode

- [x] 3.1 Define versioned and bounded JSON WebSockets message envelopes (`v: 1`, payload, seq, timestamp) in `backend/models.py` with strict Pydantic validator unit tests. Enforce `extra="forbid"`, 4096-byte UTF-8 frame limits, and 64-character string limits on ID fields.
- [x] 3.2 Implement in-memory `DuelPlayer`, `DuelRoom`, and `DuelRoomManager` in a new file `backend/duel.py` to manage real-time matchmaking, seat assignments (exactly 2 seats), and in-memory room storage (max 100 rooms). Implement deterministic piece synchronization using a shared room seed and index-based generation (`get_piece_at_index(index, seed)`) to prevent finite queue exhaustion.
- [x] 3.3 Implement the FastAPI WebSocket route `/api/ws/duel/{room_id}` in `backend/main.py`. Ensure strict `Origin` header validation during handshake (HTTP 403 Forbidden for missing, null, or foreign origins), seat-level input scoping (P1 cannot control P2 board), monotonic sequence checks, and generation gates (board spawn generation matches action message) for stale action rejection.
- [x] 3.4 Implement serialized room update grouping and evaluations under a room-level lock (`asyncio.Lock()`) to handle same-update draw conditions (both boards topping out in the same gravity tick). Ensure outcomes are committed exactly once.
- [x] 3.5 Implement WebSocket disconnect event handlers to trigger immediate forfeit victories, cancel background gravity loops, and close connections. Add an asyncio-based background room sweeper running every 60 seconds to prune finished rooms after 60s, and inactive rooms (no action messages received) after 240 seconds, guaranteeing memory release within 5 minutes.
- [x] 3.6 Extend `frontend/src/App.tsx` and custom hooks (like `useDuel`) to support WebSockets connections, side-by-side rendering of local and opponent Canvas boards, input routing, old-socket cleanup, and stale state protection.
- [x] 3.7 Create a comprehensive WebSocket test suite in `backend/test_duel.py` using synthetic clock injection for cleanup, covering matchmaking start gates, seat boundaries, stale action rejection (seq and generation gates), disconnect forfeits, and concurrent top-out draw conditions.

## 4. Milestone 4 - Docker Integration, Benchmark & Coverage Validation

- [x] 4.1 Update `docker-compose.yml` to run as a non-root isolated network. Run the backend internally (using `expose: - "8000"`) with NO host port exposure. Configure Nginx in `frontend/nginx.conf` to serve as a production reverse proxy and WebSocket gateway (handling `Upgrade` and `Connection` headers), exposing ONLY the same-origin reverse proxy port `5514` (reconciled from Stage 3 port `5183`) on the host. Configure a persistent named volume for the solo SQLite database.
- [x] 4.2 Establish automated Playwright integration tests executing two independent browser clients against the production reverse proxy. Verify start gating, seat ownership, movement/rotation synchronization, disconnect forfeit, room isolation, and concurrent top-out draws (which are evaluated as deterministic server draw fixtures rather than client-driven browser flows). Use screenshots/pixel checks linked to authoritative state changes to verify Canvas drawing.
- [x] 4.3 Configure and verify coverage reports: backend pytest MUST output XML coverage (`coverage.xml`), and frontend Jest/Vitest MUST output LCOV files (`coverage/lcov.info`). Ensure a SonarQube-compatible NEW-CODE coverage checkpoint of >=80% is met across all modified/new files, with all production code left in scope.
- [x] 4.4 Update `playwright-benchmark.js` with the exact, measurable Chromium benchmark protocol:
  - Run foreground production Chromium under window size `1280x900` with DPR = 1.0.
  - Execute a 5-second warm-up period, followed by 3 independent 30-second trials for EACH scenario (solo and duel), utilizing real moves and rotations.
  - Capture and report: server (unavailable/null due to core common seed limits) and client scheduler intervals, Canvas API DRAW operations (excluding async callbacks and coordinate reads), state/pixel-verified draws, local causal input-to-visible latency, and remote input-to-opponent-visible latency.
  - Retain raw counts, timestamps, trace data, hardware profiles, and visual evidence.
  - Explicitly designate that benchmarks MUST NOT be executed during the planning phase.

## 5. Stage 10 Continuation - Test Remediation & Playwright Benchmark Implementation

- [x] 5.1 Implement the WebSocket message draining sync helper in `backend/test_main_remediation.py` using anyio.fail_after to drain queued start messages and correctly capture the expected WebSocketDisconnect (codes 1003 and 1008) for binary, oversized, invalid JSON, and forbidden messages.
- [x] 5.2 Fix App.test.tsx S8985 side-effect inside waitFor by dispatching fireEvent outside and only asserting inside waitFor.
- [x] 5.3 Handle any expected child sweeper task cancellation elegantly during backend lifespan shutdown, preventing it from propagating as a lifespan failure (S7497).
- [x] 5.4 Run the full backend pytest test suite to ensure all 83+ tests pass successfully.
- [x] 5.5 Implement the new Playwright benchmark instrument in `playwright-benchmark.js` verifying input window activation, Canvas draw metrics, and causal latency calculations, corrected for prototype preservation, strict target port URL 5514, exact local/opponent canvas identification, required and permitted CanvasRenderingContext2D.getImageData pixel matches, and precise clock alignment.
- [x] 5.6 Run a brief bounded self-test/probe of the Playwright benchmark using pure non-network fixtures to verify all semantic correction logic.
- [x] 5.7 Apply the 8 critical corrections from the independent source review to `playwright-benchmark.js` (ReferenceError fix, unified clock mapping, multiplayer state isolation, strict window end, verification details, drift calibration, atomic phase JSON, trace cleanup).
- [x] 5.8 Verify the benchmark corrections with the updated self-test suite via node playwright-benchmark.js --self-test.

> **Benchmark Instrumentation Correction Note (Stage 4)**
> A set of 6 crucial instrumentation issues in `playwright-benchmark.js` have been corrected:
> 1. Restored the live entry point execution (`!isSelfTest` calling `runBenchmark()`).
> 2. Added strict causal window [winStart, winEnd) bounds filtering.
> 3. Recorded logical node bounds for all phases and wrote `phase-timing.json` atomically.
> 4. Tracked exact browser DOM keydown events with event ID and eliminated fallback.
> 5. Strengthened same-piece effect checks and avoided re-using network responses.
> 6. Identified callback batches (renamed verifiedDraws to callbackbatches) and derived pixel-verified changed draws.

> **Benchmark Phase Timing Correction Note**
> A concrete metadata bug was identified in `playwright-benchmark.js` where `phaseTimings.measure` was written non-atomically via `writeFileSync` before the measurement start/end bounds were defined. In that state, the phase remained `'warmup'` instead of `'measure'`, and logical node bounds (`warmupEndNode`/`Iso`, `measurementStartNode`/`Iso`, `measurementEndNode`/`Iso`) were never assigned or stored, causing stats to read undefined values. This has been corrected by:
> 1. Capturing `warmupEndNode` and `warmupEndIso` precisely at warmup completion.
> 2. Setting `measurementStartMono` and computing `measurementEndMono` as start + duration.
> 3. Setting the phase to `'measure'`, and recording all bounds (`warmupEndNode`/`Iso`, `measurementStartNode`/`Iso`, `measurementEndNode`/`Iso`) on the phase object.
> 4. Atomically writing `phase-timing.json` AFTER all assignments and BEFORE activating measurement.
> 5. Removing the old non-atomic write.
> 6. Adding a pure shared helper to construct and validate the phase timings object with test assertions.
