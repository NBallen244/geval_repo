# Data Model & State Transitions: Extend Tetris to Stage 2

This document details the updated schemas, validation rules, state-machine transitions, and lifecycle invariants for the Stage 2 single-player Tetris implementation.

---

## Entity Schemas

### 1. GameSession (Game State)
The primary in-memory container that represents the authoritative, server-validated state of a single-player Tetris session.

#### Python Pydantic Model (Backend)
```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class TetrominoSchema(BaseModel):
    type: str = Field(..., description="One of 'I', 'O', 'T', 'S', 'Z', 'J', 'L'")
    cells: List[List[int]] = Field(..., description="Exactly 4 coordinate pairs: [[row, col], ...]")
    origin: List[int] = Field(..., description="Pivot coordinate: [row, col]")

class GameSessionSchema(BaseModel):
    id: str = Field(..., description="Unique UUID string representing the game session")
    board: List[List[int]] = Field(..., description="20x10 grid. 0 = empty cell; 1-7 = settled piece colors")
    active_piece: Optional[TetrominoSchema] = Field(None, alias="activePiece")
    status: str = Field(..., description="Session status: 'playing' or 'game_over'")
    
    # Stage 2 Extended Properties
    score: int = Field(0, description="Cumulative score for the session")
    total_lines: int = Field(0, description="Total number of lines cleared in this session", alias="total_lines")
    level: int = Field(1, description="Current game level, starting at 1")
    gravity_interval_ms: int = Field(500, description="Tick speed interval in milliseconds, ranging from 100 to 500")
    next_piece: str = Field(..., description="The one-letter tetromino type of the next piece queued to spawn")
    hold_piece: Optional[str] = Field(None, description="The one-letter tetromino type currently stored in the Hold slot, or null")
    can_hold: bool = Field(True, description="True if the user can perform a Hold/Swap action; False if already swapped this piece")

    class Config:
        populate_by_name = True
```

#### TypeScript Interfaces (Frontend)
```typescript
export interface Tetromino {
  type: 'I' | 'O' | 'T' | 'S' | 'Z' | 'J' | 'L';
  cells: [number, number][]; // [row, col] coordinates on the 20x10 board
  origin: [number, number];   // [row, col] rotation/positional pivot
}

export interface GameSession {
  id: string;
  board: number[][]; // 20 rows x 10 columns
  activePiece: Tetromino | null;
  status: 'playing' | 'game_over';
  score: number;
  total_lines: number;
  level: number;
  gravity_interval_ms: number;
  next_piece: 'I' | 'O' | 'T' | 'S' | 'Z' | 'J' | 'L';
  hold_piece: 'I' | 'O' | 'T' | 'S' | 'Z' | 'J' | 'L' | null;
  can_hold: boolean;
}
```

---

## Validation & Boundary Constraints

### 1. Board Structural Validation
- **Row Count**: Must contain exactly $20$ rows.
- **Column Count**: Each row must contain exactly $10$ cells.
- **Cell Range**: Each cell value must be an integer in the range $[0, 7]$ (where `0` is empty, and `1-7` map to colored tetromino blocks).

### 2. Piece Attribute Validation
- **Type**: Must be one of `{"I", "O", "T", "S", "Z", "J", "L"}`.
- **Cells**: An array containing exactly $4$ coordinate pairs `[row, col]`.
- **Coordinates boundaries**: For every cell `[row, col]`, `0 <= row <= 19` and `0 <= col <= 9`.
- **Origin**: A coordinate pair `[row, col]` representing the piece's rotation pivot, bounded within `[0, 19]` (rows) and `[0, 9]` (columns).

### 3. Extended Stage 2 Field Ranges
- **Score**: Integer, must be non-negative ($\ge 0$).
- **Total Lines**: Integer, must be non-negative ($\ge 0$).
- **Level**: Integer, must be $\ge 1$.
- **Gravity Interval**: Integer, bounded between `100` and `500` ms (inclusive).
- **Hold Piece**: Must be `null` or one of the seven valid single-letter tetromino types.

---

## State Transitions & Life-Cycle

The game session transitions through the following actions:

```
                          +------------------------+
                          |   POST /api/games      |
                          +-----------+------------+
                                      |
                                      v
                        +-------------+------------+
                        |  State: "playing"        |
                        |  score = 0, level = 1    |
                        |  active_piece & next_piece |
                        |  hold_piece = null        |
                        +---+---------+--------+---+
                            |         |        |
         POST /api/.../move |         |        | POST /api/.../hold
         (left, right, down)|         |        |
                            v         v        v
                        +-------------+------------+
                        |                          |
                        |   Game Loop / Tick       | <------+
                        |   (POST /api/.../tick)   |        |
                        |                          |        | Normal
                        +---+------------------+---+        | Gravity
                            |                  |            | Tick
                            | Collision on     | No         |
                            | Gravity Tick     | Collision  |
                            v                  v            |
                    +-------+-------+     +----+---+--------+
                    | Lock Piece &  |     | Move   |
                    | Clear Lines   |     | Down   |
                    +-------+-------+     +--------+
                            |
                     Spawn New Piece (from next_piece)
                            |
                 Is Spawning Coordinate Blocked?
                     /                  \
                    /                    \
            Yes    v                      v No
            +------+--------+     +-------+-------+
            | "game_over"   |     | Reset         |
            | activePiece=  |     | can_hold=true |
            | null          |     +---------------+
            +---------------+
```

### 1. Initialization (Create/Restart)
Triggered by `POST /api/games`.
- **Action**: Resets or initializes a session.
- **State Changes**:
  - `board` is filled with $20 \times 10$ zeros (`0`).
  - `score` is set to `0`.
  - `total_lines` is set to `0`.
  - `level` is set to `1`.
  - `gravity_interval_ms` is set to `500`.
  - `hold_piece` is set to `null`.
  - `can_hold` is set to `true`.
  - `status` is set to `"playing"`.
  - `active_piece` spawns at top-center with a randomly generated tetromino type.
  - `next_piece` is populated with a second, randomly generated tetromino type (independent of `active_piece`).

### 2. Manual Move (Left / Right / Down)
Triggered by `POST /api/games/{id}/move` with `direction = "left" | "right" | "down"`.
- **Constraint**: If `status == "game_over"` or `active_piece == null`, ignore the command.
- **Action**:
  - Computes proposed cells:
    - `"left"`: `[r, c - 1]`
    - `"right"`: `[r, c + 1]`
    - `"down"` (Soft drop): `[r + 1, c]`
  - Performs a collision check `has_collision(board, proposed_cells)`.
  - If no collision: Updates `active_piece` cells and origin coordinate.
  - If collision: Keeps current coordinates. **Note**: Manual soft drop down NEVER triggers piece locking or scoring.

### 3. Piece Swapping (Hold)
Triggered by `POST /api/games/{id}/hold`.
- **Constraint**: If `status == "game_over"` or `can_hold == false`, ignore the command and return current state.
- **Action (When Hold slot is Empty - `hold_piece == null`)**:
  - Store current `active_piece.type` in `hold_piece`.
  - Spawn a new `active_piece` at the top-center using the `next_piece` type.
  - Generate a new random tetromino type for `next_piece`.
  - Set `can_hold = false`.
- **Action (When Hold slot is Occupied - `hold_piece != null`)**:
  - Swap current `active_piece.type` with `hold_piece` (the current active piece's type is stored in `hold_piece`, and the previously held piece type is spawned as the new `active_piece` at the top-center in its initial unrotated orientation).
  - Do NOT modify or consume `next_piece`.
  - Set `can_hold = false`.
- **Edge Case**: If the newly spawned piece coordinates from a Hold action overlap with settled blocks at the top-center spawn origin, transition `status` to `"game_over"` and set `active_piece = null`.

### 4. Gravity Tick (Ticking, Locking, Line Clearing & Spawning)
Triggered by `POST /api/games/{id}/tick`.
- **Constraint**: If `status == "game_over"`, ignore and return current state.
- **Action**: Computes proposed cells shifted down by one row: `[r + 1, c]`.
- **Path A (No Collision)**:
  - Updates `active_piece` cells and origin down by one row.
- **Path B (Collision - Lock, Score & Respawn)**:
  - Write active piece colors to the board: `board[r][c] = color_id` (where color_id matches the piece type 1-7).
  - Scan the board for complete horizontal rows (all 10 cells are non-zero) and filter them out.
  - Insert empty rows of `[0] * 10` at row index 0 to replace cleared rows.
  - Let `cleared_count` be the number of rows removed.
  - If `cleared_count > 0`:
    - Add scoring points: `score += multiplier * level` (using the level active *immediately before* clearing):
      - 1 row: `100 * level`
      - 2 rows: `300 * level`
      - 3 rows: `500 * level`
      - 4 rows: `800 * level`
    - Add to total: `total_lines += cleared_count`.
    - Recalculate level: `level = 1 + floor(total_lines / 10)`.
    - Recalculate speed: `gravity_interval_ms = max(100, 500 - 50 * (level - 1))`.
  - Reset `can_hold = true`.
  - Spawn the next piece from the queue: Create a new `active_piece` at top-center using `next_piece` type.
  - Generate a new random piece type for `next_piece`.
  - If the newly spawned piece's coordinates collide with settled blocks, set `status = "game_over"` and `active_piece = null`.
