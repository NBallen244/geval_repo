# Implementation Plan: Tetris Stage 4 Option A

## Overview

This plan turns the corrected, not-yet-approved Stage 4 design (a researcher review rejected the prior planning attempt; this plan reflects the corrections and awaits a new review before any M1 code) into an incremental, test-driven set of coding tasks for the brownfield extension of the existing Stage 3 backend (`backend/app`, Python + FastAPI) and frontend (`frontend/src`, React + TypeScript). The work is ordered by the three milestones defined in the design: **M1 (server-side rotation)**, then **M2 (Canvas board rendering)**, then **M3 (WebSocket duel)**. Each milestone layers on top of the inherited structure without disturbing it, and each ends with a coverage check framed as a check to run (never a claimed result).

M1 adds the pure `Rotation_Engine` (`app/rules/rotation.py`), the `orientation` field on `ActivePiece`, the pure `engine.rotate`, the `POST /api/games/{id}/rotate` route, and the single-player rotation controls, routed through the inherited generation / FIFO / stale-response machinery. M2 replaces the DOM cell grid (`Board.tsx`) with `CanvasBoard.tsx` while preserving the accessible DOM controls, panels, and status region, the solo HTTP contract, SQLite persistence, and the leaderboard. M3 adds the in-memory duel (`app/ws/contract.py`, `app/ws/duel.py`, `app/duel/rooms.py`, `app/duel/gravity.py`) over same-origin WebSockets on the same single worker, kept fully separate from the solo HTTP stores and the solo SQLite leaderboard, plus the isolated Stage 4 Docker/Compose/CI, the benchmark design extension, the process guardrail, and honest documentation.

The inherited specs under `.kiro/specs/tetris-stage1-option-a/`, `.kiro/specs/tetris-stage2-option-a/`, and `.kiro/specs/tetris-stage3-option-a/` are never edited. Each task references the file(s) from the design and the requirement clauses it satisfies. Test-authoring sub-tasks sit next to or before the code they verify; property-based test sub-tasks reference the design's numbered Correctness Properties. Every task is left unchecked; no command is executed as part of this planning phase, and no coverage, container, CI, or benchmark result is claimed.

## Tasks

<!-- =====================  MILESTONE M1: ROTATION  ===================== -->

- [x] 1. Add orientation state to the active piece (M1)
  - [x] 1.1 Add `orientation` to `ActivePiece` and reset it on every entry path
    - Add `orientation: int = 0` to the `ActivePiece` dataclass in `backend/app/domain/models.py`; keep the serialized `type`/`origin`/`cells` shape unchanged so `GameStateOut` and inherited tests are unaffected (`orientation` is internal engine state, not a new serialized key)
    - In `backend/app/rules/engine.py`, set `orientation = 0` in `_place` for every entry path: the queue-spawn path and BOTH Hold paths (first-Hold and swap-Hold), so a piece always enters play at orientation `0` at `SPAWN_ORIGIN` regardless of the orientation it held before
    - Keep the inherited once-per-active-piece `can_hold` rule unchanged
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 2. Implement the pure rotation engine (M1)
  - [x] 2.1 Create `backend/app/rules/rotation.py` with the orientation tables and helpers
    - Create the pure module importing only typing and the domain/pieces modules (no FastAPI, no `sqlite3`, no new third-party dependency)
    - Declare `KICK_OFFSETS = [0, -1, 1, -2, 2]` (column-only candidate order) and the `RotationDirection = Literal["cw", "ccw"]` alias
    - Declare `ORIENTATIONS[type][orientation_index]` as four `(row, col)` offset lists per piece anchored to `spawn0`, where orientation `0` equals `pieces.SHAPES[type]`; every piece's four orientations are rigid 90-degree quarter-turns about ONE declared fixed pivot POINT (I = (1.5, 1.5); O = (0.5, 0.5); T/S/Z/J/L = (1, 1)); the `I` table about the fixed pivot (1.5, 1.5) is exactly orientation 0 `[(0,0),(0,1),(0,2),(0,3)]` (spawn0 row 0), orientation 1 `[(0,3),(1,3),(2,3),(3,3)]`, orientation 2 `[(3,0),(3,1),(3,2),(3,3)]`, orientation 3 `[(0,0),(1,0),(2,0),(3,0)]`, never an SRS table that assumes the `I` spawns on row 1; the `O` piece is a FULL no-op (same four offsets across all indices AND the orientation index itself is left unchanged by `engine.rotate`)
    - Implement `cells_for(piece_type, orientation, origin)` returning exactly four distinct absolute cells, and `next_orientation(orientation, direction)` returning `(o + 1) mod 4` for `cw` and `(o - 1) mod 4` for `ccw`
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 2.6, 2.8, 1.1, 1.2_
  - [x] 2.2 Add the pure `engine.rotate(game, direction)` wall-kick search in `backend/app/rules/engine.py`
    - No-op and return unchanged when `game.status != "playing"` or `game.active is None`; `engine.rotate` ALSO returns immediately when `game.active.type == "O"` (a full no-op: orientation index and cells unchanged), in addition to the not-playing / no-active guards
    - Compute the target orientation via `rotation.next_orientation`, then evaluate `rotation.KICK_OFFSETS` in the exact order `0, -1, +1, -2, +2`, applying a COLUMN-only offset to the rotated origin and testing each candidate with the inherited `_is_valid` (bounds `0..19`/`0..9` plus no locked-cell overlap)
    - On the first fitting candidate, set `active.orientation`, `active.origin`, and `active.cells` and return; evaluate no later candidate once one is accepted
    - On a fully rejected rotation (no candidate fits), return before mutating anything; never call `lock`, `tick`, or the generator, and never touch `score`, `level`, `total_lines`, `next_type`, `hold_type`, `can_hold`, `gravity_interval_ms`, `board`, or `status`
    - _Requirements: 1.1, 1.2, 1.8, 1.9, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 7.1, 7.2, 7.3, 7.4_
  - [x] 2.3 Write independent-oracle rotation table unit tests in a NEW backend test module `backend/tests/test_stage4_rotation.py`
    - Declare the expected per-piece per-orientation occupied-cell tables INDEPENDENTLY in the test (not imported from `rotation.ORIENTATIONS`) and assert `rotation.cells_for` matches them for every `(type, orientation 0..3)` at a representative origin
    - Assert the `O` rotation is a no-op in both directions and that the `I` piece uses the corrected fixed-pivot (1.5,1.5) row-0 spawn geometry across all four orientations; the independently-declared expected table for the `I` piece must match orientation 1 `[(0,3),(1,3),(2,3),(3,3)]`, orientation 2 `[(3,0),(3,1),(3,2),(3,3)]`, and orientation 3 `[(0,0),(1,0),(2,0),(3,0)]`
    - _Requirements: 9.1, 9.2, 9.3, 2.3, 2.4, 2.5, 2.7_
  - [x] 2.4 Write hypothesis property tests for Properties 1-4 in `backend/tests/test_stage4_rotation_properties.py`
    - **Property 1: CW/CCW four-cycle identity** — tag `# Feature: tetris-stage4-option-a, Property 1`, run at least 100 iterations; **Validates: Requirements 2.3, 9.2**
    - **Property 2: CW then CCW is the identity** — tag `# Feature: tetris-stage4-option-a, Property 2`, run at least 100 iterations; **Validates: Requirements 2.7**
    - **Property 3: `O` rotation is a no-op** — tag `# Feature: tetris-stage4-option-a, Property 3`, run at least 100 iterations; **Validates: Requirements 2.4**
    - **Property 4: Every orientation has exactly four distinct cells** — tag `# Feature: tetris-stage4-option-a, Property 4`, run at least 100 iterations; **Validates: Requirements 2.1, 2.5, 2.6**
    - _Requirements: 2.1, 2.3, 2.4, 2.5, 2.6, 2.7, 9.2_
  - [x] 2.5 Write hypothesis property tests for Properties 5-9 in `backend/tests/test_stage4_rotation_properties.py`
    - **Property 5: Rejected rotation is fully immutable** — tag `# Feature: tetris-stage4-option-a, Property 5`, run at least 100 iterations; **Validates: Requirements 3.5, 4.1, 4.2, 4.3, 4.4, 4.5**
    - **Property 6: Accepted rotation changes only orientation and (on a kick) origin** — tag `# Feature: tetris-stage4-option-a, Property 6`, run at least 100 iterations; **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
    - **Property 7: Wall-kick first-fit in the exact order** — tag `# Feature: tetris-stage4-option-a, Property 7`, run at least 100 iterations; **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.6**
    - **Property 8: Spawn and Hold reset orientation to 0** — tag `# Feature: tetris-stage4-option-a, Property 8`, run at least 100 iterations; **Validates: Requirements 6.1, 6.2, 6.3, 6.4**
    - **Property 9: Lock preserves rotated geometry** — tag `# Feature: tetris-stage4-option-a, Property 9`, run at least 100 iterations; **Validates: Requirements 7.1, 7.2, 7.3**
    - _Requirements: 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3_
  - [x] 2.6 Write deterministic kick/reject/O/I fixture tests in `backend/tests/test_stage4_rotation.py`
    - Cover a left-wall kick, a right-wall kick, a floor kick, and a locked-cell kick, including a case where the first fitting candidate in `0, -1, +1, -2, +2` is selected over a later fitting candidate
    - Cover a fully rejected rotation asserting that the origin, orientation index, `gravity_interval_ms`, `score`, `level`, `total_lines`, `next_piece`, `hold_piece`, and `can_hold` are each unchanged
    - _Requirements: 9.4, 9.5, 3.1, 3.2, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 3. Expose the rotation API surface (M1)
  - [x] 3.1 Add `RotateRequest` in `backend/app/api/schemas.py`
    - Add `RotateRequest` with `model_config = ConfigDict(extra="forbid")` and `direction: Literal["cw", "ccw"]` (exactly the two documented case-sensitive values)
    - Keep `GameStateOut` unchanged so the rotate response reuses the eleven inherited keys
    - _Requirements: 1.5, 1.6_
  - [x] 3.2 Add `POST /api/games/{id}/rotate` in `backend/app/api/games.py`
    - Add the route reusing the existing single-lock `_mutate` helper so it acquires `finalization._LOCK` once, calls `_get_or_404`, runs `engine.rotate(g, body.direction)`, and serializes under the lock
    - Return HTTP 200 with the exact eleven-key `GameStateOut` shape on success; 404 for an unknown id; 422 for a malformed body (missing/extra field, non-string or undocumented `direction`); leave the `game_over` and no-active cases as unchanged no-ops returning the current state; keep the inherited 503 pending-finalization behavior unchanged (rotation adds no new 503 condition)
    - Keep all rotation-related labels, statuses, and messages in English
    - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10_
  - [x] 3.3 Write rotation API integration tests in `backend/tests/test_stage4_api.py`
    - Assert HTTP 200 and the exact eleven-key `GameStateOut` shape on an accepted rotation
    - Assert a rotation against a `game_over` game and against a game whose `active_piece` is absent change no authoritative state field
    - Assert HTTP 422 for a missing-direction payload, a non-string-direction payload, and an extra-field payload, and HTTP 404 for an unknown game id, each leaving authoritative state unchanged
    - _Requirements: 1.3, 1.4, 1.6, 1.7, 1.8, 1.9, 9.6, 9.7_

- [x] 4. Add single-player rotation controls to the frontend (M1)
  - [x] 4.1 Add `rotateGame` in `frontend/src/api.ts`
    - Add `rotateGame(id, direction: "cw" | "ccw")` that `POST`s `{ direction }` to `${API_BASE}/games/{id}/rotate`, mirroring `moveGame` and throwing on non-ok responses
    - _Requirements: 1.5, 8.5_
  - [x] 4.2 Add the `rotate` callback in `frontend/src/useGame.ts`
    - Add a `rotate(direction)` callback built exactly like `move`: capture the current generation, no-op when `idRef.current` is null, call `cancelTick()` at dispatch time, and enqueue onto the inherited per-generation FIFO via `enqueue`, so a stale rotation response is discarded when its generation no longer matches and the automatic-tick scheduler is never cleared, blocked, or rescheduled outside the inherited reconciliation; introduce no new machinery
    - _Requirements: 8.5, 8.7_
  - [x] 4.3 Bind keyboard and on-screen rotation controls in `frontend/src/App.tsx`
    - Bind `ArrowUp` to one `rotate("cw")` per key-down and `Z`/`z` to one `rotate("ccw")` per key-down; add two accessible on-screen buttons (one CW, one CCW, each a real focusable `<button>` with an English accessible name) issuing one corresponding rotation per activation
    - Gate every rotation entry point on `state.status === "playing"` so none fires when the game is not playing; keep the inherited left/right/soft-drop/Hold/restart controls unchanged
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.6, 8.7_
  - [x] 4.4 Write real-event frontend rotation tests in `frontend/src/App.rotation.test.tsx`
    - Fire a real `ArrowUp` key event, a real `Z` key event, and activate each on-screen rotation control, asserting exactly one rotation request per event/activation routed through the FIFO and bound to the current generation
    - Assert no rotation request is issued from any entry point when the status is not `playing`, and that rotation is never asserted solely through internal function calls
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.6, 9.8_

- [x] 5. Checkpoint - M1 rotation
  - Ensure all backend and frontend rotation tests pass, ask the user if questions arise.

- [x] 6. M1 coverage check (check to run; left unchecked)
  - [x] 6.1 Run and record the M1 coverage and quality checks
    - During a later implementation invocation, produce the backend coverage report in XML and the frontend coverage report in LCOV, exercising the rotation and error branches rather than only the happy path
    - Evaluate the independent Sonar analysis so that NEW-code coverage `>= 80%`, code duplication `<= 3%`, and `0` new static-analysis findings are each a SEPARATE outcome; do not weaken thresholds, add production-code coverage exclusions, or reset the baseline, and do not treat passing coverage as proof the overall gate passed
    - Report actual findings honestly; fabricate no coverage, duplication, or static-analysis numbers
    - _Requirements: 24.2, 24.3, 24.4, 24.5, 24.6_

<!-- =====================  MILESTONE M2: CANVAS  ===================== -->

- [x] 7. Build the Canvas board component (M2)
  - [x] 7.1 Create `frontend/src/CanvasBoard.tsx` replacing the DOM cell grid
    - Create a React + TypeScript `CanvasBoard({ state })` component that draws the authoritative board on a Canvas 2D surface and never renders the main board as a grid of per-cell React DOM elements
    - Preserve the inherited per-type colors (`COLORS`/`TYPE_CODE` from `Board.tsx`) as the Canvas palette; draw exactly the 200 settled cells (board code `0` empty, `1..7` -> type color) and overlay the active piece's rotated occupied cells (`state.active_piece.cells` at its current origin) in its type color so active and settled blocks are visually distinguishable
    - On each draw, reset the transform and `clearRect` the whole backing store so no residual pixels from a prior state survive
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 11.6_
  - [x] 7.2 Implement redraw triggers and device-pixel-ratio sizing in `frontend/src/CanvasBoard.tsx`
    - Redraw in a `useEffect` keyed on the authoritative `state` so a rotate, move, tick, lock, line clear, and restart each trigger exactly one redraw from the new state
    - Observe the canvas layout box with a `ResizeObserver`; when the measured pixel width or height changes from its previous value, recompute the backing-store size as `cssWidth * devicePixelRatio` by `cssHeight * devicePixelRatio`, scale the context by `devicePixelRatio`, and redraw so the full 10x20 board renders within the layout box without stretching or clipping at DPR `1` and DPR `2`
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  - [x] 7.3 Write native unit fixtures for the Canvas renderer in `frontend/src/CanvasBoard.test.tsx`
    - Verify renderer draw calls, 2D-context setup/cleanup, and safe behavior when the 2D context is absent, as behavioral coverage only
    - Explicitly document in the test module that these draw-call records and any DOM data attributes are NOT pixel evidence
    - _Requirements: 14.1, 14.2_

- [~] 8. Wire the Canvas board into the application (M2)
  - [x] 8.1 Replace the DOM board with `CanvasBoard` and preserve accessible DOM in `frontend/src/App.tsx`
    - Render `<CanvasBoard state={state} />` in place of the `Board.tsx` cell grid; keep accessible DOM controls for left, right, soft drop, CW rotation, CCW rotation, Hold, and restart, and accessible DOM elements for score, level, line count, Hold piece, next-piece preview (`Preview.tsx`), leaderboard/ranking (`HighScores.tsx`), and game status
    - Provide an accessible text/status region exposing the game status (`playing`/`game_over`) so status never depends solely on Canvas pixels; keep the inherited per-generation FIFO serialization and stale-response protection unchanged
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  - [x] 8.2 Preserve the solo contract, persistence, and leaderboard under the Canvas change
    - Confirm the Canvas is a rendering-only change: the solo HTTP contract (`POST /api/games`, `GET /api/games/{id}`, `/tick`, `/move`, `/hold`, and the rotate route), the SQLite persistence and once-only finalization, and `GET /api/high-scores` ordering/shape remain unchanged, with the backend the single authoritative owner and the Canvas rendering only backend-reported state
    - _Requirements: 13.1, 13.2, 13.3, 13.4_
  - [x] 8.3 Capture production-bundle pixel evidence and the isolated clear fixture
    - Capture actual rendered pixel masks or screenshots from the UNMODIFIED production bundle tied to a spawned piece, a rotated piece, a moved piece, a locked piece, and a cleared-line state; do not treat mock draw-call records or DOM data attributes as pixel evidence, and add no debug/injection/interception hooks to the production bundle
    - Drive the hard-to-reach multi-line-clear state through the production clear path with an explicitly-declared isolated fixture that is never claimed to be the production backend
    - ACCEPTED (bookkeeping, native `07-m2-acceptance-and-m3-contract-finalize`, 2026-11-06): consistent with the supplied EXTERNAL-researcher acceptance. A real Chrome 156.0.8078.81 independent run (`docs/validation/m2-pixels-03/report.json`) passed 348/348 checks: 66 Canvas RGBA masks, 66 composited PNG screenshots, 66 DPR backing-store dimension checks (200 cell centers each), and 142 HTTP 200 samples (53 against the actual host `5517`, 89 against a separate explicitly-declared own-engine fixture), covering a production natural lock/restart path and the declared 1-line and 2-line clear fixtures. These are SUPPLIED researcher facts, not native checks this tool personally re-ran.
    - PLACEMENT/ROLE EXCEPTION (documented, not worked around): the accepted functional pixel evidence lives in the researcher reports under `docs/validation/m2-pixels-03/report.json`, `docs/validation/m2-independent-02/report.json`, and `docs/final/docker/m2-native-02/report.json` - NOT in a newly generated `perf/` harness. No `perf/` pixel-harness files or results are fabricated; the Playwright-convention framing is satisfied by the researcher report corpus.
    - _Requirements: 14.3, 14.4, 14.6_
  - [x] 8.4 Document the superseded `Board.test.tsx` DOM-cell assertions and the layout check
    - In `frontend/src/Board.test.tsx` (or an accompanying note) document which inherited DOM-cell assertions are superseded by the Canvas migration and that their semantic coverage (correct per-type colors at correct board positions) is replaced by the Canvas pixel evidence from task 8.3
    - Add a `1280x900` layout check confirming the full 10x20 board is visible with no control/panel overlap, that the solo view is reachable, and that the layout does not require three boards to render simultaneously
    - _Requirements: 14.5, 15.1, 15.2, 15.3_

- [x] 9. Checkpoint - M2 canvas
  - Ensure all frontend Canvas and layout tests pass, ask the user if questions arise.
  - ACCEPTED (bookkeeping, native `07-m2-acceptance-and-m3-contract-finalize`, 2026-11-06): the M2 checkpoint is marked accepted consistent with the supplied EXTERNAL-researcher acceptance (`docs/validation/m2-acceptance-01/report.json`): independent 95/95 frontend test + build pass, a full LCOV module inventory pass, frontend-only Docker on host `5517` with matching source/image/HTTP assets (backend container/image/mounts unchanged), and the desktop `1280x900` DPR 1/2 layout at page height 900 with no overflow/overlap/clipping and the actual document title and h1 reading "Stage 4". Backend XML / 295 backend tests / locks / infra are explicitly REUSED from the unchanged accepted M1 (not re-run for M2). These are SUPPLIED researcher facts, not native checks re-run here. Resize-scope disclosure: the extra 240px probe (216x432 backing store) proves actual DPR resize but is CANVAS QUALIFICATION ONLY, not full mobile usability at 240px.

- [~] 10. M2 coverage check (run-and-recorded; COVERAGE accepted, ZERO-STATIC target FAILED, overall gate NOT passed)
  - [x] 10.1 Run and record the M2 coverage and quality checks
    - During a later implementation invocation, produce the backend XML and frontend LCOV coverage reports, exercising the Canvas rendering, resize, and API branches rather than only the happy path
    - Evaluate the independent Sonar analysis with NEW-code coverage `>= 80%`, duplication `<= 3%`, and `0` new static findings each as a SEPARATE outcome; do not weaken thresholds, add production-code exclusions, or reset the baseline
    - Report actual findings honestly; fabricate no numbers
    - RUN-AND-RECORDED (bookkeeping, native `07-m2-acceptance-and-m3-contract-finalize`, 2026-11-06): the supplied EXTERNAL-researcher Sonar analysis id `c4816b15-3816-4259-a45c-b4dec1e4ae14`, version 2.0 (fixed PREVIOUS_VERSION 1.0 baseline; all conditions actually evaluated; no import warnings; no changed source; no changed gate) reports NEW-code coverage 91.9%, global coverage 94.2%, NEW-code duplication 0%, overall gate ERROR, 16 NEW static-analysis CODE_SMELLS (21 total), bugs 0, vulnerabilities 0. The COVERAGE outcome is ACCEPTED (91.9% NEW >= 80%, 0% NEW duplication <= 3%); the ZERO-NEW-STATIC-FINDINGS target FAILED (16 > 0). Completing this run-and-record step does NOT mean its zero-static target passed; the overall M2 quality gate is NOT marked passed. Task 10 stays unchecked because the zero-static target and overall gate did not pass. These are SUPPLIED researcher facts, not a Sonar run this tool performed.
    - _Requirements: 24.2, 24.3, 24.4, 24.5, 24.6_

<!-- ------------------  M2 LAYOUT/RESIZE CORRECTION (2026-11-06)  ------------------ -->
<!--
NATIVE CORRECTION, dated 2026-11-06. Pre-correction + results note on disk at
`docs/native-checks/06-m2-layout-correction/NOTE.md` (written BEFORE any code
edit per the correction guardrail). An independent 1280x900 Chromium run (DPR 1
and 2) reported 10 FAIL among 338 checks; all backing-store masks, DPR
dimensions, API samples, moves/rotation/Hold/restart, palette, lock, and
isolated clears PASS and are preserved. The 10 FAIL were:
  A) 4x desktop page-bounds: document.scrollHeight 940 > 900 (playing + terminal,
     DPR 1 and 2). Root cause: root `min-height:100vh` under content-box + 12px
     padding + default 8px body margin + no CSS reset.
  B) 2x meaningful-resize: Canvas stayed 240x480 at every narrower viewport
     because App wrapped CanvasBoard in a FIXED width:240 box.
  C) 4x small-viewport PNG cropping: board x=-60 at 480px, x=-130 at 340px -
     non-wrapping fixed row pushed the board off-screen (colors were correct).
  D) stale <title>Tetris - Stage 2</title> while the h1 was correctly Stage 4.
Applied correction (own frontend only; no backend/lock/dep/infra/M3/benchmark):
  - NEW `frontend/src/index.css` reset (box-sizing:border-box all elements,
    margin:0 html/body), imported in `main.tsx` -> fixes A. Confirmed in the
    production bundle CSS.
  - `App.tsx` root box-sizing:border-box + width:100% (A); main row flex-wrap
    wrap + centered + max-width 920 (C); board wrapper changed from fixed
    width:240 to adaptive flex:1 1 240px / min-width:160 / max-width:320 so the
    canvas content-box width actually changes on resize (B). 10x20 geometry
    preserved by the existing canvas aspect-ratio; drawing/colors/DPR logic
    unchanged.
  - `index.html` title -> "Tetris - Stage 4" (D); confirmed in `dist/index.html`.
  - `App.layout.test.tsx` narrative updated to the real box-model + adaptive fix
    and correct number (940); jsdom honesty markers preserved; no faked
    scrollHeight, no relaxed/deleted assertion, no style-literal mirror.
Self-checks (this invocation, NOT a browser run): vitest 95/95 passed (14 files);
frontend LCOV unchanged scope/thresholds (Stmts 92.51% / Branch 80.2% /
Funcs 96.92% / Lines 96.09%); `npm run build` (tsc + vite) PASS. Backend and
browser pixel/API evidence are PRIOR, reused, not re-run here.
Acceptance (as written on 2026-11-06 during the layout correction): tasks 8.3 /
9 / 10.1 were recorded as NOT yet fully accepted pending independent researcher
re-confirmation of production pixels/layout and NEW coverage. The meaningful
targeted test-narrative regression preserves the existing 95 tests and the
one-real-event exact-call keyboard tests.
SUPERSEDED 2026-11-06 by native08-finish: the independent EXTERNAL-researcher M2
acceptance recorded in `docs/native-checks/07-m2-acceptance-and-m3-contract-finalize/NOTE.md`
HAS re-confirmed the production pixels/layout (real Chrome 156 run, 348/348 checks)
and NEW coverage (91.9% NEW >= 80%), so tasks 8.3 / 9 / 10.1 are ACCEPTED as recorded
on those tasks below. This paragraph is retained as history; it is NOT a current
"not accepted" claim. The ZERO-NEW-STATIC target remains FAILED (16 new findings)
and the overall M2 Sonar gate is NOT marked passed, recorded honestly on task 10.
-->
<!--
NATIVE M3 CONTRACT-CORRECTION FINISH, dated 2026-11-06. Pre-correction + results
note on disk at `docs/native-checks/08-m3-contract-correction-finish/NOTE.md`
(written BEFORE any schema/spec/corpus edit per the correction guardrail). This
resumed the transiently-failed native08 (exit 1, ~762s, ClientNetworkError /
TRANSIENT) and closed the five remaining M3 CONTRACT defects: (1) the `action_id`
FULL-STRING grammar (trailing `(?![\s\S])` replaces `$`, which wrongly accepted a
trailing LF/CR/CRLF/U+2028/U+2029); (2) synchronizing every LIVE normative block
(removed the obsolete `unknown_action_id` semantics and phantom correlation field
from design and tasks; reason enum now stale_revision/future_revision/not_seat_owner/
not_started/bad_type/missing_field/extra_field/rate_limited/oversize/
duplicate_action_conflict); (3) `StateFrame.room_status` made REQUIRED on every
state frame; (4) a schema-valid uncorrelatable-malformed path via the new
`ErrorFrame.reason = malformed_message` (no invented placeholder id); (5) literal
operational close-reason strings (`sequence_exhausted`, `scalar_overflow`,
`peer_unavailable_forfeit`, `waiting_room_timeout`, `idle_timeout`,
`handshake_timeout`, `server_shutdown`, `normal_completion`) and the forfeit-vs-
operational-abort distinction. This is SPEC/SCHEMA/CORPUS + self-validation ONLY;
NO M3/benchmark implementation was written; M3 implementation tasks (11-17 and the
M3-touching cross-cutting tasks) stay UNEXECUTED. Real local validation was run
with `docs/runtime/.venv` jsonschema 4.26.0 Draft202012Validator via
`docs/native-checks/08-m3-contract-correction-finish/validate_contract.py`; the
actual output is retained in that directory's `validate-run1.txt`.
-->

<!--
NATIVE M3 WIRE UTF-8 / TRANSPORT CLARIFICATION, dated 2026-11-06 (native09). Note on
disk at `docs/native-checks/09-m3-wire-utf8-transport-clarification/NOTE.md`, written
BEFORE any spec/schema/task/description edit per the guardrail. SPEC/CONTRACT-LAYER
CLARIFICATION + self-validation ONLY; NO application/test/infra/dependency/benchmark/
prototype code was created or modified, NO package installed, and NO wire field, enum
member, timeout, bound, pattern, required list, or example SEMANTIC was changed. The
narrow correction splits malformed-input handling into two layers: (a) an APPLICATION-
VISIBLE malformed JSON / uncorrelatable-or-wrong-typed `action_id` / in-band BINARY
frame keeps the existing `ErrorFrame(reason malformed_message)` path UNCHANGED; (b) a
WIRE-LEVEL invalid-UTF8 TEXT frame is rejected by the WebSocket transport BEFORE ASGI
and is failed with the standard close code 1007 (RFC 6455 §8.1 fail-the-connection /
§7.4.1), with a library-managed bounded reason and NO required application-controlled
JSON reply or exact reason string. A 1007 close in a STARTED room triggers the ordinary
disconnect/forfeit/once-only cleanup; a waiting-alone 1007 fabricates no winner. A later
PUBLIC test sends a raw masked TEXT byte 0xFF expecting 1007, DISTINCT from a browser
binary Uint8Array 0xFF (application-visible) case. IMPLEMENTATION CAVEAT: the locked
Pydantic 2.10.4 cannot compile the canonical `action_id` lookahead as its default
Rust-backed `Field.pattern` (expected SchemaError, lookaround unsupported - a
qualification observation, not an application failure); later code must enforce the
IDENTICAL full-string grammar with an equivalent explicit full-string validator and MUST
NOT weaken the canonical lookahead. M2 stays ACCEPTED with the disclosed static ERROR /
16 NEW findings (no false all-quality claim). M3 implementation tasks (11-17 and the
M3-touching cross-cutting tasks) stay UNEXECUTED. Real local validation was re-run with
`docs/runtime/.venv` jsonschema 4.26.0 Draft202012Validator via
`docs/native-checks/09-m3-wire-utf8-transport-clarification/validate_contract.py`; the
actual output is retained in that directory's `validate-run1.txt`.

MANDATORY GUARDRAIL (verbatim): "after ANY failed check, write a NEW dated native
spec/task note ON DISK describing that exact observed failure and intended correction
BEFORE editing code/tests/config/schema; chat narration/old broad note is insufficient.
If a child cannot write a note, return failure to the parent and STOP correcting until
the parent writes it. Preserve failed outputs. Historical 03 missed notes remain
disclosed; do not retrofit them or claim universal compliance. Never fix a flake by
repeated input or treat unchanged repeated passes as correction."
-->

<!-- =====================  MILESTONE M3: WEBSOCKET DUEL  ===================== -->

- [x] 11. Define the versioned duel wire contract (M3)
  - [x] 11.1 Create `backend/app/ws/contract.py` with the versioned Pydantic models
    - Create the `app/ws/` package and `contract.py`; define inbound models `Hello` and `ActionMessage` and outbound models `Welcome`, `StateFrame`, `Ack`, `Reject`, `ErrorFrame`, and `Outcome`, each with `model_config = ConfigDict(extra="forbid")`, an explicit integer `protocol_version` starting at `1`, and an enumerated `type` discriminator
    - Enumerate exactly the design's values: `ActionMessage.kind` in `{left, right, down, cw, ccw, hold}`; `Reject.reason` in `{stale_revision, future_revision, not_seat_owner, not_started, bad_type, missing_field, extra_field, rate_limited, oversize, duplicate_action_conflict}` (there is intentionally NO `unknown_action_id`; the uncorrelatable-malformed path uses `ErrorFrame.reason = malformed_message`); `ErrorFrame.reason` in `{room_not_found, room_full, room_closed, protocol_version_unsupported, handshake_timeout, malformed_message, internal}`; `Outcome.result` in `{win, draw, forfeit}`; `seat_id` in `{A, B}` (nullable only in `ErrorFrame`); `StateFrame.room_status` in `{waiting, playing, finished}` REQUIRED on every state frame
    - Make `StateFrame` board/active-piece/queue/Hold fields consistent with `GameStateOut` and the `TYPE_CODES` mapping (`board` 20x10 ints `0..7`, active piece `type`/`origin`/`cells`), plus the duel-only `seat_id` and non-negative `revision`; define every field's type, range, and nullability as in the design
    - The Pydantic models MUST conform to the canonical machine-readable JSON Schema at `.kiro/specs/tetris-stage4-option-a/contract/duel-wire.schema.json` (Draft 2020-12) and stay consistent with the separate examples corpus at `.kiro/specs/tetris-stage4-option-a/contract/duel-wire.examples.json`; use the concrete bounds and close codes declared in the design (room_id/action_id length 1..64, max_rooms 100, max_msg_bytes 4096, action_rate_per_seat 20/s, outbound_queue_depth 64, handshake_timeout 10s, idle_timeout 60s, finished_room_retention 15s, waiting_room_retention 120s; standard close codes 1000 normal / 1008 policy-or-origin / 1009 oversize / 1008+`rate_limited` for rate violation / 1001 going-away deliberately SHARED by idle timeout, handshake timeout, and server shutdown and disambiguated by reason semantics); split coordinates so `origin` is an anchor coord (row -4..19, col -3..9) and each occupied cell is an on-board coord (row 0..19, col 0..9) with `cells` holding exactly four DISTINCT cells; enforce the status/active_piece relationship (`playing` => non-null active piece, `game_over` => null) and the per-`result` outcome relationships (win = two distinct seats + null forfeiter; draw = all three null; forfeit = loser == forfeiter and winner the other seat); apply SAFE integer upper bounds (revision/expected_revision/score/total_lines/final_revision 0..9007199254740991, level 1..100000, gravity_interval_ms 100..500); enforce the canonical FULL-STRING `action_id` grammar `^(A|B)-([1-9][0-9]{0,14})(?![\s\S])` (the trailing negative lookahead replaces `$` so a trailing LF/CR/CRLF/U+2028/U+2029 is rejected) on `ActionMessage`/`Ack`/`Reject`, with the per-seat prefix==seat_id rule on `ActionMessage`; IMPLEMENTATION CAVEAT (native09 2026-11-06): the locked Pydantic 2.10.4 cannot compile this lookahead as its default Rust-backed `Field.pattern` (independent local qualification raised the EXPECTED `SchemaError`, lookaround unsupported - a qualification-tool observation, not an application failure), so the code MUST enforce the IDENTICAL full-string grammar with an equivalent explicit full-string validator (for example a Python `re`-backed custom validator, or another documented compatible engine) with explicit LF/CR/CRLF/U+2028/U+2029 boundary tests, and MUST NOT weaken the canonical lookahead back to a soft `$`/dollar anchor; make `StateFrame.room_status` REQUIRED on every state frame; make `Ack.applied` const true; include the `not_started` and `duplicate_action_conflict` reject reasons and the `malformed_message` ErrorFrame reason; there is intentionally NO `unknown_action_id` reason, NO reference-to-prior-id/correlation field, and NO `client_name`/authentication/player-name field
    - _Requirements: 20.1, 20.2, 20.3, 21.1, 21.2, 21.3, 21.4, 21.5, 21.6_
  - [x] 11.2 Write wire-contract schema tests in `backend/tests/test_stage4_contract.py`
    - Assert the documented JSON example messages (`hello`, `welcome`, `action`, `state`, `ack` including the no-op `applied:true,no_op:true` case, `reject`, `error`, `outcome` for win/draw/forfeit) parse and conform to their models with no placeholders, ellipsis, or pipe-delimited enum strings
    - Assert that a wrong-typed field, a missing required field, and an extra undocumented field each fail validation, and that no reason/error string leaks a filesystem path, SQL text, an exception/class name, or a stack trace
    - Validate the examples corpus against the canonical JSON Schema with a local Draft 2020-12 validator (`jsonschema`); assert every positive example conforms and every negative example whose `schema_rejects` flag is true is rejected by the schema, while the single documented runtime-only `lexical_float_revision` case (`schema_rejects` false) is NOT required to be schema-rejected (the already-available `jsonschema` 4.26.0 in `docs/runtime/.venv` is reused for this, not installed; the native amendment run recorded 16/16 positives conforming and 20/20 schema-reject negatives rejected in `docs/native-checks/04-m3-contract-amendment/`)
    - Add a STRICT RUNTIME TYPING test obligation: assert that inbound `protocol_version`, `expected_revision`, and `revision` reject a bool, a string, and a float (including a lexical `1.0`) at runtime, because JSON Schema `integer` alone may accept a mathematically integral `1.0`; this strict runtime integer check is an additional semantic rule, not schema-expressible
    - _Requirements: 20.11, 21.1, 21.3, 21.4, 21.6_

- [x] 12. Implement duel rooms, seats, and the room manager (M3)
  - [x] 12.1 Create `backend/app/duel/rooms.py` with `Seat`, `Room`, and `RoomManager`
    - Create the `app/duel/` package and `rooms.py`; define `Seat` (seat_id `A`/`B`, a private `engine.new_game` `Game`, per-seat RNG seed derived from the room seed, monotonic per-seat `revision`, a per-seat monotonic high-water mark `last_action_seq` plus a bounded 256-entry per-seat `reply_cache` idempotency structure, bounded `outbound` queue, `connected`, `gravity_due_monotonic`), `Room` (bounded `room_id`, up to two seats, room `seed`, `status` in `{waiting, playing, finished}`, a SHORT per-room `state_lock` for snapshotting only, monotonic timestamps, set-once `outcome`), and `RoomManager` (rooms map, injectable monotonic `clock`, `assign_seat`, `cleanup_tick`)
    - Both seats receive the IDENTICAL room seed and each constructs its OWN independent `random.Random` instance (its own `engine.new_game(game_id, room_seed)`), so both boards start with this tool's same initial seeded 7-bag sequence while advancing independently; no global RNG is shared and advancing one seat never advances the other or the solo sequence; keep each seat's queue, first-Hold availability, Hold swap, and lock consumption independent, and keep each seat's state private except through broadcast state frames
    - Never register duel `Game`s in `store.py`, never expose them via `GET /api/games/{id}`, never write them to the solo SQLite, and never add a duel entry to the solo leaderboard
    - Define bounds: `max_rooms`, `room_id_max_len`, `max_msg_bytes`, `action_rate_per_seat`, `outbound_queue_depth`, `handshake_timeout`, `idle_timeout`
    - Implement `cleanup_tick` to run periodically even without new traffic, with a finished-room retention policy DISTINCT from the waiting/inactive-room retention policy, each bounded; a cancelled room, slow peer, failed send, and shutdown each release the room entry, gravity task, and sockets with no leaked room/task/socket; take the short per-room `state_lock` only to snapshot and perform bounded ordered outbound I/O OUTSIDE the lock; a restart after a duel yields a fresh room, never reusing a finished room's state
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 17.1, 17.2, 17.3, 17.4, 17.5, 19.1, 19.2, 19.3, 19.5, 19.6, 19.7, 22.3_
  - [x] 12.2 Write hypothesis property tests for Properties 10, 11, 13, 14, 16 in `backend/tests/test_stage4_duel_properties.py`
    - **Property 10: Duel seat independence** — tag `# Feature: tetris-stage4-option-a, Property 10`, run at least 100 iterations; **Validates: Requirements 17.3, 17.4, 17.5**
    - **Property 11: Per-board revision monotonicity** — tag `# Feature: tetris-stage4-option-a, Property 11`, run at least 100 iterations; **Validates: Requirements 20.2, 20.8, 20.9**
    - **Property 13: Duplicate action idempotency** — tag `# Feature: tetris-stage4-option-a, Property 13`, run at least 100 iterations; **Validates: Requirements 20.5**
    - **Property 14: Seat-ownership enforcement** — tag `# Feature: tetris-stage4-option-a, Property 14`, run at least 100 iterations; **Validates: Requirements 20.10**
    - **Property 16: Room cleanup is bounded** — tag `# Feature: tetris-stage4-option-a, Property 16`, run at least 100 iterations, using the injectable monotonic clock; **Validates: Requirements 19.1, 19.2, 19.3**
    - _Requirements: 17.3, 17.4, 17.5, 19.1, 19.2, 19.3, 20.2, 20.5, 20.8, 20.9, 20.10_

- [x] 13. Implement per-board server-side gravity (M3)
  - [x] 13.1 Create `backend/app/duel/gravity.py`
    - Apply gravity on the server independently per board on the injectable monotonic clock, deriving each board's due time from its `level` and the inherited formula `gravity_interval_ms = max(100, 500 - 50 * (level - 1))`; advance only boards whose `gravity_due_monotonic` has elapsed (calling `engine.tick` on that seat's `Game`) and recompute the next due time from the current `gravity_interval_ms`
    - Evaluate ALL due boards before deciding a single outcome: a simultaneous top-out of both boards in the same evaluation is a DRAW; if exactly one board remains playable the surviving seat wins; an active seat that disconnects while the duel is in progress forfeits, resolving the duel EXACTLY once (a finished room is never resolved a second time); on a terminal outcome stop advancing that room's gravity and emit the terminal-outcome frame
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 19.4_
  - [x] 13.2 Write hypothesis property test for Property 15 and injectable-clock gravity tests in `backend/tests/test_stage4_gravity.py`
    - **Property 15: Simultaneous top-out is a draw; otherwise last survivor wins** — tag `# Feature: tetris-stage4-option-a, Property 15`, run at least 100 iterations; **Validates: Requirements 18.3, 18.4, 18.5**
    - Using the injectable fake monotonic clock, cover per-board gravity advancement, simultaneous top-out (draw), last-survivor win, forfeit-once on disconnect, and a disconnect-plus-gravity race resolving the duel exactly once
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 19.4_

- [x] 14. Implement the duel WebSocket endpoint (M3)
  - [x] 14.1 Create `backend/app/ws/duel.py` with the `/ws/duel` endpoint
    - Validate the request `Origin` against an EXACT allow-list bound to the proxy host/port (`http://localhost:5517` and `http://127.0.0.1:5517` by default, configurable and fail-closed like the HTTP CORS list), denying a disallowed Origin at the HTTP upgrade before any WebSocket is established (an HTTP-level denial, not a received WebSocket CLOSE frame)
    - Run the handshake (`hello` -> `welcome` assigning a seat via `RoomManager.assign_seat`), gate the start on both seats being connected, and thereafter apply actions to only the sender's private board
    - Enforce strict EQUALITY between an action's `expected_revision` and the target board's authoritative revision; reject a lower value as `stale_revision` and a higher value as `future_revision` without mutating the board; handle a duplicate `action_id` idempotently via the per-seat high-water mark plus bounded 256-entry reply cache (return the cached ack/rejection when still cached; reject with `duplicate_action_conflict` an already-seen id at or below the high-water mark that has been evicted, never re-applying it or accepting it as new; treat only an id whose ordinal exceeds the high-water mark as a new action); acknowledge a legal no-op with `applied:true,no_op:true` and the unchanged revision; reject `not_seat_owner`, `not_started` (action while the room is `waiting`, which does NOT consume the ordinal/high-water mark), `bad_type`, `missing_field`, `extra_field`, `rate_limited`, and `oversize` cases without mutating any board; answer an APPLICATION-VISIBLE UNCORRELATABLE malformed inbound message (missing/wrong-typed/non-canonical `action_id`, invalid JSON, or an in-band binary frame) with a schema-valid `ErrorFrame` (`reason:"malformed_message"`, no `action_id`) rather than an invalid echo or an invented id, and never burn another seat's sequence; a WIRE-LEVEL invalid-UTF8 TEXT frame is NOT this application path - it is failed by the WebSocket transport BEFORE ASGI with the standard close code 1007 (RFC 6455 §8.1 / §7.4.1, library-managed bounded reason, no required application-controlled JSON reply or exact reason string)
    - Use the standard close codes per close reason with explicit LITERAL reason strings (1000 `"normal_completion"`; 1008 policy/origin violation; 1009 oversize message; 1008 with a `rate_limited` reason for a rate violation; 1001 going-away deliberately SHARED and disambiguated by the literal reason string `"idle_timeout"` / `"handshake_timeout"` / `"server_shutdown"` / the gameplay forfeit `"peer_unavailable_forfeit"` for a failed-send/slow-peer disconnect in a STARTED room / the operational aborts `"waiting_room_timeout"`, `"sequence_exhausted"`, and `"scalar_overflow"`); a failed-send/slow-peer disconnect in a STARTED room is a GAMEPLAY FORFEIT resolving the duel exactly once, whereas a never-started waiting-room cancellation is a separate OPERATIONAL ABORT that fabricates no winner; fail a wire-level invalid-UTF8 TEXT frame at the transport layer with the standard close code 1007 (RFC 6455 §8.1 / §7.4.1, library-managed bounded reason, no required application-controlled JSON reply or exact reason string), and if it occurs in a STARTED room apply the ordinary disconnect/forfeit/once-only cleanup (a waiting-alone 1007 fabricates no winner); reject an oversize message, a rate-limit breach, malformed JSON and in-band binary frames, and a room-at-maximum condition boundedly without exhausting worker memory and without leaking any exception/stack in `detail`; never emit a schema-invalid scalar
    - _Requirements: 16.1, 17.1, 17.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8, 20.9, 20.10, 20.11, 22.1, 22.3, 22.4, 22.5_
  - [x] 14.2 Write hypothesis property test for Property 12 and connection tests in `backend/tests/test_stage4_duel_ws.py`
    - **Property 12: Strict expected-revision acceptance window** — tag `# Feature: tetris-stage4-option-a, Property 12`, run at least 100 iterations; **Validates: Requirements 20.4, 20.6, 20.7**
    - Cover malformed/stale/future/duplicate/seat-ownership messages, oversize and rate-limit bounds, room-at-maximum, origin rejection, slow-peer and failed-send cleanup, concurrent-terminal resolution, cleanup, and shutdown; DRAIN the queued handshake, state, and error frames before asserting the socket reached CLOSE
    - Include a PUBLIC invalid-UTF8 test that sends a raw masked TEXT frame carrying byte `0xFF` and expects a transport close with the standard code 1007 (RFC 6455 §8.1 / §7.4.1), DISTINCT from a browser binary `Uint8Array` `0xFF` frame (an application-visible BINARY payload) which expects the `malformed_message` `ErrorFrame` path; assert a 1007 close in a STARTED room triggers the ordinary disconnect/forfeit/once-only cleanup and a waiting-alone 1007 fabricates no winner
    - Assert duel results stay separate from the solo leaderboard (never in `GET /api/high-scores`), that solo play and solo SQLite persistence continue during a duel, and that the restrictive HTTP CORS policy is preserved unchanged
    - _Requirements: 20.4, 20.6, 20.7, 22.5, 22.6, 23.1, 23.2, 23.3, 23.4, 16.6_

- [x] 15. Wire the duel into the app and the runtime dependency (M3)
  - [x] 15.1 Register the duel and cleanup task in `backend/app/main.py`
    - Register the `/ws/duel` endpoint, start the `RoomManager.cleanup_tick` periodic task in the FastAPI lifespan, and apply the WebSocket `Origin` allow-list bound to the proxy host/port; keep the solo CORS policy and all solo routes unchanged
    - _Requirements: 16.1, 16.6, 19.1, 22.1, 23.2_
  - [x] 15.2 Add a real WebSocket protocol engine runtime dependency to the backend
    - Add a pinned real WebSocket protocol engine dependency (for example `websockets` or `wsproto`) that implements uvicorn's WebSocket upgrade to `backend/requirements.txt` and the runtime lock `backend/requirements.lock.txt`, and ensure it is installed in the runtime image; note that `anyio` alone does not satisfy the upgrade requirement
    - _Requirements: 22.7_
  - [x] 15.3 Proxy `/ws/duel` through Nginx in `frontend/nginx.conf`
    - Add a `location /ws/duel` block performing the WebSocket upgrade (`Upgrade`/`Connection` headers) and preserving `Host` and `Origin` and the proxy port through to the backend worker so the same-origin WS URL reaches it
    - _Requirements: 22.2_

- [~] 16. Checkpoint - M3 duel
  - Ensure all backend duel tests pass, ask the user if questions arise.

- [x] 17. M3 coverage check (check to run; left unchecked)
  - [x] 17.1 Run and record the M3 coverage and quality checks
    - During a later implementation invocation, produce the backend XML and frontend LCOV coverage reports, exercising the duel-room, gravity, cleanup, wire-contract, and error/race branches rather than only the happy path
    - Evaluate the independent Sonar analysis with NEW-code coverage `>= 80%`, duplication `<= 3%`, and `0` new static findings each as a SEPARATE outcome; do not weaken thresholds, add production-code exclusions, or reset the baseline
    - Report actual findings honestly; fabricate no numbers
    - _Requirements: 24.2, 24.3, 24.4, 24.5, 24.6_

<!-- =====================  CROSS-CUTTING  ===================== -->

- [x] 18. Preserve inherited Stage 1/2/3 regression assertions
  - [x] 18.1 Confirm inherited backend regression coverage is intact
    - During a later implementation invocation, run the inherited Stage 1/2/3 backend rules/scoring/API/persistence/finalization/leaderboard tests and confirm they pass unchanged; do not alter inherited assertions or the inherited spec directories
    - _Requirements: 24.1, 29.1, 29.2, 29.3_
  - [x] 18.2 Confirm inherited frontend regression coverage is intact
    - During a later implementation invocation, run the inherited Stage 2/3 frontend request-ordering/lifecycle/leaderboard tests (`useGame.test.tsx`, `useGame.races.test.tsx`, `useGame.queued-timers.test.tsx`, `useGame.highscores.test.tsx`) and confirm they pass unchanged
    - The single documented exception is the superseded `Board.test.tsx` DOM-cell assertions (task 8.4), whose semantic coverage is replaced by the Canvas pixel evidence
    - _Requirements: 24.1, 14.5, 29.2, 29.3_

- [x] 19. Isolated Stage 4 containerization and CI
  - [x] 19.1 Create the isolated Stage 4 Docker and Compose configuration
    - Define the Stage 4 Compose stack with project name `tetris-stage4-kiro`, an isolated network, and a named volume for the backend SQLite directory; publish ONLY the frontend on host port `5517` and keep the backend reachable only on the internal network
    - Run the backend and frontend each as a non-root user (distinct users) and run exactly one backend worker (`--workers 1`) so the single worker owns both solo games and duel rooms; resolve `TETRIS_DB_PATH` inside the named volume; add per-service health checks
    - Never start, stop, modify, or remove the inherited Stage 3 resources (project `tetris-stage3-kiro`, host `5183`) or any other tool's containers/volumes/networks
    - _Requirements: 25.1, 25.2, 25.3, 25.4_
  - [x] 19.2 Add the isolated Stage 4 CI workflows under `.github/workflows/`
    - Define CI jobs for backend tests with coverage, frontend tests and build, the backend/frontend image builds, and a SEPARATE performance job; treat the local workflow file and local clean-equivalent checks as configuration artifacts only, not evidence of a hosted Actions run
    - Ensure CI runs do not delete data outside declared temporary fixtures and preserve the solo SQLite data and the restrictive HTTP CORS policy
    - _Requirements: 25.1, 25.4, 25.5, 25.6_

<!-- ==========  NATIVE 21: BENCHMARK HARNESS AUTHORIZATION  ========== -->
<!--
Dated 2026-11-06 (native 21). Note on disk at
`docs/native-checks/21-stage4-benchmark-harness-authorization/NOTE.md`, written BEFORE
this task was amended, per the correction guardrail. The former task 20 "DESIGN ONLY;
no execution" posture is LIFTED per amended Requirements 26-27 and the amended design
"Benchmark harness (AUTHORIZED IMPLEMENTATION ...)" section: actual harness IMPLEMENTATION
and the harness's OWN semantic self-checks are authorized now (20.1, 20.2, both left
unchecked / not executed in this call). The SIX measured production trials - two short
headful probes (20.3) and three Solo + three Duel 35s trials (20.4) - remain
SEPARATELY AUTHORIZED and are NOT executed here. Every pre-existing measurement-honesty,
exclusion, calibration, and target-vs-qualification obligation is preserved unchanged;
no accepted application source, test, dependency lock, infrastructure, or canonical duel
wire contract is touched; physical presentation latency stays UNKNOWN and the overall
Sonar quality gate is NOT all-pass. Dependency order: 20.1 (implement) -> 20.2
(self-checks) -> 20.3 (probes, separately authorized) -> 20.4 (six trials, separately
authorized); 20.3 and 20.4 stay UNCHECKED and UNEXECUTED.
-->

- [~] 20. Implement the benchmark harness and its own semantic self-checks (measured trials separately authorized, NOT executed)
  - Dependency order within this task: 20.1 (implement the harness) -> 20.2 (harness semantic self-checks) -> 20.3 (two short headful probes, separately authorized) -> 20.4 (three Solo + three Duel 35s trials, separately authorized). Only 20.1 and 20.2 are implementable now; 20.3 and 20.4 are left UNCHECKED and are NOT executed in this call.
  - [x] 20.1 Implement (not just design) the `perf/` harness by EXTENDING this tool's own `perf/benchmark.mjs` + `perf/validate-instrument.mjs`
    - EXTEND this tool's own `perf/benchmark.mjs` and `perf/validate-instrument.mjs` plus small modular helpers (reuse the canonical implementation leaf; do NOT add an executor-per-metric), using the native Canvas palette/schema and this tool's own native Stage 3 perf source; install the harness's own perf `node_modules` from the existing pinned Playwright `1.56.0` lock with NO browser/runtime/dependency version upgrade; target the production URL `http://127.0.0.1:5517` with the installed production Chrome channel, sandbox enabled, HEADFUL only (no hidden/headless fallback), a `1280x900` viewport, and DPR `1`
    - Provide a runnable CLI entrypoint that actually invokes the trial driver and exits NONZERO if no trial executed; identify the two OWNED Chrome process identifiers through a genuinely-verified PUBLIC Playwright API (`launchServer` / `browser.process()`), never guessing a PID from the Node process or the current foreground window
    - Add READ-ONLY Win32 / native PowerShell foreground telemetry (HWND/PID/title/visibility/rectangle) that NEVER activates, moves, or fakes foreground; emit a `READY_FOR_FOREGROUND` signal carrying the actual actor identity AFTER both clients open/join and wait BOUNDEDLY for a real foreground transition (no `SetForegroundWindow`/`SendKeys`/PowerShell UI-automation); use a SINGLE actual Canvas image-buffer read plus 200 cell centers for pixel qualification, with a SEPARATE lightweight `requestAnimationFrame`-scheduling observer; keep paired Node `hrtime` / browser `performance` pre/post calibration with an explicit uncertainty bound
    - Drive source input via the declared fixed ~5Hz pattern `(right, right, right, down, cw, left, left, left, left, left, left, down, ccw, right, right, right)`, using only passive read-only DOM input / rAF / Canvas recorders plus passive Playwright HTTP/WS observation (NO `fetch`/`WebSocket` monkeypatch or interception, NO React internals or debug hooks, NO injected authority); reference the actual UI controls from design.md (`role="tab"` Solo/Duel, the `"Room name"` input, the `"Create or join"` button, the actor Canvas `'[aria-label="Your Tetris board"] canvas'` and peer Canvas `'[aria-label="Opponent Tetris board (read-only)"] canvas'`), with left/right `ArrowLeft`/`ArrowRight`, soft-drop `ArrowDown`, CW `ArrowUp`, CCW `z`/`Z`
    - This leaf is IMPLEMENTABLE now and left UNCHECKED (not yet executed in this call); do not launch any measured production trial, probe, or measured window as part of implementation
    - _Requirements: 26.1, 26.2, 26.3, 26.4, 26.7, 26.10, 26.11, 26.12, 26.13, 27.1, 27.2, 27.3, 27.10, 27.12, 27.13_
  - [x] 20.2 Implement the harness's OWN semantic self-checks (authorized now)
    - Deliberately REJECT each of: a wrong cell mask; a scalar-only or unchanged no-op mask treated as an action; a wrong `revision`/`room`/`seat`; a cross-clock subtraction; an invalid focus; an out-of-window sample; and a no-op CLI; prove via an actual CLI self-check that the entrypoint calls the driver and returns NONZERO when there is no functional work
    - No mirror-only tests that merely restate a helper and no self-check that only repeats its own formula; this leaf is IMPLEMENTABLE now and left UNCHECKED (not executed in this call); run no measured production trial, probe, or measured window
    - _Requirements: 26.12, 27.1, 27.3, 27.14, 27.15_
  - [ ] 20.3 Run the two short headful foreground PROBES (separately authorized; NOT executed in this call)
    - Gated on 20.1 and 20.2, run two short headful foreground probes to qualify the instrument, source, and method (owned-Chrome-PID identification, read-only foreground telemetry, single-buffer pixel read, clock calibration) before any measured trial, using the installed production Chrome channel, sandbox enabled, HEADFUL only, at `1280x900` DPR `1` against `http://127.0.0.1:5517`; retain the probe outputs honestly and assert no measured metric
    - This is SEPARATELY AUTHORIZED work that is NOT executed in this call; left UNCHECKED, with no reused executor-per-metric
    - _Requirements: 26.5, 26.6, 26.8, 26.9, 27.8_
  - [ ] 20.4 Run the three Solo + three Duel 35s measured TRIALS (separately authorized; NOT executed in this call)
    - Gated on 20.1, 20.2, and 20.3, run exactly three Solo and three Duel trials of `35s` each with `>= 5s` warm-up excluded and a fixed `30s` measured window on a monotonic clock, a fresh session per trial, no hidden restart or timer reset inside the measured window, opening BOTH duel clients before approving actual-actor input foreground and observing OS foreground plus native focus throughout; for duel trials identify the actor's real process identifier, window title, and window handle
    - Retain all samples, counts, exclusions, median, p95, p99, screenshots, and traces with each excluded-sample reason; do NOT pool samples across trials or make statistical-significance/scalability/physical-presentation claims; state the `>= 55 FPS` mean and `<= 25 ms` p95 rAF interval as SCHEDULING TARGETS ONLY, kept separate from measurement qualification
    - This is SEPARATELY AUTHORIZED work that is NOT executed in this call; left UNCHECKED, with no reused executor-per-metric
    - _Requirements: 26.3, 26.4, 26.5, 26.6, 26.8, 26.9, 27.4, 27.5, 27.6, 27.7, 27.9, 27.11_

- [x] 21. Process-guardrail note before any corrective change
  - [x] 21.1 Enforce the on-disk dated note before any correction
    - Before any later corrective code, test, configuration, or benchmark change made in response to a failed or defective check, write a NEW dated native note on disk under `docs/native-checks/<nn>/` identifying the observed defect and the intended correction BEFORE applying the change; chat narration and a pre-existing broad note are not sufficient
    - IF a check fails AND the required dated on-disk note cannot be written first THEN report the failure and stop rather than silently applying the correction
    - _Requirements: 28.1, 28.2, 28.3, 28.4_

- [x] 22. Truthful native-completion documentation
  - [x] 22.1 Document Stage 4 honestly in `backend/README.md` (or a Stage 4 section)
    - Document the Stage 4 rotation API, the Canvas board, the duel endpoint and wire contract, the isolated Docker/Compose operations (build/start/stop/persistence-across-restart on host `5517`), and the benchmark design
    - Fabricate no completed approvals, checks, metrics, CI runs, tokens, costs, screenshots, Docker successes, coverage numbers, duplication numbers, or performance results; report any value not actually executed as not executed; perform no commits, pushes, image publishing, or external deployment
    - _Requirements: 25.5, 29.6, 29.7_

- [~] 23. Two-browser production-proxy duel verification (optional; manual)
  - [~] 23.1 Verify a real duel against the production proxy (left unchecked)
    - Against the actual production proxy on host `5517`, open two browsers and verify start gating (no start until both seats connect), move/rotation synchronization between seats, disconnect forfeit resolution, room isolation (one seat's actions never affect the other), and terminal result delivery
    - This is a manual verification probe, planned and left unchecked; execute no run as part of planning
    - _Requirements: 16.1, 16.2, 17.1, 17.5, 18.5_

- [~] 24. Final checkpoint - M1/M2/M3 integration
  - Ensure all backend and frontend tests pass across the three milestones, ask the user if questions arise.

<!-- ==========  M3 NATIVE 14 CORRECTION: LIFECYCLE / DELIVERY / FRONTEND  ========== -->
<!--
Dated 2026-11-06 (native 14). Pre-correction note on disk at
`docs/native-checks/14-m3-lifecycle-delivery-frontend-correction/NOTE.md`, written BEFORE
these tasks were added and BEFORE any code/test/config edit, per the correction guardrail.
The independent researcher checkpoint after native 12
(`docs/validation/12-m3-source-review/report.json`) rejected M3 as
M3_NOT_ACCEPTED_ACTUAL_PUBLIC_START_BROADCAST_BLOCKER_AND_CLIENT_MISSING: the waiting peer
never receives the start/playing frame (blocked reader, no independent writer), gravity does
not publish states, no on_outcome is wired, cleanup leaves idle sockets blocked,
`_emit_cached` hides failed sends, operational aborts (sequence_exhausted/scalar_overflow)
are not wired at the endpoint, and the entire frontend duel client/view is MISSING. These
tasks close those seams. tasks 11-17 stay as recorded (their artifacts exist) but M3 is NOT
accepted until these correction tasks and the independent checkpoint pass. The canonical
accepted wire schema/corpus and numeric/policy decisions remain FROZEN.
-->

- [x] 30. Independent per-connection writer and both-boards delivery (M3 correction)
  - [x] 30.1 Add an independent bounded ordered per-connection writer with safe lifecycle in `backend/app/ws/duel.py` and `backend/app/duel/rooms.py`
    - Give each connected socket a SINGLE independent writer task that flushes queued frames WITHOUT requiring recipient inbound traffic, running concurrently with the `receive` reader; take the SHORT per-room `state_lock` ONLY to produce consistent DETACHED snapshots, then enqueue onto each recipient's bounded outbound queue (depth 64) and perform all bounded network I/O (5s send bound) OUTSIDE the lock, with no unbounded task/queue/send retries so one slow peer blocks neither the other peer, nor another room, nor the worker
    - Fix `_emit_cached` so it never returns `drain_result or True`: a failed cached send is reported as a failure and never pretended to have succeeded; deliver the cached reply through the same bounded writer
    - On every teardown path (normal completion, forfeit, operational abort, idle/handshake timeout, shutdown) cancel and await BOTH the reader and the writer and release the socket, the room gravity task, and the room map entry with no leaked task/socket/room; propagate/handle `CancelledError` so cancellation actually reaches the awaited reader/writer/gravity resources and is never silently swallowed (the lifecycle semantics behind independent BUG python:S7497 at `backend/app/duel/gravity.py` and `backend/app/main.py`), correcting those findings with tests rather than suppressing them
    - _Requirements: 16.1, 17.1, 17.2, 19.3, 19.5, 19.6, 22.3, 22.4, 22.5_
  - [x] 30.2 Broadcast BOTH authoritative boards to BOTH peers for every transition in `backend/app/ws/duel.py`, `backend/app/duel/gravity.py`, and `backend/app/main.py`
    - Deliver both seat boards (each a `StateFrame` with its own target `seat_id` and per-board `revision`) to both connected peers, strictly room-scoped, for the mandatory waiting and start transitions, ordinary own and remote accepted movement/rotation/Hold, server no-input gravity, terminal outcome, and forfeit; publish state frames from the gravity loop after it advances boards; wire the room `on_outcome` in `main.py` so terminal/forfeit outcome frames are actually emitted to both peers; deliver traffic-free waiting/idle/finished/shutdown cleanup frames through the independent writer to both recipients
    - Keep server monotonic deadlines independent of manual actions; advance all boards due at a logical instant BEFORE deciding one outcome; register no duel state in `store.py` or the solo SQLite and preserve normal solo behavior during a duel
    - _Requirements: 16.2, 17.3, 17.4, 17.5, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 19.4, 20.2, 20.8, 20.9, 23.1, 23.2, 23.3, 23.4_
  - [x] 30.3 Wire the operational aborts at the endpoint in `backend/app/ws/duel.py`
    - Make the max valid ordinal `999999999999999` consumable, then close the room on the next-higher ordinal with code 1001 + literal reason `"sequence_exhausted"` (no fabricated winner); close the room with code 1001 + literal reason `"scalar_overflow"` when a scalar WOULD overflow the SAFE integer bound (no out-of-range state/revision emitted), instead of closing only the actor and invoking the ordinary disconnect/forfeit; keep these DISTINCT from the gameplay `peer_unavailable_forfeit`; preserve STRICT decoded-int typing (reject bool/string/1.0) and the full-string `action_id` grammar (reject LF/CR/CRLF/U+2028/U+2029 via the Python `re`-backed custom full-string validator, never a soft `$`-anchored pattern)
    - _Requirements: 20.3, 20.4, 20.5, 20.6, 20.7, 20.10, 20.11, 22.4, 22.5_
  - [x] 30.4 Write meaningful native backend tests exposing the production-visible delivery/lifecycle/abort behavior in `backend/tests/test_stage4_duel_delivery.py`
    - Assert server pushes reach a peer WITHOUT that peer sending inbound traffic (the waiting peer receives the start/playing frame after both connect); assert both peers receive BOTH seat boards across waiting/start/movement/rotation/Hold/gravity/terminal/forfeit; assert traffic-free waiting/idle/finished/shutdown cleanup with no leaked room/task/socket using the injectable clock; assert a failed/slow-peer send does not block the other peer or room and that `_emit_cached` reports a failed send honestly; assert the `sequence_exhausted` and `scalar_overflow` operational aborts (boundary, once-only, peer cleanup, no fabricated winner) distinct from forfeit; drain queued handshake/state/error frames before asserting CLOSE
    - These are meaningful production-visible tests, not pure-helper-only tests; do not remove or weaken any assertion
    - _Requirements: 16.6, 18.5, 19.1, 19.2, 19.3, 20.4, 20.5, 20.6, 20.7, 22.5, 22.6_

- [x] 31. Frontend duel WebSocket client (M3 correction)
  - [x] 31.1 Create `frontend/src/duelClient.ts` with a real standard WebSocket client
    - Open a same-origin `/ws/duel` WebSocket, send `hello` with the chosen `room_id`, and expose a typed callback stream of `welcome`/`state`/`ack`/`reject`/`error`/`outcome`; own exactly one socket and its listeners; `close()` removes only its own listeners and closes only that socket; emit EXACTLY ONE canonical `action` per authorized local input with a monotonically increasing own-seat ordinal (prefix matching the assigned seat) and the last authoritative OWN-board revision as `expected_revision`; perform NO local-predicted board/seed/gravity; ignore stale/wrong-room/wrong-generation frames and never let a late/old `ack` roll back newer authority; never cross-wire A/B
    - Add no production debug hook/endpoint, no React-internal access, no source input interception, no WebSocket/fetch monkeypatch, and no auth/player-name/feature outside the seed
    - _Requirements: 16.1, 17.1, 17.2, 20.3, 20.4, 20.8, 20.9, 20.10_

- [x] 32. Frontend duel view and mode switch (M3 correction)
  - [x] 32.1 Create `frontend/src/DuelView.tsx` and add the solo/duel mode switch in `frontend/src/App.tsx`
    - Add an accessible solo/duel mode switch keeping solo reachable; provide accessible named-room create/join/wait/start/error/finished/return/restart flows (a restart is a FRESH room, never a reused finished room); reuse `CanvasBoard` for BOTH authoritative boards (own + opponent); show meaningful own and opponent status/score/lines/level/next/Hold plus own controls; keep the opponent board read-only; bind one real ArrowUp/z/Z (rotate), ArrowLeft/ArrowRight (move), ArrowDown (soft drop), and Hold to EXACTLY ONE canonical action each through the duel client, gated on `playing` and on owning the acting seat
    - Fit both boards + panels + own controls within `1280x900` at DPR 1 and 2 with no page overflow/clipping/overlap; do not require three simultaneous boards; clean up only OWNED sockets/listeners/handlers on mode switch/restart/unmount; ensure NO hidden solo autotick or solo keyboard listener while in duel and no stale duel/solo socket effect after a fresh room or mode switch
    - _Requirements: 16.1, 16.2, 17.1, 17.5, 15.1, 15.2, 15.3_
  - [x] 32.2 Write meaningful behavioral frontend duel tests in `frontend/src/DuelView.test.tsx` and `frontend/src/duelClient.test.ts`
    - Explicit event sends with EXACT action counts and the triggering input performed OUTSIDE `waitFor`, covering: start gating (no action while waiting), one-input-one-action with monotonic ordinals and the last own revision, both-boards render from authoritative frames, old/late-ACK no-rollback, stale/wrong-room/wrong-generation frame rejection, no A/B cross-wiring, error/race paths, unmount/mode-switch/restart cleanup (no leaked socket/listener, no solo autotick or solo key listener during duel, no stale socket after a fresh room), and the start/sync path
    - These native mocks are SELF-TESTS only and are never treated as production wire/pixel/focus/performance proof; do not remove or weaken any assertion
    - _Requirements: 16.1, 16.2, 17.1, 17.5, 18.5_

- [x] 33. Native fresh self-checks for the M3 correction (run-and-record; no gate self-acceptance)
  - [x] 33.1 Run and record full backend/frontend coverage and build for the correction
    - Produce full backend coverage (XML) and full frontend coverage (LCOV) with every executable new client/view module included (no source/coverage exclusion, no assertion removal, no threshold/scope/baseline weakening), plus the frontend build; run the inherited Stage 1/2/3 regressions and the new duel delivery/client/view tests; run local audits / pip check; preserve failures and raw outputs
    - Do NOT mark the independent Sonar NEW-coverage/static gate accepted here (including the overall ERROR, 45 NEW static findings and the 2 BUG python:S7497 lifecycle findings, which are corrected by task 30.1 with tests, not suppressed); report actual findings honestly and fabricate no numbers; the independent Sonar/acceptance checkpoint runs after this call closes; run no benchmark/perf trial in this call
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.6_

- [x] 34. Align the single coherent native Stage 4 reproducible configuration (M3 correction)
  - [x] 34.1 Reconcile `docker-compose.yml` and `docker-compose.stage4.yml` to one coherent configuration and document the canonical command
    - Keep the CURRENT accepted solo SQLite volume and the deployed `docker-compose.yml` (the one in `docs/final/docker/m3-native-01/report.json`) as canonical; if the named standalone `docker-compose.stage4.yml` is retained, align its project/volume/network with the actual existing Stage 4 resources (no new/foreign volume) and document the single canonical build/start/stop/persistence-across-restart command in `backend/README.md`; do not silently switch away from the accepted solo volume, delete any foreign resource/volume, or perform any schema/data migration/reset
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 29.6, 29.7_

<!-- ==========  M3 NATIVE 19 CORRECTION: FORFEIT DELIVERY / WRITER WAKE / HELLO CAP / MODEL STRICTNESS / Z DIRECTION  ========== -->
<!--
Dated 2026-11-06 (native 19). Pre-correction note on disk at
`docs/native-checks/19-m3-forfeit-writer-hello-model-z-correction/NOTE.md`, written BEFORE
these tasks were added and BEFORE any code/test/config/schema edit, per the correction guardrail.
The independent researcher checkpoint after native 13
(`docs/validation/13-m3-source-review/report.json`) REJECTED M3 as
M3_NOT_ACCEPTED_ACTUAL_FORFEIT_WRITER_HELLO_CAP_AND_Z_DIRECTION_FAILURES even though native 13
closed exit 0 with green self-tests (497 backend / 151 frontend) that MISSED these
production-visible cases: (F1) a started-room disconnect/1007/failed-send/full-queue resolves the
forfeit set-once but NEVER broadcasts the outcome/state to the remaining peer, because
`_handle_disconnect` publishes nothing and `main._publish_room_outcome` only fires when a gravity
step NEWLY resolves a room (an already-finished/removed room is skipped forever); (F2) a writer
failure marks `send_failed` and returns without waking/terminating the blocked reader or running
central forfeit/cleanup, including the cached-ACK path; (F3) `_cleanup_loop` / `_DuelRuntime.stop`
only drop entries / shutdown without requesting a real socket close, waking blocked
receives/writers, or releasing/awaiting owned tasks; (F4) the FIRST Hello bypasses the 4096 UTF-8
byte bound and closes 1008 instead of the required 1009; (F5) outbound duel models coerce a boolean
board cell to int and accept True for `Literal[1]` protocol_version; (F6) scalar_overflow /
sequence_exhausted operational abort must close BOTH sockets 1001 + literal reason with no forfeit /
no out-of-range emitted state, checked on action AND gravity transitions; (F7, frontend)
`DuelView.actionKindForKey` maps ArrowUp, z, Z all to cw, so z sends cw instead of the required ccw.
These tasks close those seams. tasks 11-17 and 30-34 stay as recorded (their artifacts exist) but M3
is NOT accepted until these correction tasks and the independent checkpoint pass. The canonical
accepted wire schema/corpus and numeric/policy decisions remain FROZEN; no benchmark/perf is run and
M3 is not self-accepted. The still-out-of-scope benchmark (20.1) and manual (23.1) tasks remain
gated AFTER these correction waves and are not executed in this call.
-->

- [x] 35. Centralized forfeit delivery, writer wake, lifecycle close, Hello cap, and model strictness (M3 correction)
  - [x] 35.1 Centralize exactly-once terminal resolution AND actual publication/close on disconnect/transport/send failure in `backend/app/ws/duel.py`, `backend/app/duel/gravity.py`, and `backend/app/main.py`
    - On an actual disconnect / transport 1007 / failed send / full outbound queue in a STARTED room, resolve the duel EXACTLY once, enqueue the valid terminal `outcome` (and the final `StateFrame`s for both boards) to the remaining peer(s) through the independent writer, DRAIN in FIFO, close with the documented standard close code and LITERAL reason (`peer_unavailable_forfeit`, 1001), and release the owned room/gravity-task/socket resources; do NOT rely on a future gravity step or any further client input, and do NOT leave an already-finished/removed room unpublished (fix the `_handle_disconnect` -> no-broadcast seam and the `on_outcome`-only-on-newly-resolved gap). A waiting-room cancellation fabricates NO winner (operational abort, `waiting_room_timeout`). Normal gravity terminal ALSO emits the final state/outcome to both peers and a bounded close with no further client traffic, with all due boards evaluated before the single decision. Keep room-scoped only; preserve finished-15s / waiting-120s / playing-idle-60s / cadence-1+slack-1 semantics and the forfeit-vs-operational-abort distinction
    - _Requirements: 16.1, 16.2, 17.3, 17.4, 17.5, 18.5, 18.6, 19.1, 19.2, 19.3, 19.4, 20.2, 20.8, 20.9, 22.3, 22.4, 22.5_
  - [x] 35.2 Make a writer failure wake and terminate the blocked reader and trigger central forfeit/cleanup without another flush in `backend/app/ws/duel.py` and `backend/app/duel/rooms.py`
    - A writer failure (new or cached ACK) must wake/terminate the blocked reader and trigger the central forfeit/cleanup WITHOUT waiting for another `_flush_and_check`; fix the writer-owner coordination so a `send_failed`/in-flight-send race cannot leave the reader blocked forever; route close directives through the SAME single ordered writer/socket rather than concurrent unsynchronized sends; preserve ONE ordered writer/socket, queue depth 64, 5s send bound, short detached snapshot locks, all I/O outside the lock, no retries / no leaked tasks; cancellation truly propagates and owned tasks are awaited boundedly
    - _Requirements: 17.1, 17.2, 19.3, 19.5, 19.6, 22.3, 22.4, 22.5_
  - [x] 35.3 Make cleanup and shutdown actually close sockets, wake blocked receives/writers, and release/await owned tasks in `backend/app/main.py` and `backend/app/duel/rooms.py`
    - `_cleanup_loop` (reaped waiting/idle/finished rooms) and `_DuelRuntime.stop` / `manager.shutdown()` must request a proper socket close, wake blocked receives/writers, and release/await owned tasks; do not fabricate a gameplay winner on a lifecycle/operational abort; use the native 120/60/15/1-second constants in production (smaller instance bounds or a fake clock ONLY in private unit fixtures)
    - _Requirements: 19.1, 19.2, 19.3, 19.5, 19.6_
  - [x] 35.4 Apply the 4096 UTF-8 byte bound to the FIRST Hello/handshake before parse with CLOSE 1009 in `backend/app/ws/duel.py`
    - Apply the 4096 UTF-8 byte bound (including binary classification) to the FIRST Hello/handshake BEFORE JSON/model parse, closing with the standard code 1009 on oversize instead of 1008; keep the malformed-visible-JSON/binary schema-valid ErrorFrame path (no invented ids), the pre-upgrade Origin 403, the raw invalid TEXT 1007 before ASGI, and all working rate/cache/highwater/sequence paths unchanged
    - _Requirements: 20.3, 20.11, 22.4, 22.5_
  - [x] 35.5 Apply targeted strict scalar/bool validators to the outbound duel models in `backend/app/ws/contract.py`
    - Make a boolean board cell and a boolean/float/string `protocol_version` reject (not silently coerce) in the OUTBOUND models as well; keep all 22 positive native examples / R negative contract cases and the negative I-anchor valid/invalid exactly as documented; do NOT globally enable strict tuple-collection rejection (valid decoded JSON arrays must still map to coordinate tuples); no schema/corpus rewrite, no new Pydantic version or dependency; outbound builders still emit the canonical type/version/required room_status
    - _Requirements: 20.11, 21.1, 21.3, 21.4, 21.6_
  - [x] 35.6 Preserve scalar_overflow / sequence_exhausted operational abort checked on action AND gravity, aborting before publishing, in `backend/app/ws/duel.py` and `backend/app/duel/gravity.py`
    - Preserve the scalar_overflow / sequence_exhausted operational abort with BOTH sockets closed 1001 + literal reason and NO forfeit / no out-of-range emitted state; check the action AND the gravity transition: if a scalar WOULD exceed the safe ceiling, stop/abort BEFORE publishing (no dead gravity task from a ValidationError); keep these DISTINCT from the gameplay `peer_unavailable_forfeit`
    - _Requirements: 20.11, 22.4, 22.5_
  - [x] 35.7 Write meaningful real-lifecycle backend tests with actual receiver frames and no follow-up input in `backend/tests/test_stage4_duel_delivery.py` and `backend/tests/test_stage4_duel_writer.py`
    - Assert the remaining peer ACTUALLY receives the forfeit outcome + final state frames after a real disconnect / transport 1007 / failed send / full queue with NO further input from either peer, and reaches CLOSE with the documented literal reason; assert a writer failure (new and cached ACK) wakes/terminates the blocked reader and triggers central forfeit/cleanup without another flush; assert cleanup/shutdown actually CLOSE the idle peer with a documented reason and no new traffic (not merely an empty rooms map); assert the oversize-Hello CLOSE 1009; assert outbound bool-board / bool-version rejection; assert scalar_overflow / sequence_exhausted close BOTH sockets 1001 + literal reason with no forfeit, using a real consistent engine terminal fixture (active=None when game_over) rather than bypassing on_state or asserting internal objects; diagnose hangs with `pytest -o faulthandler_timeout=15`, keep bounded per-command time, write outputs to files, preserve timeouts, no unbounded drain; do not remove or weaken any assertion
    - _Requirements: 16.6, 17.1, 17.2, 18.5, 19.1, 19.2, 19.3, 20.11, 22.4, 22.5, 22.6_

- [x] 36. Split ArrowUp (cw) from z/Z (ccw) in the duel view (M3 correction)
  - [x] 36.1 Correct `DuelView.actionKindForKey` and the visible help text in `frontend/src/DuelView.tsx`
    - Split the key mapping so `ArrowUp` -> `cw` and `z`/`Z` -> `ccw`, matching the M1 solo mapping, with each real input emitting EXACTLY ONE canonical action; correct the visible help text accordingly; preserve the client generation / old-ACK / race / cleanup / mode-switch behavior, both Canvas panels and the desktop bounds; add no production debug hook/endpoint, no WebSocket/fetch replacement or interception, no React internals, and no predicted board/gravity/seed; solo stays reachable and unmounted while in duel; a restart reaches an actual fresh room state; retain the existing good layout rather than redesigning
    - _Requirements: 16.1, 17.1, 17.2, 8.2, 8.3_
  - [x] 36.2 Update the meaningful duel-view direction tests in `frontend/src/DuelView.test.tsx`
    - Update the native tests so pressing `z`/`Z` asserts exactly ONE `ccw` action and `ArrowUp` asserts exactly ONE `cw` action, with the triggering input performed OUTSIDE `waitFor`, the exact direction, and the exact count; these native mocks are SELF-TESTS only and are never treated as production wire/pixel/focus/performance proof; do not remove or weaken any other assertion
    - _Requirements: 16.1, 17.1, 8.2, 8.3_

<!-- ==========  M3 NATIVE 20 CORRECTION: TERMINAL SOCKET LIFETIME / NORMAL-COMPLETION CLOSE CODE / QUEUE-FULL CLASSIFICATION  ========== -->
<!--
Dated 2026-11-06 (native 20). Pre-correction note on disk at
`docs/native-checks/20-m3-terminal-socket-lifetime-close-code-queue-overflow/NOTE.md`, written
BEFORE this task was added and BEFORE any code/test/config edit, per the correction guardrail.
The independent researcher checkpoint after native 14
(`docs/validation/14-m3-source-review/report.json`) REJECTED M3 as
M3_NOT_ACCEPTED_TERMINAL_SOCKET_LIFETIME_CLOSE_CODE_AND_QUEUE_OVERFLOW even though native 14
closed exit 0 with 555 backend / 154 frontend green self-tests. Three production-visible
backend defects remain: (D1) a STARTED-room disconnect / transport 1007 / failed new-or-cached
ACK DELIVERS the forfeit to the idle survivor but NEVER ends the survivor socket/reader -- the
actual raw 5517 m3-started-text-utf8-02 observes no terminal CLOSE after the FULL 17.2s
(15 finished retention + 1 cadence + 1 slack) because `_handle_disconnect` broadcasts the
terminal then `release_room` removes the manager entry WITHOUT a survivor close directive, so
the retention cleanup never sees the room to close it; (D2) the normal simultaneous-top-out
gravity terminal (actual `_DuelRuntime` + real Starlette + real engine) closes BOTH peers 1001
`normal_completion` instead of the canonical 1000 because `main._release_room_resources`
unconditionally requests `CLOSE_CODE_GOING_AWAY` for every reason; (D3) a FULL outbound queue
(depth 64) ALONE is silently ignored -- `Seat.enqueue_outbound` returns `False` but the
`broadcast_room_state`/`broadcast_outcome`/`broadcast_terminal` publishers ignore it and never
classify the peer unavailable or wake its reader, so with a TIMELY in-flight send (released at
0.05s, well before the unchanged 5s bound) the healthy idle peer gets no forfeit. These tasks
close those seams. tasks 11-17, 30-34, and 35-36 stay as recorded (their artifacts exist) but
M3 is NOT accepted until this correction task and the independent checkpoint pass. The canonical
accepted wire schema/corpus and numeric/policy decisions remain FROZEN; the frontend is FROZEN;
no benchmark/perf/Docker/Sonar is run and M3 is not self-accepted. The out-of-scope benchmark
(20.1) and manual (23.1) tasks remain gated AFTER this wave and are not executed in this call.
-->

- [x] 37. Terminal socket lifetime, normal-completion close code, and queue-full classification (M3 correction)
  - [x] 37.1 Close the surviving terminal socket, select the normal-completion close code, and classify a full outbound queue as an unavailable peer in `backend/app/ws/duel.py`, `backend/app/main.py`, and `backend/app/duel/rooms.py`
    - D1 (survivor never closes): on an actual disconnect / transport 1007 / failed new-or-cached ACK / full queue in a STARTED room, after resolving the forfeit EXACTLY once and publishing the terminal (final both-board `StateFrame`s then the single `outcome`) to the remaining peer through the independent writer, ALSO close the SURVIVING peer's socket through the SAME single ordered writer and terminate its reader, releasing/awaiting the owned writer/reader/gravity resources so the survivor reaches CLOSE WITHIN the bounded finished retention WITHOUT any further input from either side and WITHOUT relying on a future gravity step; do NOT remove the manager room entry in a way that orphans an unclosed survivor socket from the periodic retention cleanup (fix the `_handle_disconnect` release-without-survivor-close seam); a normal terminal MAY drain before closure within the bounded finished retention and never requires recipient input to close; preserve the once-only outcome, the room-name fresh-restart behavior, and the failed-seat 1001 `peer_unavailable_forfeit` vs the ordinary normal-completion 1000 distinction
    - D2 (wrong normal-completion code): in `main._release_room_resources`, select the close code BY REASON instead of unconditionally `CLOSE_CODE_GOING_AWAY` -- a reaped `finished`/`normal_completion` room closes 1000 `normal_completion`, while `waiting_room_timeout` / `idle_timeout` / `server_shutdown` / the operational aborts keep 1001; pass the correct `(code, reason)` into `Seat.request_close` so the one ordered writer closes with the canonical code; the already-passing waiting / idle / shutdown R cases stay unchanged
    - D3 (queue-full ignored): make the common publication seam(s) OBSERVE `Seat.enqueue_outbound` returning `False` at depth 64 and, in a STARTED room, mark the peer send-failed exactly ONCE and wake its own reader (via the writer-gone signal) so a full queue is classified as an unavailable peer and the healthy idle peer is notified / resolved exactly once, rather than silently dropping frames; keep depth <= 64, the 5s send bound, the once-outcome guard, and terminal ordering all unchanged, and do NOT invent a winner on a waiting / operational-abort / finished room
    - Keep every real terminal path (gravity / manual / disconnect / 1007 / failed new ACK / failed cached ACK / full queue) closing the ACTUAL sockets and awaiting owned tasks; preserve short detached-snapshot locks, all network I/O outside the lock, the 256-entry LRU, the per-seat high-water mark, the same-seed private RNG, the forfeit-vs-operational-abort distinction, and every set-once-outcome / room-scoped invariant; add no app hooks or injected prod state; the source engine / API / FIFO / SQLite / Canvas, the canonical wire schema/corpus, and the bounds / byte cap / rate / writer-wake / strict-model improvements are FROZEN; the frontend is unchanged
    - _Requirements: 16.1, 16.2, 17.3, 17.4, 17.5, 18.5, 18.6, 19.1, 19.2, 19.3, 19.4, 20.2, 20.8, 20.9, 22.3, 22.4, 22.5_
  - [x] 37.2 Write meaningful real-lifecycle backend tests asserting the actual survivor CLOSE, the normal-completion code, and the queue-full classification in `backend/tests/test_stage4_duel_delivery.py`, `backend/tests/test_stage4_duel_writer.py`, and `backend/tests/test_stage4_gravity.py`
    - Assert the survivor ACTUALLY reaches CLOSE with the documented standard code + LITERAL reason AND its endpoint reader/task is DONE after the close ack, following a real disconnect / transport 1007 / failed new-and-cached ACK / full queue in a STARTED room, with NO further input from either peer (not merely an internal room flag, an empty rooms map, a `send_failed` flag, or a tiny fixture bound); assert the simultaneous-natural-top-out gravity terminal closes BOTH peers 1000 `normal_completion` (and that `waiting_room_timeout` / `idle_timeout` / `server_shutdown` keep 1001) using a real consistent engine terminal fixture (active=None when game_over); assert the full-queue-ALONE case uses a TIMELY successful in-flight send (released well before the 5s bound) so the overflow -- not the send timeout -- is what classifies the peer unavailable and notifies the healthy idle peer, and that no winner is fabricated on a waiting / operational-abort / finished room; drain queued handshake/state/error frames before asserting CLOSE; diagnose hangs with `pytest -o faulthandler_timeout=15`, keep bounded per-command time, write raw outputs to files under distinct filenames, and preserve any failing output; do not remove or weaken any existing assertion
    - _Requirements: 16.6, 17.1, 17.2, 18.5, 18.6, 19.1, 19.2, 19.3, 22.4, 22.5, 22.6_

## Notes

- Tasks are ordered by milestone: M1 (tasks 1-6), then M2 (tasks 7-10), then M3 (tasks 11-17), then cross-cutting work (tasks 18-24).
- The verification (test-authoring) sub-tasks are mandatory, not optional; they cover the independently-expected rotation tests, the Canvas pixel evidence, and the duel wire/connection/property tests called out in Requirements 9, 14, and 20-23. The only optional/manual item is the two-browser production-proxy duel verification (task 23), kept as a manual probe left unchecked; the Stage 3 convention kept such manual/measurement probes as unchecked rather than marking them with `*`, and this plan follows that convention (no sub-task is postfixed with `*`).
- Each property-based test sub-task references a numbered Correctness Property from the design, is tagged `# Feature: tetris-stage4-option-a, Property N`, and runs at least 100 iterations.
- Each task references specific requirement clauses for traceability.
- Checkpoints (tasks 5, 9, 16, 24) and the per-milestone coverage checks (tasks 6, 10, 17) provide incremental validation boundaries; coverage/Sonar/Docker/CI/benchmark steps are described as checks to run in a later implementation invocation and assert no executed result or number.
- The engine stays pure: `rotation.py` imports only typing + domain/pieces, and the duel reuses the pure `engine.new_game`/`engine.tick` without coupling to solo persistence.
- The inherited spec directories under `.kiro/specs/tetris-stage1-option-a/`, `.kiro/specs/tetris-stage2-option-a/`, and `.kiro/specs/tetris-stage3-option-a/` are never edited, and the inherited solo HTTP contract, SQLite persistence, leaderboard, and restrictive CORS are preserved.
- The dated on-disk correction note for THIS planning-review correction was written first at `docs/native-checks/01-stage4-planning-review-corrections/NOTE.md`, satisfying Requirement 28 for this revision; it does not substitute for the per-correction notes required before any LATER code/test/config/benchmark change.

## Task Dependency Graph

M1 (rotation) must complete before M2 (Canvas), which must complete before M3 (duel); each milestone's coverage check depends on that milestone's implementation and test tasks. Test/coverage/benchmark tasks depend on the implementation tasks whose code they exercise.

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3"] },
    { "id": 3, "tasks": ["2.4", "2.5", "2.6", "3.1"] },
    { "id": 4, "tasks": ["3.2", "4.1"] },
    { "id": 5, "tasks": ["3.3", "4.2"] },
    { "id": 6, "tasks": ["4.3"] },
    { "id": 7, "tasks": ["4.4"] },
    { "id": 8, "tasks": ["6.1"] },
    { "id": 9, "tasks": ["7.1"] },
    { "id": 10, "tasks": ["7.2", "7.3"] },
    { "id": 11, "tasks": ["8.1"] },
    { "id": 12, "tasks": ["8.2", "8.3", "8.4"] },
    { "id": 13, "tasks": ["10.1"] },
    { "id": 14, "tasks": ["11.1"] },
    { "id": 15, "tasks": ["11.2", "12.1"] },
    { "id": 16, "tasks": ["12.2", "13.1"] },
    { "id": 17, "tasks": ["13.2", "14.1"] },
    { "id": 18, "tasks": ["14.2", "15.1", "15.2", "15.3"] },
    { "id": 19, "tasks": ["17.1"] },
    { "id": 20, "tasks": ["30.1", "34.1"] },
    { "id": 21, "tasks": ["30.2", "31.1"] },
    { "id": 22, "tasks": ["30.3", "32.1"] },
    { "id": 23, "tasks": ["30.4", "32.2"] },
    { "id": 24, "tasks": ["33.1"] },
    { "id": 25, "tasks": ["35.1", "36.1"] },
    { "id": 26, "tasks": ["35.2", "35.3", "35.4", "35.5", "35.6", "36.2"] },
    { "id": 27, "tasks": ["35.7"] },
    { "id": 28, "tasks": ["37.1"] },
    { "id": 29, "tasks": ["37.2"] },
    { "id": 30, "tasks": ["18.1", "18.2", "19.1", "19.2", "20.1", "21.1", "22.1", "23.1"] },
    { "id": 31, "tasks": ["20.2"] },
    { "id": 32, "tasks": ["20.3"] },
    { "id": 33, "tasks": ["20.4"] }
  ]
}
```



