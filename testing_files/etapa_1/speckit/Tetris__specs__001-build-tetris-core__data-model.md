# Data Model & State Transitions: build-tetris-core

## Entity Schemas

### 1. GameSession (Game State)
The primary state container represents an ongoing single-player Tetris session.

#### Python Pydantic Model (Backend)
```python
from pydantic import BaseModel, Field
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

    class Config:
        populate_by_name = True
```

#### TypeScript Interfaces (Frontend)
```typescript
export interface Tetromino {
  type: 'I' | 'O' | 'T' | 'S' | 'Z' | 'J' | 'L';
  cells: [number, number][]; // [row, col]
  origin: [number, number];   // [row, col]
}

export interface GameSession {
  id: string;
  board: number[][]; // 20 rows x 10 columns
  activePiece: Tetromino | null;
  status: 'playing' | 'game_over';
}
```

---

## Validation & Boundary Constraints

### 1. Board Structural Validation
- **Row Count**: Must contain exactly $20$ rows.
- **Column Count**: Each row must contain exactly $10$ cells.
- **Value Domain**: Cells must only store values between `0` and `7` (inclusive).
  - `0`: Empty.
  - `1`: I Piece (Cyan)
  - `2`: O Piece (Yellow)
  - `3`: T Piece (Purple)
  - `4`: S Piece (Green)
  - `5`: Z Piece (Red)
  - `6`: J Piece (Blue)
  - `7`: L Piece (Orange)

### 2. Piece Boundary Validation
Any active piece's cells coordinates `(r, c)` must satisfy:
- $0 \le r \le 19$
- $0 \le c \le 9$

If any cell coordinate falls outside these bounds, or if the cell overlaps a non-zero index in `board[r][c] != 0`, a **Collision Exception** is raised internally, and the state-mutating command is rejected (reverted with no changes).

---

## State Machine and Lifecycle Transitions

The game session executes a predictable, deterministic state machine driven by client requests.

```text
       +---------------------------------------------+
       |                                             |
       v                                             |
[ INITIALIZE ] --> (Spawn Piece) --> [ PLAYING ] ----+ (Tick - No Collision)
                                        |   |
                                        |   +--------> (Move command - Left/Right/Down)
                                        |
                             (Tick - Collision)
                                        |
                                        v
                                  [ LOCK PIECE ]
                                        |
                                        v
                               [ CHECK LINE CLEARS ]
                                        |
                                        +-------------------+
                                        |                   |
                               (No Spawn Overlap)   (Spawn Overlap)
                                        |                   |
                                        v                   v
                                 (Spawn Next Piece)   [ GAME OVER ]
                                        |                   |
                                        v                   |
                                    [ PLAYING ]             |
                                        ^                   |
                                        |                   |
                                        +----(Restart)------+
```

### 1. Transition: Initialize Game / Restart
- **Trigger**: `POST /api/games` or Restart command.
- **Pre-State**: Any state (or none).
- **Post-State**: `status = "playing"`
- **Actions**:
  1. Initialize `board` to a $20 \times 10$ matrix filled entirely with `0`.
  2. Select a random standard shape from the $7$ shapes with equal probability ($14.28\%$).
  3. Create an `activePiece` at the predefined top-center starting coordinates.
  4. Generate and return a unique UUID for the session.

### 2. Transition: Horizontal Move (Left/Right)
- **Trigger**: `POST /api/games/{id}/move` with direction `"left"` or `"right"`.
- **Pre-State**: `status == "playing"` (ignored if `"game_over"`).
- **Actions**:
  1. Calculate potential target coordinates: `(r, c - 1)` for left, `(r, c + 1)` for right for all 4 cells.
  2. Run collision check.
  3. If no collision: update `activePiece.cells` and `activePiece.origin` column coordinates.
  4. If collision: ignore, leaving existing coordinates intact (reverts to previous coordinates).

### 3. Transition: Manual Down Move (Soft Drop)
- **Trigger**: `POST /api/games/{id}/move` with direction `"down"`.
- **Pre-State**: `status == "playing"` (ignored if `"game_over"`).
- **Actions**:
  1. Calculate potential target coordinates: `(r + 1, c)` for all 4 cells.
  2. Run collision check.
  3. If no collision: update `activePiece.cells` and `activePiece.origin` row coordinates.
  4. If collision: **Do not lock yet**. Lock behavior is exclusively executed on automatic gravity ticks to allow players timing slide maneuvers.

### 4. Transition: Gravity Tick
- **Trigger**: `POST /api/games/{id}/tick`.
- **Pre-State**: `status == "playing"` (ignored if `"game_over"`).
- **Actions**:
  1. Calculate potential target coordinates: `(r + 1, c)`.
  2. Run collision check.
  3. **Case A: No Collision**:
     - Increment row coordinates of all active piece cells by $1$.
     - Increment row coordinate of active piece origin by $1$.
  4. **Case B: Collision Detected**:
     - Write the active piece's colors into the `board` matrix.
     - Scan and remove completed horizontal rows. Shift preceding rows downward and fill top row with `0`s.
     - Spawn a new random piece at top-center.
     - Check if newly spawned piece collides with any settled blocks:
       - If collision detected: set `status = "game_over"`, and set `activePiece = null`.
       - If no collision: keep status as `"playing"`.
