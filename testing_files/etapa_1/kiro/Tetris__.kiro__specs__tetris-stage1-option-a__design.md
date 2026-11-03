# Design Document

## Overview

Stage 1, Option A is a decoupled two-tier application. A Python FastAPI backend owns the authoritative Tetris game state and all rules. A React + TypeScript frontend renders state fetched from the backend HTTP API and forwards player controls. There is no database and no authentication; all state lives in an in-memory store.

The backend is organized into three layers to keep game rules testable without the HTTP layer:

- **Domain models** (`domain/`): pure data structures for pieces, board, and game state.
- **Game rules** (`rules/`): pure functions that operate on domain models (spawn, move, tick, lock, clear lines, detect game over). No framework dependencies.
- **HTTP controllers** (`api/`): FastAPI routers that translate requests into rule calls and serialize domain models to JSON.

An in-memory repository holds games by id. A deterministic piece generator (seeded) produces the tetromino sequence for reproducibility.

## Architecture

```
frontend (React + TS)
  │  HTTP JSON
  ▼
FastAPI app
  ├── api/games.py         # controllers (routers)
  ├── api/schemas.py       # request/response Pydantic models
  ├── store.py             # in-memory game repository
  ├── rules/engine.py      # pure game rules
  ├── rules/pieces.py      # tetromino definitions + seeded generator
  └── domain/models.py     # Board, ActivePiece, Game dataclasses
```

### Request flow

1. `POST /api/games` -> controller asks the store to create a Game via `engine.new_game(seed)`; returns serialized state.
2. `GET /api/games/{id}` -> controller fetches Game from store; 404 if missing; returns serialized state.
3. `POST /api/games/{id}/tick` -> controller calls `engine.tick(game)`; store updated in place; returns serialized state.
4. `POST /api/games/{id}/move` -> controller validates direction (Pydantic), calls `engine.move(game, direction)`; returns serialized state.

## Components and Interfaces

### Domain models (`domain/models.py`)

```python
PieceType = Literal["I", "O", "T", "S", "Z", "J", "L"]
Status = Literal["playing", "game_over"]

@dataclass
class ActivePiece:
    type: PieceType
    origin: tuple[int, int]        # (row, col) of bounding-box top-left
    cells: list[tuple[int, int]]   # absolute occupied (row, col)

@dataclass
class Game:
    id: str
    status: Status
    board: list[list[Optional[PieceType]]]  # 20 x 10, None = empty
    active: Optional[ActivePiece]
    rng: random.Random                        # seeded generator state
    seed: int
```

### Pieces (`rules/pieces.py`)

- `SHAPES: dict[PieceType, list[tuple[int,int]]]` — relative offsets for the initial orientation (as defined in requirements).
- `SPAWN_COLUMN = 3`, `SPAWN_ROW = 0`.
- `PieceGenerator`: wraps a seeded `random.Random`; `next_type()` returns the next `PieceType`. To guarantee all seven types can appear and to keep the sequence bounded, it uses a shuffled 7-bag; the bag is refilled and shuffled with the seeded RNG when empty. This keeps reproducibility (Req 4) and full coverage (Req 3.3).

### Game rules (`rules/engine.py`)

Pure functions (no FastAPI imports):

- `new_game(game_id: str, seed: int) -> Game`: empty board, status `playing`, spawn first piece.
- `_absolute_cells(type, origin) -> list[tuple[int,int]]`: offsets + origin.
- `_is_valid(board, cells) -> bool`: all cells in bounds AND not overlapping settled blocks.
- `spawn(game) -> None`: build next piece at spawn origin; if invalid -> status `game_over`, `active = None`.
- `move(game, direction) -> None`: compute candidate cells/origin; for `left`/`right` apply if valid else no-op; for `down` apply if valid else `lock(game)`.
- `tick(game) -> None`: if `active` can move down, move down; else `lock(game)`. No-op if `game_over`.
- `lock(game) -> None`: write active cells into board; `clear_lines(game)`; then `spawn(game)`.
- `clear_lines(game) -> int`: remove fully filled rows, shift down, insert empty rows at top; returns count.

Ordering guarantee (Req 21): `lock` calls `clear_lines` before `spawn`.

### API schemas (`api/schemas.py`)

- `MoveRequest`: `direction: Literal["left","right","down"]` (invalid -> 422 automatically, Req 26).
- `ActivePieceOut`: `type`, `origin: [row,col]`, `cells: [[row,col],...]`.
- `GameStateOut`: `id: str`, `status: str`, `board: list[list[int]]`, `active_piece: Optional[ActivePieceOut]`.

Board serialization maps `None -> 0` and a piece type -> a stable small integer code (I=1, O=2, T=3, S=4, Z=5, J=6, L=7) so the frontend can color cells while keeping the payload compact. `active_piece.type` remains the letter for clarity.

### Controllers (`api/games.py`)

FastAPI `APIRouter` with the four endpoints. Uses the in-memory `store`. Unknown id -> `HTTPException(404)`.

### In-memory store (`store.py`)

- `create(seed) -> Game` generates a uuid id, builds via `engine.new_game`, saves in a dict.
- `get(id) -> Game | None`.

A single fixed default seed is used so the study is reproducible; the seed constant is documented in the README.

### Frontend (`frontend/`)

Vite + React + TypeScript.

- `src/api.ts`: typed fetch client for the four endpoints. Base URL from `VITE_API_BASE` (default `http://localhost:8000`).
- `src/types.ts`: `GameState`, `ActivePiece` mirroring the API.
- `src/useGame.ts`: hook holding game state; a `useEffect` sets a `setInterval` of 500 ms that calls tick while `playing`; clears interval on `game_over` (Req 30). Exposes `move`, `restart`.
- `src/Board.tsx`: renders a 20x10 grid. Merges settled board with active piece cells for display (active cells overlaid at their color). Rendering only; no rule logic (Req 29.3).
- `src/App.tsx`: layout, keyboard listeners (ArrowLeft/ArrowRight/ArrowDown), Restart button, and game-over message.

Keyboard mapping (Req 31): ArrowLeft -> left, ArrowRight -> right, ArrowDown -> down.

## Data Models

### Board

`list[list[Optional[PieceType]]]`, 20 rows x 10 columns, `None` = empty. Serialized to integer codes for the API.

### Coordinate system

Row 0 top, row 19 bottom; column 0 left, column 9 right. Downward move increases row index. This is applied consistently in rules and rendering.

## Error Handling

- Unknown game id on `GET`/`tick`/`move` -> HTTP 404 (Req 7.2, 26.2).
- Invalid or missing `direction` -> HTTP 422 via Pydantic (Req 26.1).
- Tick/move after `game_over` -> no-op, state returned unchanged (Req 23).
- CORS is enabled for the local frontend origin so the browser can call the API during development.

## Testing Strategy

Backend tests use `pytest` against the pure rule functions plus a thin set of API tests via FastAPI `TestClient`:

- Board size and initialization (Req 1).
- Spawn position and bounds (Req 5), piece set coverage and determinism under a fixed seed (Req 3, 4).
- Legal left/right/down moves and rejection at walls and against the stack (Req 9–15).
- Bottom collision and locking on blocked tick and on blocked soft drop (Req 11, 14, 16).
- Single-line clear, multi-line clear, and no-clear cases with row-shift correctness (Req 18–20).
- Clearing precedes spawn ordering (Req 21).
- Game-over on spawn collision and input no-ops afterward (Req 22, 23).
- API contract: creation, read, 404, 422, payload shape (Req 2, 7, 25, 26).

To construct deterministic collision/clear scenarios independent of the random sequence, rule tests build `Game` objects directly with a crafted board and a chosen active piece, then invoke `engine` functions. This keeps tests atomic and independent of the piece generator.

Frontend reproducibility is validated by running the production build (`npm run build`) which type-checks (via `tsc`) and bundles with Vite (Req 35.2).

### Documented commands

- Backend install: `python -m venv .venv` then activate and `pip install -r requirements.txt`.
- Backend run: `uvicorn app.main:app --reload` (from `backend/`).
- Backend tests: `pytest` (from `backend/`).
- Frontend install: `npm install` (from `frontend/`).
- Frontend dev: `npm run dev`.
- Frontend build: `npm run build`.
