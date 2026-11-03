# OpenSpec Core Specification: Tetris Game Mechanics & API Contracts

## Purpose
Core game mechanics, coordinate systems, tetromino definitions, spawning rules, collision and locking logic, line clearing, and authoritative REST API contracts for Tetris Stage 1 Option A.

## 1. Board Geometry & Coordinate System
- The game board is a grid of 20 rows (index 0 to 19 from top to bottom) and 10 columns (index 0 to 9 from left to right).
- Coordinates are represented as `[row, col]`.
- The origin coordinates `[0, 0]` represent the top-left cell of the board.
- The bottom-right coordinate is `[19, 9]`.
- Settled blocks are stored in a 20-row by 10-column matrix where `null` denotes empty cells, and positive integers or strings indicate block presence.

## 2. Tetromino Definitions & Spawning
All seven standard tetrominoes are represented by a set of coordinates relative to their own local coordinate grid in `[row, col]` format:

1. **I Piece:** Local coordinate cells: `[[1, 0], [1, 1], [1, 2], [1, 3]]` (horizontal row)
2. **O Piece:** Local coordinate cells: `[[1, 1], [1, 2], [2, 1], [2, 2]]` (2x2 square)
3. **T Piece:** Local coordinate cells: `[[1, 1], [2, 0], [2, 1], [2, 2]]` (T-shape)
4. **J Piece:** Local coordinate cells: `[[1, 0], [2, 0], [2, 1], [2, 2]]` (J-shape)
5. **L Piece:** Local coordinate cells: `[[1, 2], [2, 0], [2, 1], [2, 2]]` (L-shape)
6. **S Piece:** Local coordinate cells: `[[1, 1], [1, 2], [2, 0], [2, 1]]` (S-shape)
7. **Z Piece:** Local coordinate cells: `[[1, 0], [1, 1], [2, 1], [2, 2]]` (Z-shape)

### Spawning Logic
- When a new piece spawns, its bounding box origin is initialized at row index 0 and column index 3 (`[0, 3]`) such that the piece is centered horizontally at the top of the grid.
- Pieces spawn in their initial orientations only.

## 3. Collision, Movement, & Locking
- **Movement Left:** `[row, col - 1]`. Shifting left is legal if and only if all cells of the shifted piece lie within column index bounds `[0, 9]` and do not overlap with settled blocks.
- **Movement Right:** `[row, col + 1]`. Shifting right is legal if and only if all cells of the shifted piece lie within column index bounds `[0, 9]` and do not overlap with settled blocks.
- **Soft Drop / Gravity Tick:** `[row + 1, col]`. Advancing down is legal if all cells of the shifted piece lie within row index bounds `[0, 19]` and do not overlap with settled blocks.
- **Locking Logic:** If a downward shift (soft drop or gravity tick) is illegal because it would exceed the bottom border (row > 19) or collide with any settled block, the active piece is immediately locked into its current coordinates.
- **Line Clearing:** Following a lock, any row index in `[0, 19]` where all 10 columns are filled is cleared. Full rows are removed. All rows above are shifted down by the number of cleared rows. Empty rows are prepended at the top (row index 0) with a value of `null`.
- **GameOver Condition:** If a newly spawned piece collides with already settled blocks, the game status transitions to `game_over`.

## 4. REST API Endpoint Specification

### 4.1. POST `/api/games`
Creates or restarts a game session.
- **Request Body:** None
- **Response Status:** 201 Created
- **Response Body (JSON):**
```json
{
  "id": "e6384dd1-d4d3-4a03-948f-de8fa3f80c65",
  "board": [
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null],
    [null,null,null,null,null,null,null,null,null,null]
  ],
  "active_piece": {
    "type": "T",
    "cells": [[1,4], [2,3], [2,4], [2,5]],
    "origin": [0, 3]
  },
  "status": "playing"
}
```

### 4.2. GET `/api/games/{id}`
Retrieves the current game state.
- **Response Status:** 200 OK
- **Response Body (JSON):** Same as `POST /api/games`.

### 4.3. POST `/api/games/{id}/tick`
Advances the active piece down by one row due to gravity.
- **Response Status:** 200 OK
- **Response Body (JSON):** Same as `POST /api/games`, showing the piece in its new position or the updated board state (with locking, spawning, or game over applied).

### 4.4. POST `/api/games/{id}/move`
Executes a movement.
- **Request Body (JSON):**
```json
{
  "direction": "left"
}
```
*Allowed directions:* `"left"`, `"right"`, or `"down"`.
- **Response Status:** 200 OK
- **Response Body (JSON):** Same as `POST /api/games`.

---

## ADDED Requirements

### Requirement: REQ-001 Board Width
Board width MUST be exactly 10 columns.

#### Scenario: Validate board width
- **GIVEN** a new game is created
- **WHEN** the board is retrieved
- **THEN** every row in the board grid has exactly 10 columns

### Requirement: REQ-002 Board Height
Board height MUST be exactly 20 rows.

#### Scenario: Validate board height
- **GIVEN** a new game is created
- **WHEN** the board is retrieved
- **THEN** the board grid has exactly 20 rows

### Requirement: REQ-003 Empty Cell Representation
Empty cells MUST be represented by `null`.

#### Scenario: Empty board initialization
- **GIVEN** a new game is created with an empty board
- **WHEN** the board state is retrieved
- **THEN** every cell on the board has a value of `null`

### Requirement: REQ-004 Tetromino Selection
Spawning MUST pick one of the 7 standard tetromino shapes (I, O, T, S, Z, J, L).

#### Scenario: Spawning a standard tetromino
- **GIVEN** a new game is created or a locked piece triggers a spawn
- **WHEN** a new piece spawns
- **THEN** its type is one of I, O, T, S, Z, J, L

### Requirement: REQ-005 Spawning Centered
Spawning MUST center the tetromino horizontally at the top of the grid.

#### Scenario: Validate initial horizontal spawn position
- **GIVEN** a piece is spawning
- **WHEN** the spawn occurs
- **THEN** the active piece origin is set to `[0, 3]`

### Requirement: REQ-006 Initial Orientation
A spawned piece MUST start in its default initial orientation.

#### Scenario: Validate default spawning orientation
- **GIVEN** a piece is spawning
- **WHEN** the spawn occurs
- **THEN** its active cells match its default local coordinates shifted by the spawn origin `[0, 3]`

### Requirement: REQ-007 Spawn Visibility
Newly spawned pieces MUST be immediately visible at the top of the grid.

#### Scenario: Verify spawned piece visibility
- **GIVEN** a new game is created
- **WHEN** the initial state is fetched from `/api/games`
- **THEN** the active piece cells are returned and are visible on the grid

### Requirement: REQ-008 Left Control Movement
Left control MUST shift the active piece exactly one cell to the left.

#### Scenario: Successful left movement
- **GIVEN** an active piece at coordinate origin `[row, col]` with no left obstructions
- **WHEN** left move is requested via POST `/api/games/{id}/move` with direction "left"
- **THEN** the active piece coordinate origin becomes `[row, col - 1]`

### Requirement: REQ-009 Right Control Movement
Right control MUST shift the active piece exactly one cell to the right.

#### Scenario: Successful right movement
- **GIVEN** an active piece at coordinate origin `[row, col]` with no right obstructions
- **WHEN** right move is requested via POST `/api/games/{id}/move` with direction "right"
- **THEN** the active piece coordinate origin becomes `[row, col + 1]`

### Requirement: REQ-010 Soft Drop Control
Soft drop control MUST shift the active piece exactly one cell down.

#### Scenario: Successful soft drop
- **GIVEN** an active piece at coordinate origin `[row, col]` with no downward obstructions
- **WHEN** down move is requested via POST `/api/games/{id}/move` with direction "down"
- **THEN** the active piece coordinate origin becomes `[row + 1, col]`

### Requirement: REQ-011 Left Boundary Block
Shifting left MUST be blocked if any part of the piece exceeds column boundary index 0.

#### Scenario: Blocked by left boundary
- **GIVEN** an active piece has at least one cell with column index 0
- **WHEN** left move is requested
- **THEN** the move is blocked and the active piece position is unchanged

### Requirement: REQ-012 Right Boundary Block
Shifting right MUST be blocked if any part of the piece exceeds column boundary index 9.

#### Scenario: Blocked by right boundary
- **GIVEN** an active piece has at least one cell with column index 9
- **WHEN** right move is requested
- **THEN** the move is blocked and the active piece position is unchanged

### Requirement: REQ-013 Bottom Boundary Block
Piece movement downwards MUST be blocked when any cell's row index would exceed 19 (row > 19).

#### Scenario: Blocked by bottom boundary
- **GIVEN** an active piece has at least one cell with row index 19
- **WHEN** downward movement (soft drop or gravity tick) is triggered
- **THEN** the movement is blocked and the piece cannot advance further down

### Requirement: REQ-014 Left Settled Block Collision
Shifting left MUST be blocked if any target cell overlaps with a settled block.

#### Scenario: Blocked by settled block on left
- **GIVEN** a settled block is present at cell `[row, col]`
- **WHEN** left move is requested for an active piece cell at `[row, col + 1]`
- **THEN** the move is blocked and the active piece position is unchanged

### Requirement: REQ-015 Right Settled Block Collision
Shifting right MUST be blocked if any target cell overlaps with a settled block.

#### Scenario: Blocked by settled block on right
- **GIVEN** a settled block is present at cell `[row, col]`
- **WHEN** right move is requested for an active piece cell at `[row, col - 1]`
- **THEN** the move is blocked and the active piece position is unchanged

### Requirement: REQ-016 Downward Settled Block Collision
Downward movement MUST be blocked if any target cell overlaps with a settled block.

#### Scenario: Blocked downward by settled block
- **GIVEN** a settled block is present at cell `[row, col]`
- **WHEN** downward movement is triggered for an active piece cell at `[row - 1, col]`
- **THEN** the movement is blocked and the piece cannot advance further down

### Requirement: REQ-017 Locking Execution
A piece MUST lock down immediately when a downward movement (soft drop or gravity) is blocked.

#### Scenario: Piece locking on collision
- **GIVEN** downward movement is blocked by a settled block or the bottom border (row > 19)
- **WHEN** a gravity tick or soft drop is executed
- **THEN** the active piece locks down in its current coordinates

### Requirement: REQ-018 Lock Integration
Locked pieces MUST become part of the settled board state.

#### Scenario: Locked piece turns into settled blocks
- **GIVEN** an active piece of type "T" is at coordinates `[[19, 3], [19, 4], [19, 5], [18, 4]]`
- **WHEN** it locks down
- **THEN** the board cells at those coordinates are updated to the piece's block value in the matrix

### Requirement: REQ-019 Active Status Removal
Locked pieces MUST lose their active status and cannot be further controlled.

#### Scenario: Locked piece is no longer active
- **GIVEN** a piece has locked down
- **WHEN** movement or drop controls are requested
- **THEN** they cannot affect the locked piece and the locked blocks remain in place

### Requirement: REQ-020 Completed Row Detection
Completed rows (containing 10 filled cells) MUST be identified immediately upon locking.

#### Scenario: Identify completed rows
- **GIVEN** a piece locks down and fills every column (0 to 9) of row 19
- **WHEN** the post-lock scan runs
- **THEN** row 19 is identified as a completed row for clearing

### Requirement: REQ-021 Row Clearing Execution
Identified completed rows MUST be cleared from the board.

#### Scenario: Clear completed rows
- **GIVEN** row 19 is identified as completed
- **WHEN** line clearing is processed
- **THEN** all cell values in row 19 are removed and cleared

### Requirement: REQ-022 Upper Row Shifting
Settled rows above cleared rows MUST shift down by the corresponding number of cleared rows.

#### Scenario: Shift upper settled rows down
- **GIVEN** row 19 is cleared and row 18 has settled blocks
- **WHEN** line clearing is processed
- **THEN** the settled blocks in row 18 are shifted down to row 19

### Requirement: REQ-023 Top Row Replacement
Cleared rows MUST be replaced by empty rows inserted at the very top of the board.

#### Scenario: Prepend empty rows at top
- **GIVEN** one row is cleared
- **WHEN** the board is updated
- **THEN** a new row containing all `null` cells is inserted at row 0

### Requirement: REQ-024 Multiple Line Clearing
Clearing multiple lines simultaneously (up to 2) MUST shift upper rows down sequentially.

#### Scenario: Simultaneous clearing of two rows
- **GIVEN** rows 18 and 19 are completed simultaneously by locking a piece (such as the "O" block)
- **WHEN** line clearing is processed
- **THEN** both rows 18 and 19 are cleared and all rows above are shifted down by 2 rows sequentially

### Requirement: REQ-025 Post-Lock Spawning
Immediately following a lock-down, a new piece MUST be spawned at the top center.

#### Scenario: Spawn new piece after locking
- **GIVEN** a piece has locked and completed rows have been cleared
- **WHEN** the lock-down phase finishes
- **THEN** a new random active piece is spawned at coordinate origin `[0, 3]`

### Requirement: REQ-026 Game Over Condition
The game status MUST transition to `game_over` if a newly spawned piece overlaps any settled blocks.

#### Scenario: Game over trigger
- **GIVEN** settled blocks are present at row 0, column 3 (i.e. cell `[0, 3]`)
- **WHEN** a new piece attempts to spawn at origin `[0, 3]`
- **THEN** the game status transitions to `game_over`

### Requirement: REQ-027 Control Rejection on Game Over
Active piece movements MUST be rejected if the game status is `game_over`.

#### Scenario: Input blocked after game over
- **GIVEN** the game status is `game_over`
- **WHEN** any movement control is requested via `/api/games/{id}/move`
- **THEN** the request is rejected or has no effect, and the state remains unchanged

### Requirement: REQ-028 Reset Game Control
Restart control MUST reset the settled grid and generate a new game with status `playing`.

#### Scenario: Restart game from game over
- **GIVEN** a game session with status `game_over` and populated board matrix
- **WHEN** a post request is made to `/api/games` to restart
- **THEN** the board is reset with all empty cells as `null`, a new active piece spawns at origin `[0, 3]`, and status becomes `playing`

### Requirement: REQ-029 Authority of Backend
The backend API MUST own the authoritative coordinate grid, validation, and collision states.

#### Scenario: Authoritative state retrieval
- **GIVEN** a movement is processed on the backend
- **WHEN** the client requests `/api/games/{id}`
- **THEN** the response contains the authoritative board matrix, active piece coordinates, and game status

### Requirement: REQ-030 Decoupled Frontend Rendering
The frontend MUST fetch status from `/api/games/{id}` and render the exact grid cells received.

#### Scenario: Rendering authoritative cells
- **GIVEN** the frontend fetches game status
- **WHEN** a response is received with a specific `board` grid layout
- **THEN** the frontend maps and renders the exact blocks at `[row, col]` specified in the response without computing movement logic locally
