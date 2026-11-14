---
title: 'Stage 3 Tetris Study (Option A)'
type: 'feature'
created: '2026-11-02'
status: 'completed'
baseline_commit: 'NO_VCS'
route: 'oneshot'
review_loop_iteration: 0
followup_review_recommended: false
context: [
  "_bmad-output/stage3/planning-artifacts/prds/prd-stage3-option-a/prd.md",
  "_bmad-output/stage3/planning-artifacts/prds/prd-stage3-option-a/addendum.md",
  "_bmad-output/stage3/planning-artifacts/architecture/stage3-option-a/ARCHITECTURE-SPINE.md",
  "_bmad-output/stage3/epics.md",
  "_bmad-output/stage3/implementation-artifacts/sprint-status.yaml",
  "_bmad-output/stage3/implementation-artifacts/validation-final-stage3.md"
]
warnings: []
deferred: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The existing Tetris prototype lacks high score persistence, containerization, an automated performance benchmark, and a continuous integration pipeline, which are required to complete the Stage 3 (Option A) research goals.

**Approach:** Implement persistent high scores using Python's standard `sqlite3` module at `TETRIS_DB_PATH` (defaulting to `./data/high-scores.sqlite3`), protecting mutations and finalizations with a process-wide `threading.RLock`. Enforce strict payload body validations, controlled 503 error responses, and retriable terminal persistence. Create a React High Scores sidebar panel with distinct loading, empty, and error states, and configure dynamic same-origin relative `/api` routing. Securely package the backend and frontend into multi-stage non-root Docker images and coordinate them via Docker Compose. Write an executable Playwright Chromium performance benchmark to measure frame intervals, and write a pinned GitHub Actions CI workflow with audits.

</frozen-after-approval>

## Implementation Notes

- **CORS Config Correction**: Modified `backend/app/main.py` to prevent wildcard `*` from being used with `allow_credentials=True`. If `CORS_ALLOWED_ORIGINS` is `*`, `allow_credentials` is set to `False`. For multiple values, any wildcard `*` is filtered out while explicit origins retain `allow_credentials=True`.
- **Test DB & Sonar Remediation**: Updated `backend/app/tests/test_stage3_features.py` to use pytest `tmp_path` and `monkeypatch` instead of physical SQLite files or manual global overrides. Refactored the concurrent worker exception handler to reraise `AssertionError` to prevent hiding assertion failures (remediating Sonar S5779 and S8997). Removed useless `yield` in `test_stage3_features.py` setup fixture to satisfy Sonar S9100.
- **Frontend High Scores Panel & Stale Ranking Protection**: Implemented a React component inside `App.tsx` managing loading, empty, and error states. Protected leaderboard fetches from race conditions or late-arriving responses via `scoresRequestIdRef` request-ownership and mount-ownership tracking. Added a frontend regression test inside `App.test.tsx` checking that out-of-order response delays are handled, while keeping all original assertions.
- **Docker Compose & Multi-stage Packaging**: Set up multi-stage non-root Docker configurations for frontend (unprivileged Nginx, custom configuration) and backend (FastAPI on internal port 8000, 1 worker, writable volume) with a named volume `tetris-stage3-bmad-db` bound to backend storage, healthchecks, and internal routing. Excluded `app/tests`, caches, data, credentials, and dependency folders in both context `.dockerignore` files.
- **Python Exact-pinned Lockfiles**: Created `backend/requirements-prod.lock` and `backend/requirements-dev.lock` for fully exact-pinned Python 3.12 reproducible dependency locks. Docker context uses `requirements-prod.lock` to construct production images securely.
- **CI GHA Workflow with Audits**: Established `.github/workflows/ci.yml` targeting Node 24 and Python 3.12. It installs the native frozen dev lock for backend tests/coverage, executes unmasked real `pip-audit` checks, executes unmasked frontend `npm audit`, runs unit tests with full code coverage (explicitly tracking `main.tsx`), and performs Docker image build verification.
- **Robust Playwright Performance Benchmark**: Replaced the incomplete benchmark script under `frontend/benchmark.js` with a fully compliant Playwright Chromium protocol. Runs 3 independent headed trials, exercises deterministic gameplay inputs, executes warmup/measurement windows, collects in-page rAF timings, domestic `.board` mutation updates, per-action signature updates and transition latency, API RTT metrics, and saves results under a new immutable timestamped run folder.

## Addendum for Corrective Verification

We address concrete findings from execution 08 with the following actions:
1. **Frontend Package Lock**: Regenerate `frontend/package-lock.json` using Node 24/npm 11 to include `playwright@1.64.1` and `playwright-core@1.64.1` correctly, ensuring clean CI installation.
2. **Backend Locks**: Complete exact coherent `requirements-prod.lock` and `requirements-dev.lock` to include resolved transitive packages: `annotated-types0.0.5` (or specified transitive inventory like `annotated-doc0.0.5` and `typing-inspection0.4.4` for prod, plus `colorama0.4.6`, `pyparsing3.3.3`, `sortedcontainers2.4.0` for dev), and update README/Docker/CI to match.
3. **Vulnerability Remediation**: Resolve the `certifi` vulnerability (PYSEC-2026-4320/GHSA-6q48-6c7w-9gw2) by upgrading and pinning `certifi` to `2026.10.19` (or latest secure version) in locks, ensuring zero vulnerability findings without any ignore/mask filters.
4. **Benchmark Verification Protocol**: Enhance `frontend/benchmark.js` to enforce explicit Chromium sandbox support, precise locators (`Start Session`), gameplay initiation prior to 5-second warmup, unified performance.now timeline tracking for rAF pairs, request mapping via request IDs (avoiding clock mismatch with page Clock), full 200-cell board class checking, visibility/focus validation, and graceful exception-handling results persistence.
5. **Detailed Resolution of Benchmark Defects**: Correct the following remaining 6 static defects:
   - *Fixed bounds calibration*: Set declared page clock bounds `warmupEnd = warmupStart + 5000`, `measureStart = warmupEnd`, `measureEnd = measureStart + 30000` once during setup. Never replace declared bounds with observed stop/overshoot timestamps. Calculate approximate FPS with denominator exactly equal to `30000` ms. End action loop when page clock hits declared `measureEndPage`. Stop all active observers (rAF, DOM observers, focus samplers) prior to capturing the final screenshot.
   - *Playing status detection*: Prior to declared `warmupStart`, wait explicitly for actual gameplay initiation (the `.status-playing` element or authoritative playing response after clicking `Start Session`). Handle game restarts in warmup seamlessly using correct status/restart timestamps.
   - *DOM updates & MutationObserver dataset*: Collect raw mutation callback details `{timestamp, mutationCount, fullsignature}` upon each invocation, keeping true board state transitions separate. Compute final measured DOM count as the sum of raw mutation counts within the `[measureStart, measureEnd]` interval.
   - *Action latency filtration*: Restrict action latency metrics to actions and corresponding visible updates occurring entirely inside `[measureStart, measureEnd]`. Track candidates via unique action IDs, safely marking same-direction requests that are heuristically overlapping (e.g. from gravity) as ambiguous, excluding them from successful metrics, and ensuring successful samples have API status 200. Document causality limits.
   - *Focus and visibility snapshots*: Persist precise, timestamped focus/visibility state snapshots at initialization, warmup start, measure start, and stop, plus periodic and event-driven samples. Fail if the browser is blurred or hidden during measurement. Log full runtime environment details (`launch_configuration`, exact Playwright versions read from installed packages, OS, hardware, etc.).
   - *Graceful exception handling & telemetry recovery*: Fully capture and save all available page arrays, errors, traces, and screenshots to the raw results files *before* throwing validation exceptions or closing the browser/context, ensuring telemetry is not lost.
   - *Telemetry & focus snapshots calibration (Run 09)*: Ensure `benchmarkData.raw_mutations` is stored as `raw_mutations` in both successful and failed trial raw JSON results to ensure auditability of DOM counts. Transition all 4 focus snapshots (`init`, `warmupStart`, `measureStart`, and `stop`) to use a unified `page.evaluate` returning precise page clock timestamp, focus status, and visibility state rather than using backdated timestamps or multiple separate evaluate statements. Update any misleading board cell count comments from 400 cells to 200 cells/400 characters.

## Visual Qualification & Keyboard Scroll Correction (Run 11 Rejection Resolution)

- **Previous Raw Run Rejection**: Although previous performance runs recorded successful FPS and low latency, visual inspection of the final 1280x900 PNG screenshot revealed that the top of the `.board` was slightly clipped, and the `ArrowDown` key triggered default document scrolling in the browser.
- **Narrow Keyboard Event Fix**: The keyboard event listener in `frontend/src/App.tsx` has been corrected so that during an active playing game, recognized keys (`ArrowLeft`, `ArrowRight`, `ArrowDown`) call `e.preventDefault()` immediately at the very beginning of the handler, prior to any return guards or queue checks. Unrelated keys and non-playing states remain untouched and do not call `e.preventDefault()`.
- **Benchmark Viewport Calibration**: The benchmark suite in `frontend/benchmark.js` is updated to scroll the `.board` into the viewport automatically if needed after starting the game and before declaring the warmup start, validating that its bounding rect is completely within the 1280x900 viewport. It records bounds, viewport, scroll, and focus states, samples geometry periodically, and aborts with a failed raw payload if the board leaves the visible viewport.

## SonarQube Analysis Remediation (typescript:S6582 Rule)

- **SonarQube Finding S6582**: Prefer optional chain (`?.`) over explicit binary logic checks. Specifically, in `frontend/src/App.tsx` at line 330: `currentGame && currentGame.status === "playing"` should be written as `currentGame?.status === "playing"`.
- **Refactoring Applied**: Modified the `isPlaying` declaration inside the `handleKeyDown` listener of `frontend/src/App.tsx` to use optional chaining, preserving the logic and ensuring full compatibility with existing tests and behavior.

## Verification

**Commands:**
- `python -m pytest` -- expected: all backend unit and integration tests pass
- `npm run test` -- expected: all frontend vitest tests pass
- `npm run build` -- expected: frontend production build completes successfully
- `npx vitest run --coverage` -- expected: frontend coverage includes `main.tsx` and all source elements
- `pip-audit -r backend/requirements-dev.lock` -- expected: zero python dependency vulnerabilities
- `npm audit` -- expected: zero high-severity frontend vulnerabilities
- `node benchmark.js` -- expected: performance benchmark completes gracefully (headed browser, 30s trials)

**Audit Report:**
- Detailed verification results, Docker image metrics, SonarQube quality gate statuses, and performance benchmark observations are recorded in [validation-final-stage3.md](./validation-final-stage3.md).
