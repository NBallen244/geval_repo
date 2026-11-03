# Implementation Research: build-tetris-core

## Domain Analysis & Core Mechanics

### 1. Board Representation & Coordinate System
The game board is modeled as a 2D grid matrix of size $20 \times 10$ ($20$ rows, $10$ columns).
- **Coordinate Conventions**: Row index $0$ represents the absolute top of the board, and row index $19$ is the bottom row. Column index $0$ is the leftmost column, and column index $9$ is the rightmost column.
- **Cell States**: Cells are integers. `0` represents an empty cell, while non-zero integers (e.g., `1` through `7` mapped to standard tetromino colors/types) represent settled blocks.
- **Active Piece Coordinates**: An active piece has a shape type, its current cells (an array of four coordinates `(row, col)` representing its active blocks), and its origin coordinate `(row, col)` which acts as the anchor.

### 2. Standard Tetromino Initial Predefined States
Since rotation is excluded, each of the standard $7$ tetrominoes only exists in its initial predefined shape:
- **I Piece**: Spawns horizontally occupying cells on row 0: `[(0, 3), (0, 4), (0, 5), (0, 6)]` with origin `(0, 4)`.
- **O Piece**: Spawns as a $2 \times 2$ block occupying cells on rows 0 and 1: `[(0, 4), (0, 5), (1, 4), (1, 5)]` with origin `(0, 4)`.
- **T Piece**: Spawns horizontally with central protrusion pointing down: `[(0, 4), (1, 3), (1, 4), (1, 5)]` with origin `(1, 4)`.
- **S Piece**: Spawns horizontally: `[(0, 4), (0, 5), (1, 3), (1, 4)]` with origin `(1, 4)`.
- **Z Piece**: Spawns horizontally: `[(0, 3), (0, 4), (1, 4), (1, 5)]` with origin `(1, 4)`.
- **J Piece**: Spawns horizontally with left tail pointing up: `[(0, 3), (1, 3), (1, 4), (1, 5)]` with origin `(1, 4)`.
- **L Piece**: Spawns horizontally with right tail pointing up: `[(0, 5), (1, 3), (1, 4), (1, 5)]` with origin `(1, 4)`.

All pieces spawn at the top-center (rows 0 and 1) such that they are centered horizontally within the 10-column board.

### 3. Collision Detection Math
A collision check function `has_collision(board, cells)` takes the board grid and the proposed candidate cells of the active piece:
- **Boundary Collisions**: Returns `true` if any proposed cell has `row < 0` (above top is not blocked but let's constrain `row >= 0` for game play), `row > 19` (below bottom), `col < 0` (left of left wall), or `col > 9` (right of right wall).
- **Settled Block Collisions**: Returns `true` if any cell has `board[row][col] != 0`.

### 4. Movement Mechanics
- **Left/Right Moves**: On manual commands, compute proposed cells as `(row, col - 1)` or `(row, col + 1)`. If `has_collision` is false, update active piece cells and column coordinates. If true, keep current state unchanged.
- **Downward Moves (Gravity / Soft Drop)**: Compute proposed cells as `(row + 1, col)`.
  - If `has_collision` is false: Update active piece cells.
  - If `has_collision` is true:
    - On gravity tick: Lock the piece immediately.
    - On manual down command: Do not move. (Locking only happens on a gravity tick when in contact with a block/floor, or on a subsequent gravity tick).

### 5. Locking and Line Clearing Logic
When a downward gravity tick results in a collision:
1. **Lock Piece**: Write the active piece's shape color index to the board matrix: `board[row][col] = piece_color_id` for each cell in `active_piece.cells`.
2. **Line Check**: Scan rows from $19$ up to $0$. A row is completed if all $10$ cells have non-zero values.
3. **Clear Rows**: Remove any completed rows.
4. **Shift Rows**: For each cleared row, shift all rows above it down by 1.
5. **Append Top Rows**: Insert empty rows of `[0, 0, ..., 0]` at row index $0$.
6. **Spawn Next Piece**: Generate a new random piece at top-center. If `has_collision` is true immediately upon spawn, transition game status to `"game_over"`.

---

## Technical Design Decisions

### 1. Backend: FastAPI and Pydantic
FastAPI is chosen for the backend due to its outstanding speed, automatic validation with Pydantic, and OpenAPI generation capabilities.
- **State Management**: Game sessions are held in a global, thread-safe in-memory Python dictionary `games: dict[str, GameState]`. No database is needed.
- **Tick Loop**: There is no active backend-driven thread timer for gravity ticks. This keeps the backend server simple, stateless across sessions, and resource-light. The frontend holds the primary clock and executes gravity tick endpoints via POST requests.

### 2. Frontend: React, TypeScript & Vite
Vite is selected as the fast build tool. React state manages the visual presentation.
- **Rendering**: The board is rendered as a clean grid of cells using native CSS Grid.
- **Styling**: Vanilla CSS is used for custom theme parameters, colors, and layout. No TailwindCSS is used.
- **Tick Synchronization**: A robust React `useEffect` interval calls the `/api/games/{id}/tick` endpoint every 500 ms while status is `"playing"`. This ensures the backend remains the authority on state transitions while keeping client-side loops easy to manage.

---

## Alternatives Considered

### 1. WebSocket for State Synchronization
- **Description**: Maintaining a persistent TCP connection via WebSockets and pushing tick states from a backend thread timer.
- **Rejection Reason**: Over-engineered for a simple single-player study with 500ms intervals. HTTP polling is extremely reliable, easy to inspect, stateless, and fully conforms to the interface requirements.

### 2. Frontend-Driven Game State
- **Description**: Managing all collision, locking, and line-clearing logic on the frontend, using the backend only to log scores.
- **Rejection Reason**: Violates the directive "backend MUST own the authoritative game state and rules". Keeping rules backend-centric ensures clean separation of concerns and high testability of the core logic.
