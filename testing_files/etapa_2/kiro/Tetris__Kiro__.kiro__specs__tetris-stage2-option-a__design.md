# Design Document

## Overview

Stage 2, Option A extends the existing Stage 1 two-tier application (Python FastAPI backend, React + TypeScript frontend) as a brownfield change. The backend remains the single authoritative owner of all game state and rules; the frontend only renders backend state and forwards controls. No database, no authentication, in-memory state only.

Stage 2 adds, entirely inside the existing layered backend and the existing frontend structure:

- a **scoring** system (per-lock award by cleared-row count, multiplied by the pre-lock level),
- a **cumulative line counter** and derived **level**,
- a **progressive gravity interval** derived from level,
- a backend-owned **one-piece next-piece preview queue**,
- a **one-piece Hold** with once-per-active-piece availability,
- a new endpoint `POST /api/games/{id}/hold`,
- a frontend that renders the new fields, offers a Hold button and `C`/`c` key, and schedules gravity from `gravity_interval_ms` with strict request-ordering and lifecycle safety.

The design preserves every Stage 1 contract: `POST /api/games` returns HTTP 200; the board serializes to integer codes (`0` empty, `1..7` types); the active piece stays under the `active_piece` key; spawn origin is `(0,3)`; the seeded shuffled 7-bag and canonical unrotated shapes are unchanged; the lock -> clear -> spawn ordering is the baseline; and the 39 existing backend regression tests continue to pass (with one necessary exception: the single top-level key-set equality in `test_state_payload_shape` is widened to include the Stage 2 fields that Requirement 6.1 mandates, while that test's active-piece sub-shape assertion and all other behavioral assertions stay unchanged).

The queued/spawn/Hold rules, canonical shapes, and 7-bag behavior are taken exactly as frozen in the Stage 1 seed and this tool's own Stage 1 baseline: an incoming held piece that is blocked at the canonical spawn origin ends the game; `next_piece` remains a valid queued type after game over; and state reads, rejected actions, and post-game-over actions perform no extra generator draw. The preliminary obstruction assumptions are therefore resolved by the seed, not reopened here.

The engine functions remain pure (no FastAPI imports) so rules stay unit-testable, including the isolated-domain fixtures needed to verify 3- and 4-row clears that ordinary unrotated play cannot reach.

## Architecture

```
frontend (React + TS)
  |  HTTP JSON
  v
FastAPI app
  |-- api/games.py         # controllers: adds POST /{id}/hold; serializes Stage 2 fields
  |-- api/schemas.py       # GameStateOut gains score/total_lines/level/gravity_interval_ms/
  |                        #   next_piece/hold_piece/can_hold; board stays integer codes
  |-- store.py             # in-memory repository (unchanged responsibility)
  |-- rules/engine.py      # new_game/spawn/lock/tick/move extended; adds hold(); scoring+level
  |-- rules/scoring.py     # NEW: pure scoring/level/gravity formulas (small, isolated)
  |-- rules/pieces.py      # canonical shapes + seeded 7-bag (UNCHANGED)
  +-- domain/models.py     # Game gains next/hold/can_hold/score/total_lines/level/gravity fields
```

```
frontend/src
  |-- types.ts     # GameState gains the 7 new fields; new hold() direction/endpoint types
  |-- api.ts       # adds holdGame(); unchanged create/get/tick/move
  |-- useGame.ts   # generation-scoped FIFO queue, coalesced per-generation tick scheduler,
  |                #   dynamic interval, StrictMode-safe cleanup; exposes move/hold/restart
  |-- Board.tsx    # unchanged rendering of the 20x10 grid + active overlay
  |-- Preview.tsx  # NEW: renders a single piece type (next and hold) as a mini grid
  |-- Sidebar.tsx  # NEW (or inline in App): score/lines/level, next, hold, Hold button
  +-- App.tsx      # adds C/c key + Hold button wiring; keeps existing controls/labels
```

### Request flow (Stage 2 additions in **bold**)

1. `POST /api/games` -> `store.create()` -> `engine.new_game(seed)`; returns serialized state **including the 7 new fields**.
2. `GET /api/games/{id}` -> fetch; 404 if missing; returns serialized state **with no side effects (no generator draw, no counter change)**.
3. `POST /api/games/{id}/tick` -> `engine.tick(game)`; a resulting lock runs `engine.lock`, which **scores, updates total_lines/level/gravity, then spawns (consuming the preview and drawing one new preview)**.
4. `POST /api/games/{id}/move` -> validate direction; `engine.move`; `down` may lock (same scoring path); **soft drop never adds score**.
5. **`POST /api/games/{id}/hold` -> `engine.hold(game)`; returns serialized state in the same shape.**

## Components and Interfaces

### Domain model changes (`domain/models.py`)

`Game` gains fields (names chosen to match the API payload one-to-one):

```python
@dataclass
class Game:
    id: str
    status: Status
    board: Board
    active: Optional[ActivePiece]
    rng: random.Random
    seed: int
    bag: List[PieceType]
    # --- Stage 2 additions ---
    score: int = 0
    total_lines: int = 0
    level: int = 1
    gravity_interval_ms: int = 500
    next_type: PieceType = ...      # the queued preview piece (always set while readable)
    hold_type: Optional[PieceType] = None
    can_hold: bool = True
```

Notes:
- `next_type` is the authoritative preview. It is populated during `new_game` by drawing the first preview from the 7-bag and is refilled whenever a spawn consumes it. It remains a valid queued type after game over (no further draws occur).
- `ActivePiece`, `Board`, `PieceType`, `Status`, `empty_board`, `ROWS`, `COLS` are unchanged.
- No shape or generator change; `pieces.py` is untouched.

### Scoring formulas (`rules/scoring.py`, new, pure)

```python
LINE_SCORES = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}

def line_award(cleared: int, pre_lock_level: int) -> int:
    return LINE_SCORES[cleared] * pre_lock_level

def level_for(total_lines: int) -> int:
    return 1 + total_lines // 10

def gravity_ms_for(level: int) -> int:
    return max(100, 500 - 50 * (level - 1))
```

These are the only places the numeric controls live, so they can be unit-tested directly and reused by the engine. `level_for(0..9) == 1`, `level_for(10..19) == 2`; `gravity_ms_for(1) == 500`, `gravity_ms_for(2) == 450`, `gravity_ms_for(9) == 100`, `gravity_ms_for(10+) == 100`.

### Level and gravity boundaries (worked examples)

The leveling boundary this stage must make explicit is the **TOTAL LINES 9 -> 10 threshold**, because it is where the first level change occurs during ordinary play:

- **Primary threshold scenario (9 -> 10 lines).** Pre-lock state: `level == 1`, `total_lines == 9`. A lock clears exactly 1 row. The award uses the pre-lock level 1: `line_award(1, 1) == 100`, so `score += 100`. Then `total_lines` becomes `10`, `level` becomes `level_for(10) == 2`, and `gravity_interval_ms` becomes `gravity_ms_for(2) == 450`. This is the canonical acceptance scenario and is verified through the real production clear-and-score path (see Testing Strategy), not merely through the formula helpers.
- **Optional higher boundary (89 -> 90 lines).** If an additional single-step boundary example is retained, it uses `total_lines 89 -> 90`: pre-lock `level == 9`, a 1-row clear awards `line_award(1, 9) == 900` (score += 900), then `total_lines` becomes `90`, `level` becomes `level_for(90) == 10`, and `gravity_interval_ms` becomes `gravity_ms_for(10) == 100` (the floor). This example scores with pre-lock level 9 and is the correct way to exercise the level-9-to-10 crossing; it does not claim that a one-line clear can move `total_lines` from 9 directly into level 10.

### Engine changes (`rules/engine.py`, pure)

The queue model: the engine keeps exactly one previewed type in `game.next_type`. A helper encapsulates "consume preview and draw one new preview":

```python
def _draw_preview(game) -> PieceType:
    return pieces.next_type(game.rng, game.bag)   # exactly one generator draw

def _consume_preview(game) -> PieceType:
    incoming = game.next_type
    game.next_type = _draw_preview(game)           # refill: exactly one draw
    return incoming
```

- `new_game(game_id, seed)`:
  1. build empty board, `score=0`, `total_lines=0`, `level=1`, `gravity_interval_ms=500`, `hold_type=None`, `can_hold=True`;
  2. `game.next_type = _draw_preview(game)` (first preview draw);
  3. `spawn(game)` which consumes that preview as the first active piece and draws the next preview.

- `spawn(game)`: instead of drawing a type directly, it now **consumes the preview** (`piece_type = _consume_preview(game)`), places it at `(SPAWN_ROW, SPAWN_COLUMN)`; on overlap -> `game_over`, `active=None` (no extra draw beyond the one preview refill already performed). This keeps "normal spawn = exactly one preview draw" (Requirement 7.1).

- `lock(game)`:
  1. settle active cells into the board;
  2. `cleared = clear_lines(game)` (returns count -- already exists);
  3. `pre_lock_level = game.level`; `game.score += scoring.line_award(cleared, pre_lock_level)`;
  4. `game.total_lines += cleared`; `game.level = scoring.level_for(game.total_lines)`; `game.gravity_interval_ms = scoring.gravity_ms_for(game.level)`;
  5. `game.can_hold = True` (re-enable Hold for the next active piece);
  6. `spawn(game)` (consumes preview, draws one new preview, may end the game).

  Ordering is preserved: settle -> clear -> score/level/gravity -> re-enable hold -> spawn. Scoring uses the **pre-lock** level captured before step 4. At the 9 -> 10 lines threshold this yields the primary scenario above (award 100 at pre-lock level 1, then level 2 and gravity 450 ms).

- `tick(game)` / `move(game, direction)`: unchanged control flow; `down`/blocked-tick still route through `lock`. Soft drop adds no score because score only changes inside `lock` via `line_award` (Requirement 9).

- `hold(game)` (new):
  ```
  if game.status != "playing" or game.active is None: return          # Req 8.7, 10.1
  if not game.can_hold: return                                        # Req 8.4 reject, no draws
  current = game.active.type
  if game.hold_type is None:
      game.hold_type = current
      incoming = _consume_preview(game)          # one draw (Req 7.2)
  else:
      incoming = game.hold_type
      game.hold_type = current                   # swap, no draw (Req 7.3)
  cells = _absolute_cells(incoming, SPAWN_ORIGIN)
  if not _is_valid(game.board, cells):
      game.status = "game_over"; game.active = None   # Req 8.3
      game.can_hold = False
      return
  game.active = ActivePiece(incoming, SPAWN_ORIGIN, cells)
  game.can_hold = False                          # once per active piece (Req 8.1/8.2/8.5)
  ```
  `can_hold` returns to `True` only in `lock` when the next piece locks (Requirement 8.5). A held piece re-enters at the canonical spawn origin `(0,3)` in its initial orientation, and an obstructed spawn there ends the game (seed-frozen behavior).

State reads never call engine mutators, so reads cause zero generator draws and no counter changes (Requirements 6.5, 7.5, 10.3). Rejected Holds and post-game-over actions likewise make no extra draw.

### API schema changes (`api/schemas.py`)

`GameStateOut` gains the new fields; the board stays integer-coded and the active piece stays under `active_piece`:

```python
class GameStateOut(BaseModel):
    id: str
    status: str
    board: List[List[int]]
    active_piece: Optional[ActivePieceOut]
    # Stage 2:
    score: int
    total_lines: int
    level: int
    gravity_interval_ms: int
    next_piece: PieceType
    hold_piece: Optional[PieceType]
    can_hold: bool
```

`serialize(game)` maps `game.next_type -> next_piece`, `game.hold_type -> hold_piece`, `game.can_hold -> can_hold`, and copies the scalar counters. The existing board/active serialization is untouched, so the 39 regression tests (which assert the existing keys/values) continue to pass, except that the single exact top-level key-set equality in `test_state_payload_shape` must be widened to include the Stage 2 keys that Requirement 6.1 mandates (an exact-equality top-level key set cannot coexist with new required keys). That test's active-piece sub-shape assertion is preserved as-is, and the expanded top-level key set is additionally asserted in a *new* test; no behavioral regression assertion is weakened. The HTTP 200 create contract, the integer-coded board, the `active_piece` key, and the `(0,3)` spawn origin are all preserved.

### Controller changes (`api/games.py`)

Add one route, mirroring the existing pattern and 404 handling:

```python
@router.post("/{game_id}/hold", response_model=GameStateOut)
def hold_game(game_id: str) -> GameStateOut:
    game = _get_or_404(game_id)
    engine.hold(game)
    return serialize(game)
```

`POST /api/games` still returns HTTP 200 (FastAPI default for the existing decorator). Existing routes keep their signatures.

### Frontend changes

**`types.ts`** -- `GameState` gains:
```ts
score: number;
total_lines: number;
level: number;
gravity_interval_ms: number;
next_piece: PieceType;
hold_piece: PieceType | null;
can_hold: boolean;
```

**`api.ts`** -- add:
```ts
export async function holdGame(id: string): Promise<GameState> {
  const r = await fetch(`${API_BASE}/api/games/${id}/hold`, { method: "POST" });
  return asJson(r);
}
```

**`useGame.ts`** -- the core of the lifecycle-safety requirements. Design:

- **Generation token.** A `generationRef` integer increments on every create/restart and on unmount-disposal. Every async operation captures the generation value at dispatch and compares it to `generationRef.current` after `await fetch(...)` and again after `await response.json()`; if they differ, the result is discarded and must not touch state, the scheduling guard, or the timer (Requirements 16.2, 16.4, 16.5). Create/restart themselves bump the generation first, so an in-flight old Hold cannot adopt the new id or block the new queue (Requirement 16.2, 16.6).
- **FIFO queue per generation.** A promise-chain (`queueRef`) serializes manual mutating requests (move, hold) in submission order for the current generation. Enqueued work re-checks the generation before applying its result, so stale completions drop out (Requirements 16.1, 16.3). A fresh generation starts a fresh queue so old queued work cannot block the new game.
- **Coalesced tick scheduler.** Automatic ticks are owned per generation via a single `timeoutRef`. At most one tick is queued or in flight: a new tick is scheduled only after the previous tick's response resolves (or is discarded), using `setTimeout(gravity_interval_ms)` rather than a fixed `setInterval`, which both honors the dynamic interval (Requirement 15) and prevents bursts behind slow network calls (Requirement 16.7).
- **Exact cancellation + reschedule.** Manual input, restart, interval change, game over, and unmount call a single `cancelTick()` that clears exactly the pending `timeoutRef` and nulls it; scheduling then resumes (when still playing) with the latest `gravity_interval_ms` (Requirement 16.8). Because the scheduler keys off the applied state's interval, a level-up reschedules automatically.
- **StrictMode safety.** The effects use stable refs and idempotent setup/cleanup so React 18 StrictMode's mount->unmount->remount does not leave an orphan timer or a stale generation; cleanup increments the generation (or sets a disposed flag) so a late response from the first mount is discarded (Requirement 16.9). Restart goes through the same generation bump path.
- **Guard clearing rule.** Only a completion whose captured generation equals the current generation may clear the scheduling guard or pending timer; stale error/finally handlers return early (Requirement 16.5).
- **Post-result timeout reconciliation (R4/R5, Requirements 16.25-16.31).** The dispatch-time `cancelTick()` in `move`/`hold` (Requirement 16.19) is necessary but not sufficient when two or more manual mutating operations are already queued in FIFO order before either completes. Root cause in the pre-fix design: manual completions are serialized through the per-generation FIFO `enqueue`. When a current-generation manual completion applies while still playing, it calls `scheduleTick(gen)`, but `scheduleTick` early-returns when `timeoutRef.current !== null`. So when two manual operations are queued, the FIRST completion schedules a gravity timeout from its own (now stale) `gravity_interval_ms` (for example `500` ms); when the SECOND completion applies with a fresh interval (for example `450` ms) or a terminal `game_over` status, its `scheduleTick` sees the predecessor's live timeout and does not replace it. The result is R4 (a tick fires at the stale `t500` deadline instead of the fresh `450` ms-from-`t100` deadline at `t550`) and R5 (on `game_over` the manual path schedules nothing but never cancels the predecessor's timeout, so one tick fires after terminal state).

  The fix reconciles the exact pending gravity timeout on EACH current-generation authoritative manual completion. In the `enqueue` task body, after the generation re-check and after `applyIfCurrent`, the handler cancels the exact pending gravity timeout BEFORE deciding whether to reschedule: it calls `cancelTick()` (which clears only `timeoutRef`, never the `tickBusyRef` coalescing guard), then, only if the applied result's status is `playing`, calls `scheduleTick(gen)` so a fresh timeout is scheduled measured from now using the latest authoritative `gravity_interval_ms`. If the status is non-playing (`game_over`), it does NOT reschedule; the cancel alone leaves zero pending timeouts (R5).

  This reconciliation runs for every current-generation manual result, including one whose predecessor already created a timeout (R4). Because `cancelTick()` only touches `timeoutRef` and never `tickBusyRef`, it does not clear a coalescing guard owned by an in-flight or queued automatic tick (preserves R3 / Requirements 16.21, 16.24). Stale previous-generation completions still return early on the generation check and never touch the current generation's queue, guard, or timer (preserves R1 isolation / Requirements 16.10-16.15). The existing dispatch-time `cancelTick()` in `move`/`hold` stays (R2 / Requirement 16.19); the fix ADDS the post-result reconciliation, so the timeout is cancelled at dispatch AND after each current-generation authoritative manual result, each under a generation check, preserving FIFO ordering (Requirements 16.3, 16.16-16.18) and one-owned-tick coalescing (Requirement 16.22). The automatic-tick path is unchanged: it still nulls `timeoutRef` when it fires, takes `tickBusyRef`, and reschedules its single successor after its own response; a manual `cancelTick()` of a non-null `timeoutRef` therefore only ever cancels a scheduled-but-not-yet-fired timeout, never a guard owned by a tick already in flight.

Exposed API: `{ state, error, move, hold, restart }`.

**`App.tsx`** -- add a `keydown` branch for `"c"`/`"C"` that calls `hold()` when playing; add a Hold button wired to `hold()` and `disabled` when `!can_hold || status !== "playing"`; keep existing Left/Right/Soft Drop/Restart controls and English labels; title updated to Stage 2.

**`Sidebar`/`Preview`** -- render `score`, `total_lines`, `level` (and, for context, `gravity_interval_ms` optionally), the `next_piece` mini-grid, and the `hold_piece` mini-grid (empty state when `null`). Rendering only; no rule logic (Requirement 13.5).

## Data Models

- **Board:** unchanged `list[list[Optional[PieceType]]]`, serialized to integer codes.
- **Preview queue:** a single `PieceType` (`game.next_type`), not a list. "One-piece preview" means exactly one queued type; consuming it draws exactly one replacement.
- **Hold slot:** a single nullable `PieceType` (`game.hold_type`) plus a `can_hold` boolean gate.
- **Counters:** `score`, `total_lines`, `level`, `gravity_interval_ms` as integers on `Game`.

## Error Handling

- Unknown id on `GET`/`tick`/`move`/`hold` -> HTTP 404 (reuses `_get_or_404`).
- Invalid/missing `direction` on `move` -> HTTP 422 via Pydantic (unchanged).
- Hold while `can_hold` is `false`, or any action after `game_over` -> engine no-op; serialized unchanged state returned (Requirements 8.4, 8.7, 10.1).
- Hold whose incoming piece cannot be placed -> `game_over`, active cleared (Requirement 8.3).
- Frontend: non-OK responses throw and are surfaced via `error`; stale responses are silently discarded by the generation check and never shown as errors against the new game.

## Dependencies and Test/Coverage Tooling

The Stage 1 baseline pins exactly five backend runtime/test packages in `backend/requirements.txt` (`fastapi==0.115.6`, `uvicorn==0.34.0`, `pydantic==2.10.4`, `pytest==8.3.4`, `httpx==0.28.1`). **`pytest-cov` is not present**, and no `--cov` flag is available with this baseline. The frontend `package.json` pins React 18.3.1, Vite 5.4.11, TypeScript 5.6.3, and the Vite React plugin, with **no test framework**. These runtime pins must be preserved unless an explicit, compatible remediation is justified.

To emit coverage without assuming an unavailable flag, Stage 2 adds dev-only tooling in the implementation phase and documents exact installation and commands:

- **Backend coverage.** Add a dev requirements file `backend/requirements-dev.txt` that includes the runtime pins via `-r requirements.txt` plus a compatible `pytest-cov` pin (`pytest-cov==6.0.0`, which supports `pytest==8.3.4`). Coverage runs install this file first; plain `pytest` continues to work with only `requirements.txt`. The runtime pins in `requirements.txt` are left unchanged.
  - Install (coverage only): from `backend/`, `pip install -r requirements-dev.txt`.
  - Coverage command (only after the dev install): from `backend/`, `pytest --cov=app --cov-report=xml:../docs/coverage.xml`.
  - If, in a given environment, the dev install is not performed, coverage is obtained instead via the stdlib `coverage` run form documented in the README rather than claiming the `--cov` flag exists.
- **Frontend coverage.** Add Vitest + Testing Library as dev dependencies with the `@vitest/coverage-v8` provider so LCOV can be emitted for the full production `frontend/src` tree. Pins are chosen compatible with Vite 5 (Vitest 2.x) and are recorded in `package.json` during the implementation phase only.
  - Full production-src LCOV: from `frontend/`, `npm run test -- --coverage` producing `frontend/coverage/lcov.info` covering every module under `frontend/src` (no coverage exclusions of production files).

No coverage exclusions, weakened gates, or weakened tests are used to reach the quality thresholds. The reproducible frontend build (`npm run build`) and an honest `npm audit` remediation (see below) are produced alongside the coverage artifacts.

## Testing Strategy

Backend (`pytest`, extends existing files or adds Stage 2 files without altering the 39 legacy assertions):

- **Scoring (`rules/scoring.py`)**: `line_award` for 0/1/2/3/4 rows at several levels; `level_for` boundaries (9->1, 10->2); `gravity_ms_for` at levels 1, 2, 9, 10+ (100 ms floor).
- **Isolated-domain multi-row clears (Requirement 5)**: explicitly labeled fixtures build a `Game` with prefilled complete rows and invoke the real `engine.lock`/`clear_lines` path to verify 1/2/3/4-row awards and the resulting `total_lines`/`level`/`gravity_interval_ms`. These fixtures do not mutate canonical shapes, do not invent rotated or custom gameplay pieces, and do not claim rotated UI play. 0/1/2-row cases also covered via ordinary-style fixtures.
- **Primary 9 -> 10 lines threshold (runnable production path)**: a fixture sets `total_lines = 9`, `level = 1`, prefills exactly one complete row, and drives the real `engine.lock` path. It asserts the award is `100` (pre-lock level 1), then `total_lines == 10`, `level == 2`, and `gravity_interval_ms == 450`. This is a production-path test on `engine.lock`, not merely a `scoring` helper test.
- **Optional 89 -> 90 lines boundary (runnable production path)**: a fixture sets `total_lines = 89`, `level = 9`, prefills one complete row, drives `engine.lock`, and asserts the award is `900` (pre-lock level 9), then `total_lines == 90`, `level == 10`, and `gravity_interval_ms == 100`. This is the correct exercise of the level-9-to-10 crossing; no test asserts a 9->10 lines clear reaching level 10.
- **Preview draw counts (Requirement 7)**: assert exactly one generator draw on normal spawn and on first Hold, zero on occupied-slot swap, zero on rejected Hold / reads / post-game-over actions. Verified by comparing bag/rng progression or by counting via a spy around `pieces.next_type`. `next_piece` stays a valid queued type on game over.
- **Hold mechanics (Requirement 8)**: empty-slot hold, occupied swap, rejection when `can_hold` false, re-enable after lock, spawn-collision on incoming piece at the canonical origin -> game over, 404 on unknown id, no-op after game over, response shape.
- **State read purity (Requirement 6.5/10.3)**: repeated `GET` leaves all fields and generator state unchanged, with no extra draw.
- **API contract (Requirement 12)**: `POST /api/games` -> 200 with the 7 new fields present; board still integer codes; `active_piece` key retained; spawn origin `(0,3)`; new `hold` endpoint returns the same shape. The one legacy payload-shape test that asserts an exact top-level key set (`test_state_payload_shape`) has only that top-level equality widened to include the Stage 2 fields required by Requirement 6.1; its active-piece sub-shape assertion is preserved as-is, and the expanded top-level key set is additionally asserted in a **new** test. No behavioral regression assertion is weakened.
- **Regression**: run the full suite to confirm all 39 legacy test functions still pass, with the single documented top-level key-set widening in `test_state_payload_shape` being the only change to a legacy assertion.

Frontend (Vitest + Testing Library, added in the implementation phase as specified under Dependencies and Test/Coverage Tooling; it integrates natively with the existing Vite toolchain and emits LCOV via `@vitest/coverage-v8`):

- Dynamic gravity scheduling: interval derived from `gravity_interval_ms`; reschedules on change (including the 500 -> 450 change at the first level-up); stops on game over.
- Request ordering / lifecycle: delayed `fetch` and delayed `response.json()` across restart; FIFO manual actions; stale error/finally paths discarded; old-vs-new Hold (new game's Hold proceeds while old Hold pending); repeated restart; queue isolation across generations; tick coalescing (no burst after slow tick); exact timeout cancellation on manual input/restart/interval change/game over/unmount; StrictMode setup/cleanup/re-setup.
- Queued-predecessor gravity-timeout reconciliation (R4/R5, Requirements 16.25-16.31, verified by Requirement 18.17): two native production-path tests drive the real `useGame` hook and `api` transport boundary with independently deferred `fetch` headers and `response.json()` bodies and fake timers, without mocking the hook. Both tests use the shared scenario in which two manual mutating operations are already queued in FIFO order before either completes, the first (predecessor) completes at `t0` with `gravity_interval_ms` `500` and schedules a gravity timeout, and the second completes at `t100`.
  - **R4 level-up case.** The second completion returns a fresh `level` `2` / `gravity_interval_ms` `450` state. The test asserts that advancing `449` ms after the second completion at `t100` produces zero `POST /api/games/{id}/tick` requests, and that advancing one additional millisecond (the full `450` ms from `t100`) produces exactly one `/tick` request.
  - **R5 game-over case.** The second completion returns status `game_over`. The test asserts that advancing `1000` ms after the terminal second completion produces zero `/tick` requests.
- Rendering/controls: score/lines/level shown from state; next preview; hold display and disabled Hold button per `can_hold`; `C`/`c` key and Hold button click dispatch a hold request; existing controls still work; all visible text in English.
- Tests exercise production modules (`frontend/src/*`) so LCOV at `frontend/coverage/lcov.info` includes all production files; assertions observe requests/state/timer timing rather than restating implementation internals.

### Verification distinctions and evidence

- **Isolated-domain evidence** (engine/scoring fixtures, including 3-/4-row clears) is labeled and kept separate from **user-visible / browser evidence** (frontend tests and the production build) in the recorded results.
- Build/coverage/audit artifacts to produce in the implementation phase: backend `docs/coverage.xml`; frontend `frontend/coverage/lcov.info` covering the full production `frontend/src`; TypeScript production build log; `npm audit` with exact exit status (baseline: 3 vulns -- 1 moderate, 2 high -- plan a compatible, non-breaking remediation such as a patch-level `vite` bump within the allowed range and record the final audit honestly, with no suppression).
- The controlled Sonar gate (new coverage >= 80%, new duplication <= 3%, zero new violations) is honored without weakening thresholds, suppressing findings without evidence, excluding uncovered production files, or altering legacy regression assertions.
- When the R4/R5 production-path tests (Requirement 18.17) are added, existing frontend and backend test instances and their assertions are preserved (parametrization may change instance counts only with documented equivalent coverage). Every executable frontend production module, including `frontend/src/main.tsx`, remains in the LCOV report with no production exclusions, and the researcher harnesses, fixtures, reports, their config, and shared helpers remain untouched. React 18 / TypeScript behavior and the security-fixed explicit pins are preserved unless a documented compatible remediation is required.

### Documented commands

- Backend install (runtime): from `backend/`, `python -m venv .venv`, activate, `pip install -r requirements.txt`.
- Backend run: from `backend/`, `uvicorn app.main:app --reload`.
- Backend tests: from `backend/`, `pytest`.
- Backend coverage (implementation phase, after `pip install -r requirements-dev.txt`): from `backend/`, `pytest --cov=app --cov-report=xml:../docs/coverage.xml`.
- Frontend install: from `frontend/`, `npm install`.
- Frontend build: from `frontend/`, `npm run build`.
- Frontend tests + LCOV (implementation phase, after adding Vitest + `@vitest/coverage-v8`): from `frontend/`, `npm run test -- --coverage` producing `frontend/coverage/lcov.info`.
- Frontend audit: from `frontend/`, `npm audit --json`.

### Native Feature Spec lifecycle note

This design was reviewed and revised through the tool's native Spec workflow (requirements -> design -> tasks) with artifacts under `.kiro/specs/tetris-stage2-option-a/`. The preliminary artifacts were produced by an earlier headless invocation that, despite its CLI flag, ran in vibe mode; it is not claimed to have executed a native automated spec workflow. The present revision was performed in the native Spec context. Any actual limitation observed in automated workflow integration is recorded in the project research log rather than asserted here; the presence of the three Markdown artifacts alone is not treated as proof of workflow execution.
