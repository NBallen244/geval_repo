# Tessl Session Notes: Browser-Based Tetris Study - Stage 4, Option A (Tetromino Rotation, Canvas 2D & Real-time Duel WebSockets)

## 1. Tessl Integration Status & Environment Evidence

We have queried the workspace's Tessl environment to verify available local skills and active project status.

- **Tessl Status Check (`mcp_tessl_status`):**
  - **manifest.summary.inSync:** 2 (`maria/fastapi` and `softaworks/agent-toolkit` are fully synchronized locally).
  - **Readiness State:** `"partial"` due to a `"not-authenticated"` blocker (as expected, remote CLI authentication is unavailable in headless/CI agent contexts, which is an environment limitation we log here).
- **Tessl Skills Check (`mcp_tessl_skills_available`):**
  - **Outcome:** Reported authentication requirement (reconfirmed remote tool limitation).
- **Local Plugins & Skills Mapping:**
  - The local skills are fully discoverable and vendored at `.tessl/plugins/`:
    - `maria/fastapi` (includes `run-check-server` and `scaffold-project` skills).
    - `softaworks/agent-toolkit` (includes the `react-dev` skill with event-handlers, hooks, react-19-patterns, and routing integration references).

These findings establish that our toolchains, local plugins, and files are in place. We proceed purely in Specifications/Planning Mode without writing any code edits or starting server runs.

---

## 2. Key Architecture & Material Design Decisions

### 2.1 Server-Authoritative 90-Degree Rotation (Milestone 1)
- **Model Modifications:**
  - `ActivePieceModel` in `backend/app/models/game.py` is extended with `orientation: int = 0` (constrained to `[0, 1, 2, 3]`).
- **Rotation Engine Logic:**
  - **Cyclic Transitions:** Clockwise (CW) transitions orientation to `(orientation + 1) % 4`. Counterclockwise (CCW) transitions orientation to `(orientation - 1) % 4`. This orientation loop is strictly cyclic, not monotonic.
  - **Deterministic Pivots:**
    - **'I' piece:** Fixed Pivot `(1.5, 1.5)`. The coordinates for 'I' are:
      - Orientation 0 (Spawn): `[(0, 0), (0, 1), (0, 2), (0, 3)]` (exact inherited cells at row 0)
      - Orientation 1 (CW 90°): `[(0, 3), (1, 3), (2, 3), (3, 3)]`
      - Orientation 2 (CW 180°): `[(3, 0), (3, 1), (3, 2), (3, 3)]`
      - Orientation 3 (CW 270°): `[(0, 0), (1, 0), (2, 0), (3, 0)]`
    - **Other Non-O pieces ('T', 'S', 'Z', 'J', 'L'):** Fixed Pivot `(1, 1)`.
    - **'O' piece:** No pivot, strict no-op. Skipping kick and collision checks, leaving orientation and coordinates completely unchanged.
  - **Horizontal Wall Kicks:** Tried sequentially with column offsets `dc = [0, -1, +1, -2, +2]`. No vertical column offsets or vertical kicks are checked.
  - **Rotation Rejection Immutability:** If none of the 5 horizontal offsets produce a legal position (within board boundaries and not overlapping locked cells), the rotation command is fully rejected: active piece's row, col, orientation, cells, board state, score, lines, next, hold, and gravity timers remain completely unchanged (immutable on failure).
  - **Lifecycle Isolation:** Rotation does not advance gravity, award points, lock the piece, or mutate next/hold pieces.
  - **Spawn/Retrieve Orientation:** Newly spawned or held pieces retrieved from Hold enter play at `(0, 3)` with `orientation = 0` (spawn orientation).

---

### 2.2 High-Performance Canvas 2D Rendering (Milestone 2)
- **Visual Rendering Strategy:**
  - Replace the React DOM grid cells (`TetrisBoard.tsx`) with a single HTML `<canvas>` element.
  - **DPR Scaling:** To ensure razor-sharp block edges at both DPR 1 and DPR 2, scale the canvas back-buffer dimensions dynamically:
    ```typescript
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    ```
  - **Color Representation:** Draw occupied board cells and active piece blocks using filled rectangles with colors mapped to their tetromino type ('I' = cyan, 'O' = yellow, 'T' = purple, 'S' = green, 'Z' = red, 'J' = blue, 'L' = orange). Empty cells are rendered with the background grid color.
- **State Testability Gating:**
  - JSDOM does not execute native Canvas drawing or pixel checks, which could break our unit tests.
  - To prevent JSDOM test failures while maintaining Vitest state assertions, the `TetrisBoard` component exposes serialized HTML data-attributes (`data-status`, `data-active-piece-type`, `data-active-piece-orientation`, `data-board-hash`).
- **Real-Browser Visual Suite (Playwright):**
  - Actual production-browser visual testing using Playwright is required at both DPR 1 and DPR 2.
  - Verification includes:
    - Verifying RGBA colors at occupied cell coordinates on the canvas.
    - Confirming pixels are cleared and redrawn on move/CW/CCW/lock/reset.
    - Verifying same-count pixel centers to ensure no blocks are lost during rendering.
    - Unchanged-board no-op checks to ensure that rejected rotations or blocked moves do not trigger canvas repaints.

---

### 2.3 Real-Time Two-Player WebSocket Duel Mode (Milestone 3)
- **WebSocket Route:** `WS /api/ws/duel/{room_id}`
- **CSWSH and Origin Gating:**
  - The WebSocket handler strictly validates the `Origin` header to match exact authorized Stage 4 origins (`http://localhost:5515` or `http://127.0.0.1:5515`) without wildcard broadening. It also binds and verifies the `Host` header.
- **Seat Mapping & Start Gating:**
  - Connection 1 is assigned `"player1"` (Left Board), connection 2 is assigned `"player2"` (Right Board). Subsequent connections are immediately closed with code `4001` (Room Full).
  - Game status remains `"waiting"` until both players are connected.
- **Deterministic Infinite Sequence:**
  - Upon starting, both players receive a shared seed.
  - An O(1) random-access seeded hash function (e.g. `hash(seed + "_" + piece_index) % 7`) is used to deterministically generate tetrominoes infinitely on demand, avoiding repeating or array exhaustion issues.
- **Independent Server-Side Gravity:**
  - Server-side background gravity loops tick at 50Hz (every 20ms).
  - Each board is evaluated independently based on its own gravity tick due-time.
  - **Simultaneous Update evaluation:** If both player boards are due for a gravity tick, the server evaluates BOTH boards *within the same update cycle* before checking for a topout. This ensures that a simultaneous topout yields a `"draw"`, preventing artificial win/loss evaluation.
- **Revision Equality & Action Deduplication:**
  - Every player board state change increments a monotonic integer `revision`.
  - Client actions must supply an `action_id` (independent unique increasing sequence per seat) and an `expected_revision` (exact expected board revision integer).
  - The server rejects messages where `expected_revision != current_server_revision`. Stale inputs are acknowledged with a no-op ACK.
  - If `action_id <= highest_processed_action_id` for that seat, the message is discarded as a duplicate.
- **Locking & Non-Blocking Broadcasts:**
  - State mutations inside each room are protected via an independent `asyncio.Lock` per room.
  - **Snapshot outside lock pattern:** State snapshots are written under a short room lock, and the actual socket broadcasts are executed OUTSIDE of the lock to prevent network delays on one player's socket from blocking the opponent's engine loop.
- **Active Idle Sweeping:**
  - A background task sweeps inactive rooms every 60 seconds.
  - Sweeping actively cancels background gravity tasks and closes open client sockets rather than just deleting dictionary entries.
  - Monotonic clocks are mockable/injectable to allow instant fast-forwarding in tests without sleeping.

---

## 3. Boundary, Error Mitigation & CORS Rules
- **Oversized/Malformed Message Rejection:**
  - Any binary message or invalid JSON message immediately closes the connection with code `1003` (Unsupported Data).
  - Messages exceeding 4096 bytes immediately close the connection with code `1009` (Message Too Big).
  - Invalid types, missing required fields, or illegal score/state injections from a client close the connection with code `1008` (Policy Violation).
- **Inbound rate limits:** Clients are restricted to 50 messages per second. Excess messages close the connection with code `1008` (Policy Violation).
- **Solo SQLite isolation:** Duel results are never persistent in the solo SQLite database.
- **Outcome delivery:** Final duel results are delivered exactly once. Socket retries or late connections receive the cached finished room state.

---

## 4. Quality Gates & Phased Traceable Checklist

We establish the following traceable task checklist to map the Stage 4 requirements completely. All tasks remain **OPEN** until real execution.

### Post-M1: Rotation Core
- [ ] **Task S4-1.1 (SHAPES Orientations definition):** Create the exact mathematical coordinate dictionary for all 7 pieces and all 4 orientations in `backend/app/domain/pieces.py`. [OPEN]
- [ ] **Task S4-1.2 (ActivePiece model expansion):** Add `orientation: int = 0` to `ActivePieceModel` in `backend/app/models/game.py`. [OPEN]
- [ ] **Task S4-1.3 (Rotation rule implementation):** Implement `rotate_active_piece` with horizontal kicks `[0, -1, +1, -2, +2]` and strict no-op for 'O' in `backend/app/domain/rules.py`. [OPEN]
- [ ] **Task S4-1.4 (Rotation endpoint exposure):** Add `POST /api/games/{id}/rotate` in games controller with extra="forbid" payload validations. [OPEN]
- [ ] **Task S4-1.5 (ArrowUp/Z keyboard mapping):** Wire CW rotation on `ArrowUp` and CCW rotation on `Z`/`z` keys in `frontend/src/App.tsx`. [OPEN]
- [ ] **Task S4-1.6 (Rotation Unit tests):** Author Python tests for CW/CCW rotations, wall/floor collision rejections, and kick priority. [OPEN]

### Post-M2: Canvas Rendering
- [ ] **Task S4-2.1 (React Canvas implementation):** Replace the React cells grid with an HTML `<canvas>` element in `TetrisBoard.tsx`. [OPEN]
- [ ] **Task S4-2.2 (DPR sharp rendering):** Scale back-buffer dimensions by `window.devicePixelRatio` for high-DPI screens. [OPEN]
- [ ] **Task S4-2.3 (State diagnostics serialization):** Serialize board and active piece state to `data-` attributes on the canvas component. [OPEN]
- [ ] **Task S4-2.4 (Playwright visual suite):** Build browser tests checking physical pixel colors at DPR 1 and DPR 2 after moves, rotations, locks, and resets. [OPEN]
- [ ] **Task S4-2.5 (Layout and controls check):** Ensure 1280x900 viewport visibility for both single-player and WebSocket duel boards. [OPEN]

### Post-M3: WebSocket Duel Mode
- [ ] **Task S4-3.1 (WebSocket Router):** Implement the `WS /api/ws/duel/{room_id}` route with exact Stage 4 `Origin` and `Host` validation. [OPEN]
- [ ] **Task S4-3.2 (Seeded Infinite Hashing):** Code the O(1) seeded piece hashing function to generate infinite shared tetrominoes deterministically. [OPEN]
- [ ] **Task S4-3.3 (Server-Side Gravity Loop):** Implement background server-gravity task executing independent, level-based board ticks. [OPEN]
- [ ] **Task S4-3.4 (Simultaneous Update check):** Program the single-loop gravity tick evaluator to assess both player boards before declaring outcomes. [OPEN]
- [ ] **Task S4-3.5 (Revision Matcher & Deduplicator):** Filter client actions using expected board revision equality and `action_id` deduplication. [OPEN]
- [ ] **Task S4-3.6 (Forfeit & Draw execution):** Wire draw outcomes on simultaneous topout, and forfeit outcomes on disconnect. [OPEN]
- [ ] **Task S4-3.7 (Active Sweeper & Sockets close):** Build background sweeper task using injectable clocks to prune inactive and finished rooms. [OPEN]
- [ ] **Task S4-3.8 (WebSocket Integration suite):** Write backend tests covering malformed/oversized messages, duplicates, and socket error safety. [OPEN]

### Infrastructure and Verification
- [ ] **Task S4-4.1 (Non-root Compose config):** Build `docker-compose.yml` deploying non-root backend and frontend proxy networks with a named volume. [OPEN]
- [ ] **Task S4-4.2 (Chromium Performance Benchmark):** Set up foreground Chrome benchmark measuring rAF, visual latency, and Action-to-ACK times over 6 timed trials. [OPEN]

---

## 5. Coverage Gates compliance
- **Independent Sonar NEW Coverage:** >= 80% line coverage required on all modified files.
- **Independent Sonar Duplication Gate:** <= 3% across modified files.
- **Static Analysis Gate:** Exactly 0 new static analysis bugs or security warnings.
- **Disclose errors:** Any static analysis finding or coverage deficit fails the build.

---

## 6. Execution Logs & Verification Command History

### Dated Session Note: November 5, 2026 - Milestone 1 Implementation
**Goal:** Implement Milestone 1 (90-degree clockwise/counterclockwise rotation of active tetrominoes with deterministic horizontal kicks, REST API, UI integration, and rigorous tests).
**Intended Files to Modify/Create:**
- `backend/app/models/game.py`: Extend `ActivePieceModel` to include `orientation: int = 0`.
- `backend/app/domain/pieces.py`: Define absolute relative coordinates for all 7 pieces across all 4 orientations (CW/CCW cycle) and update `get_relative_cells`.
- `backend/app/domain/rules.py`: Add `rotate_game` rule with strict 'O' piece no-op, horizontal kick offsets `[0, -1, +1, -2, +2]`, and validation. Ensure spawn/hold reset orientation.
- `backend/app/controllers/games.py`: Expose `POST /api/games/{id}/rotate` endpoint and pass direction to `rotate_game`.
- `frontend/src/types.ts`: Incorporate `orientation` into frontend TS types.
- `frontend/src/App.tsx`: Wire CW (`ArrowUp`) and CCW (`Z` or `z`) key controls and UI buttons, passing actions to rotation API endpoint with stale-request queuing.
- `backend/tests/test_rotation.py`: Create dedicated backend rotation tests.
- `frontend/src/components/TetrisBoard.test.tsx` (or similar tests): Add frontend verification tests for key triggers and API interaction.

*Planning completed. Transitioning to implementation.*

### Dated Session Note: November 5, 2026 - Milestone 2 Implementation & Layout Correction
**Goal:** Implement Milestone 2 (high-performance Canvas 2D rendering replacing 200 DOM cells on the main Tetris board with DPR scaling and state testability attributes, and layout correction to support 1280x900 viewport visibility without overlapping or scrolling).
**Intended Files to Modify/Create:**
- `frontend/src/components/TetrisBoard.tsx`: Replace 200 DOM cells grid with a single `<canvas>` element. Use `useRef` and `useEffect` to scale and render occupied board cells and the active piece on state update. Handle DPR scaling and resize operations using ResizeObserver to ensure crisp lines. Add fallback and safety checks for JSDOM context. Expose required `data-` attributes on the canvas element.
- `frontend/src/components/TetrisBoard.test.tsx`: Modify tests to reflect the transition from DOM cells to Canvas. Mock getContext to handle absent context in JSDOM environment, test that the canvas element renders, and verify the correct data-attributes (`data-status`, `data-active-piece-type`, `data-active-piece-orientation`, `data-board-hash`) are serialized correctly. Add canvas rendering tests.
- `frontend/src/index.css`: Update `.tetris-board` CSS styles to support canvas element display instead of a grid, add explicit width/height defaults for `canvas.tetris-board`, and modify the game-container and panels layout to guarantee they fit within a 1280x900 viewport. Add custom button styling for rotation/control buttons if applicable.
- `frontend/src/App.test.tsx`: Adjust any assertions that depend on `.board-cell` DOM nodes to instead look at the canvas state via the exposed data attributes or mock functions.

### Dated Session Note: November 5, 2026 - M2 Correction Planning & M3 Contract Alignment
**Goal:** Address M2 independent evaluation layout failures and test synchronization flakiness, and resolve contradictions in the M3 duel protocol design before implementing corrections.

**Layout Correction Strategy:**
- **The Issue:** At a 1280x900 viewport, the document `scrollHeight` was 1117px. This exceeded the 900px limit and caused layout overflow.
- **The Cause:** The canvas element (300x600px), game status/controls, and the high-scores panel stacked vertically or had large padding/margins, pushing the layout past 900px.
- **The Solution:** We must make the dashboard layout compact.
  1. Wrap panels in a CSS grid or flex layout that allocates space efficiently.
  2. Implement an inner scroller for the high scores panel, limiting its visible height to 10 rows with scrollable overflow inside that panel, rather than scrolling the entire page.
  3. Reduce global margins, paddings, and header heights.
  4. Ensure `overflow: hidden` on the `html, body` is NOT used as a cheap trick; the layout must naturally fit within the 1280x900 bounds.
  5. Preserve the exact `<canvas>` display dimensions (300x600px) and functional controls/buttons.

**Test Synchronization Correction Strategy:**
- **The Issue:** A race condition occurred in `App.test.tsx` for keyboard actions (`ArrowUp` and `Z`), where only 1 fetch call was detected instead of 2. Additionally, React emitted warnings about updates not being wrapped in `act(...)`.
- **The Cause:** The keyboard event was fired before the game session creation fetch call completed and registered its state update fully, or state transitions after key actions occurred asynchronously without proper `act()` or wait synchronization.
- **The Solution:** 
  1. Await the complete initialization and mounted state before firing event triggers.
  2. Wrap keyboard triggers and actions in `await act(async () => { ... })`.
  3. Ensure that after firing key events, the test awaits the actual resulting state mutation or fetch callback rather than using fixed timeouts or arbitrary promise resolves.
  4. Add robust, non-dummy unit tests for the `rotateGame` API helper in `frontend/src/api.test.ts` to cover CW/CCW rotations, ensuring high coverage of the new API code path.

*Plan updated. Proceeding to update native M3 specifications before implementing any code/style corrections.*

### Dated Session Note: November 6, 2026 - M2 Correction Resumption & Implementation
**Goal:** Document resumption under authorized new project `project-f593a869-be0a-442d-a85` following the previous `BILLING_DISABLED` pause and planning-only phase, and implement M2 layout, test synchronization, and api coverage corrections.

**Layout Corrections (Viewport Height <= 900px):**
- **Action:** Modify `frontend/src/index.css` to compact the layout.
  - Implement a dedicated scroll container for high scores panel, limiting it to exactly 10 rows without growing the page.
  - Reduce excessive header, dashboard, and panel margins/padding.
  - Arrange elements cleanly to naturally fit within the 1280x900 viewport (such that document `scrollHeight <= 900` and `scrollWidth <= 1280` without using `body { overflow: hidden }` or hidden overlays to cheat checks).
  - Ensure canvas remains exactly 300x600px.

**App Test Keyboard Race Corrections:**
- **Action:** Edit `frontend/src/App.test.tsx` around the key action tests (such as line 661).
  - Wait for the active game UI to load and React effects to flush fully before firing keyboard events.
  - Wrap both CW (`ArrowUp`) and CCW (`Z`) keyboard actions in `await act(async () => { ... })`.
  - Use `waitFor` to assert the actual rotation request count, request payload, and resulting rendered orientation. No fixed sleeps, skips, or lowered counts.

**API Helper Rotation Coverage:**
- **Action:** Add robust unit tests for `rotateGame` (CW/CCW directions and HTTP errors) inside `frontend/src/api.test.ts` to guarantee genuine coverage.

*Transitioning to implementation of M2 layout, test synchronization, and api coverage fixes.*

### Dated Session Note: November 6, 2026 - Acknowledging M2 Partial Delivery & Precise Test Fixes Plan
Following the partial delivery in Stage 4/Milestone 2 (where Native07 closed exit 0 with a future-tense response but left the keyboard race condition and rotateGame API helper tests unaddressed, and did not run the promised checks), we are now executing the remaining corrections:
1. **Addressing Keyboard Race in `App.test.tsx`:**
   - Instead of merely checking the absence of `Initializing...` text, we will wait for actual game UI (e.g. score or other components) and effects to flush.
   - We will fire exactly ONE key inside `await act(async () => { ... })` for each rotation.
   - We will await the exact fetch counts (2 and 3) and verify that the correct rotation request payload (direction `'cw'` and `'ccw'`) is sent to the `/rotate` endpoint using `waitFor` without repeated inputs, fixed sleeps, or weakened assertions.
   - We will assert the resulting state and orientation, ensuring JSDOM test-visible outcomes.
   - We will apply proper synchronization to the accessible rotation-button tests to match this pattern.
   - We will preserve FIFO, stale-request, restart, and `StrictMode` testcases intact.
2. **Implementing `rotateGame` Tests in `api.test.ts`:**
   - We will implement actual test cases for `rotateGame` in `frontend/src/api.test.ts`.
   - We will cover both `'cw'` and `'ccw'` directions, ensuring that request URLs and bodies are strictly validated, and that correct `GameState` is returned.
   - We will also cover HTTP error propagation cases.
3. **Execution of Quality Checks:**
   - We will run Vitest, check LCOV coverage, perform TypeScript typechecks/lint, and run production build.
   - We will capture and preserve the exact stdout, stderr, and exit status outputs in `docs/native-evidence/08-m2-tests` under unique filenames.

### Dated Session Note: November 6, 2026 - Milestone 3 Specification, Schema, and Corpus Corrections
**Goal:** Complete Milestone 3 specifications, JSON schema corrections, and wire-examples JSON corpus. Focus on robust real-time duel specifications, resolving 8/10 adversarial state check vulnerabilities, and ensuring syntax validity across all JSON files and markdown code blocks.

**Key Design and Specification Decisions:**
1. **Adversarial State Checks Validation (JSON Schema):**
   - **Exactly 4 Cells & Uniqueness:** Define `cells` inside `active_piece` with `"minItems": 4, "maxItems": 4` and `"uniqueItems": true`.
   - **Absolute Boundaries:** Restrict cell coordinates inside `cells` to row `0..19` (minimum: 0, maximum: 19) and column `0..9` (minimum: 0, maximum: 9).
   - **Origin Anchors:** Validate origin coordinates row and column separately using a positional tuple. The row component is restricted to `minimum: -3, maximum: 19` and the column component to `minimum: -3, maximum: 9` to admit rotated negative 'I' piece anchors under Milestone 1 geometry.
   - **Playing & Game Over Mutex conditions:** Use `allOf` with conditional `if`/`then`/`else` structures in `game_state` schema. If `status` is `"playing"`, `active_piece` MUST be an object. If `status` is `"game_over"`, `active_piece` MUST be `null`.
   - **Level and Gravity:** Set level `minimum: 1` and gravity interval `minimum: 1` (must be positive).
   - **Safe JS Integer Bounds:** Apply `minimum: 0, maximum: 9007199254740991` (Number.MAX_SAFE_INTEGER) to all integers like score, revisions, and action IDs.
   - **Strict ASCII Identifiers:** Restrict all identifiers (`room_id`, `client_id`, `player1_id`, `player2_id`, state `id`) using `{ "$ref": "#/$defs/identifier" }` which requires `^[a-zA-Z0-9_-]{1,64}$` and `not: { "pattern": "[\\r\\n\\u2028\\u2029]" }` to reject CR, LF, and other line break/control characters.

2. **Every Live Message Formats Alignment:**
   - Consolidate all obsolete/vague markdown examples in `requirements.md` into the formal `{"version": "1.0", "type": "...", "payload": { ... }}` envelope structure.
   - Replace the invalid indented ACK code fence (Fence 8) with a correct enveloped ACK message.
   - Correct Fence 7 (Unified Board Schema) to be a complete valid JSON representing a proper `GameState` object.
   - Specify outcomes `"win"`, `"loss"`, `"draw"`, `"forfeit"`, `"operational-abort"` explicitly.

3. **Action/Revision Lifecycle Resolution:**
   - Client sends strictly monotonic integer `action_id` and `expected_revision`.
   - The server rejects stale actions where `expected_revision < current_board_revision` (returning status `"noop"` with reason `"stale revision"`) or future actions where `expected_revision > current_board_revision` (returning status `"rejected"` with reason `"future revision"`).
   - For valid actions with `expected_revision == current_board_revision`, the action is evaluated against the current state, returning `"accepted"` or `"rejected"`.
   - Duplicate actions (`action_id <= highest_processed_action_id`) are discarded silently with O(1) memory overhead.

4. **Single Exact Bounds Integration:**
   - Globally active room count limit is exactly 100 active rooms.
   - Message size limit is exactly 4096 bytes (socket closes on overflow with code 1009).
   - Inbound rate limit is exactly 50 messages per second per client socket (socket closes on overflow with code 1008).
   - Outbound broadcast queue limit is exactly 100 messages.
   - Outbound write timeout is exactly 200 milliseconds.
   - Hello handshake timeout is exactly 10 seconds.
   - Finished room retention is exactly 300 seconds.
   - Waiting / playing idle timeout is exactly 120 seconds.
   - Active sweeper interval is exactly 60 seconds.
   - WebSockets are routed through Nginx forwarding `$http_host` (preserving port 5515). CORS and origin validations align with dev port 3000 (Vite) and production port 5515.

5. **JSON Verification Corpus:**
   - Create a complete, syntactically correct `wire-examples.json` corpus at `specs/stage4/wire-examples.json` containing complete JSON structures for each message shape, normal playing boards, safe numeric bounds, negative anchors, terminal outcomes, and invalid/malformed error message structures.
   - Parse and verify all markdown JSON fences and file states using Python's standard `json` module, outputting the verification logs to `docs/native-evidence/09-m3-contract/check_output.txt`.

*Planning completed. Proceeding to update files.

### Dated Session Note: November 6, 2026 - Stage 4 Protocol & Contract Correction Phase
**Goal:** Address outstanding schema, examples, and specification mismatches identified during comprehensive validation of Stage 4. Apply rigorous corrections to `duel-protocol.schema.json`, `requirements.md`, and `wire-examples.json`, followed by automated Python verification of all markdown JSON codeblocks and JSON files against the exact math domain pieces orientations.

**Key Corrections Planned:**
1. **Conditional Action Schema Restrictions:**
   - Enforce that `client_action` allows:
     - `move` direction: `left`, `right`, `down` only (explicitly reject any others, including `cw` or null).
     - `rotate` direction: `cw`, `ccw` only (explicitly reject any others, including `left`, `right` or null).
     - `hold` payload: must be `null` only (explicitly reject any non-null).
     - Reject illegal actions like `rotate-left`, `move-cw`, `hold-left`, `move-null`. Add a specific corpus entry and verification logic for counterexamples.
2. **Deterministic Geometry & Absolute Cell Alignment:**
   - Resolve 7 geometry errors in both specifications, markdown examples, and JSON corpus by deriving absolute cells strictly from the actual `orientations` database from `pieces.py` with pivot anchors.
   - Tori1 piece (which is the T piece at orientation 1) at `[0, 3]` (representing row 0, col 3) must have cells: `[[0, 4], [1, 4], [1, 5], [2, 4]]`.
   - Tori0 piece (T piece at orientation 0) at `[0, 3]` must have cells: `[[0, 4], [1, 3], [1, 4], [1, 5]]`.
   - Keep schema requirements for 4 unique in-bounds absolute cells: row `0..19`, col `0..9`, and anchor/origin row `[-3..19]`, col `[-3..9]`.
   - Re-evaluate the artificial level limit (remove artificial `level <= 100` cap which contradicts the actual Solo formula; instead use a Javascript safe bound matching actual gravity min/max formulas).
3. **Monotonic Action/Revision Lifecycle & Protocol-Policy Definition:**
   - Create a compact, authoritative `protocol-policy.md` or a highly focused protocol policy section within `requirements.md`. Ensure all contradictory parts of `requirements.md` are directly edited and aligned to point to it (not just appended).
   - Authoritative highwater policy rules:
     - Each NEW client action with `action_id > highwater_action_id` consumes that ID, regardless of whether it results in an accepted, no-op, or rejected state change.
     - Stale revisions (`expected_revision < current_revision` or `expected_revision > current_revision`) result in an ACK of status `"rejected"` or `"stale"` with the precise reason and the current board, consuming the ID.
     - Duplicate actions (`action_id <= highwater_action_id`) are completely ignored without re-applying, side effects, or any ACK broadcast reply, even if the payload differs.
     - Before-start actions (actions sent before both players join and game status is `"playing"`) get rejected with status `"not_started"` containing current own board, consuming that action's ID.
     - Schema-invalid messages do not produce a fake ACK, but instead get a canonical WebSocket close or error message.
     - Outcome transition happens exactly once, and a subsequent readback of the retained room state must be distinguished from a second outcome transition.
4. **WebSocket Rate and Resource Limits:**
   - Exactly 100 maximum concurrent active/retained rooms. Room creation requests above 100 are rejected, but players can still join an existing available room even if room count is at 100.
   - Handshake Hello deadline is exactly 10s. If first valid client handshake message is not received within 10s of socket connection, the connection is closed. This is not a deadline for the second player to arrive.
   - Waiting peer timeout is exactly 120s.
   - Inbound rate limits of 50 messages per 1s fixed monotonic window per socket, 4096 bytes max size.
   - Outbound broadcast queue of 100 messages with 200ms send timeout outside of room state lock, with specific numeric grace.
   - Sweeper executes every 60s, checking for idle rooms (waiting or playing idle > 120s, finished retention > 300s), where finished retention inactivity takes precedence.
   - Queue full/send failure/disconnect during `playing` results in forfeit win for the survivor. Wait-state abort has no invented winner.
   - Exact numeric WebSocket close codes: normal terminal (1000), policy violation (1008), binary unsupported data (1003), oversize (1009), invalid text/UTF-8 transport before ASGI (1007).
5. **Deterministic Shared Piece Generation:**
   - Define the exact deterministic hashing/index formula for piece generation using seed and individual per-board indexes, avoiding randomized state or Python's randomized hash, and ensuring no precomputed array limitations.
   - Gravity updates must evaluate all due boards in a single tick before checking outcomes.

*Strategy validated. Ready to apply corrections.**

### Dated Session Note: November 6, 2026 - Stage 4 Final Spec Corrections and Verification
**Goal:** Address outstanding schema contradictions, refine enums and conditional constraints, repair missing player2 board segments in positive scenarios, move invalid client actions to a negative examples file, clarify WebSocket close codes and stable piece hashes, and execute full syntax/geometry/conditional verification.

**Key Corrections Planned:**
1. **Canonical Outcome Reason Enums and Positive Board Complete Repair:**
   - Modify positive outcome reasons in `wire-examples.json` to canonical enums:
     - `server_state_update_finished_player1_won` -> `topout-player2`
     - `finished_draw` -> `simultaneous-topout`
     - `finished_forfeit` -> `forfeit-player2`
   - Repair `server_state_update_safe_bounds_negative_anchor` (which has status `"playing"`) to include a full valid `player2` board instead of `null`, maintaining the negative-anchor player1 board.
   - Apply the same board completion fix to `requirements.md` JSON code block (Fence 5).
2. **Isolate Negative Client Actions:**
   - Move the four keys containing `client_action_invalid_` from `wire-examples.json` to `specs/stage4/schema-negative-examples.json` along with their expected rejection reasons.
3. **Wording Gaps & Waiting-Aborted Outcome Reason:**
   - Add explicit `waiting-aborted` outcome reason to `duel-protocol.schema.json` for wait-state disconnect/queuefull/sendfailure/server shutdown (status finished, winner_seat null, player1 board playing, player2 null).
   - Ensure `waiting-peer-timeout` remains distinct.
   - Add valid examples for both `waiting-aborted` and `operational-abort` cases in the positive corpus.
   - Update `protocol-policy.md` and `requirements.md` consistently.
4. **WebSocket Close Codes and Stable Piece Hash Clarification:**
   - Update policy and requirements to clarify that close code `1003` is strictly for binary data, and `1007` is for invalid UTF-8/text transport before ASGI.
   - Define unambiguous stable piece hash formula: UTF-8 decimal nonnegative seed + `_` + decimal index (no padding), SHA-256 digest interpreted as big-endian integer modulo 7, piece order exactly `[I, O, T, S, Z, J, L]`.
   - Explicitly choose compatible websocket pin (e.g. `websockets==14.1`).
5. **Execution of Automated Verification Checks:**
   - Implement checking script to validate JSON syntax for all JSON files and markdown fences.
   - Check AST and piece geometry for all 7 tetrominoes over 4 orientations.
   - Verify explicit conditional constraints (e.g., status "playing" must have both boards, valid enums, etc.).
   - Save output files under `docs/native-evidence/11-m3-final-examples` with exit status.


### Dated Session Note: November 6, 2026 - M3 Duel Implementation Scope and Errata Repair
**M3 Implementation Scope:**
- Full implementation of Milestone 3 (M3) real-time 2-player WebSocket duel.
- Two independent server-side Tetris engines per room driven by 50Hz (20ms) server-side gravity loop.
- Client actions (move, rotate, hold, hard-drop, soft-drop) authenticated and routed based on seat/room, rejecting LF/CR/CRLF/U2028/U2029 ASCII identifiers.
- One-based action highwater policy (retaining last highwater ACK/NACK status and ignoring duplicate Actions <= highwater).
- Shared seed hash deterministic piece sequence modulo 7 using SHA-256 (UTF-8 format `seed_index`).
- Room capacities, connection rate limiting, and 60s idle sweeping.
- Sharp DPR 1/2 responsive Canvas 2D rendering representing two independent boards side-by-side with no third board.
- Complete deterministic python tests, Vitest UI/canvas tests, and locked websockets dependency configuration.

**Document Errata Repaired:**
1. Copy of the entire valid `wire-examples.json['server_state_update_playing']` object into `requirements.md` JSON fence 5, replacing the invalid partial board example.
2. In `protocol-policy.md`, change close code `1003` to represent binary data ONLY (removing invalid UTF-8 reference). Close code `1007` is set as the sole code for invalid text UTF-8 framing / transport data before ASGI dispatch (with no guaranteed JSON reply).


### Dated Session Note: November 6, 2026 - Stage 13 M3 Backend Completion & Robust WebSocket Dual-Engine Testing
**Goal:** Address and repair the 12 concrete, independently reproduced defects from the previous Stage 12 partial backend implementation, wire the dual-engine real-time WebSocket duel into the main router, declare proper `websockets` package dependencies, and execute a comprehensive suite of automated tests.

**Defects & Architectural Issues Addressed:**
1. **Strict Payload & Action Validation:**
   - REJECT action payloads with non-integer or coerced values (such as `action_id=True` or `1.0`, or non-string `expected_revision='0'`).
   - REJECT movement and rotation actions that lack required directions, or have incorrect conditional moves/rotations (e.g., move only left/right/down, rotate only cw/ccw, hold only null).
   - REJECT client handshake payloads with room_id containing trailing/leading whitespace or newlines (e.g., `'r\n'`) instead of silently normalizing them.
   - Forbid unknown fields at ALL levels of envelopes and payloads, matching canonical JSON schemas.
   - Rejects CRLF/LF/CR/U2028/U2029 in all ASCII identifiers (action_id, room_id, player_id).
2. **Deterministic Full-SHA Seed Generation:**
   - Fix piece selection at index `i` to use the ENTIRE 32-byte big-endian SHA256 digest of the UTF-8 string `"seed_i"` modulo 7, rather than using only the first 4 bytes of the digest.
   - Implement per-seat independent sequence generator indices (no global RNG monkeypatching).
3. **Injectable Monotonic Clock & Deterministic Gravity Engine:**
   - Replace standard `time.time()` and global mock time-advancing `mockable_sleep` with an injectable production/test monotonic clock framework.
   - Ensure gravity ticks apply strictly and independently to all due boards before final outcome, leaving not-due boards untouched. Gravity loop or user inputs do not stall gravity deadlines. Protect with single-finish guard.
4. **Out-of-Lock Bounded Writers & State Handling:**
   - Route EVERY outbound message (ACK, error, state updates, closes) outside of critical room locks via per-peer bounded task-safe writers.
   - Snapshots taken under room locks, and then enqueued for async write after releasing locks.
   - Handle outbound queue fullness (100 msgs) strictly, triggering instant forfeiture, survivor state transitions, and close code `1000`.
   - Bounded connection write timeout of 200ms and cancel grace of 50ms.
   - Disconnected or blocked reader endpoints must cancel and drain tasks promptly.
   - Retain exactly one terminal cached state update for 300s, preventing any resurrection or secondary state transitions.
   - Correctly distinguish outcome reasons: `waiting-aborted` when a game in "waiting" is aborted (with null winner/reason), and standard draws or operational aborts with exact canonical reasons.
5. **Main Router Integration & Sweeper Service:**
   - Integrate `duel.router` into `app/main.py`.
   - Wire WebSocket endpoints and lifecycle hooks properly.
   - Set up startup/shutdown sweeps: room limit of 100, hello timeouts (10s), state-based expiration (waiting 120s, playing idle 120s, finished 300s + sweeper 60s slack).
   - Rate limit to 50 messages/1s. Max message size 4096 UTF-8 bytes.
   - Specific close codes: binary `1003`, policy `1008`, oversize `1009`, invalid UTF-8/text `1007`.
   - Validate HTTP WebSocket Origins (port 5515 and dev 3000).
6. **Highwater-Only Policy & Revision Event Semantics:**
   - Retain strict one-based highwater ACK/NACK status and ignore duplicate or stale actions <= highwater without re-replying.
   - If an action is rejected, the client gets a NACK containing the current authoritative board revision.
   - Both clients transition to `playing` automatically on second join.

**Verification Plan:**
- Run independent test suites for WebSocket protocol negative cases, concurrency, and monotonic clock gravity.
- Save execution logs in `docs/native-evidence/13-m3-backend` to verify 100% completion.


### Dated Session Note: November 7, 2026 - M3 Backend Defect Identification & Refactoring Strategy
**Acknowledge and Map Actual Failures:**
1. **Pydantic ClientActionPayload Schema Discrepancy:** The schema requires direction to be `null` for `hold` actions explicitly (no default in JSON), but Pydantic was accepting missing `direction` due to `= None` default. This must be a required nullable field in Pydantic.
2. **Prestart Waiting Board and ACK Board Violation:** During prestart (waiting status), the player 2 board is correctly `null` but the player 1 board was being serialized as `None`/`null` inside ACKs and state updates because `player1_board` was not initialized until both players joined. The canonical schema requires `player1_board` to be an object with status `"playing"` during the waiting state. We must initialize `player1_board` immediately on first-seat join.
3. **Incorrect Waiting Failure Outcome:** A writer failure or shutdown during the waiting state was incorrectly producing a terminal state with winner `"player2"`, outcome reason `"forfeit-player1"`, and board `None`. It must produce `"waiting-aborted"` with a `null` winner and a real, valid `player1_board`. Waiting expiry must produce `"waiting-peer-timeout"` with a `null` winner. Playing idle must produce `"operational-abort"` with a `"draw"`. All terminal transitions must occur exactly once.
4. **Missing Close Gating on Normal Topouts:** Normal topouts updated room fields but did not schedule any close or stop gravity. This leaves surviving sockets waiting on inbound forever. All terminal paths must deliver exactly one final state update and close with code 1000.
5. **Sweeper/Shutdown Task Cancellation Race and Lifespan Ownership:** The sweeper was canceling writers before calling `enqueue_close`, so the close frames were never delivered. Sweeper task itself was unowned and untracked. Actual lifespan must own the background sweeper task and shut down or restart cleanly.
6. **Finished Room Lock I/O Violation:** Finished room readback was directly awaiting `send_text` and `close` while holding the room lock, causing network I/O blockages inside critical sections. Every outbound (including pre-room/handshake errors, readback, and close) must use an owned bounded peer writer outside of locks.
7. **Ignoring Enqueue Failures:** The return values of `enqueue_message` were ignored for ACKs. We must handle queue fullness on ALL paths, triggering instant forfeiture/abort synchronously without infinite recursive loops or task-creation storms.
8. **Rate Limiter Discrepancy:** The sliding window implementation violates the contract of a fixed monotonic 1-second window of 50 messages including duplicates.
9. **Direct WebSocket Closes for Schema Mismatch:** Malformed JSON/schema-invalid JSON closed the socket directly without sending a canonical error payload first. We must send a canonical error payload and then close with code `1008`.
10. **Seat Ownership and ID Discrepancies:** Duplicate clients or full rooms could overwrite/forfeit existing valid seats through endpoint cleanup defaults. URL room_id and handshake room_id discrepancies must be rejected.
11. **Revision and Integer Overflow Preflight:** Monotonic integer fields (revisions, score, lines, level) can overflow JS max integer. We must preflight them and operational-abort if any would exceed `9007199254740991`.


## Dated Session Note: November 7, 2026 - Reproduction of 6 Specific Backend Failures
We have identified the following six backend issues from independent diagnostics and will write regression tests to reproduce them.

1. **PRESTART ACK WRONG REASON:**
   - **Problem:** When an action is sent before both players have joined, the server returns an ACK with `reason='not_playing'`. However, the accepted policy requires exactly `'not_started'`.
   - **Expectation:** The server must return `'not_started'` when the status is `'waiting'`. The waiting board must be fully preserved. We must test the hello handshake followed by a prestart action, asserting the canonical frame, correct reason, and highwater consumption. Subsequent duplicate actions must be ignored.

2. **PLAYING SHUTDOWN WRONG WINNER:**
   - **Problem:** When the room is active (`status='playing'`) and shutdown is requested via `await room.shutdown_room()`, the winner is currently recorded as `None` and the reason is `"operational-abort"`. The policy requires that if the game had already started (`status='playing'`), the winner must be `"draw"` and the reason `"operational-abort"`.
   - **Expectation:** A waiting room that is shut down retains a `None` winner and `"waiting-aborted"`. A playing room that is shut down gets a `"draw"` winner and `"operational-abort"`. We must test both paths and ensure they don't just clear `ROOMS` but properly transition states.

3. **WAITING EXPIRY DELETES ROOM IMMEDIATELY:**
   - **Problem:** When a waiting room times out or playing room goes idle, the room is swept and deleted from `ROOMS` instantly during `sweep_once`. However, the retention policy requires retaining the terminal snapshot in memory for 300 seconds of inactivity (retention period) before deletion.
   - **Expectation:** Rooms must transition to their terminal state (e.g. status finished and outcome reason `"waiting-peer-timeout"` or `"operational-abort"`) on timeout/expiry, but they must NOT be removed from `ROOMS` until 300 seconds have elapsed since the last activity in that terminal state. A readback (querying or reading from the room) must reset the inactivity timer without mutating the final snapshot. Also, global `ROOMS_LOCK` must not block on room I/O or socket drains; locks must be held briefly.

4. **FAILED SOCKET NEVER ACTUALLY CLOSED:**
   - **Problem:** When a websocket connection experiences write timeout (200ms) or is overflowed (queue full > 100), the Peer writer loop exits and sets `closed_event`, but the server fails to call `websocket.close(code)`.
   - **Expectation:** The transport close must always be completed via a bounded `websocket.close(1000)` call (or appropriate code like `4001` or `1008`) even if the writer loop is dead. The healthy survivor gets exactly one final state update and normal close code `1000`, and the failed peer gets bounded cleanup. We must enforce a 200ms write timeout + 50ms cancel grace, and avoid unbounded awaits or orphaned tasks.

5. **TERMINAL ACTION ACK LOST:**
   - **Problem:** When an action causes a topout/game-over, the server transitions the state to finished and broadcasts the final state update and close before enqueuing the ACK for the triggering action. As a result, the triggering player does not receive the ACK.
   - **Expectation:** Reorder atomic state modifications and outgoing transmissions so that the triggering action gets its ACK first, followed by exactly one final state update snapshot, and then the websocket is closed.

6. **REMAINING BOUNDS/TESTGAPS:**
   - **Problem:** (a) No validation checks on preflight variables like `score`/`total_lines`/`level` before actions or tick logic, only revisions are checked. If any would overflow JS max integer, they must operational-abort to a draw. (b) The `ALLDUE` simultaneous tick test artificially pre-marked both boards as `game_over` rather than executing actual simultaneous tick logic on legal boards, which doesn't verify simultaneous gravity correctness. (c) The websocket rate/schema/size error testing did not strictly assert exact close codes or enforce strict outgoing schema validation against the official specification JSON.
   - **Expectation:** Preflight all model fields for integer overflow. Replace artificial tests with genuine legal gravity ticks and simultaneous topout assertions. Replace the weak schema/rate tests with strict assertions for close codes `1008`, `1009`, `1003`, and exact binary/text boundary handling.


### Dated Session Note: November 7, 2026 - Execution of 6 Specific Backend Defect Fixes (Native 16)
We are starting Native 16 execution. Our immediate steps are:
1. Add failing regression tests representing the 6 reproduced defects into `backend/tests/test_m3_duel.py`.
2. Run pytest to confirm they fail and record the outputs under `docs/native-evidence/15-m3-backend`.
3. Modify `backend/app/controllers/duel.py` to fix all 6 issues sequentially.
4. Rerun pytest to verify all tests (including new regressions) pass cleanly.


### Dated Session Note: November 7, 2026 - M3 Duel Frontend Specification & Implementation
**Goal:** Implement the actual M3 Duel Frontend and its associated unit/integration tests without breaking existing Solo mode regressions.

**Detailed Design and Implementation Plan:**
1. **Mode Isolation:**
   - Create a top-level `mode` switch ('solo' | 'duel') in `App.tsx`.
   - By default, `mode` is 'solo', maintaining 100% test compatibility and immediate Solo game setup.
   - When transitioning to `'duel'`, the Solo component is completely unmounted. This automatically cleans up its timers, keyboard event listeners, and pending HTTP requests via its unmount logic.
   - Returning to `'solo'` remounts the Solo component cleanly with a fresh lifecycle.
2. **Unguessable Client IDs & Room ID Validation:**
   - Room ID input must be ASCII, restricted to alphanumeric characters, dashes, and underscores (`^[a-zA-Z0-9_-]{1,64}$`). No trailing or leading whitespace, and no newlines. Length 1..64.
   - Generate a cryptographically secure or unguessable random client ID (`clientID`) for each connection.
   - Auto-generate an unguessable room ID for "Create Room" to avoid collisions.
3. **Connection & Handshake:**
   - Establish WebSocket connection using `new WebSocket(wsUrl)` connecting to `ws://${window.location.host}/api/ws/duel/${roomId}` (handling ws vs wss).
   - Only establish connection when user clicks "Create Room" or "Join Room" (never before).
   - Send canonical 1.0 client handshake immediately on connection:
     `{"version": "1.0", "type": "handshake", "payload": {"room_id": roomId, "client_id": clientId}}`
   - Store own seat assigned by server: `"player1"` or `"player2"`.
4. **Authoritative UI Rendering:**
   - Render two `TetrisBoard` components side by side for Player 1 and Player 2.
   - Player 2 canvas board shows a waiting placeholder if status is `'waiting'` and player 2 has not joined yet.
   - Both boards render state authoritatively from WebSocket updates: `score`, `total_lines`, `level`, `next_piece`, `hold_piece`.
   - There are no client-side gravity timers or gravity ticks in Duel mode.
5. **Robust Action Queue FIFO with Revision Reconciliation:**
   - Keep a `pendingAction` state or reference representing the single action currently in flight.
   - Keep a `queue` of pending action payloads.
   - Only send one action at a time. Send action payload:
     `{"version": "1.0", "type": "action", "payload": {"action_id": actionId, "expected_revision": currentBoardRevision, "action_type": actionType, "direction": direction}}`
   - Every action has a unique positive JS-safe `action_id` (starts at 1 and increases monotonically per connection).
   - On keydown (move/hold/CW ArrowUp/CCW Z) or clicking buttons, if playing and active:
     - Check if any input elements are focused (`document.activeElement` is input/textarea/contenteditable) - if so, ignore the key.
     - Generate a new action payload and enqueue it.
     - Process queue: if there's no pending action in flight, send the first in the queue using the LATEST own board revision.
     - Explicitly set `direction: null` for `'hold'` actions.
   - On receiving an ACK:
     - Verify if the `action_id` matches the in-flight `pendingAction`.
     - If it matches, resolve the pending state and proceed to the next action in the queue.
     - If we receive an ACK of status `'rejected'`, reconcile by setting own board state to the `authoritative_board` returned in the ACK.
     - If a state update has a higher `room_revision` than we have seen, apply it. Never let a stale ACK overwrite a newer state update broadcast.
     - Set a timeout (e.g. 5000ms) for the pending action in flight. If it expires, error/close the connection to prevent infinite hanging.
6. **Room Lifecycle & Cleanup:**
   - Clicking "Forfeit" or "Leave Room" explicitly closes the WebSocket connection with normal close code `1000`.
   - On room change or return to Solo, close any active WebSocket, clear timeouts/intervals, clear queues.
   - If WebSocket closes with code `1000`, preserve the final outcome (do not treat as error).
   - Visibly show any unexpected close/error, allowing the user to create/join a new room or return to Solo.
7. **Layout & Dimensions:**
   - Use compact flex/grid layout in CSS to ensure that at 1280x900, both boards (240x480) and all UI controls fit without overflow.
8. **Frontend Testing Suite:**
   - Create extensive unit/integration tests using a mocked WebSocket environment in Vitest.
   - Cover: mode unmounting, normal close, error close, seat binding, FIFO queue action ID uniqueness, revision reconciliation, stale state updates rejection, keyboard events bypass during typing, and new room transition.

### Short-Dated Execution Note: November 7, 2026
We are executing the final, complete Duel UI Integration and Testing phase to fully resolve M3 UI requirements. This work is restricted strictly to frontend components, types, styles, and unit/integration tests without any backend modifications, Git operations, or external deployments.

Our architectural corrections cover:
1. **App Mode Switching**: Isolate single-player logic inside a dedicated `SoloGame` component and wire up the top-level mode switch ('solo' vs 'duel') in `App.tsx`. Switching unmounts the current game type, automatically destroying single-player automatic gravity loops, event listeners, and promise queues. Returning to solo remounts a completely fresh Solo instance.
2. **Robust FIFO Queue & Reconciliation**: Correct the critical FIFO bug. The queue processes actions sequentially and tracks the in-flight action ID with a 5-second timeout. Incoming matching ACKs (accepted, noop, or rejected) immediately reconcile the returned authoritative board state and revision synchronously in our roomState reference *before* triggers of `setRoomState` and `sendNextAction`. Stale ACKs and state updates are securely filtered out.
3. **Correct WS Payload Types**: Extend `types.ts` to include the `ServerHandshakeMessage` union member so that `msg.type === 'handshake'` compiles correctly. Correct `ServerErrorMessage` schema where the code field is actually `error_code: number` (integer) matching the FastAPI backend payload.
4. **Unguessable IDs & Strict ID Rules**: Use `crypto.randomUUID` (or standard browser crypto API) to produce private unguessable room/client IDs. Enforce exact whitespace/newline rejection rules (no soft normalization or trimming) on joining room IDs.
5. **Duel Workspace Layout & Responsive CSS**: Introduce detailed responsive styling for Duel containers, lane boards (downscaled to 240x480 to fit 1280x900 viewports with zero overflows or overlaps), compact headers, and controls.
6. **Vitest Real-Time Mock Test Suite**: Code thorough real-time WebSocket mocked tests verifying unmounting single-player loops, handshake/seat bindings, FIFO queue serialization, out-of-order ACK protection, keyboard bypass on typing, normal closing vs unexpected error, and new room transition.

### Dated Session Note: November 7, 2026 - Target M3 Correction & Quality Improvements
**Goal:** Implement precise architectural fixes and targeted code corrections for the five Sonar bugs, the cancel-resistant send deadlock, the safe boundary and gravity operational abort checks, the frontend actionID wrap prevention, and minimal code duplication. We also aim to enhance test coverage to reach >=85% line/branch coverage in duel.py and >=80% overall backend coverage.

**Detailed Fix Strategy:**
1. **Cancel-Resistant Send Deadlock**:
   - Refactor `socket_writer_loop` to launch `websocket.send_text` as a strongly-referenced Task.
   - Use a bounded `asyncio.wait_for` of 200ms on a shield of the send task.
   - On timeout, cancel the send task and perform a 50ms bounded grace wait using `asyncio.wait`, which avoids waiting for cancellation indefinitely if the WebSocket remains stubborn.
   - Then immediately call `peer.close_transport()` to close the socket and unblock any pending operations.
2. **Sonar Bugs (duel.py)**:
   - Re-raise `asyncio.CancelledError` in all catch blocks (lines 322, 574, 584, 635) to prevent swallowing the exception and breaking cancellation propagation.
   - Replace the fire-and-forget `asyncio.create_task(peer.close_transport())` inside the `finally` block of `socket_writer_loop` with a direct, clean `await peer.close_transport()`.
   - Replace `random.randint(0, 1000000)` with cryptographically secure `secrets.randbelow(1000001)` to address S2245 while preserving the exact SHA sequence properties.
3. **Safe Bounds & Gravity Operational Abort**:
   - Verify that any started operational abort transitions the room to a draw.
   - Implement preflight checks for overflow on board and room revisions, score, level, lines, and action IDs. Reject any bounds-exceeding actions with a rejected ACK and close connection.
4. **Frontend Action ID Wrap**:
   - Stop play with a visible UI error if `actionIdRef` approaches `Number.MAX_SAFE_INTEGER`.
5. **Code Duplication Reductions**:
   - Extract redundant transaction finalization block in `backend/app/controllers/duel.py` into a helper function `commit_and_ack_action_sync`.
   - Extract the mini-grid renderer in `frontend/src/App.tsx` and `frontend/src/components/DuelGame.tsx` into a typed `PiecePreview` component.
6. **Coverage Enhancement**:
   - Add targeted pytest cases verifying boundary overflow, binary/oversized frame rejections, rate limiting with 50-message windows, inactive room sweeping, and other uncovered branches.

### Dated Session Note: November 13, 2026 - 21-m3-scalar-resumed note admitting native19 scalar claim incomplete
We acknowledge that the previous native19 scalar claims regarding complete coverage of monotonic overflow and revision limits were incomplete. In this resumption session, we address seven precise failure modes and three remaining SonarQube quality findings to ensure full operational safety and protocol compliance:
1. **Revisions MAX Overflow**: If `room_revision` or any player's `board_revision` reaches `9007199254740991` (`Number.MAX_SAFE_INTEGER`), the duel must immediately terminate as a draw with `winner = None` and status reason `'operational-abort'`.
2. **Monotonic Counter MAX Overflow**: If any player's `score`, `total_lines`, or `level` reaches `9007199254740991` (`Number.MAX_SAFE_INTEGER`), the duel must immediately terminate as a draw with `winner = None` and status reason `'operational-abort'` under both gravity and player action ticks.
3. **Preflight Candidate Overflow & Deep Validation**: In candidate crossing checks, if a line clear or lock-in would push score, lines, or level past the MAX limit, we must abort with a draw ('operational-abort') BEFORE committing any invalid states, rollback the active block, preserve the previous valid state (board/score/revisions/action ID sequences), reject the triggering action with an integer overflow ACK, and close the WebSocket.
4. **Room Sweeper Cancellation Recovery**: Fix `room_sweeper_loop` to correctly re-raise `asyncio.CancelledError` after its cleanup block to avoid swallowing external parent cancellation.
5. **Strict Test Assertions**: Replace vacuous try/except assertions in `test_m3_duel.py` with rigorous endpoint tests validating handshake, exact rejected ACK error messages on overflow/bounds violations, and clean draws.

### Failed Test Checks & Resolution Note: November 13, 2026
During backend testing, the initial run of `test_action_candidate_boundary_overflow` failed with two NameErrors:
1. `NameError: name 'SpeculativeSupplier' is not defined` (occurring on import check in test file).
2. `NameError: name 'move_game' is not defined` (occurring inside test evaluation).

These errors were caught and resolved BEFORE finalization:
- **Resolution 1**: Imported `SpeculativeSupplier` and `is_board_overflow` directly from `app.controllers.duel` into `backend/tests/test_m3_duel.py`.
- **Resolution 2**: Qualified `move_game` to `duel.move_game` inside `test_action_candidate_boundary_overflow`.
- **Result**: Subsequent pytest execution succeeded with all 83 backend tests passing successfully (100% green).
- **Evidence preservation**: All stdout, failed outputs, and JUnit report xml were cleanly written to `docs/native-evidence/21-m3-scalar/`.

