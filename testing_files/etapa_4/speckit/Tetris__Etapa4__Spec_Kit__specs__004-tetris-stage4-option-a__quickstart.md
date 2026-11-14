# Quickstart Validation Guide

This guide describes how to run validation checks for Stage 4 Option A to verify the implementation of Authoritative Tetromino Rotation, High-DPI Canvas 2D Board, and Real-Time WebSocket Duel.

---

## 1. Prerequisites

Ensure your development environment meets the following specifications before running checks:
- **Python**: Version 3.11 (inherited CI and containers baseline) / Version 3.12.4 (independent Windows verification runtime)
- **Node.js**: Version 24 (standard major)
- **Docker & Docker Compose**: Installed and configured for non-root execution
- **Playwright**: Browser binaries installed (`npx playwright install chromium`)

---

## 2. Setup and Execution [INF-01]

To set up the workspace and start the application under Docker, execute the following commands.

### 2.1 Backend Setup and Verification (Host Machine)
```bash
# Navigate to the backend directory
cd backend

# Install dependencies including dev requirements
pip install -r requirements.txt -r requirements-dev.txt

# Run backend verification (pytest, coverage, and pip-audit)
pytest --cov=app tests/
pip-audit
```

### 2.2 Frontend Setup (Host Machine)
```bash
# Navigate to the frontend directory
cd frontend

# Install pinned dependencies
npm ci

# Run production build and tests (compiles TypeScript and bundles via Vite)
npm run build
npm test
```

### 2.3 Starting the Multi-Container Production Environment
```bash
# Navigate to the project root and start services via Docker Compose
docker compose up --build -d

# Verify that both the frontend (reverse proxy) and backend containers are healthy
docker compose ps
```
- The application frontend is exposed on Host Port **5183** (`http://localhost:5183`).
- The backend remains internal, securely proxied behind Nginx.

---

## 3. Verification Scenarios & Validation Commands

Validation is split into three independent milestones matching the requirements. Run each suite sequentially, creating verification evidence snapshots between phases.

### Milestone 1: Authoritative Tetromino Rotation [ROT-01, ROT-02, ROT-03]
To verify backend rotation mechanics, deterministic horizontal kick offsets, and collision rejections:

```bash
# Run backend unit tests specifically targeting tetromino rotation
pytest tests/unit/test_game_engine_us1.py -v
```

**What to Check in the Test Output**:
- [X] ROT-01: T, I, S, Z, L, J cycle through four unobstructed orientations and return to Orientation 0 on the 4th rotation.
- [X] ROT-01: O piece rotation operates as a strict, state-invariant no-op with identical orientations.
- [X] ROT-02: Horizontal offsets are checked in the exact order `0, -1, +1, -2, +2`.
- [X] ROT-02: Rotations overlapping boundaries, the floor, or locked cells attempt kicks and successfully fallback to no-op if all five offsets fail.
- [X] ROT-03: Rotation does not advance gravity, trigger locks, or update scores.
- [X] ROT-03: Active piece orientation resets to 0 (Spawn orientation) whenever spawning a new piece or retrieving a piece from Hold.

---

### Milestone 2: High-DPI Canvas 2D Board Rendering [CAN-01, CAN-02]
To verify DOM decommissioning, canvas mounting, and pixel ratio scaling checks:

```bash
# Run frontend unit tests to assert Canvas mounting and resize events
npm run test --tests/App.test.tsx -u
```

**What to Check**:
- [X] CAN-01: Traditional cell div selectors (`div.cell` / `.board-grid`) are fully decommissioned.
- [X] CAN-01: Frontend tests assert that the Canvas element mounts successfully and triggers repaints on resize.
- [X] CAN-01: Verify that the Canvas backing store dimensions programmatically match `cssDimensions * window.devicePixelRatio`.
- [X] CAN-02: Assert redraws occur on movement, rotation, line-clears, locking, restart, and resize.
- [X] CAN-02: Confirm that persistent solo scoring finalizations survive.

---

### Milestone 3: Two-Player Real-Time Duel over WebSockets [NET-01, NET-02, NET-03]
To verify same-seed piece sequences, start gating, WebSocket origin handshakes, seat ownership, draw update logic, room cleanup, and reverse-proxy integrity:

```bash
# Run backend duel room unit and integration tests
pytest tests/unit/test_duel_manager.py -v
pytest tests/integration/test_api_ws.py -v
```

**What to Check in the Log Outputs**:
- [X] NET-01: Handshake strictly validates the `Origin` header, returning `403 Forbidden` on unauthorized upgrade requests.
- [X] NET-01: Room join routes deterministically; unknown or finished room IDs fail connection with custom code `4004`, full room fails with `4001`, omitted ID creates a fresh room.
- [X] NET-02: Game stays in `waiting` state until two separate sockets connect, then starts simultaneously with identical seed sequences.
- [X] NET-02: Actions targeting the opponent's seat are rejected.
- [X] NET-02: Monotonic sequence deduplication and generation-level stale rejection are enforced. State updates include sequence correlation fields (`last_action_seat`, `last_action_seq`, `last_action_observable_change`).
- [X] NET-02: Bounded 1KB payload enforcement disconnects oversized payloads.
- [X] NET-03: Double-gravity DRAW tie evaluation logic is checked (if both seats top out in the same server gravity update tick).
- [X] NET-03: Disconnect immediately forfeits, awarding the win to the surviving player.
- [X] NET-03: Timed garbage collection frees room states and cancels gravity event loops after 5 minutes of inactivity.

---

## 4. Browser Performance Benchmark Protocol [PERF-01]

To capture performance and frame scheduling statistics, execute the Playwright scenario runner:

```bash
# Execute the performance benchmark script
node node_modules/tsx/dist/cli.mjs tests/performance-benchmark.ts --channel chrome --base-url http://127.0.0.1:5513 --output benchmark-output --runs 3 --warmup-seconds 5 --measure-seconds 30

# Or execute a fast smoke scenario check
node node_modules/tsx/dist/cli.mjs tests/performance-benchmark.ts --channel chrome --base-url http://127.0.0.1:5513 --smoke --output docs/runtime/native17-smoke
```

### Protocol Guidelines:
1. **Target**: Visible production Chromium window sized at `1280x900` with device scale factor `1`.
2. **Procedure**: Employs a frozen piece seed across a six-trial protocol (3 solo, 3 duel) with configurable warmups (default 5 seconds) and active runs (default 30 seconds).
3. **CLI Options**:
   - `--base-url <url>`: Host URL of the target application (default: `http://127.0.0.1:5513`).
   - `--output <dir>`: Directory where reports, screenshots, and traces are saved (default: `benchmark-output`).
   - `--runs <num>`: Number of trials per scenario (default: `3`).
   - `--warmup-seconds <num>`: Warmup period duration in seconds (default: `5`).
   - `--measure-seconds <num>`: Active measurement duration in seconds (default: `30`).
   - `--smoke`: Run in smoke validation mode with a single quick run (2s warmup, 3s measurement) to verify the instrument.
   - `--channel <name>`: Specify the browser channel to launch via Playwright (default: `chrome`). No silent fallback is employed.
   - `--foreground-gate`: Optional boolean switch (default off). Enables the file-system handshake to verify real OS-level foreground focus before warmup/game setup starts.
   - `--foreground-gate-timeout-seconds <num>`: Bounded timeout in seconds for the foreground approved handshake (default: `120`).
4. **Constraint**: Both duel clients are run in visible, isolated browser contexts to ensure accurate scheduler performance.
5. **Telemetry & Calibration**:
   - Tracker injection uses an IIFE to ensure correct initialization.
   - Measures raw scheduler intervals (`requestAnimationFrame` delta endpoints filtered to measurement bounds), candidate `fillRect` Canvas 2D calls, action-to-visible-update latency, and remote action-to-opponent-visible latency.
   - Canvas pixel validation uses Euclidean distance classification with a maximum distance tolerance of 30 and an empty-cell source-derived color of `[19, 19, 23]` to account for alpha overlay blending.
   - Saves raw timestamps, calibration probe clock offsets, window bounds, visibility events, and full logs in partial runs.
6. **Capture**: Collects frame-scheduling intervals, local action-to-repaint latency, and opponent-visible latency by binding canvas image state hashes and sequence/board state attributes.
7. **Report**: Outputs a structured `performance-report.json` with median, p95, and p99 distributions. Scheduling-only targets (mean rate >= 55 FPS, p95 interval <= 25 ms) are reported, and any unavailable measures are recorded as "unavailable".

---

## 5. Headed Launch Correction & Failure Row Retention

To address potential Chromium launch failures and ensure robust telemetry collection, the Playwright performance benchmark includes targeted corrections:
- **Browser Channel Configuration**: Passes the requested browser channel (e.g. `chrome`) to all three Playwright chromium launch calls (Solo, Duel Client A, and Duel Client B).
- **Solo Headed Settings**: Applies specific window position (`0,0`) and size (`1280,900`) parameters directly during solo headed launch to match reported telemetry claims.
- - **Robust Failure Retention**: Employs a Node-side launch wrapper (`safeLaunch`) to capture and record browser launch failures as empty telemetry rows in `runsReport`, preserving the execution record and failing gracefully before rethrowing to the suite handler. If Duel Client B launch fails, any already-opened Client A browser is closed cleanly.

---

## 6. Final Native Documentary Closure and Quality Gate Metrics

This section documents the verified performance execution results, audited dependencies, and SonarQube quality findings for the final closure of Stage 4 Option A (feature004).

### 6.1 Performance Benchmark Verification
- **Test Environment**:
  - **Browser**: Chrome 156.0.8078.80 headed
  - **Viewport**: 1280x900, Device Pixel Ratio (DPR) 1
  - **Execution Protocol**: 6 total trials (3 solo, 3 duel), 5s warmup + 30s fixed window each. 180 scenario seconds total / 270 client-run seconds.
  - **Total Native Execution Time**: 294.219s including manual gate wait delays.
  - **Active OS Foreground Window Samples**: 1,650 samples captured inside active windows.
- **Key Findings & Metrics**:
  - **Frame Scheduling Rate**: 164.67 to 164.93 scheduling events/s (Exceeds target >= 55 events/s).
  - **Scheduling Interval Performance**: p95 interval of approximately 6.2ms (Within target <= 25ms).
  - **Captured Latency Samples**:
    - *Solo Local Repaints*: 75 valid samples
    - *Duel Local Repaints*: 62 valid samples
    - *Duel Remote Latency*: 61 valid samples
  - **Receipt Path**: `docs/gate-performance-verified.json`

### 6.2 Dependency Audit Reconciliation
- **Audit File**: `docs/audit-inputs/final-reconciliation-21-01/report.json`
- **Total Audited Dependencies**: 49 selected packages
- **Audit Metrics**: 48 aggregate rows plus direct packaging 26.3 query.
- **Security Vulnerabilities**: 0 known advisories. No universal vulnerability-free claim is asserted.

### 6.3 SonarQube Code Quality & Coverage Metrics
- **Analysis Execution ID**: `35f7531d-2a56-4a33-bd38-2934eacc1ffc`
- **Computation Status**: SUCCESS
- **Quality Gate Status**: **ERROR** (Failed)
- **Quality Gate Metric Breakdown**:
  - **New Coverage**: **50.9%** (Failed; Threshold: < 80%)
  - **New Violations/Issues**: **40** (Failed; Threshold: > 0)
  - **New Duplicated Lines Density**: **2.83358%** (Passed; Threshold: <= 3%)
- **Global Analysis Metrics**:
  - **Global Code Coverage**: 65.1%
  - **Global Duplicated Line Density**: 4.2%
  - **Complexity**: 516
  - **Cognitive Complexity**: 554
  - **Code Smells**: 38
  - **Bugs**: 1
  - **Vulnerabilities**: 1
  - **Security Hotspots**: 0
- **Interpretation & Closure Statement**:
  Static analysis computation was completed successfully, but the dedicated study Quality Gate status is marked as **ERROR** due to new coverage of 50.9% (below the 80% threshold) and 40 new violations. No production source fixes or gate tuning are authorized in this phase; hence, the experimental execution is closed with measured quality limitations.
