# Design Document

## Overview

Stage 4, Option A extends this tool's own final Stage 3, Option A implementation (the Python FastAPI backend in `backend/` and the React + TypeScript client in `frontend/`) as a brownfield change. The backend remains the single authoritative owner of all solo game state and rules; the frontend renders backend state and forwards controls. Live solo game state stays in memory for the lifetime of a single backend worker, and completed-game high scores persist once-only to SQLite exactly as inherited.

Stage 4 adds three ordered milestones, each layered on top of the existing structure without disturbing it:

- **M1 (Rotation):** authoritative, server-side 90-degree rotation of the active piece, clockwise and counter-clockwise, computed by a new pure `Rotation_Engine` in `backend/app/rules/`. Rotation is defined by declared per-piece per-orientation occupied-cell data tables anchored to the inherited `spawn0` geometry, uses a horizontal-only wall-kick search in the exact order `0, -1, +1, -2, +2`, changes only orientation and (on a kick) origin, and is exposed through a new `POST /api/games/{id}/rotate` route that mirrors the inherited `move` conventions. Single-player keyboard and on-screen rotation controls route through the inherited `useGame.ts` generation / FIFO / stale-response machinery (Requirements 1-9).
- **M2 (Canvas):** replacement of the main 10x20 React DOM cell board (`Board.tsx`) with a Canvas 2D rendering surface for the active and settled blocks, keeping the React + TypeScript application and all accessible DOM controls, status, and panels. The Canvas redraws on every authoritative state change and on resize, is device-pixel-ratio aware at DPR 1 and 2, and clears residual pixels. The solo HTTP contract, SQLite persistence, and leaderboard are unchanged (Requirements 10-15).
- **M3 (WebSocket duel):** a two-player real-time duel over same-origin WebSockets, served by the same single FastAPI worker, with an in-memory `RoomManager` holding `Room`s, each with two `Seat`s and independent private per-seat game states that reuse the pure engine and are never registered in the solo store or persisted in the solo SQLite. The duel has per-board server-side gravity on an injectable monotonic clock, a bounded room lifecycle with idle cleanup, and a single versioned machine-readable wire contract. It is kept fully separate from the inherited solo HTTP game stores and the solo leaderboard (Requirements 16-23).

Stage 4 also plans, as specification-only statements of WHAT must hold, the regression-preservation and coverage obligations (Requirement 24), isolated Stage 4 containerization and CI (Requirement 25), an **authorized performance-benchmark harness implementation** (plus its own semantic self-checks) following this tool's own `perf/` convention, with the six measured production trials separately authorized and NOT executed under this authorization (Requirements 26-27), and an on-disk process guardrail that must precede any later corrective change (Requirement 28), within the retained scope boundaries (Requirement 29).

This document states WHAT will be built and HOW. It does **not** claim that any build, test, lint, audit, container run, container build, CI run, benchmark, timing trial, screenshot, coverage number, duplication number, or any other metric has been executed, produced, measured, or approved. Any such value is produced only by an actual execution during a later phase, and this document asserts no such execution or result. The inherited specifications under `.kiro/specs/tetris-stage1-option-a/`, `.kiro/specs/tetris-stage2-option-a/`, and `.kiro/specs/tetris-stage3-option-a/` are preserved byte-for-byte and are not edited by this stage.

### Preserved baseline (Stage 1 / Stage 2 / Stage 3 contracts, unchanged)

Stage 4 preserves every inherited contract. These are inputs, not features to re-derive, and are confirmed against the actual source in this workspace:

- **Stack and ownership.** A Python FastAPI backend holds authoritative in-memory solo game state and rules (`backend/app`); a React + TypeScript frontend renders state and forwards controls (`frontend/src`). Exactly one backend process owns in-memory games (`--workers 1`).
- **Board.** 20 rows by 10 columns (`ROWS = 20`, `COLS = 10` in `domain/models.py`). Row `0` top, row `19` bottom; column `0` leftmost, column `9` rightmost.
- **Pieces and `spawn0` geometry.** The seven standard tetrominoes. `SHAPES` in `rules/pieces.py` gives top-left-bounding-box-relative `(row, column)` offsets in the initial orientation: `I = [(0,0),(0,1),(0,2),(0,3)]` (row `0`), `O = [(0,0),(0,1),(1,0),(1,1)]`, `T = [(0,1),(1,0),(1,1),(1,2)]`, `S = [(0,1),(0,2),(1,0),(1,1)]`, `Z = [(0,0),(0,1),(1,1),(1,2)]`, `J = [(0,0),(1,0),(1,1),(1,2)]`, `L = [(0,2),(1,0),(1,1),(1,2)]`. Spawn origin is `SPAWN_ORIGIN = (SPAWN_ROW, SPAWN_COLUMN) = (0, 3)`. The `I` piece spawns on **row 0**; Stage 4 must not import any rotation table that assumes the `I` piece spawns on row 1.
- **Piece generator.** A seeded deterministic shuffled 7-bag (`refill_bag` / `next_type` in `pieces.py`); the same seed produces the same type sequence; exactly one preview piece is exposed (`next_type`).
- **Validity.** `engine._is_valid` accepts a cell set only when every cell has `0 <= row < 20`, `0 <= col < 10`, and `board[row][col] is None`.
- **Board serialization.** `schemas.serialize` maps board cells to integer codes via `TYPE_CODES` (`I=1, O=2, T=3, S=4, Z=5, J=6, L=7`), `0` = empty. The active piece is exposed under `active_piece` with `type`, `origin` (a 2-tuple), and `cells` (a list of 2-tuples). `GameStateOut` keys are exactly `id`, `status`, `board`, `active_piece`, `score`, `total_lines`, `level`, `gravity_interval_ms`, `next_piece`, `hold_piece`, `can_hold`.
- **Endpoints.** `POST /api/games` returns HTTP 200 (not 201) and accepts a bodyless request (`CreateGameRequest`, `extra="forbid"`). `GET /api/games/{id}`, `POST /api/games/{id}/tick`, `POST /api/games/{id}/move` (`MoveRequest`, `extra="forbid"`, `direction: Literal["left","right","down"]`), and `POST /api/games/{id}/hold` keep their request/response compatibility. `GET /api/high-scores` returns at most ten entries. `/health` is retained.
- **Lock / clear / spawn ordering.** `engine.lock` settles the active piece, calls `clear_lines`, applies scoring/level/gravity using the pre-lock level, re-enables Hold (`can_hold = True`), and then spawns the next piece. Scoring is `{0:0, 1:100, 2:300, 3:500, 4:800} * pre_lock_level`; `level = 1 + floor(total_lines / 10)`; `gravity_interval_ms = max(100, 500 - 50 * (level - 1))`; soft drop grants no points.
- **Finalization and persistence.** The single non-reentrant `finalization._LOCK` is acquired once per mutating request and held across mutation, finalization, and serialization; `GET` takes the same lock once for a coherent read-only snapshot without mutating or finalizing. Completed-game high scores persist once-only to SQLite (`persistence/store.py`) keyed by `game_id` with a UNIQUE constraint, with a pending-retry path and a controlled JSON 503 (`StorageError` -> HTTP 503) that leaks no internals.
- **CORS.** `main.py` builds a restrictive, configurable allow-list via `_resolve_allowed_origins` that fails closed (`CORSConfigurationError`) when a wildcard origin is combined with credentials; `allow_credentials=True`, `allow_methods=["GET","POST"]`, `allow_headers=["Content-Type"]`; default origins `http://localhost:5173,http://127.0.0.1:5173`.
- **Engine purity.** `rules/engine.py` imports only `random`, typing, and the domain/pieces/scoring modules; no FastAPI or `sqlite3`. Stage 4 keeps the engine pure so the rules (including rotation) stay unit-testable.
- **Frontend lifecycle safety.** `useGame.ts` generation tokens, per-generation FIFO serialization of all mutations, the coalesced per-generation automatic-tick scheduler, dynamic gravity scheduling from `gravity_interval_ms`, and stale-response discarding after both `fetch` and `response.json()` resolve are preserved.
- **Containers / perf convention.** Stage 3 published the frontend on host port `5183` behind an Nginx reverse proxy for `/api`; the `perf/` harness is a Playwright-driven headful-Chrome benchmark following the convention in `perf/README.md` and `perf/benchmark.mjs` + `perf/validate-instrument.mjs`. Stage 4 reuses these conventions with isolated resources and host port `5517`.

## Architecture

```
                         Host
                           |
                   publish 5517 (frontend ONLY)
                           v
+-----------------------------------------------------------------------+
|  Stage 4 Docker Compose network (isolated; backend NOT published)     |
|  project: tetris-stage4-kiro   network: stage4-internal               |
|                                                                        |
|  +--------------------------+     /api  (HTTP)      +---------------+  |
|  | frontend container       | -------------------->  | backend       | |
|  | (node build -> nginx)    |   /ws/duel (WS upgrade)| container     | |
|  | Canvas board + duel client| ------------------->  | single worker | |
|  | non-root user A          |   Host/Origin preserved| non-root user B| |
|  +--------------------------+                        +-------+-------+  |
|                                                              |         |
|                               named volume (isolated SQLite dir)       |
|                                    TETRIS_DB_PATH                       |
+-----------------------------------------------------------------------+

Frontend (React + TS, frontend/src)
  |  HTTP JSON  (solo: configurable API base, default same-origin "/api")
  |  WebSocket  (duel: same-origin ws(s)://<host>/ws/duel)
  v
FastAPI app (backend/app)  --- ONE worker owns solo games AND duel rooms ---
  |-- main.py                 # app + lifespan: init HighScoreStore (unchanged)
  |                           #   NEW: start RoomManager cleanup task; register
  |                           #   /ws/duel; restrictive CORS + WS Origin allow-list
  |-- api/games.py            # existing solo routes; NEW POST /{id}/rotate
  |-- api/high_scores.py      # UNCHANGED: GET /api/high-scores
  |-- api/schemas.py          # NEW RotateRequest (extra="forbid"); GameStateOut reused
  |-- ws/duel.py              # NEW: WebSocket endpoint /ws/duel; handshake + frames
  |-- ws/contract.py          # NEW: versioned wire-contract models (extra="forbid")
  |-- duel/rooms.py           # NEW: RoomManager, Room, Seat; bounded lifecycle
  |-- duel/gravity.py         # NEW: per-board server-side gravity (monotonic clock)
  |-- service/finalization.py # UNCHANGED: solo lock + finalize-on-game_over + retry
  |-- persistence/store.py    # UNCHANGED: HighScoreStore (stdlib sqlite3)
  |-- store.py                # UNCHANGED: solo in-memory game repository
  |-- rules/engine.py         # UNCHANGED pure rules + NEW pure rotate() (no new deps)
  |-- rules/rotation.py       # NEW pure Rotation_Engine: orientation tables + kicks
  |-- rules/pieces.py         # UNCHANGED SHAPES + seeded 7-bag
  +-- domain/models.py        # ActivePiece gains orientation; NEW duel board state

Out-of-band tooling (not shipped in runtime images, not in ordinary unit CI):
  perf/                       # Playwright headful-Chrome benchmark harness (AUTHORIZED IMPLEMENTATION; measured trials NOT executed)
  .github/workflows/*         # isolated Stage 4 backend/frontend/image checks + perf
  docs/native-checks/..       # dated on-disk process-guardrail notes (Req 28)
```

### Request / event flow (Stage 4 additions in **bold**)

1. Solo `POST /api/games`, `GET /api/games/{id}`, `/tick`, `/move`, `/hold` behave exactly as inherited (single `finalization._LOCK` boundary, 404/422/503 contracts unchanged).
2. **Solo `POST /api/games/{id}/rotate`** -> acquire `finalization._LOCK` once -> `_get_or_404` -> run the pure `engine.rotate(game, direction)` through the same `run_mutation` path -> serialize under the lock. Rotation never locks, never advances gravity, never scores, never touches the queue or Hold, so finalization observes no terminal transition from rotation alone. 200 on success, 404 for unknown id, 422 for a malformed body, 503 only if a concurrent terminal finalization is pending (behavior unchanged from `move`).
3. **Duel WebSocket `/ws/duel`** -> validate `Origin` against the exact proxy allow-list -> accept the upgrade -> handshake (client `hello` -> server `welcome` assigning a seat) -> `RoomManager` places the connection into a waiting or new `Room`. When both seats are connected the room starts; thereafter each seat's actions mutate only that seat's private board, and per-board gravity advances on the monotonic clock. State frames, acks, rejections, errors, and a terminal-outcome frame are emitted per the wire contract. The duel never touches `store.py` or the solo SQLite.

## Components and Interfaces

### Rotation engine (`app/rules/rotation.py`, new; pure)

`rules/rotation.py` is a new pure module imported by `engine.py`. It imports only typing and the domain/pieces modules (no FastAPI, no `sqlite3`, no new third-party dependency), preserving the engine's testability.

**Representation decision (Req 2.1, 2.2, 2.8).** Orientation is represented as an explicit **orientation index `0..3` plus declared per-piece per-orientation occupied-cell data tables**, each table anchored to the inherited `spawn0` geometry so orientation `0` equals the inherited `SHAPES` set. This representation is chosen over a computed pivot transform because the data tables are themselves the authoritative, independently-assertable specification: a test can compare the engine's cells for `(type, orientation)` against the same declared table without re-deriving them through the rotation algorithm under test (Req 9.1). The tables are declared as top-left-bounding-box-relative `(row, column)` offsets added to the piece origin, exactly like `SHAPES`, so orientation `0` is literally `SHAPES[type]` and the four-orientation table for each piece is a superset keyed by orientation index.

```python
# app/rules/rotation.py  (pure; imports only typing + domain + pieces)
from typing import Dict, List, Literal
from ..domain.models import Coord, PieceType

RotationDirection = Literal["cw", "ccw"]

# Candidate COLUMN offsets, in the exact evaluation order (Req 3.2, 3.4).
# Horizontal only: no row offset is ever applied (Req 3.3).
KICK_OFFSETS: List[int] = [0, -1, 1, -2, 2]

# ORIENTATIONS[type][orientation_index] -> list of 4 (row, col) offsets from the
# piece origin. orientation 0 == pieces.SHAPES[type]. Declared data, NOT derived
# at runtime from the algorithm under test (Req 2.8, 9.1).
ORIENTATIONS: Dict[PieceType, List[List[Coord]]] = { ... }  # see Data Models

def cells_for(piece_type: PieceType, orientation: int, origin: Coord) -> List[Coord]:
    """Absolute cells for a piece at (orientation, origin). Exactly 4, distinct (Req 2.6)."""
    row0, col0 = origin
    return [(row0 + dr, col0 + dc) for dr, dc in ORIENTATIONS[piece_type][orientation % 4]]

def next_orientation(orientation: int, direction: RotationDirection) -> int:
    """cw -> (o + 1) mod 4 ; ccw -> (o - 1) mod 4 (Req 1.1, 1.2)."""
    return (orientation + (1 if direction == "cw" else -1)) % 4
```

The engine gains one new pure function that mutates only orientation and origin:

```python
# app/rules/engine.py  (addition; still imports only random + typing + domain/pieces/scoring)
from . import rotation

def rotate(game: Game, direction: rotation.RotationDirection) -> None:
    """Rotate the active piece CW/CCW with a horizontal-only wall-kick search.

    No-op when not playing or there is no active piece (Req 1.8, 1.9). On a
    rejected rotation nothing changes (Req 4.*). Never locks, advances gravity,
    scores, or touches the queue/Hold (Req 5.*)."""
    if game.status != "playing" or game.active is None:
        return
    if game.active.type == "O": return  # O is a full no-op: orientation index and cells unchanged (Req 2.4)
    target = rotation.next_orientation(game.active.orientation, direction)
    row0, col0 = game.active.origin
    for dc in rotation.KICK_OFFSETS:                 # order 0, -1, +1, -2, +2
        kicked_origin = (row0, col0 + dc)            # COLUMN offset only
        cells = rotation.cells_for(game.active.type, target, kicked_origin)
        if _is_valid(game.board, cells):             # bounds + no locked overlap
            game.active.orientation = target         # accept: orientation + origin only
            game.active.origin = kicked_origin
            game.active.cells = cells
            return
    # Every candidate collided -> rejected rotation: leave everything unchanged.
```

Design details mapped to requirements:

- **Direction and orientation (Req 1.1, 1.2).** `cw` advances the index by one modulo four; `ccw` decreases it by one modulo four. The index is stored on the active piece (see Data Models).
- **Four orientations, four-cycle identity (Req 2.2, 2.3).** Each non-`O` table is a rigid 90-degree turn of the adjacent orientation about that piece's single declared fixed pivot (recorded alongside the table in Data Models), with no reflection or scaling. Four successive `cw` (or `ccw`) turns with no intervening collision return the orientation index and the occupied-cell set to the start, because `(o + 4) mod 4 == o` and the table at `o` is fixed.
- **`O` no-op (Req 2.4).** O rotation is a FULL no-op in both directions: `engine.rotate` detects `game.active.type == "O"` and returns immediately WITHOUT changing the orientation index and WITHOUT changing the occupied cells, so an O rotation never mutates any field. Consequence for M3 duel semantics: an O rotation action is a legal no-op that the server acknowledges with `applied=true, no_op=true` and the UNCHANGED authoritative revision (no revision increment), exactly like a fully rejected rotation.
- **`I` uses `spawn0` row-0 geometry (Req 2.5).** `ORIENTATIONS["I"][0] == [(0,0),(0,1),(0,2),(0,3)]` (horizontal on row 0), and the vertical orientations are derived from that row-0 spawn, never from an SRS table that assumes the `I` spawns on row 1 (shown explicitly in Data Models).
- **Exactly four distinct in-bounds cells (Req 2.6).** Every declared orientation has four distinct offsets; `_is_valid` enforces that the absolute cells are within rows `0..19` / columns `0..9` and do not overlap a locked cell when the rotation is accepted.
- **cw then ccw identity (Req 2.7).** `next_orientation(next_orientation(o, "cw"), "ccw") == o`, and when no kick is needed the origin is unchanged, so an immediate `cw` then `ccw` restores the index and the occupied-cell set.
- **Wall kick (Req 3.1-3.6).** The loop evaluates `KICK_OFFSETS` in the exact order `0, -1, +1, -2, +2`, applies a **column-only** offset to the rotated set, accepts the **first** candidate that is fully in bounds and overlaps no locked cell (and evaluates no later candidate), and sets both orientation and the accepted kicked origin. If every candidate collides the rotation is rejected and nothing changes.
- **Rejected-rotation immutability and side-effect isolation (Req 4.*, 5.*).** On rejection the function returns before any mutation. On acceptance the only mutated fields are `active.orientation`, `active.origin`, and the derived `active.cells`; `score`, `level`, `total_lines`, `next_type`, `hold_type`, `can_hold`, `gravity_interval_ms`, `board`, and `status` are untouched. Because `rotate` never calls `lock`, `tick`, or the generator, it cannot award points, advance gravity, or draw a piece.
- **Spawn and Hold orientation reset (Req 6.*).** Both Hold paths reset orientation to `0`. `engine._place` sets the new active piece's `orientation = 0` at `SPAWN_ORIGIN` for every entry path (queue spawn, first-Hold, and swap-Hold), so a piece always enters play in orientation `0` regardless of the orientation it held before. The inherited once-per-active-piece `can_hold` rule is unchanged.
- **Rotated geometry under movement and locking (Req 7.*).** `engine.move` and `engine.tick` translate `active.cells` by the move delta and leave `active.orientation` unchanged; `engine.lock` settles whatever `active.cells` currently is (the rotated set) and then applies the inherited lock/clear/score/level/gravity/Hold/spawn ordering unchanged. A blocked downward tick locks without changing the orientation; a soft drop grants zero points.

### Rotation API surface (`app/api/schemas.py` + `app/api/games.py`)

A new strict request model and a new route, consistent with `move`:

```python
# app/api/schemas.py  (addition)
class RotateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")       # reject extra fields (Req 1.6)
    direction: Literal["cw", "ccw"]                  # exactly two documented values (Req 1.5)
```

The two documented, case-sensitive direction strings are **`"cw"`** (clockwise) and **`"ccw"`** (counter-clockwise). Any other string, a missing field, a non-string value (boolean, number, array, object, null), or any extra field fails Pydantic validation and yields HTTP 422 (Req 1.5, 1.6).

```python
# app/api/games.py  (addition; reuses the single-lock _mutate helper)
@router.post("/{game_id}/rotate", responses=_STORAGE_503_RESPONSES)
def rotate_game(game_id: str, body: RotateRequest) -> GameStateOut:
    """Rotate the active piece CW/CCW and return the updated state."""
    return _mutate(game_id, lambda g: engine.rotate(g, body.direction))
```

- **Success shape (Req 1.3, 1.4).** The route returns the `GameStateOut` model via the existing `serialize`, so the response contains exactly the eleven inherited keys and HTTP 200, identical to `move`.
- **404 / 422 (Req 1.6, 1.7).** `_mutate` calls `_get_or_404`, so an unknown id yields 404 with no state change; a malformed body yields 422 before any engine call, so no authoritative field changes.
- **`game_over` and no-active no-op (Req 1.8, 1.9).** `engine.rotate` returns immediately when `status != "playing"` or `active is None`; `_mutate` then serializes the current (unchanged) terminal or no-active state, returning status `game_over` or the current state with no field changed.
- **503 unchanged (Req 1.*, 4.*).** Rotation never drives a terminal transition, so the only way the shared `_mutate` path returns 503 is an inherited pending finalization on an already-terminal game; rotation itself adds no new 503 condition.
- **English (Req 1.10).** All rotation-related labels, statuses, and messages are in English.

### Rotation controls in the frontend (`frontend/src`)

- **`api.ts`** gains `rotateGame(id, direction: "cw" | "ccw")` that `POST`s `{ direction }` to `${API_BASE}/games/{id}/rotate`, mirroring `moveGame`.
- **`useGame.ts`** gains a `rotate(direction)` callback built exactly like `move`: it captures the current generation, no-ops when `idRef.current` is null, calls `cancelTick()` at dispatch time, and enqueues onto the per-generation FIFO via `enqueue`, reusing the inherited manual-action timeout ownership and reconciliation: `cancelTick()` cancels the exact current-generation pending automatic tick at dispatch, then `enqueue` reschedules at most one replacement tick derived from the authoritative `gravity_interval_ms` (or none on a terminal result). It introduces no competing scheduler and no second queue, and does not itself tick, lock, change `gravity_interval_ms`, or consume RNG, while preserving the inherited stale-response/generation/coalescing protection (Req 8.5, 8.7). No new machinery is introduced.
- **`App.tsx`** binds keyboard and on-screen controls (Req 8.1-8.4, 8.6): `ArrowUp` -> one `rotate("cw")` per key-down; `Z`/`z` -> one `rotate("ccw")` per key-down; two accessible on-screen buttons (one CW, one CCW, each a real focusable `<button>` with an English accessible name) each issue one corresponding rotation per activation. All rotation entry points are gated on `state.status === "playing"`, so none fires when the game is not playing. The inherited left/right/soft-drop/Hold/restart controls are unchanged.

### Canvas board (`frontend/src`, M2)

`Board.tsx` (the DOM cell grid) is replaced by a Canvas 2D component that draws the same authoritative state; the inherited per-type colors in `Board.tsx` (`COLORS` / `TYPE_CODE`) are preserved as the Canvas palette so active and settled blocks look the same and remain visually distinguishable.

**Component shape.**

```tsx
// frontend/src/CanvasBoard.tsx  (replaces the DOM cell grid of Board.tsx)
interface CanvasBoardProps { state: GameState; }
export function CanvasBoard({ state }: CanvasBoardProps) {
  const ref = useRef<HTMLCanvasElement | null>(null);
  // 1) measure layout box; 2) size backing store = CSS px * devicePixelRatio;
  // 3) draw on every state change and on resize (see below).
}
```

- **Real Canvas 2D rendering (Req 10.1-10.4).** The board is drawn with real Canvas 2D drawing calls (`fillRect` per cell against `ctx.fillStyle`) obtained from the live `HTMLCanvasElement.getContext("2d")`; it is never a grid of per-cell DOM elements and never a set of data-attributes standing in for pixels. The renderer draws exactly the 200 settled cells from the authoritative `state.board` (code `0` -> the inherited background color, codes `1..7` -> the inherited per-type `COLORS`), then overlays the active piece's rotated occupied cells (`state.active_piece.cells` at its current origin) using that type's color, so active and settled blocks use the inherited palette and stay visually distinguishable. The active piece's geometry is whatever the backend reports after rotation/movement, so the rendered shape matches the authoritative rotated orientation.
- **Reset + clear the whole backing store each draw (Req 11.6).** Every draw first calls `ctx.setTransform(1, 0, 0, 1, 0, 0)` (reset to identity) and `ctx.clearRect(0, 0, backingWidth, backingHeight)` over the entire backing store, then re-applies the DPR scale, then draws the current state. This guarantees no cumulative scaling across redraws and no residual pixels from any prior state inside the board area; each frame is a complete redraw of the current authoritative state, not an incremental overlay.
- **Redraw triggers (Req 11.1, 11.2).** The component redraws in a `useEffect` keyed on the authoritative `state`, and in a `ResizeObserver` callback on the canvas layout box. Because `useGame` produces a new `GameState` for every applied authoritative change, the Canvas redraws on: same-count movement (left/right/soft-drop with the piece count unchanged), a CW rotation, a CCW rotation, a gravity tick, a lock, a line clear, and a restart. Each such change triggers exactly one redraw from the new state. A no-op rotation (O piece or fully rejected) produces an unchanged authoritative state, so it needs no visible change.
- **DPR 1 and 2, backing store + transform (Req 11.3, 11.4, 11.5).** The backing-store dimensions are computed as `round(cssWidth * devicePixelRatio)` by `round(cssHeight * devicePixelRatio)` and set on `canvas.width` / `canvas.height`, while the CSS box stays at `cssWidth` by `cssHeight`. After sizing, the transform is reset and the context is scaled by `devicePixelRatio` so one logical cell maps to the same CSS area at DPR 1 and DPR 2. The board is crisp at both ratios and the full 10x20 board (all 200 cells) renders within the layout box without clipping or stretching at both ratios. When the measured pixel width or height of the layout box changes from its previously measured value (a meaningful resize), the component recomputes the backing-store size, resets the transform, re-applies the DPR scale, and redraws; an unchanged measurement does not force a resize-driven resize of the backing store.
- **Safe handling and cleanup (Req 10.5, 12.5).** If `getContext("2d")` returns `null` (no 2D context), the component renders the canvas element and its accessible surroundings and skips drawing without throwing. If `ResizeObserver` is unavailable in the environment, the component still draws from state on every state change and simply does not subscribe to layout-box resizes (it does not throw and does not fall back to a DOM cell grid). On unmount the component disconnects any `ResizeObserver` it created and drops the canvas ref so no observer or draw callback fires after unmount. None of this adds any production debug hook, state-injection hook, hidden React accessor, network interception, or test-only endpoint.
- **React + TS preserved (Req 10.5).** The Canvas is a React + TypeScript component; the rest of the application (controls, panels, hooks) is unchanged.

**Accessible DOM preserved (Req 12.*).** The Canvas replaces only the visual cell grid. The frontend keeps accessible DOM controls for left, right, soft drop, CW rotation, CCW rotation, Hold, and restart, and accessible DOM elements for score, level, line count, Hold piece, next-piece preview (`Preview.tsx`), leaderboard/ranking (`HighScores.tsx`), and game status. A DOM status region exposes the game status (playing / game_over) as text so status never depends solely on Canvas pixels. Keyboard controls behave exactly as inherited for left/right/soft-drop/Hold/restart plus the Stage 4 rotation keys, and the inherited per-generation FIFO and stale-response protection in `useGame.ts` are preserved.

**Preserved solo contract and persistence (Req 13.*).** The Canvas is a rendering change only: the solo HTTP contract (including the new rotate route), the SQLite persistence and once-only finalization, and `GET /api/high-scores` ordering and shape are unchanged; the backend remains the single authoritative owner and the Canvas renders only backend-reported state.

**Superseded DOM-cell assertions and pixel evidence (Req 14.*).** The Canvas migration removes the 200-element per-cell DOM grid, so the inherited `frontend/src/Board.test.tsx` DOM-cell assertions are intentionally superseded. The exact superseded assertions and their Canvas semantic replacements are:

| Inherited `Board.test.tsx` assertion | What it covered | Canvas semantic replacement |
| --- | --- | --- |
| "renders a 20x10 grid of cells" — `.board` has exactly `200` child elements | the board is drawn as 200 positioned cells | the renderer issues one fill per board cell (200 cells) plus the active-piece overlay against the live 2D context — covered by Canvas **behavioral** draw-call assertions, and the correct per-type colors at the correct board positions are confirmed by later **independent** production-bundle pixel evidence |
| "renders with a null active piece (settled board only)" — the same 200-child DOM grid with no active piece | settled cells render with no active overlay | with `active_piece === null` the renderer draws the 200 settled cells and issues no active-piece overlay — covered by Canvas behavioral draw-call assertions plus the same independent pixel evidence |

Their semantic coverage — that settled cells and the active piece render at the correct board positions with the correct inherited per-type colors — is replaced by **Canvas pixel evidence**: actual rendered pixel masks or screenshots captured from the **unmodified production bundle** tied to meaningful authoritative states (a spawned piece, a rotated piece, a moved piece, a locked piece, and a cleared-line state). Mock draw-call records, DOM data attributes, and fabricated RGBA are explicitly **not** treated as pixel evidence. Where a state such as a multi-line clear is hard to reach through ordinary play, the production clear path is driven with an explicitly-declared **isolated own-engine fixture** that is never claimed to be the production backend. Native unit fixtures MAY still verify renderer draw calls, 2D-context setup/cleanup, and safe behavior when the 2D context is absent, but those are **behavioral coverage only, not pixel proof**. No production debug hooks, backend-state injection hooks, hidden React accessors, network interception, fake RGBA, or data-attributes standing in for pixels are introduced into the production bundle. The immutable prior Stage 3 and M1 evidence is preserved and not rewritten; the independent researcher separately tests actual byte-bound production-bundle pixels and the isolated own-engine clear fixtures **after** this milestone closes.

**Layout (Req 15.*).** At a `1280x900` CSS-pixel viewport, at DPR 1 and DPR 2, the active solo board and all relevant controls and panels fit entirely within the viewport with no clipping, no control or panel overlapping another, and no page overflow (the document `scrollHeight` is `<= 900` at `1280x900`). As part of M2 layout, two inherited defects observed on the M1 frontend are fixed: (1) the inherited solo view overflows the viewport height — `scrollHeight` is `964` at `1280x900` (64px over) — and (2) the visible page title still reads "Stage 2" (`frontend/src/App.tsx` currently renders `<h1>Tetris - Stage 2</h1>`). The layout fix is a **real M2 layout change** that makes the board and controls/panels fit within `1280x900` while keeping usable, readable controls and cell geometry, and the title is updated to "Stage 4". The fix is explicitly **not** shrinking screenshots or the viewport, **not** relaxing or deleting the layout/overflow assertion, and **not** degrading cell/control readability to force a pass.

The solo single-player view is a distinct, independently usable view; when a duel is active the solo view remains reachable, and the layout never requires three boards to render simultaneously.

**Duel viewport (design-only, NOT implemented in M2).** The later M3 duel view, when a duel is active, will show **both** duel boards together with their controls and panels inside the same `1280x900` viewport, with the solo view reachable as a separate mode. There is no requirement to render three boards (two duel boards plus the solo board) simultaneously: solo and duel are distinct modes. This paragraph is a design statement about M3 layout and is not implemented, built, or measured in this M2 invocation.

### Duel transport and rooms (`app/ws/`, `app/duel/`, M3)

The duel is served by the **same single FastAPI worker** that serves the solo HTTP API, over a same-origin WebSocket endpoint **`/ws/duel`**, proxied through Nginx (see Deployment). It adds four new backend modules and touches `main.py` only to register the endpoint, start the cleanup task, and apply the WS Origin allow-list. The solo `store.py`, `finalization.py`, `persistence/store.py`, and `rules/engine.py` are reused but never coupled to the duel's persistence (there is none) — duel rooms hold their own private per-seat `Game` objects created with the pure `engine.new_game`.

**`RoomManager` / `Room` / `Seat` (`app/duel/rooms.py`, new).**

```python
class Seat:
    seat_id: Literal["A", "B"]      # stable per-room seat identity
    game: Game                      # private per-seat engine state (engine.new_game)
    rng_seed: int                   # equal to the room seed; each seat owns an independent random.Random (same start sequence, independent advancement)
    revision: int                   # authoritative per-board revision, monotonic
    reply_cache: "OrderedDict[str, AckOrReject]"  # bounded 256-entry per-seat idempotency reply cache (most-recent action_ids -> their ack/reject)
    last_action_seq: int            # per-seat monotonic high-water mark of the highest accepted/acknowledged action ordinal
    outbound: Deque[ServerFrame]    # bounded per-seat outbound queue
    connected: bool
    gravity_due_monotonic: float    # next due time on the injectable clock

class Room:
    room_id: str                    # bounded-length id
    seats: dict[str, Seat]          # at most two seats: "A", "B"
    seed: int                       # room seed; per-seat seeds derived from it
    status: Literal["waiting", "playing", "finished"]
    state_lock: threading.Lock      # SHORT per-room lock for snapshotting only
    created_monotonic: float
    last_activity_monotonic: float
    finished_monotonic: float | None
    outcome: TerminalOutcome | None # set exactly once

class RoomManager:
    rooms: dict[str, Room]
    clock: Callable[[], float]      # injectable monotonic clock (Req 19.4, 18.1)
    # bounds (Req 22.3): max_rooms, room_id_max_len, max_msg_bytes,
    #   action_rate_per_seat, outbound_queue_depth, handshake_timeout, idle_timeout
    def assign_seat(self, room_id, origin) -> (Room, Seat): ...
    def cleanup_tick(self) -> None: ...   # periodic, runs even without traffic
```

- **Transport and worker model (Req 16.1, 16.6).** `/ws/duel` runs on the one worker alongside the solo API. Solo HTTP games continue to work independently while a duel is in progress; the duel adds no additional process.
- **Private per-seat state (Req 16.2, 16.3, 17.5).** Each `Room` holds up to two `Seat`s, each owning an independent private `Game`. A seat's state is shared with the opponent only through broadcast state frames defined by the wire contract. A move/rotation/soft-drop/Hold/lock on one seat affects only that seat's `Game`.
- **No solo registration or persistence (Req 16.4, 16.5, 23.*).** Duel `Game`s are never inserted into `store.py`, never exposed via `GET /api/games/{id}`, never written to the solo SQLite, and never added to the leaderboard. The inherited restrictive HTTP CORS policy and the solo SQLite persistence/finalization are retained unchanged. Solo SQLite data is never deleted, moved, or cleared outside the duel's own declared temporary test fixtures.

**Seeding and independent progression (`app/duel/rooms.py` + `rules/engine.py`, Req 17.*).** When both seats are connected the room starts exactly two distinct seats. Each seat begins with **this tool's same initial seeded 7-bag sequence**: both seats receive the IDENTICAL room seed, and each seat constructs its OWN independent `random.Random` instance (its own `Game` via `engine.new_game(game_id, room_seed)`), so BOTH boards start with this tool's same initial seeded 7-bag sequence while advancing independently. Advancing one seat's queue/Hold/lock never advances the other seat's queue or the solo sequence, because each seat owns a private RNG and no global RNG is shared. Both seats' identical starting 7-bag sequence and each seat's independent Hold-path progression are TEST OBLIGATIONS (declared, not fabricated results). Because every seat has its own `random.Random` inside its own `Game`, the two seats advance their queues, first-Hold availability, Hold swaps, and lock consumption **independently**, and nothing touches or alters the solo global sequence or couples the seats. The duel never shares a global RNG.

**Per-board server-side gravity (`app/duel/gravity.py`, Req 18.*).** Gravity is applied on the server, independently per board, using a per-board due time derived from that board's `level` and the inherited formula `gravity_interval_ms = max(100, 500 - 50 * (level - 1))`. A gravity evaluation reads the injectable monotonic clock, advances only boards whose `gravity_due_monotonic` has elapsed (calling `engine.tick` on that seat's `Game`), and recomputes the next due time from the current `gravity_interval_ms`. The evaluation advances **all due boards before deciding a single outcome**, so a simultaneous top-out of both boards in the same evaluation is a **DRAW**; if exactly one board remains playable the surviving seat wins; an active seat that disconnects while the duel is in progress forfeits, resolving the duel **exactly once** (a `finished` room is never resolved a second time on a later event). On a terminal outcome the room stops advancing gravity and emits the terminal-outcome frame.

**Waiting/start semantics and pre-start actions (`app/ws/duel.py` + `app/duel/rooms.py`, Req 17.1, 20).** A seat learns that the peer joined and the room started through the EXISTING authoritative `state` frame, which carries a REQUIRED `room_status` field (enum `waiting`/`playing`/`finished`) on EVERY state frame alongside the per-seat board `status` (`playing`/`game_over`). `room_status` being required on every `state` frame (not optional) removes the prior contradiction of relying on an optional field; the schema lists `room_status` in `StateFrame.required` and every example carries it. No undocumented "magic" event and no client prediction is introduced. The start transition is emitted MANDATORILY and exactly: when seat A connects to a one-seat room the server sends a `welcome` (`room_status: "waiting"`) followed by a `state` frame carrying `room_status: "waiting"`; when seat B connects and the room transitions to `playing`, the server MUST emit, to BOTH seats, a `state` frame carrying `room_status: "playing"`, so each seat observes the transition through the authoritative `state` frame it already consumes; the terminal transition to `finished` is likewise carried on the `state`/`outcome` frames both seats receive. An action received while the room `room_status` is `waiting` (a PRE-START action) is REJECTED with the reason `not_started` and is NOT applied: it does not mutate the board, does not advance the per-seat `revision`, and does NOT consume the seat's action ordinal / high-water mark. This is an HONEST, explicitly-stated exception to "every well-typed owned action is cached": the room-status/start gate is check step (4), which runs BEFORE the reply-cache lookup (step 5) and the ordinal/high-water stage (step 6), so a `not_started` reject is deliberately NOT cached and does NOT consume the ordinal - the action's format and seat ownership are validated, but the gate stops it before the cache/ordinal/revision stages, so no sequence inconsistency arises. `not_started` is a `Reject.reason` member justified because no existing member expresses "the room has not started" (`room_closed` is an `ErrorFrame` reason meaning the room is gone, a different condition).

**Room lifecycle, cleanup, and concurrency (`app/duel/rooms.py`, Req 19.*, 22.3, 22.4).** `RoomManager.cleanup_tick` runs **periodically even when no new traffic arrives**, scheduled from the lifespan task against the injectable clock on a fixed **1-second cleanup cadence with a 1-second deadline slack**. Retention is bounded and keyed by STATUS so the timeouts never contradict one another: a `waiting`/inactive room uses the **120-second waiting/inactive retention** (a `waiting` room has NO gravity, so its lifetime is governed solely by this retention); a `playing` room uses the **60-second idle timeout** measured from `last_activity_monotonic`, and a gravity-driven state change during `playing` DOES refresh `last_activity_monotonic` (so an actively-progressing board is never reaped as idle); a `finished` room uses the **15-second finished retention** to let terminal frames drain, after which its sockets are closed with code **1000 (normal completion)** and its data is released. The per-seat inbound action rate limit is a **FIXED 1-second window counting inbound action frames only** (handshake and other non-action frames are not counted); 20 actions per seat per second. The per-frame outbound **SEND timeout is 5 seconds**; a send that exceeds it is a FAILED SEND. When a seat's 64-frame outbound queue is FULL, or a send fails, the server treats the peer as a failed/slow peer, stops enqueuing to it, and schedules the room for cancellation cleanup, never blocking the worker. A cancelled room, a full/stalled queue, a failed send, and server shutdown all release the room's resources (room entry, gravity task, sockets) with no leaked room, task, or socket. All scheduling uses the injectable monotonic clock so tests advance time deterministically. When mutating a room the manager holds a **short per-room `state_lock` only to take a consistent snapshot**, then performs **bounded, ordered outbound I/O OUTSIDE that lock**; it never holds a global lock across outbound I/O, so one slow or blocked peer cannot stall the whole worker. A player who restarts after a duel gets a fresh room or a fresh solo game; the finished room's state is never reused.

**Failed-send / slow-peer classification, and operational-abort close reasons (literal strings).** A failed send or a full/stalled outbound queue on a STARTED (`playing`) room is treated as a GAMEPLAY FORFEIT: the unavailable seat forfeits, the duel resolves EXACTLY ONCE as a `forfeit` outcome (the other seat wins), and that seat's socket is then closed with the standard going-away code `1001` carrying the literal close reason string `"peer_unavailable_forfeit"`. This is a gameplay outcome and uses the normal `Outcome` resolution (all due boards are still evaluated before the single outcome is decided). By contrast, a WAITING room that is cancelled or times out (it never started, so there is no game to resolve) is an OPERATIONAL ABORT, NOT a gameplay outcome: its sockets are closed with code `1001` carrying the literal reason `"waiting_room_timeout"` and NO gameplay winner is fabricated. A `finished` room that has drained its terminal frames is closed with code `1000` carrying the literal reason `"normal_completion"`. Server shutdown closes with code `1001` carrying the literal reason `"server_shutdown"`, and a `playing` room reaped for idleness closes with code `1001` carrying the literal reason `"idle_timeout"`; a handshake that does not complete in time closes with code `1001` carrying the literal reason `"handshake_timeout"`. These shared-`1001` reasons are distinguished by their literal reason strings, not by the numeric code. In every case the room entry, gravity task, and ALL sockets are released with no leak, and no schema-invalid scalar is ever emitted. A forfeit/terminal transition MUST also END the SURVIVING peer: after the terminal frames are enqueued to the remaining peer through its single ordered writer, that peer's socket is CLOSED (the survivor's normal completion is code `1000` `normal_completion`; the unavailable/offending seat keeps `1001` `peer_unavailable_forfeit`) and its reader terminated WITHIN the bounded finished retention, WITHOUT any further input from either side and WITHOUT relying on a future gravity step; the room entry is never released in a way that orphans an unclosed survivor socket from the periodic retention cleanup (a normal terminal MAY drain its queued frames before the close, but never requires recipient input to close).

### Duel wire contract (`app/ws/contract.py`, new; Req 20, 21)

The SINGLE canonical, machine-readable contract is now defined as a JSON Schema (Draft 2020-12) file at `.kiro/specs/tetris-stage4-option-a/contract/duel-wire.schema.json`, with a SEPARATE valid examples corpus at `.kiro/specs/tetris-stage4-option-a/contract/duel-wire.examples.json` (positive and negative cases). The Pydantic models in `app/ws/contract.py` MUST conform to that schema, and the JSON examples shown inline below are illustrative and kept consistent with the canonical schema/corpus. These concrete bounds are stated now (no deferral): protocol_version = 1; room_id is a string of length 1..64; `action_id` is a string of length 1..64 that ADDITIONALLY follows the canonical FULL-STRING grammar `^(A|B)-([1-9][0-9]{0,14})(?![\s\S])` (described below; the trailing negative lookahead `(?![\s\S])` replaces `$` so a trailing line terminator cannot slip through); max_rooms = 100, max_msg_bytes = 4096, action_rate_per_seat = 20 per second over a FIXED 1-second window counting inbound action frames only, outbound_queue_depth = 64, outbound_send_timeout = 5 s, cleanup_cadence = 1 s, handshake_timeout = 10 s, idle_timeout (playing) = 60 s, finished_room_retention = 15 s, waiting_room_retention = 120 s. Integer fields carry explicit SAFE upper bounds so no JS-imprecise magnitude is accepted: `revision`, `expected_revision`, `score`, `total_lines`, and each `final_revision` seat value range `0 .. 9007199254740991` (`2^53 - 1`, the largest integer exactly representable as an IEEE-754 double); `level` ranges `1 .. 100000`; `gravity_interval_ms` is bounded `100 .. 500` inclusive, consistent with the inherited formula `max(100, 500 - 50*(level - 1))`.

**Action-id grammar and ordinal (Req 20.3, 20.5).** `action_id` is a client-generated per-seat string with the canonical FULL-STRING grammar `^(A|B)-([1-9][0-9]{0,14})(?![\s\S])`: a seat letter (`A`/`B`), a hyphen, then a positive decimal ordinal with NO leading zeros and 1..15 digits, with NO character permitted after the ordinal. The trailing negative lookahead `(?![\s\S])` is used INSTEAD of `$` because, under the Draft 2020-12 validator, `$` matches BEFORE a trailing line terminator, which wrongly accepted `action_id` values such as `"A-1\n"`; `(?![\s\S])` asserts that no character at all (including a trailing LF `\n`, CR `\r`, CRLF, U+2028 LINE SEPARATOR, or U+2029 PARAGRAPH SEPARATOR) may follow the ordinal, so the FULL string must be exactly the grammar (superseded the prior `$`-anchored pattern 2026-11-06 by native08-finish). The ordinal is extracted by stripping the `A-`/`B-` prefix and parsing the decimal. The 15-digit decimal cap expresses an ACTUAL maximum ordinal of `999999999999999` (fifteen nines); this is the HONEST documented maximum and is NOT claimed to equal `2^53 - 1` (it is a smaller, exactly-expressible bound that stays within the safe-integer ceiling). On an `ActionMessage` the prefix letter MUST equal `seat_id` (enforced in the schema by per-seat `if/then` patterns that use the same trailing-lookahead full-string anchoring); a mismatch (for example `seat_id: "A"` with `action_id: "B-3"`) is schema-rejected. The schema applies the grammar `pattern` to `action_id` on `ActionMessage`, `Ack`, and `Reject` (on `Ack`/`Reject` the grammar is enforced but the prefix is not tied to the reply's `seat_id`, since a `not_seat_owner` reject legitimately echoes an action id whose prefix differs from the targeted seat). Ordinals may legitimately JUMP (a client need not send consecutive ordinals); a skipped ordinal is simply never seen. The ordinal is NEVER conflated with `revision`; no reference-to-prior-id field exists.

**Bound-overflow behavior (Req 21.1).** The server never emits a schema-invalid number and never fabricates a gameplay winner to escape a bound. If an applied action or gravity step WOULD drive `revision`, `score`, `total_lines`, or `level` past its documented ceiling, the server stops incrementing that scalar and performs an OPERATIONAL ABORT: it closes the room with the standard going-away code `1001` carrying the LITERAL close reason string `"scalar_overflow"`, classified separately from the win/draw/forfeit gameplay outcomes. Likewise, a seat that reaches the maximum action ordinal `999999999999999` cannot represent a higher ordinal under the grammar; a further action fails the `pattern`, is rejected, and the seat's connection is closed with code `1001` carrying the LITERAL close reason string `"sequence_exhausted"` rather than overflowing. These operational aborts are NOT gameplay outcomes, fabricate no winner, and never produce an out-of-range scalar; they are distinguished from the shared-`1001` gameplay forfeit (reason `"peer_unavailable_forfeit"`) and the shared-`1001` lifecycle reasons (`"idle_timeout"`, `"handshake_timeout"`, `"waiting_room_timeout"`, `"server_shutdown"`) purely by the literal close reason string.

**Coordinate split (schema-enforced).** The active piece `origin`/anchor and its OCCUPIED cells use DIFFERENT schema definitions. The `origin` uses `anchorCoord` (row `-4..19`, column `-3..9`) so a valid negative anchor is expressible (for example an `I` piece whose anchor column is negative while its four occupied cells remain on the board). Each OCCUPIED cell uses `occupiedCell` (row `0..19`, column `0..9`); these simple absolute per-cell bounds ARE expressed in JSON Schema (they are not a runtime-only rule). `active_piece.cells` is exactly four cells with `uniqueItems: true`, so the schema enforces four DISTINCT on-board cells. The public solo active-piece `type`/`origin`/`cells` shape and the integer board `0..7` are preserved. The schema also enforces the status/active_piece relationship on a `state` frame: `status == "playing"` requires a non-null `active_piece`; `status == "game_over"` requires `active_piece: null` (encoded with `if`/`then`/`else`). The `outcome` seat relationship is enforced per `result` (encoded with `if`/`then` per result): `win` requires `winning_seat` and `losing_seat` to be two DISTINCT seats with `forfeiting_seat: null`; `draw` requires all three seat fields null; `forfeit` requires `losing_seat == forfeiting_seat` and `winning_seat` the other (surviving) seat, distinct from the forfeiter.

**Close-code mapping (coherent, standard codes).** Each close reason maps to a STANDARD WebSocket close code, and two reasons deliberately SHARE the standard "going away" code, disambiguated by the accompanying close reason semantics rather than by a unique numeric code: normal completion = 1000; policy/origin violation = 1008; oversize message (message-too-big) = 1009; a rate-limit violation also uses 1008 (policy) carrying the `rate_limited` reason, because standard 1009 is strictly message-size; idle timeout, handshake timeout, AND server shutdown all use 1001 (going away), explicitly documented as a deliberately shared standard code distinguished by reason semantics. Pre-upgrade Origin rejection is an actual HTTP-level denial of the upgrade (the request never becomes a WebSocket, so there is no received WebSocket CLOSE frame for that case).

**Action-id idempotency, bounded reply cache, and check order (coherent; replaces the prior contradictory wording).** There is NO `unknown_action_id` reason: all `action_id`s are client-generated, so a server-issued-id correlation is unreachable, and the reason was removed from the enum (superseded 2026-11-06 by native08-finish). An APPLICATION-VISIBLE inbound message whose `action_id` is MISSING, WRONG-TYPED, or NON-CANONICAL (failing the full-string grammar), or whose payload is invalid JSON or an in-band binary frame, is UNCORRELATABLE and is answered with a schema-valid `ErrorFrame` (`reason: "malformed_message"`, no `action_id`), never with an invalid outbound echo and never with an invented placeholder id; such malformed or unowned input is stopped at check step (1)/(2) and NEVER burns another seat's sequence. A WIRE-LEVEL invalid-UTF8 TEXT frame never reaches this application path at all: it is failed by the WebSocket transport before ASGI with the standard close code `1007` (RFC 6455 §8.1 / §7.4.1), so there is no application `ErrorFrame` and no exact application-controlled reason string for it. The reason `duplicate_action_conflict` is returned when a reused CANONICAL `action_id` arrives with a DIFFERENT request fingerprint than the originally cached action, OR when an uncached `action_id` has an ordinal at or below the high-water mark. Each seat keeps TWO bounded structures: (a) a per-seat MONOTONIC HIGH-WATER MARK `last_action_seq`, the highest action ordinal the seat has consumed (accepted-and-applied, legally no-op'd, or rejected for stale/future revision); and (b) a bounded per-seat REPLY CACHE that is a most-recent-256 LRU keyed by `action_id`, storing BOTH the complete validated request FINGERPRINT (`kind`, `expected_revision`, `room_id`, `seat_id`, `action_id`) AND the original emitted `Ack`/`Reject`. The 256 bound is purely COUNT-based; there is no enforced time-based reply-retention window (the earlier "256 >> 20/s times a 10 s window" time justification is removed, because no time policy is enforced). The EXACT ordered check sequence is: (1) schema/format + `protocol_version`; (2) seat ownership (the `action_id` prefix equals `seat_id` AND the sender owns that seat); (3) rate limit (fixed 1-second window, inbound actions only); (4) room-status/start gate (`not_started` while `waiting`); (5) reply-cache lookup; (6) ordinal vs high-water mark; (7) `expected_revision` strict equality; (8) apply to state. This order guarantees malformed, unowned, or rate-limited input NEVER reaches the cache, the ordinal, or the sequence, so it never burns another seat's sequence or advances any high-water mark. Processing rules:

- An `action_id` still in the reply cache with an IDENTICAL fingerprint returns the IDENTICAL cached reply (idempotent) and refreshes only its LRU recency; nothing is re-applied. This idempotent cached reply is NOT unconditional: the cache is consulted only at check step (5), AFTER the rate gate (step 3) and the room-status/start gate (step 4), so a rate-limit rejection or a resource-limited close (oversize, queue-full/slow-peer, shutdown) can PREEMPT a would-be cached reply; it is therefore NOT claimed that a cached reply is ALWAYS returned, only that it is returned when the earlier gates pass.
- The same cached `action_id` with a CHANGED fingerprint (different `kind`, `expected_revision`, `room_id`, or `seat_id`) is rejected with `duplicate_action_conflict` WITHOUT replacing the original cached entry and WITHOUT mutating board/RNG/gravity/revision.
- A valid, owned, NEW id (ordinal strictly greater than the high-water mark) that receives a stale/future rejection OR a legal no-op is STILL consumed: it is cached AND advances the high-water mark, so a rejected id can never later become newly applied once the revision catches up.
- An UNCACHED `action_id` whose ordinal is at or below the high-water mark ALWAYS rejects with `duplicate_action_conflict` without applying. This includes a never-seen OLD ordinal that was skipped by a jump: it is honestly labelled "at or below the high-water mark" (NOT "previously seen"); both the seen-old and the never-seen-old case reject, for the stated already-processed-or-superseded reason.
- Malformed or unowned input is never cached, never advances any high-water mark, and never burns another seat's sequence.
- SEQUENCE EXHAUSTION: a seat that reaches the maximum ordinal `999999999999999` cannot represent a higher ordinal under the grammar; the next higher action fails the `pattern`, is rejected, and the seat's connection is closed with the standard going-away code `1001` carrying the literal close reason `"sequence_exhausted"`, rather than overflowing.

STRICT RUNTIME TYPING: inbound `protocol_version`, `expected_revision`, and `revision` MUST be strict JSON-decoded Python integers; a bool, string, or float (including a lexical `1.0`) is rejected at runtime. JSON Schema `integer` may accept a mathematically integral `1.0`, so the schema ALONE does not reject lexical floats; the strict runtime integer check is an ADDITIONAL semantic rule and a native implementation TEST OBLIGATION.

**Implementation caveat - `action_id` pattern engine (spec-layer record, native09 2026-11-06).** The locked Pydantic 2.10.4 CANNOT compile the canonical full-string `action_id` grammar `^(A|B)-([1-9][0-9]{0,14})(?![\s\S])` as its DEFAULT Rust-backed `Field.pattern`: independent local qualification raised the EXPECTED `SchemaError` (lookaround unsupported by the default Rust regex engine), which is a qualification-tool observation, NOT an application failure. The canonical Draft 2020-12 lookahead remains VALID and all independent structural cases pass under the Draft 2020-12 validator, so it MUST NOT be weakened back to a soft `$`/dollar anchor (that regression was already corrected in native08-finish because `$` wrongly accepted a trailing `\n`). Later M3 code MUST enforce the IDENTICAL full-string grammar with an equivalent explicit full-string validator (for example a Python `re`-backed custom validator, or another documented compatible engine), with explicit LF / CR / CRLF / U+2028 / U+2029 boundary tests. No Pydantic / package / lock change is made on this native run and no prototype application code is written.

A **single versioned** wire contract governs all duel frames. It carries an explicit `protocol_version` (integer, starting at `1`) and covers handshake, action, state, acknowledgement, rejection, error, and terminal-outcome messages. Every inbound message is validated by a Pydantic model with `extra="forbid"`, so a wrong-typed field, a missing required field, or an extra undocumented field is rejected without mutating any board (Req 20.11, 21.*). Every message has a `type` discriminator (an explicitly enumerated string) and the `protocol_version`.

**Revision model (Req 20.2, 20.9).** Revision is **per board (per seat)**: each `Seat` owns a monotonically increasing integer `revision`, incremented by one each time an action produces a state change on that board (and by gravity-driven state changes). There is no separate room-level revision; every state frame and every ack/rejection names the `seat_id` (target board) and the authoritative `revision` of that board, so a client always knows which board and which revision a message refers to. An action's `expected_revision` is checked for **strict equality** against the target board's authoritative revision.

**Action IDs (Req 20.3, 20.5).** Each action carries a per-seat `action_id` (string) that is **independent of the revision**. The server references that exact `action_id` in the corresponding ack or rejection. A duplicate `action_id` that is still in the bounded per-seat reply cache is **idempotent**: the server returns the cached ack/rejection for that id and does not apply the action twice. The bounded eviction policy (per-seat monotonic high-water mark plus a bounded 256-entry reply cache) is described above: an already-seen id that has been evicted from the reply cache (its ordinal is at or below the high-water mark) is rejected with `duplicate_action_conflict` rather than re-applied or accepted as new, so idempotency holds even after eviction.

**Example messages (valid JSON, no placeholders, no ellipsis, no pipe-enums).**

Client handshake (`hello`; there is intentionally no `client_name` field — no authentication and no player-name collection):

```json
{"type": "hello", "protocol_version": 1, "room_id": "r-7f3a9c"}
```

Server handshake (`welcome`, assigns the seat):

```json
{"type": "welcome", "protocol_version": 1, "room_id": "r-7f3a9c", "seat_id": "A", "room_status": "waiting"}
```

Client action (`action`; `kind` is one of the enumerated strings):

```json
{"type": "action", "protocol_version": 1, "room_id": "r-7f3a9c", "seat_id": "A", "action_id": "A-42", "expected_revision": 17, "kind": "cw"}
```

The `kind` field enumerates exactly: `"left"`, `"right"`, `"down"`, `"cw"`, `"ccw"`, `"hold"`.

Server state frame (`state`; board/active_piece/queue/Hold consistent with `GameStateOut` and `TYPE_CODES`):

```json
{"type": "state", "protocol_version": 1, "room_id": "r-7f3a9c", "seat_id": "A", "revision": 18, "status": "playing", "room_status": "playing", "board": [[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0]], "active_piece": {"type": "T", "origin": [0, 3], "cells": [[0,4],[1,3],[1,4],[1,5]]}, "next_piece": "L", "hold_piece": null, "can_hold": true, "score": 0, "total_lines": 0, "level": 1, "gravity_interval_ms": 500}
```

Server acknowledgement (`ack`; references the `action_id`, names the target board and authoritative revision, reports a no-op explicitly):

```json
{"type": "ack", "protocol_version": 1, "room_id": "r-7f3a9c", "seat_id": "A", "action_id": "A-42", "revision": 18, "applied": true, "no_op": false}
```

A no-op acceptance (e.g. a fully rejected rotation that is legal to request but changes nothing) sets `"applied": true, "no_op": true` and leaves `revision` equal to the current authoritative revision (Req 20.8).

Server rejection (`reject`; stable machine-readable reason codes):

```json
{"type": "reject", "protocol_version": 1, "room_id": "r-7f3a9c", "seat_id": "A", "action_id": "A-43", "reason": "stale_revision", "authoritative_revision": 18}
```

The `reason` field enumerates exactly these stable codes: `"stale_revision"`, `"future_revision"`, `"not_seat_owner"`, `"not_started"`, `"bad_type"`, `"missing_field"`, `"extra_field"`, `"rate_limited"`, `"oversize"`, `"duplicate_action_conflict"`. `stale_revision` is used when `expected_revision` is lower than the authoritative revision (Req 20.6); `future_revision` when it is higher (Req 20.7); `not_seat_owner` when the sender does not own the targeted seat (Req 20.10); `not_started` when an owned, well-formed action arrives while the room `room_status` is `waiting` (the room has not started, so the action is not applied, does not advance the per-seat revision, and does NOT consume the seat's action ordinal / high-water mark); `bad_type` / `missing_field` / `extra_field` for schema violations on a message that DOES carry a valid canonical `action_id` to echo (Req 20.11); `rate_limited` / `oversize` for bounds (Req 22.4). There is intentionally NO `unknown_action_id` reason and NO reference-to-prior-id / server-issued-id correlation field: all `action_id`s are client-generated, so a server-issued-id correlation is unreachable, and the reason was removed from the enum (superseded 2026-11-06 by native08-finish; see the historical observation in `docs/native-checks/07-m2-acceptance-and-m3-contract-finalize/NOTE.md`). An APPLICATION-VISIBLE inbound message whose `action_id` is MISSING, WRONG-TYPED, or NON-CANONICAL (or whose payload is invalid JSON, or an in-band binary frame) is UNCORRELATABLE - it has no valid id to echo in a `Reject`, and inventing a placeholder id is forbidden - so it is answered with a schema-valid `ErrorFrame` carrying `reason: "malformed_message"` (an `ErrorFrame` has no `action_id`), never with an invalid outbound echo. A WIRE-LEVEL invalid-UTF8 TEXT frame is NOT part of this application-visible `malformed_message` set: an invalid-UTF8 TEXT payload is rejected by the WebSocket transport BEFORE ASGI / the application receives a decoded message, so (per RFC 6455 §8.1 fail-the-connection and §7.4.1) the transport fails the connection with the standard close code `1007` and a library-managed bounded reason, and the application neither sees the message nor is required to emit a JSON `ErrorFrame` or an exact application-controlled reason string for it; such a `1007` transport close in a STARTED room triggers the ordinary disconnect / forfeit / once-only cleanup to the remaining peer, and a waiting-alone `1007` fabricates no winner. `duplicate_action_conflict` is returned both when a re-used `action_id` still in the bounded reply cache arrives with DIFFERENT contents than the originally cached action, and when an already-seen OR never-seen-but-skipped `action_id` at or below the per-seat monotonic high-water mark is not present in the bounded 256-entry reply cache; in both cases the server rejects the reuse and never silently reapplies a previously accepted action or accepts a changed-content reused id as new (there is no fresh-action treatment of an evicted-or-skipped ordinal at or below the high-water mark).

Server error (`error`; carries a stable reason code, never a path/SQL/exception/stack):

```json
{"type": "error", "protocol_version": 1, "room_id": "r-7f3a9c", "seat_id": null, "reason": "room_not_found", "detail": "No such room."}
```

The `error` `reason` enumerates exactly: `"room_not_found"`, `"room_full"`, `"room_closed"`, `"protocol_version_unsupported"`, `"handshake_timeout"`, `"malformed_message"`, `"internal"`. `malformed_message` is the schema-valid outbound path for an APPLICATION-VISIBLE UNCORRELATABLE malformed inbound message (missing / wrong-typed / non-canonical `action_id`, invalid JSON, or an in-band binary frame), because such a message has no valid `action_id` to echo in a `Reject` and inventing a placeholder id is forbidden; an `ErrorFrame` has no `action_id`, so it is the correct correlation-free vehicle. A wire-level invalid-UTF8 TEXT frame is NOT answered with `malformed_message`: it is rejected by the WebSocket transport before the application receives a decoded message and is handled as a transport-level `1007` fail-the-connection close (RFC 6455 §8.1 / §7.4.1) with a library-managed bounded reason and no required application-controlled JSON reply or exact reason string. `detail` is a short English string with no filesystem path, SQL text, exception or class name, or stack trace (Req 21.6).

Server terminal outcome (`outcome`; win/loss/draw/forfeit with the winning/forfeiting seat):

```json
{"type": "outcome", "protocol_version": 1, "room_id": "r-7f3a9c", "result": "win", "winning_seat": "A", "losing_seat": "B", "forfeiting_seat": null, "final_revision": {"A": 54, "B": 51}}
```

The `result` field enumerates exactly: `"win"`, `"draw"`, `"forfeit"`. For `"win"`, `winning_seat` and `losing_seat` are the two seat ids and `forfeiting_seat` is `null`. For `"draw"` (simultaneous top-out), `winning_seat` and `losing_seat` are `null` and `forfeiting_seat` is `null`. For `"forfeit"`, `forfeiting_seat` is the seat that disconnected, `winning_seat` is the survivor, and `losing_seat` equals the forfeiting seat. (A "loss" is the same frame observed from the losing seat's perspective; the single frame names both seats, so loss is not a separate `result` value.)

**Field definitions, types, ranges, nullability (Req 21.1, 21.2).** Every field above is defined with a name, type, range, and nullability: `protocol_version` is the integer constant `1`; `room_id` is a non-empty string within the bounded id length `1..64`; `seat_id` is `"A"` or `"B"` (nullable only in `error`); `action_id` is a non-empty string `1..64` that ADDITIONALLY satisfies the canonical FULL-STRING grammar `^(A|B)-([1-9][0-9]{0,14})(?![\s\S])` (seat letter, hyphen, 1..15-digit ordinal with no leading zeros, and NO trailing character including any line terminator), and it is present on `action`/`ack`/`reject` but is ABSENT on `error` (an `ErrorFrame` is the correlation-free vehicle for an uncorrelatable malformed message with `reason: "malformed_message"`); `expected_revision` and `revision` are integers `0 .. 9007199254740991` (`2^53 - 1`); `room_status` is a REQUIRED enumerated string `"waiting"`/`"playing"`/`"finished"` on EVERY `state` frame (the room lifecycle, distinct from the per-seat board `status`); `kind`, `reason`, `result`, `type`, `status` are enumerated strings; `applied`/`no_op`/`can_hold` are booleans; `board` is a 20x10 array of integers `0..7`; `active_piece` is nullable and, when present, uses the inherited `type`/`origin`/`cells` shape where `origin` is an anchor coordinate (row `-4..19`, column `-3..9`) and `cells` is exactly four DISTINCT absolute on-board cells (row `0..19`, column `0..9`); on a `state` frame `active_piece` is non-null exactly when `status == "playing"` and null when `status == "game_over"`; `next_piece` is a nullable type-code letter; `hold_piece` is nullable; `score` and `total_lines` are integers `0 .. 9007199254740991`; `gravity_interval_ms` is an integer `100..500` inclusive; `level` is an integer `1..100000`; `final_revision` maps each seat id to its final integer revision `0 .. 9007199254740991`. All schemas/examples are valid machine-readable JSON with no placeholders, no ellipsis, and no pipe-delimited enum strings; every enumerated field lists its allowed values explicitly (Req 21.3, 21.4).

### Duel origin, bounds, close codes, and WS engine (Req 22)

- **Origin allow-list (Req 22.1, 22.2).** The WebSocket upgrade validates the request `Origin` against an **exact allow-list bound to the actual proxy host and port** (`http://localhost:5517` and `http://127.0.0.1:5517` by default, configurable like the HTTP CORS list and reusing the same restrictive, fail-closed posture); a disallowed Origin is denied at the HTTP upgrade before the socket is accepted, so the request never becomes a WebSocket and no WebSocket CLOSE frame is emitted for that case (the denial is an HTTP-level rejection, not a received close). Nginx preserves the proxy host/port and performs the WebSocket upgrade for `/ws/duel` so the same-origin WS URL reaches the backend worker.
- **Bounds (Req 22.3, 22.4).** The server bounds the room id length, the maximum inbound UTF-8 message size, the per-seat inbound action rate, the maximum number of concurrent rooms, the per-seat outbound queue depth, and the handshake and idle timeouts. An oversize message, a rate-limit violation, or a room-count-at-maximum condition is rejected with a defined rejection reason or close code and never exhausts worker memory.
- **Close codes (Req 22.5).** Each close reason maps to a STANDARD WebSocket close code, with two reasons deliberately SHARING the going-away code and disambiguated by the close reason semantics (not by a unique numeric code): normal completion = 1000; policy/origin violation = 1008; oversize message = 1009; rate-limit violation = 1008 (policy) with the `rate_limited` reason (standard 1009 is strictly message-size); idle timeout, handshake timeout, and server shutdown all = 1001 (going away). This shared-code decision resolves the earlier ambiguity coherently: the codes are the documented standard ones, and the idle/handshake/shutdown reasons are distinguished by their reason text rather than by separate numbers. Tests that assert a close must first **drain the queued handshake, state, and error frames** before asserting the socket reached CLOSE, so a close assertion never races ahead of deliverable frames (Req 22.6).
- **Real WS engine (Req 22.7).** A production uvicorn deployment must include an **actual WebSocket protocol engine dependency** that implements uvicorn's WebSocket upgrade (for example `websockets` or `wsproto`); `anyio` alone does not satisfy the upgrade requirement. This is a **runtime dependency addition** to be reflected later in the requirements/tasks and in the runtime lock/image; this design records the obligation and does **not** assert that any install, build, or run has been executed.

## Data Models

### Orientation on the active piece (`app/domain/models.py`)

```python
@dataclass
class ActivePiece:
    type: PieceType
    origin: Coord
    cells: List[Coord]
    # --- Stage 4 (M1) addition ---
    orientation: int = 0        # 0..3; 0 == spawn orientation (spawn0). Reset to
                                # 0 on every spawn and both Hold paths (Req 6.*).
```

`orientation` is the only new field on the active piece. It is set to `0` by `engine._place` for every entry path and advanced only by `engine.rotate`. The serialized `active_piece` shape (`type`, `origin`, `cells`) is unchanged, so the solo `GameStateOut` contract and the inherited tests are preserved; `orientation` is internal engine state, not a new serialized key. The `Game` dataclass needs no new field for rotation because orientation lives on the active piece.

### Orientation tables (`app/rules/rotation.py`)

`ORIENTATIONS[type][orientation]` lists four `(row, col)` offsets from the piece origin. Orientation `0` equals `pieces.SHAPES[type]`. Each non-`O` table is a rigid quarter-turn of the previous about the declared pivot recorded in the comment. The `I` piece is shown explicitly to prove the `spawn0` row-0 geometry is used (not a row-1 SRS table):

**Declared fixed pivots (one exact point per piece).** Every piece's four orientations are rigid 90-degree quarter-turns about ONE exact fixed pivot POINT (fractional allowed), declared as: I = (1.5, 1.5); O = (0.5, 0.5); T, S, Z, J, L = (1, 1). The CW transform about pivot (pr, pc) is `(r, c) -> (pr + (c - pc), pc - (r - pr))` and CCW is its exact inverse `(r, c) -> (pr - (c - pc), pc + (r - pr))`. The tables below were regenerated and independently re-checked against these fixed-point transforms (not derived from any implementation, which does not yet exist): for every non-`O` piece, cw(orientation i) equals orientation (i+1) mod 4 for all i, four successive CW turns restore orientation 0, CCW is the exact inverse of CW at every index, and each orientation has exactly four distinct cells. The I orientations stay within columns 0..9 at the spawn origin (row 0, column 3). Note that permitting a fixed pivot means a rotated/kicked origin MAY be a negative anchor; the engine's `_is_valid` bounds the ABSOLUTE occupied cells to rows 0..19 and columns 0..9, so negative origins are only accepted when every absolute cell is in-bounds.

```python
ORIENTATIONS = {
    # I: single FIXED fractional pivot at (1.5, 1.5) (the center of the 4x4 I box).
    # spawn0 (orientation 0) is HORIZONTAL on row 0 and is AUTHORITATIVE/unchanged.
    # Each orientation is a rigid 90-degree CW quarter-turn of the previous about (1.5,1.5):
    #   CW: (r,c) -> (1.5 + (c-1.5), 1.5 - (r-1.5)); CCW is its exact inverse.
    "I": [
        [(0, 0), (0, 1), (0, 2), (0, 3)],   # 0: spawn0 (row 0, cols 0..3) -- authoritative
        [(0, 3), (1, 3), (2, 3), (3, 3)],   # 1: cw  -> vertical in column 3
        [(3, 0), (3, 1), (3, 2), (3, 3)],   # 2: 180 -> horizontal on row 3
        [(0, 0), (1, 0), (2, 0), (3, 0)],   # 3: ccw -> vertical in column 0
    ],
    # O: single declared fixed pivot (0.5, 0.5); FULL no-op -- all four indices share the
    # spawn0 set AND O rotation does not change the orientation index either (see Rotation engine).
    "O": [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
    ],
    # T: pivot at (1,1); spawn0 points up.
    "T": [
        [(0, 1), (1, 0), (1, 1), (1, 2)],   # 0: spawn0
        [(0, 1), (1, 1), (1, 2), (2, 1)],   # 1: cw
        [(1, 0), (1, 1), (1, 2), (2, 1)],   # 2: 180
        [(0, 1), (1, 0), (1, 1), (2, 1)],   # 3: ccw
    ],
    # S: pivot at (1,1).
    "S": [
        [(0, 1), (0, 2), (1, 0), (1, 1)],   # 0: spawn0
        [(0, 1), (1, 1), (1, 2), (2, 2)],   # 1: cw
        [(1, 1), (1, 2), (2, 0), (2, 1)],   # 2: 180
        [(0, 0), (1, 0), (1, 1), (2, 1)],   # 3: ccw
    ],
    # Z: pivot at (1,1).
    "Z": [
        [(0, 0), (0, 1), (1, 1), (1, 2)],   # 0: spawn0
        [(0, 2), (1, 1), (1, 2), (2, 1)],   # 1: cw
        [(1, 0), (1, 1), (2, 1), (2, 2)],   # 2: 180
        [(0, 1), (1, 0), (1, 1), (2, 0)],   # 3: ccw
    ],
    # J: pivot at (1,1); spawn0 corner top-left.
    "J": [
        [(0, 0), (1, 0), (1, 1), (1, 2)],   # 0: spawn0
        [(0, 1), (0, 2), (1, 1), (2, 1)],   # 1: cw
        [(1, 0), (1, 1), (1, 2), (2, 2)],   # 2: 180
        [(0, 1), (1, 1), (2, 0), (2, 1)],   # 3: ccw
    ],
    # L: pivot at (1,1); spawn0 corner top-right.
    "L": [
        [(0, 2), (1, 0), (1, 1), (1, 2)],   # 0: spawn0
        [(0, 1), (1, 1), (2, 1), (2, 2)],   # 1: cw
        [(1, 0), (1, 1), (1, 2), (2, 0)],   # 2: 180
        [(0, 0), (0, 1), (1, 1), (2, 1)],   # 3: ccw
    ],
}
```

Each inner list has four distinct offsets. These tables are the independently-declared oracle that the rotation tests assert against (Req 2.8, 9.1); the implementation tables and the test's expected tables are declared separately so a test never re-derives its expectation from the algorithm under test.

### Duel room / seat / board state (`app/duel/rooms.py`)

The `Seat`/`Room`/`RoomManager` dataclasses are defined under Components and Interfaces. Each `Seat.game` is an ordinary `Game` from `engine.new_game`, so a duel board serializes through the **same** solo mapping (`board` as 20x10 integer codes via `TYPE_CODES`, `active_piece` as `type`/`origin`/`cells`), keeping duel board serialization consistent with the solo schema. Duel state is in memory only and is never persisted.

### Wire-contract models (`app/ws/contract.py`)

Each message is a Pydantic model with `model_config = ConfigDict(extra="forbid")`, mirroring the solo request hardening. Inbound models: `Hello`, `ActionMessage`. Outbound models (serialized to JSON): `Welcome`, `StateFrame`, `Ack`, `Reject`, `ErrorFrame`, `Outcome`. The enumerated fields use `Literal[...]` with exactly the values listed under the wire contract (`type`, `kind`, `reason`, `result`, `seat_id`, `room_status`/`status`). `StateFrame` reuses `GameStateOut`-compatible field types (`board: List[List[int]]`, an active-piece sub-model identical to `ActivePieceOut`, `next_piece`, `hold_piece`, `can_hold`, `score`, `total_lines`, `level`, `gravity_interval_ms`) plus the duel-only `seat_id` and `revision`, so the duel board shape is byte-consistent with the solo schema and the `TYPE_CODES` mapping.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Stage 4's rotation engine and duel logic are pure, deterministic, input-varying code with clear universal invariants, so they are well suited to property-based testing. The Canvas rendering, the HTTP/WS wiring, the Docker/CI configuration, and the benchmark are **not** PBT targets (they are verified by pixel evidence, example/integration tests, snapshot/config checks, and design-only benchmark narration, described in Testing Strategy); no correctness properties are declared for them.

The following properties were derived via the prework analysis using the `prework` tool and then reduced to remove redundancy (for example, a single four-cycle-identity property per direction subsumes per-piece identity checks, and one strict-equality acceptance-window property subsumes separate stale and future checks).

### Property 1: CW/CCW four-cycle identity

*For any* non-`O` piece type and any starting orientation index, applying four successive rotations in the same direction (`cw` or `ccw`) with no intervening collision, movement, or lock returns both the orientation index and the occupied-cell set to their starting values.

**Validates: Requirements 2.3, 9.2**

### Property 2: CW then CCW is the identity

*For any* piece type, orientation index, and origin, a `cw` rotation immediately followed by a `ccw` rotation (with no intervening collision, movement, or lock) restores the orientation index and the occupied-cell set to their pre-rotation values.

**Validates: Requirements 2.7**

### Property 3: `O` rotation is a no-op

*For any* origin and either direction, rotating the `O` piece leaves its occupied-cell set identical to the set immediately before the request.

**Validates: Requirements 2.4**

### Property 4: Every orientation has exactly four distinct cells

*For any* piece type, orientation index `0..3`, and origin that places the piece inside the board, the computed occupied-cell set contains exactly four cells, all distinct, each within rows `0..19` and columns `0..9`.

**Validates: Requirements 2.1, 2.5, 2.6**

### Property 5: Rejected rotation is fully immutable

*For any* game state in which the raw rotation and every kick candidate collide, a rotation request leaves the active piece's origin and orientation index, and the `score`, `level`, `total_lines`, `next_piece`, `hold_piece`, `can_hold`, `gravity_interval_ms`, `board`, and `status` values all equal to their pre-request values.

**Validates: Requirements 3.5, 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 6: Accepted rotation changes only orientation and (on a kick) origin

*For any* game state and accepted rotation, the only authoritative fields that change are the active piece's orientation index and, where a wall kick was applied, its origin (and the derived cells); `score`, `level`, `total_lines`, `next_piece`, `hold_piece`, `can_hold`, and `gravity_interval_ms` are unchanged, and the piece is neither locked nor advanced by gravity.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

### Property 7: Wall-kick first-fit in the exact order

*For any* game state where a raw rotation collides, the accepted result is the first candidate in the order `0, -1, +1, -2, +2` whose column-only–offset occupied-cell set is fully in bounds and overlaps no locked cell, and no later candidate is selected when an earlier one fits.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.6**

### Property 8: Spawn and Hold reset orientation to 0

*For any* sequence of rotations followed by a spawn or either Hold path, the piece that enters play has orientation index `0` at the spawn origin, regardless of its prior orientation.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4**

### Property 9: Lock preserves rotated geometry

*For any* rotated active piece that locks, the settled board contains exactly the rotated occupied-cell set (translated by any moves), after which the inherited lock/clear/score/level/gravity/Hold/spawn ordering is applied unchanged.

**Validates: Requirements 7.1, 7.2, 7.3**

### Property 10: Duel seat independence

*For any* room with two started seats and any sequence of actions directed at one seat, only that seat's private board state changes; the other seat's board, queue, Hold, level, and revision are unaffected, and the solo global sequence is never altered.

**Validates: Requirements 17.3, 17.4, 17.5**

### Property 11: Per-board revision monotonicity

*For any* seat and any sequence of applied state-changing actions or gravity steps, the authoritative revision is non-decreasing and increases by exactly one on each state change; a no-op leaves the revision unchanged.

**Validates: Requirements 20.2, 20.8, 20.9**

### Property 12: Strict expected-revision acceptance window

*For any* action with an `expected_revision`, the server applies it only when `expected_revision` exactly equals the target board's authoritative revision; a lower value is rejected as `stale_revision` and a higher value as `future_revision`, and in both rejection cases the board is not mutated.

**Validates: Requirements 20.4, 20.6, 20.7**

### Property 13: Duplicate action idempotency

*For any* action id already processed, re-sending the same action id does not apply the action a second time and yields the same ack-or-rejection outcome as the first processing.

**Validates: Requirements 20.5**

### Property 14: Seat-ownership enforcement

*For any* action naming a seat the sender does not own, the server rejects it with `not_seat_owner` and does not mutate the targeted board.

**Validates: Requirements 20.10**

### Property 15: Simultaneous top-out is a draw; otherwise last survivor wins

*For any* gravity evaluation that advances all due boards, if both boards top out within that evaluation the outcome is `draw`; if exactly one board remains playable the surviving seat wins; and a resolved duel is never resolved a second time.

**Validates: Requirements 18.3, 18.4, 18.5**

### Property 16: Room cleanup is bounded

*For any* sequence of room creations and clock advances, finished rooms are released after their bounded finished-retention and waiting/inactive rooms after their bounded idle-retention, so the number of retained rooms stays within the configured maximum and no room, task, or socket is leaked.

**Validates: Requirements 19.1, 19.2, 19.3**

## Error Handling

- **Rotation 422 (Req 1.6).** A missing `direction`, a non-string `direction` (boolean, number, array, object, null), a string other than `"cw"`/`"ccw"`, or any extra field fails `RotateRequest` validation (`extra="forbid"`) and returns HTTP 422 before any engine call, so no authoritative field changes.
- **Rotation 404 (Req 1.7).** An unknown game id raises HTTP 404 via `_get_or_404` with no state change.
- **Rotation no-op (Req 1.8, 1.9).** A `game_over` game or a game with no active piece returns the current state unchanged (status `game_over` or current) because `engine.rotate` returns before mutating.
- **Rotation 503 unchanged.** Rotation never drives a terminal transition, so it introduces no new 503; the only 503 reachable on the shared mutating path is the inherited pending-finalization case on an already-terminal game.
- **Duel schema rejections (Req 20.11, 21.6).** For a message that DOES carry a valid canonical `action_id` to echo: a wrong-typed field -> `bad_type`; a missing required field -> `missing_field`; an extra undocumented field -> `extra_field`; a stale/future `expected_revision` -> `stale_revision`/`future_revision`; an action for an unowned seat -> `not_seat_owner`; an action while the room is `waiting` -> `not_started`; an oversize message -> `oversize`; a rate-limit breach -> `rate_limited`. For an APPLICATION-VISIBLE UNCORRELATABLE malformed inbound message (missing / wrong-typed / non-canonical `action_id`, invalid JSON, or an in-band binary frame) there is no valid id to echo, so the server emits a schema-valid `ErrorFrame` with `reason: "malformed_message"` (no `action_id`), never an invalid outbound echo or an invented placeholder id; such malformed or unowned input never burns another seat's sequence. A wire-level invalid-UTF8 TEXT frame is NOT in this application-visible set: it is failed by the WebSocket transport BEFORE ASGI with the standard close code `1007` (RFC 6455 §8.1 / §7.4.1) and a library-managed bounded reason, with no required application-controlled JSON reply or exact reason string. None mutates a board, and no rejection or error frame leaks a filesystem path, SQL text, an exception or class name, or a stack trace.
- **Duel close codes and literal reasons (Req 22.4, 22.5, 22.6).** Each close reason maps to a standard WebSocket close code with an explicit LITERAL reason string: normal completion = 1000 (`"normal_completion"`); policy/origin violation = 1008; oversize message = 1009; rate-limit violation = 1008 (policy) with the `rate_limited` reason; and the going-away code 1001 is deliberately SHARED by several reasons distinguished only by the literal reason string - `"idle_timeout"` (a `playing` room reaped for idleness), `"handshake_timeout"`, `"server_shutdown"`, the gameplay forfeit `"peer_unavailable_forfeit"` (a failed-send / slow-peer disconnect in a STARTED room, which resolves the duel exactly once as a `forfeit` outcome), and the operational aborts `"waiting_room_timeout"` (a never-started waiting room cancelled/timed out, which fabricates NO gameplay winner), `"sequence_exhausted"`, and `"scalar_overflow"`. A disallowed Origin is denied at the HTTP upgrade (no WebSocket is established, so there is no received CLOSE frame for that case). A wire-level invalid-UTF8 TEXT frame is failed by the WebSocket transport with the standard close code `1007` (invalid payload data for the message type) and a library-managed BOUNDED reason, per RFC 6455 §8.1 (fail the connection on invalid UTF-8) and §7.4.1; this `1007` case does NOT require an application-controlled JSON reply or an exact application-controlled reason string, and if it occurs in a STARTED room it triggers the ordinary disconnect / forfeit / once-only cleanup to the remaining peer (a waiting-alone `1007` fabricates no winner). Room-at-maximum, oversize, malformed JSON, and in-band binary frames (the application-visible set) are handled boundedly without exhausting memory, with no exception/stack leaked in any `detail` (the application-visible uncorrelatable malformed cases use the `malformed_message` `ErrorFrame`). Tests drain queued handshake/state/error frames before asserting CLOSE.
- **Duel outcome resolution (Req 18.5, 19.3).** A terminal outcome resolves exactly once; a disconnect of an already-finished room does not re-resolve it. A failed-send / slow-peer disconnect in a STARTED (`playing`) room is a GAMEPLAY FORFEIT (one `forfeit` outcome, the other seat wins; close reason `"peer_unavailable_forfeit"`), whereas a never-started WAITING room cancellation is a separate OPERATIONAL ABORT that fabricates no winner (close reason `"waiting_room_timeout"`); all due boards are still evaluated before the single normal outcome. A cancelled room, slow peer, failed send, or shutdown releases the room's resources without leaking a room, task, or socket.
- **Solo storage 503 unchanged (Req 23.4).** The inherited `StorageError` -> controlled JSON 503 behavior, the pending-retry path, and the once-only finalization are preserved for the solo API.
- **Cleanup / shutdown safety (Req 19.3, 19.5, 19.6).** Room mutation takes a short per-room lock to snapshot and performs bounded ordered outbound I/O outside the lock, so a slow or blocked peer cannot stall the worker; shutdown drains and releases rooms cleanly.
- **Frontend.** A failed rotation fetch surfaces through the inherited `useGame` error path without crashing; stale rotation responses are discarded by the inherited generation check. A duel-client transport error surfaces a status without affecting the solo view.

## Testing Strategy

Stage 4 uses a dual approach: **property-based tests** for the pure rotation engine and the pure duel logic (universal invariants across generated inputs), and **example / integration / pixel-evidence tests** for everything that is not a pure input-varying function. Inherited Stage 1/2/3 regressions are preserved (Req 24.1).

### Rotation (M1)

- **Independent oracle tables (Req 9.1).** Rotation unit tests declare their own expected per-piece per-orientation occupied-cell tables, separate from `rotation.ORIENTATIONS`, and assert the engine's cells for every `(type, orientation 0..3)` against those independent tables, so a test never re-derives its expectation from the algorithm under test.
- **Property tests (Properties 1-9).** Implemented with a property-based testing library for Python (`hypothesis`), each property test runs **at least 100 iterations** and is tagged `# Feature: tetris-stage4-option-a, Property N: <text>`. Generators produce random piece types, orientations, origins, and board occupancy (including boards contrived to force each kick candidate and a fully rejected rotation).
- **Deterministic fixtures (Req 9.3, 9.4, 9.5).** Example tests cover: the `O` no-op in both directions; the `I` row-0 geometry in all four orientations; a left-wall kick, a right-wall kick, a floor kick, and a locked-cell kick, including a case where the first fitting candidate in `0, -1, +1, -2, +2` is selected over a later fitting candidate; and a fully rejected rotation asserting origin, orientation, `gravity_interval_ms`, `score`, `level`, `total_lines`, `next_piece`, `hold_piece`, and `can_hold` are each unchanged.
- **API tests (Req 9.6, 9.7).** Example tests assert HTTP 200 and the exact eleven-key `GameStateOut` shape on success; a rotation against a `game_over` game and against a game with no active piece change no authoritative field; and HTTP 422 for a missing-direction payload, a non-string-direction payload, and an extra-field payload.
- **Frontend tests (Req 9.8).** Tests fire a real `ArrowUp` key event, a real `Z` key event, and activate each on-screen rotation control, asserting one rotation request per event/activation routed through the FIFO; rotation is never asserted solely through internal function calls.

### Canvas (M2)

- **Pixel evidence from the unmodified production bundle (Req 14.2, 14.3, 14.6).** Rendering claims are backed by actual pixel masks or screenshots captured from the production build (via the Playwright harness convention), tied to a spawned piece, a rotated piece, a moved piece, a locked piece, and a cleared-line state. Mock draw-call records and DOM data attributes are explicitly not accepted as pixel evidence, and no debug/injection/interception hooks are added to the production bundle.
- **Isolated clear fixture (Req 14.4).** A state that is hard to reach through ordinary play (e.g. a multi-line clear) is driven through the production clear path with an explicitly-declared isolated fixture that is never claimed to be the production backend.
- **Native unit fixtures (Req 14.1).** May verify renderer draw calls (the per-cell fills and the active-piece overlay against a mocked 2D context), transform-reset + full-backing-store clear per draw, DPR 1/2 backing-store sizing and transform reset, redraw on each trigger (same-count movement, CW, CCW, tick, lock, line clear, restart, meaningful resize), and safe behavior when the 2D context is `null`, when `ResizeObserver` is absent, and on unmount cleanup — all as **behavioral coverage only, not pixel proof**.
- **Superseded assertions (Req 14.5).** The two inherited `Board.test.tsx` DOM-cell assertions ("renders a 20x10 grid of cells" and "renders with a null active piece") are documented as superseded by the Canvas migration; their semantic coverage is replaced by the Canvas behavioral draw-call coverage above plus the independent production-bundle pixel evidence.
- **Layout check (Req 15).** A `1280x900` viewport check (DPR 1 and 2) confirms the full board and all controls/panels are visible with no clipping, no overlap, and no page overflow (`scrollHeight <= 900`, fixing the inherited `964`), that the visible title reads "Stage 4" (not "Stage 2"), and that the solo view is reachable and does not require three simultaneous boards. Independent production-bundle pixel and layout evidence is captured after this milestone closes.

### Duel (M3)

- **Injectable monotonic clock (Req 19.4).** Duel tests inject a fake monotonic clock to advance gravity and lifecycle timeouts deterministically, exercising per-board gravity, simultaneous top-out (draw), last-survivor win, and forfeit-once.
- **Property tests (Properties 10-16).** `hypothesis`-based, at least 100 iterations each, tagged `# Feature: tetris-stage4-option-a, Property N: <text>`, covering seat independence, revision monotonicity, the strict-equality acceptance window, duplicate-action idempotency, seat-ownership, simultaneous-top-out-draw, and the cleanup bound.
- **Wire-contract and connection tests.** Cover malformed, stale, future, duplicate, and seat-ownership messages; oversize and rate-limit bounds; room-at-maximum; origin rejection; slow-peer and failed-send cleanup; and shutdown. Close-assertion tests **drain queued handshake/state/error frames before asserting CLOSE** (Req 22.6). A later PUBLIC test sends a raw masked TEXT frame carrying byte `0xFF` (invalid UTF-8 in a TEXT message) and expects a transport close with the standard code `1007` (RFC 6455 §8.1 / §7.4.1, library-managed bounded reason, no required application-controlled JSON reply or exact reason string), DISTINCT from a browser binary `Uint8Array` `0xFF` frame (an application-visible BINARY payload) which expects the `malformed_message` `ErrorFrame` path; a `1007` transport close in a STARTED room triggers the ordinary disconnect/forfeit/once-only cleanup, and a waiting-alone `1007` fabricates no winner. JSON example messages in the contract are validated as parseable and schema-conformant. The positive examples corpus is validated against the canonical JSON Schema using a local Draft 2020-12 validator (`jsonschema`), which confirmed all positive examples conform and all negative examples except the documented lexical-float case are rejected by the schema; the lexical-float case is rejected only by the additional strict runtime integer rule, which is a separate implementation test obligation.
- **Concurrent terminal and cleanup tests.** Assert a duel resolves exactly once under a disconnect-plus-gravity race and that finished vs waiting/inactive retention releases rooms within their bounds with no leaked room/task/socket.

### Preserved regressions and coverage (Req 24)

- **Inherited regressions (Req 24.1).** All Stage 1/2/3 backend and frontend regression assertions continue to pass unchanged, including request-ordering, lifecycle, persistence, and leaderboard assertions. (The superseded `Board.test.tsx` DOM-cell assertions are the one documented exception, replaced by Canvas pixel evidence per Req 14.5.)
- **Coverage reports (Req 24.2, 24.3, 24.4).** Backend coverage is produced in **XML** covering all executable backend modules including rotation, duel-room, gravity, cleanup, wire-contract, and error branches; frontend coverage is produced in **LCOV** covering Canvas rendering, resize, rotation-control, duel-client, and API branches. Coverage exercises error, race, cleanup, resize, and API branches, not only the happy path.
- **Separate Sonar outcomes (Req 24.5, 24.6).** NEW-code coverage `>= 80%`, code duplication `<= 3%`, and `0` new static-analysis findings are each treated as a **separate** outcome; passing the coverage outcome is not treated as proof the overall gate passed. Thresholds are not weakened, no production-code coverage exclusions are added, and the coverage baseline is not reset to pass a gate. This design asserts no executed Sonar run or metric.

### Containerization and CI (Req 25)

- **Isolated Stage 4 resources (Req 25.1-25.4).** A reproducible Stage 4 Docker and CI configuration uses an isolated project name (e.g. `tetris-stage4-kiro`), an isolated network, and an isolated named volume. The Stage 4 Compose stack publishes **only the frontend on host port `5517`** and keeps the backend reachable only on the internal network. Backend and frontend each run as a **non-root** user, and the backend runs **exactly one** worker (so the single worker owns both solo games and duel rooms). Stage 4 does not start, stop, modify, or remove the inherited Stage 3 resources (project `tetris-stage3-kiro`, host `5183`) or any other tool's containers/volumes/networks.
- **CI honesty (Req 25.5, 25.6).** A local workflow file and local clean-equivalent checks are treated as configuration artifacts only, not as evidence of a hosted Actions run. Tests and fixtures do not delete data outside their own declared temporary fixtures, and the solo SQLite data and the inherited restrictive HTTP CORS policy are preserved. The new runtime WebSocket-engine dependency (Req 22.7) is reflected in the Stage 4 runtime lock/image during implementation; this design asserts no executed build, audit, or run.

<!-- =====================================================================
NATIVE 21 BENCHMARK HARNESS AUTHORIZATION (2026-11-06)
Pre-correction note on disk: docs/native-checks/21-stage4-benchmark-harness-authorization/NOTE.md
Added BEFORE lifting the benchmark posture below. This section was formerly
"Benchmark (DESIGN ONLY, Req 26, 27)". Per amended Requirements 26-27 the former
DESIGN-ONLY prohibition is lifted to AUTHORIZE benchmark HARNESS IMPLEMENTATION plus
the harness's OWN semantic self-checks. The SIX measured production trials (two short
headful probes + three Solo + three Duel 35s) remain SEPARATELY AUTHORIZED and are NOT
executed under this authorization. No frozen app/engine/Canvas/wire design and no
honesty/exclusion/calibration statement is weakened. The overall Sonar quality gate is
NOT all-pass (docs/validation/m3-acceptance-01/report.json); physical presentation
latency remains UNKNOWN.
====================================================================== -->

### Benchmark harness (AUTHORIZED IMPLEMENTATION + own semantic self-checks; measured trials separately authorized and NOT executed; Req 26, 27)

This section describes an **authorized benchmark harness implementation** and the harness's **own semantic self-checks**, following this tool's own `perf/` convention (`perf/benchmark.mjs` + `perf/validate-instrument.mjs`, Playwright headful Chrome). The former DESIGN-ONLY prohibition is lifted per amended Requirements 26-27. It still does **not** assert that any timing run, trial, probe, screenshot, trace, or metric has been executed or produced: the **six measured production trials** (two short headful probes, three Solo, three Duel 35s) are **separately authorized and NOT executed** under this authorization. The overall Sonar quality gate is **NOT** all-pass, and physical presentation latency is **UNKNOWN**. Traceability: see `docs/native-checks/21-stage4-benchmark-harness-authorization/NOTE.md`.

#### Implementation architecture (grounded in this tool's own inherited perf source)

- **Own perf source only (Req 26.1, 26.2).** EXTEND this tool's own `perf/benchmark.mjs` and `perf/validate-instrument.mjs`, plus small modular helpers as needed, using the native Canvas palette/schema and this tool's own native Stage 3 perf source. Do **not** copy researcher helper implementations; the legacy perf host port `5183` and the Stage 3 **DOM-cell** approach are OBSOLETE and are not carried forward. Install the harness's own perf `node_modules` from the existing pinned Playwright `1.56.0` lock: **no** browser, model, runtime, or dependency version upgrade.
- **One coherent executor (not per-metric).** Prefer ONE coherent executor driving both the implementation and the semantic self-checks; do **not** create an executor-per-metric. Reuse the canonical perf implementation leaf, or add exactly ONE coherent perf-implementation leaf.
- **Non-vacuous CLI entrypoint.** A runnable CLI entrypoint MUST actually invoke the driver and exit **NONZERO if no trial executed**. A vacuous entrypoint that performs no functional work cannot be reported as success, and a self-check proves this exit behavior.
- **Owned Chrome PID identification (Req 26.5, 26.6).** For the two Chrome instances in a duel, identify the actual OWNED Chrome process identifiers through a genuinely-verified PUBLIC Playwright API (e.g. `launchServer` / `browser.process()`). Do **not** guess a PID from the Node process or the current foreground window.
- **Read-only foreground telemetry (Req 26.5, 26.6).** OS foreground HWND/PID/title/visibility/rectangle telemetry may use a READ-ONLY Win32 / native PowerShell instrument that NEVER activates, moves, or fakes foreground itself. The harness emits a `READY_FOR_FOREGROUND` signal carrying the actual actor identity AFTER both clients open/join, waits BOUNDEDLY for a real foreground transition, and lets the controller/user activate the window. No `SetForegroundWindow`, `SendKeys`, or PowerShell UI-automation; no user start-question is asked during code implementation. Unique measurement-window titles MAY be set as transparent instrument metadata (recording the original title) and never alter game business state.
- **Pixel oracle (Req 27.1, 27.2, 27.3).** Avoid 200 separate GPU reads per frame: use a SINGLE actual Canvas image-buffer read plus 200 cell centers when qualifying an input effect. Keep the continuous `requestAnimationFrame`-scheduling observer lightweight and SEPARATE from pixel qualification; never infer that all rAF callbacks are verified draws. Pixel-oracle validation of the settled board plus active-piece geometry is independent and uses the actual Canvas palette with 200 cell centers (NOT the obsolete Stage 3 DOM-cell `MutationObserver`).
- **Clock domains and exclusions (Req 26.7, 27.3).** The actor input/browser clock and the peer pixel clock are DIFFERENT domains; paired Node `hrtime` / browser `performance` pre/post calibration and an explicit uncertainty bound are required. Negative or ambiguous latencies are EXCLUDED WITH a recorded reason and never clamped. A last-known-authority value or an unchanged mask is NOT causal pixel proof. Gravity-only and scalar-only effects are excluded; an ACK `no_op` and an O-piece rotation are excluded from changed-mask latency. Exact `room` / `seat` / `action_id` / `revision` correlations are required. No action is performed inside a poll predicate.
- **Input pattern (Req 26.3, 26.4).** Source inputs run at ~5 Hz with a balanced horizontal/rotation/down pattern that keeps a fresh game alive 35s without resetting. A fixed declared pattern `(right, right, right, down, cw, left, left, left, left, left, left, down, ccw, right, right, right)` is permitted IF it is declared before trials. Record every actual input and its accept/reject/no-op outcome. Stop source inputs at the declared end, retain pending late effects WITHOUT extrapolation. A `>= 5s` warm-up is excluded and a fixed `30s` measured window applies, with truly calibrated bounds/drift. Do not inject board state, seed or force pieces, hide game-over/restart, or omit failed trials.
- **Allowed observers (Req 27.1).** Only standard read-only DOM input / rAF / Canvas recorders and passive Playwright HTTP/WS event observation are allowed. NO `fetch`/`WebSocket` replacement, request interception, React internals, native app debug hooks, or injected authority.
- **Actual UI controls (recorded in this design).** Mode switches are `role="tab"` Solo/Duel; the room input label is `"Room name"`; the join button is `"Create or join"`; the actor Canvas selector is `'[aria-label="Your Tetris board"] canvas'`; the peer Canvas selector is `'[aria-label="Opponent Tetris board (read-only)"] canvas'`. Real input: left/right are `ArrowLeft`/`ArrowRight`, soft-drop is `ArrowDown`, CW is `ArrowUp`, CCW is `z` and `Z`. The production URL is `http://127.0.0.1:5517`; the production container stack is `tetris-stage4-kiro` on `5517`; solo FIFO/API/SQLite and duel non-persistence are preserved; the backend is not restarted during a measured trial.

#### Semantic self-checks (authorized; deliberately reject invalid evidence)

The harness's own semantic self-checks MUST deliberately REJECT each of: a wrong cell mask; a scalar-only or unchanged no-op mask treated as an action; a wrong `revision`/`room`/`seat`; a cross-clock subtraction; an invalid focus; an out-of-window sample; and a no-op CLI. A self-check must not rely on a test that only repeats its own formula, and there are no mirror-only tests that merely restate a helper. An actual CLI self-check proves the entrypoint calls the driver and returns NONZERO when there is no functional work.

#### Environment, trials, correlation, retention (unchanged honesty obligations)

- **Environment (Req 26.1, 26.2).** Drive the production frontend in a real **headful production Chrome channel with the sandbox enabled** (no hidden/headless fallback), at a **`1280x900`** viewport, **DPR 1**, recording the exact OS, browser, browser version, channel, hardware, configuration, and source metadata.
- **Trials (Req 26.3, 26.4).** Fresh session per trial, `>= 5s` warm-up excluded from measurement, a fixed measured window, and exactly **three solo** and **three duel** trials, each exercising real left, right, soft-drop, clockwise (`cw`), and counter-clockwise (`ccw`) actions. These measured trials are SEPARATELY AUTHORIZED and NOT executed under this authorization.
- **Duel foreground identity (Req 26.5, 26.6).** A duel trial opens **both** duel clients before approving actual-actor input foreground, identifies the actor's real **process identifier, window title, and window handle**, and observes the OS foreground state plus native focus throughout the measured window; it uses no hidden/headless fallback and does not steal focus during the measured window.
- **Clocks (Req 26.7).** True monotonic start / warm-up / measured / end bounds, with paired Node and browser calibration and drift measurement.
- **Evidence and correlation (Req 27.1, 27.2, 27.3).** The `requestAnimationFrame` scheduler stream is kept **separate** from the **CHANGED 200-cell RGBA masks** and verified draws; rAF frequency is never treated as rendering-throughput proof. Each action correlates the actual source input identity, key, and timestamp with the authorized ack/HTTP result, the authoritative board-and-revision effect, and the real target pixels, in the actor and peer clock domains. A change caused by ordinary gravity or a scalar-only change is not treated as action-visible proof.
- **Retention and honesty (Req 27.4, 27.5).** Each trial retains all samples, counts, exclusions, median, p95, p99, screenshots, and traces, and reports excluded samples with reasons; results are not pooled across trials and make no statistical-significance, scalability, or physical-presentation claims.
- **Targets (Req 27.6, 27.7, 27.8).** A scheduler mean `>= 55 FPS` and a p95 frame interval `<= 25 ms` are stated as **scheduling targets only**, kept separate from measurement qualification. The measured window never auto-restarts the game. The harness implementation and its self-checks are authorized; this document asserts **no executed metric** and no executed measured trial.

### On-disk process guardrail (Req 28)

Before any later corrective code, test, configuration, or benchmark change made in response to a failed or defective check, a **new dated native note must be written on disk** in this workspace (under `docs/native-checks/<nn>/`), identifying the observed defect and the intended correction, **before** the corresponding change is applied. Chat narration and a pre-existing broad note are not sufficient. If a check fails and the required dated on-disk note cannot be written first, the implementer reports the failure and stops rather than silently applying the correction.

### Retained scope boundaries (Req 29)

Stage 4 adds only rotation, the Canvas board, and the WebSocket duel; every other inherited behavior is preserved. It does not add a ghost piece, T-Spin scoring, hard-drop scoring changes, time attack, achievements, saved/resumable games, a non-SQLite database, authentication, player-name collection, a global/networked leaderboard, or cloud deployment. Duel games remain in memory only; the only persisted data remains the inherited completed solo-game high-score rows. Stage 4 performs no commits, pushes, image publishing, or external deployment on its own, and fabricates no approvals, checks, metrics, CI runs, tokens, costs, screenshots, Docker successes, coverage numbers, duplication numbers, or performance results.

<!-- =====================================================================
NATIVE 14 M3 LIFECYCLE / DELIVERY / FRONTEND CORRECTION (2026-11-06)
Pre-correction note on disk: docs/native-checks/14-m3-lifecycle-delivery-frontend-correction/NOTE.md
Added BEFORE implementing the corrections below. The canonical accepted wire
schema/corpus and numeric/policy decisions remain FROZEN; this section adds the
delivery/lifecycle architecture and the previously-omitted frontend duel client/view
and does not weaken any frozen obligation. The independent researcher checkpoint after
native 12 (docs/validation/12-m3-source-review/report.json) rejected M3 as
M3_NOT_ACCEPTED_ACTUAL_PUBLIC_START_BROADCAST_BLOCKER_AND_CLIENT_MISSING.
====================================================================== -->

## M3 Delivery / Lifecycle Correction (native 14)

### Independent per-connection writer / notification (corrects blocked reader)

The accepted design requires both seats to receive waiting/start/state/outcome/cleanup
frames, but the prior implementation flushed frames only to a socket that happened to
have inbound traffic: `_run_action_loop` blocks in `websocket.receive`, and merely
enqueuing a peer frame did not wake the waiting peer. The independent browser pair run
observed seat A never receiving the `room_status: "playing"` start frame after B joined.

Correction: each connected socket owns an INDEPENDENT bounded ORDERED writer task that
is the SINGLE writer for that socket and flushes queued frames WITHOUT requiring any
recipient inbound traffic. The reader task (`receive`) and the writer task run
concurrently per connection. A room mutation (action apply, gravity step, start,
outcome, cleanup) takes the SHORT per-room `state_lock` ONLY to produce consistent
DETACHED snapshots of both seats, then releases the lock and enqueues the snapshots onto
each recipient's bounded outbound queue (depth 64); the writer performs all bounded
network I/O (send with a 5s bound) OUTSIDE the lock. There are no unbounded task, queue,
or send retries. One slow or blocked peer can fill only its own bounded queue and must
never block another room, the other peer, or the worker; exceeding the bound or the send
deadline closes that socket and, in a STARTED room, triggers the one-time
`peer_unavailable_forfeit`. `_emit_cached` must NOT return `drain_result or True`: a
failed cached send is reported as a failure (it must never pretend a failed send
succeeded); the cached reply is delivered through the same bounded writer.

On teardown (normal completion, forfeit, operational abort, idle/handshake timeout,
shutdown), the owning coroutine cancels and awaits BOTH the reader and the writer for
that socket and releases the socket, the room's gravity task, and the room map entry
with no leaked task/socket/room. CancelledError raised during this teardown is
propagated/handled correctly (it is never silently swallowed) so cancellation actually
reaches the awaited reader/writer/gravity resources - this is the lifecycle semantics
behind the independent static BUG findings python:S7497 at
backend/app/duel/gravity.py and backend/app/main.py, which are corrected here with tests
rather than suppressed.

### Both authoritative boards delivered to both peers

Every state broadcast delivers BOTH seat boards to BOTH connected peers (each board as a
`StateFrame` carrying its own target `seat_id` and per-board `revision`), strictly scoped
to the assigned room. This covers the mandatory waiting and start transitions, ordinary
own and remote accepted movement/rotation/Hold, server-driven no-input gravity, the
terminal outcome, and the forfeit path. The gravity loop publishes state frames after it
advances boards (previously it mutated private games silently), and `main` wires the
room's `on_outcome` callback so a terminal/forfeit outcome frame is actually emitted to
both peers. Traffic-free waiting/idle/finished/shutdown cleanup frames reach both
recipients through the independent writer. Server monotonic deadlines stay independent of
manual actions; all boards due at a logical instant advance BEFORE a single outcome is
decided. No duel state is registered in `store.py` or the solo SQLite, and normal solo
play continues during a duel.

### Operational aborts wired at the endpoint

The operational aborts already specified in Error Handling are wired into `ws/duel.py`:
the maximum valid ordinal `999999999999999` is consumable, and the next-higher ordinal
closes the room with code 1001 and the literal reason `"sequence_exhausted"` (no
fabricated winner); a scalar value that WOULD overflow the SAFE integer bound closes the
room with code 1001 and the literal reason `"scalar_overflow"` for the room (no emitted
out-of-range state/revision), rather than closing only the actor and then invoking the
ordinary disconnect/forfeit path. These operational aborts are DISTINCT from the gameplay
`peer_unavailable_forfeit`. STRICT decoded-int typing (rejecting `bool`, string, and
`1.0`) and the full-string `action_id` grammar (LF/CR/CRLF/U+2028/U+2029 rejected via a
Python `re`-backed Pydantic custom validator, never a soft `$`) are enforced as already
specified.

## M3 Frontend Duel Client and View (native 14; previously MISSING)

The seed requires each player to control a separate board AND see BOTH authoritative
boards, with real movement/rotation synchronization. The prior frontend stayed solo-only;
no duel client, view, or duel frontend test existed. This section adds the concrete
frontend design.

### Duel WebSocket client (`frontend/src/duelClient.ts`, new)

A real standard browser `WebSocket` client (no monkeypatch, no fetch/WebSocket
interception, no production debug hook/endpoint, no React-internal access, no source
input interception). It opens a same-origin `ws(s)://<host>/ws/duel`, sends `hello` with
the chosen `room_id`, and exposes a typed callback stream of `welcome`, `state` (per
seat), `ack`, `reject`, `error`, and `outcome` frames. It owns exactly the one socket and
its listeners; `close()` removes its own listeners and closes only that socket. It emits
EXACTLY ONE canonical `action` per authorized local input, with a monotonically
increasing own-seat ordinal (prefix `A-`/`B-` matching the assigned seat) and the last
authoritative OWN-board revision as `expected_revision`. It performs NO local-predicted
board, seed, or gravity; the board shown is always the latest authoritative frame.

### Duel view and mode switch (`frontend/src/DuelView.tsx` + `App.tsx` mode state)

`App.tsx` gains an accessible mode switch between the existing solo view and a new duel
view; solo stays reachable. The duel view provides accessible named-room
create/join/wait/start/error/finished/return/restart flows (a restart is a FRESH room,
never a reused finished room). It reuses `CanvasBoard` for BOTH authoritative duel boards
(own and opponent), and shows meaningful own and opponent status/score/lines/level/next/
Hold plus the own controls. The opponent board is read-only (no controls wired to it).
The whole duel layout (both boards + panels + own controls) fits `1280x900` at DPR 1 and
2 with no page overflow, clipping, or overlap; the solo view does NOT require three
simultaneous boards.

Lifecycle safety: only OWNED sockets/listeners/handlers are cleaned up on mode switch,
restart, and unmount. While in duel mode there is NO hidden solo autotick and NO solo
keyboard listener; while in solo mode there is no stale duel socket effect, and switching
to a fresh room leaves no stale socket effect. A late/old `ack` or any stale, wrong-room,
or wrong-generation frame is ignored and never rolls back newer authority; A and B state
are never cross-wired.

Input: one real `ArrowUp`/`z`/`Z` (rotate), `ArrowLeft`/`ArrowRight` (move),
`ArrowDown` (soft drop), and the Hold key each emit EXACTLY ONE canonical action through
the duel client, gated on the room being `playing` and on owning the acting seat.

### Frontend duel tests (behavioral, native self-tests)

Meaningful behavioral tests with explicit event sends and EXACT action counts, with the
triggering input performed OUTSIDE `waitFor`, covering: start gating (no action accepted
while waiting), one-input-one-action with monotonic ordinals and the last own revision,
both-boards render from authoritative frames, old/late-ACK no-rollback, stale/wrong-room/
wrong-generation frame rejection, no A/B cross-wiring, error/race paths, unmount/mode-
switch/restart cleanup (no leaked socket/listener, no solo autotick or solo key listener
during duel, no stale socket after a fresh room), and the start/sync path. These native
mocks are SELF-TESTS only; they are never treated as production wire, pixel, focus, or
performance proof (that remains an independent researcher checkpoint after this call).

### Native self-checks for this correction (Req 24, no threshold/scope change)

Full backend coverage (XML) and full frontend coverage (LCOV, with every executable new
client/view module included, no source/coverage exclusion, no assertion removal) plus the
frontend build; backend tests for actual server pushes WITHOUT inbound messages,
two-client own+opponent boards, traffic-free cleanup, the public transport seams, and the
operational bounds; local audits / pip check. No threshold/scope/baseline weakening. The
independent Sonar NEW-coverage/static gate is NOT marked accepted by this tool; it is an
independent researcher checkpoint after this call closes, and failures/raw outputs are
preserved.

