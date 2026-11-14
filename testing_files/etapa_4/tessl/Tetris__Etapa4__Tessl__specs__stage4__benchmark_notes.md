# Stage 4 Benchmark Instrument Specifications & Task Notes

### Dated Specification Note: November 13, 2026
This document specifies the design, implementation, and verification framework for the final Stage 4 benchmark instrument for the browser-based Tetris Studio application.

#### 1. Command Line Interface (CLI)
The instrument must support execution via a single-run CLI matching the exact signature:
`node benchmark.js --scenario solo|duel --mode probe|final --label UNIQUE --output ABSOLUTE_OUTPUT_DIR`

#### 2. Isolation & Focus Gating
- **Fresh Client Browsers:** One distinct, fresh Chromium browser process is launched per client (the Actor for solo/duel, and an optional second peer browser for duel). Contexts and pages are completely isolated.
- **Window Identification:** 
  - The Actor page document title is set to end with `ACTOR INPUT`.
  - The Peer page document title is set to a different text.
- **Foreground Polling:** 
  - Prior to initiating the warm-up, the instrument polls `document.hasFocus()` and `document.visibilityState === 'visible'` in a loop with a 15-second timeout.
  - The browser PID and title are recorded and printed to stdout once readiness is achieved.
  - Focus loss is tracked via page-level events and recorded inside the final report.

#### 3. Execution Flows
- **Solo Mode:** Navigate directly to the production URL, switch to Solo mode if needed, click the Restart button to ensure a fresh session, and run.
- **Duel Mode:**
  - Launch two isolated browsers: Actor and Peer.
  - Actor connects, navigates, enters Duel Mode, clicks "Create Private Room", and extracts the generated room ID from `.room-id-display`.
  - Peer connects, navigates, enters Duel Mode, inputs the room ID in `#room-id-input`, and clicks `.btn-join`.
  - The instrument monitors handshakes and seats (`player1` vs `player2`), waits for room state status `'playing'`, and starts the active measurement window.

#### 4. Timing & Mathematical Calibration
- **Measurement Windows:**
  - `--mode final`: Exactly 5000ms warm-up and 30000ms measurement phase.
  - `--mode probe`: Exactly 2000ms warm-up and 8000ms measurement phase.
- **Node-to-Browser Clock Calibration:**
  - Bracketed calibration loops run pre-trial and post-trial:
    - Node monotonic start -> Page `performance.now()` -> Node monotonic end.
  - Calibration uncertainty and drift are calculated and recorded.

#### 5. Verification & Redraw Audits
- **Canvas Pixel Checks:** 
  - Read actual RGBA pixel centers for all 200 cell coordinates on the 10x20 board canvas back-buffer (accounting for DPR scaling).
  - Map RGB colors to logical block types using a Euclidean distance threshold (< 40) against the official palette.
  - Compare actual Canvas layout with expected logical board layout from the API/WS state to verify correct, non-stale redraw.
- **Metric Analytics:**
  - Record frame scheduling (rAF intervals) separately from verified Canvas visual draws and Action latency.
  - Filter out exclusions (noop, O rotation, blocked, concurrent, or ambiguous events) from latency measurements.

### Dated Specification Note: November 13, 2026 (Benchmark Instrument Correction)
- **Playwright Browser `process()` Removal:** The Playwright `Browser` class does not expose `.process()`. Removed both unsupported `.process()` calls.
- **Window Gating and Labelling:** Browser page titles are constructed dynamically using the command-line `--label` parameter, e.g. `TESSL <label> ACTOR INPUT`, matching the exact title in the readiness JSON. A single, unified 90-second focus wait is applied, failing the trial on timeout or subsequent focus loss.
- **Chrome / Environment Configurations:** Configure Playwright to launch the headed installed Chrome channel with sandboxing, a 1280x900 viewport, and device scale factor 1. Explicitly filter out default arguments (`--disable-background-timer-throttling`, `--disable-backgrounding-occluded-windows`, `--disable-renderer-backgrounding`) and do not use unapproved focus APIs such as `Emulation.setFocusEmulationEnabled` or `bringToFront`.
- **Defensive Resource Management (Cleanup):** Place browser close/cleanup logic inside a top-level `finally` block ensuring that any partial outcomes survive failure and are serialized to disk.
- **Duel Mode Socket Gating:** Duel setup is gated on receiving actual playing wire messages (`payload.payload`) across BOTH client WebSockets, verifying matching room and seat allocations directly from the handshake, and waiting until both players' boards are active.
- **Solo Mode UI Selectors:** Verify the correctness of selectors and utilize the production app's automatic solo game creation path without introducing race conditions during restarts.
- **Duel Message/Payload Structures:** Correct the WebSocket message payload parsing to match the actual Stage 4 protocol specs: outbound actions use `action_id`, `action_type`, `direction`, and `expected_revision` inside `message.payload`. ACKs contain `status` (`applied`/`noop`/`rejected`) and `authoritative_board` inside `ack.payload`. Incoming state has `player1_board` and `player2_board` inside `message.payload`.
- **Canvas Seat-Based Ordering:** On both client pages, canvases are ordered strictly by player seat (seat 0 / player1 at index 0, seat 1 / player2 at index 1) rather than actor-relative, verifying correct board updates on both pages at the actor's seat. Intercept and register WS observations on both pages before entering Duel.
- **Trusted Keyboard Input Interception:** Real trusted DOM keydown events are monitored via a document-level listener, capturing timestamp, key, isTrusted, focus, visibility, and a per-dispatch ID staged before triggering keyboard presses. Each staged input is linked to exactly one action frame.
- **Solo WeakMap Request Correlation:** Attach immutable identifiers to Playwright Requests using a `WeakMap`. Filter only the actual POST move/rotate endpoint and game ID, matching direction from the JSON body and linking the completed response. Reject ticks, GET requests, or unmatched POST actions.
- **Action Pacing and Exclusions:** Pace actions cleanly to avoid post-window inputs. Exclude rotations of O-pieces, no-ops, blocked moves, stale states, or any other ambiguity. Ensure peer latency is measured independently from local latency (never using local WebSocket RTT).
- **Comprehensive Output Auditing:** Capture and retain all 200 RGBA values, full authority masks, canvas coordinates, and timestamps. Calibrate Node and browser clocks using pre- and post-trial bracketed calibrations, mapping all metrics into stable, persistent, named JSON files.

### Dated Specification Note: November 13, 2026 (Benchmark Instrument Refinement)
- **Node-Defined Bounds & Timing Anchors:** Rather than mixing page and Node benchmarks, all limits are defined securely in Node monotonic time: `nodeWarmupStart` (current Node performance.now), `nodeMeasureStart` (+5000ms warm-up), and `nodeMeasureEnd` (+duration, 8000ms for probe or 30000ms for final). Wall anchors `Date.now()` and `performance.now()` are captured together at start.
- **De-risked Timing Comparisons:** Page-based event timestamps (rAF frames, keydown DOM events, canvas draws, and WebSocket occurrences) are mapped to Node time using calibrated pre-trial clock offsets inside the timed loop, and the post-calibration calculations are computed *after* the timed loop finishes to avoid `postCalActor/postCalPeer` initialization/scoping crashes.
- **Robust Outbound & Canvas Verification:** Keep Keyboard and state checks accurate. Track the active piece, board-revision changes, pixel changes, and authority masks. In solo games, match responses via Request mapping. In duel games, match outbound actions with their ACK, seat indexes, and 200-cell authority state masks to qualify separate boards.
- **Advanced Metric Logging:** Ensure the output JSON preserves raw actor rAF timestamps, classifications of all intervals (eligible, cross-boundary, pre/post-window), nominal/actual UTC & Node bounds, visibility status, and chrome browser version.
- **Defensive Error Cleanup:** Maintain isolated browser instances. If focus gating or setup fails on either page, both browser instances are safely and explicitly terminated in a final block, preventing orphaned processes.

### Dated Specification Note: November 13, 2026 (Stage 4 Surgical Benchmark and Focus Gating Fixes)
- **Single Independent Trial Execution:** Modified CLI runner to execute a single trial `runTrial(..., 1, ...)` rather than hardcoding a `t=1; t<=3` loop for all runs, including probes, to comply with the external driver requirement of one independent trial per label in both modes.
- **Actor-Only Focus Gating:** Standardized the initial foreground focus check to gate exclusively on the Actor page (`document.hasFocus() + visible` after selecting the actor page), removing the requirement for simultaneous peer focus, which does not reflect realistic operating system behavior.
- **Peer Visibility & Focus Descriptive Metadata:** Preserved peer visibility and focus values as descriptive metadata in the consolidated final report, alongside its independent socket and wire evidence. The peer is permitted to remain in the background, but both clients must be active and ready prior to user focus.
- **Strict Peer Visual Latency Requirement:** Ensured that measured peer results require actual live frames/pixels on the peer's canvas to be verified and matched against the state without a canvas verification timeout.
- **Benchmark Test Isolation:** Moved the benchmark-only testing fixture from `frontend/src/benchmark.test.ts` to `frontend/benchmark-tests/benchmark.test.ts` to ensure that it does not modify the product source directory or product coverage scope, keeping product files completely untouched.

### Dated Specification Note: November 13, 2026 (Stage 4 Runtime Defect and Latency Correlation Fixes)
- **Direct CLI Windows URL Correction (ESM Guard):** Direct ESM guard is corrected to use `pathToFileURL` on `process.argv[1]` to correctly handle percent-escaped URLs on Windows (especially with unescaped spaces or drive letters). Added proof that running direct CLI with invalid arguments exits nonzero with expected CLI validation text, while module imports do not trigger main.
- **Solo Request/Response Correlation (Solo Correlator):** Correlate real metadata via `res.reqMeta` properties: method `'POST'`, exact `gameId` from the active game, `endpoint` (`move` or `rotate`) matching the action, body `direction` matching the key press, matching shared immutable `reqId`, HTTP status 200, and strict per-dispatch bounds (`time_node >= inputNodeTimestamp`).
- **Exclusion of Stale/Invalid States:** Strictly exclude O-rotations, no-ops (where post revision matches prior revision), collisions (blocked moves), gravity/intervening revisions, and any ambiguous states where `revisionDiff > 1` using real records.
- **Empty Canvas RGB & Board Precedence:** Correct the canvas empty center color to `[28, 31, 43, 255]`, reflecting CSS background `#151824` composited with `rgba(255,255,255,0.03)`. When verifying expected occupied cells, let locked board cells take precedence over active piece cells in `TetrisBoard`. If canvas pixels are missing, do not fall back to success.
- **Duel Correlator Action Chain:** Correlate exactly one outbound actor action to its accepted ACK on the actor socket, and the corresponding peer socket inbound `state_update` message matching the same room, seat, board revision, and grid contents.
- **Contemporaneous Observation Polling:** Poll actor and peer canvases in a single contemporaneous loop inside Node, recording the actual order and exact Node/page timestamps, without inferring remote observation timestamps from local round-trip times (RTT).
- **Measurement Window Gating & Timing Anchors:** Ensure the final wait in Node covers the entire fixed measurement window even if dispatching stops 300ms early. Record nominal and actual Node bounds, visibility status, and window focus. Preserve raw samples on failed or rejected attempts.
- **Focused Synthetic Tests:** Add detailed unit tests for exact Solo response matching, false candidates, empty composited RGB, and exact Duel peer authority correlation.

### Dated Specification Note: November 13, 2026 (Win32 Foreground Observer Gating)
- **Win32 Observer Focus Gate Integration:** If the environment variable `TESSL_FOREGROUND_OBSERVATION` is supplied, the focus gating loop is extended to require both browser page-level focus (`document.hasFocus() + visible` on pageActor) and Windows foreground window evidence.
- **Observer File Parsing:** The absolute path specified in `TESSL_FOREGROUND_OBSERVATION` is parsed safely. Only complete newline-terminated lines from the JSONL file are processed, discarding any partial trailing lines.
- **Validation Criteria:**
  - Standard startup and teardown metadata records (events `'start'` and `'end'`) are excluded.
  - The latest consecutive three samples of event type `'foreground'` must have:
    - `actor_title_match === true`
    - `visible === true`
    - Same `hwnd` and `pid` values across all three.
    - Newest (very last) sample's UTC timestamp (using `Date.parse`) no older than 400ms compared to the current Node clock (`Date.now()`).
  - If any sample is stale, missing, or invalid, or if the file contains insufficient records, the focus gating check fails.
- **Polling Strategy:** Within the 90-second overall timeout, the page focus state and the Win32 observer gate are checked in parallel. If `TESSL_FOREGROUND_OBSERVATION` is provided, the polling interval is set to ~100ms. If not, fallback to existing standalone browser-only focus checking (interval ~200ms) with descriptive status.
- **No OS Activation:** The benchmark runner never triggers OS-level activation (e.g. bringToFront or focus APIs beyond Playwright's native context calls).
- **Report Metrics Persistence:** The gate mode (`'win32-observer'` or `'browser-only'`) and the validated foreground evidence (including the last three timestamps, HWND, and PID) are persisted in the final consolidated performance report and individual trial results.
- **Synthetic Unit Verification:** Synthetic unit tests check stale, wrong, partial, and correct sample sequences in `frontend/benchmark-tests/benchmark.test.ts`.




