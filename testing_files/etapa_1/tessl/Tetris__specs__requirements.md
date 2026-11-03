# Requirements Specification: Browser-Based Tetris Study - Stage 1, Option A

This document contains the authoritative, atomic, and testable requirements for Stage 1, Option A of the greenfield browser-based Tetris study.

---

## 1. Atomic Requirements (Req-1 to Req-34)

### Group A: Board & Grid Dimensions
- **Req-1:** The game board grid MUST have a fixed size of exactly 10 columns (width) and 20 rows (height).
- **Req-2:** Each cell on the board grid MUST be represented by coordinates (row, col), where row index ranges from 0 (top row) to 19 (bottom row), and col index ranges from 0 (left column) to 9 (right column).
- **Req-3:** Cells on the board grid MUST be either empty (contain `null` value) or settled (contain a string value indicating the color/type of the piece that occupied it).

### Group B: Tetromino definitions & Spawning
- **Req-4:** The system MUST support exactly seven standard Tetromino shapes: 'I', 'O', 'T', 'S', 'Z', 'J', and 'L'.
- **Req-5:** The relative cell coordinates of the seven shapes in their initial orientations around an origin `(0, 0)` MUST be:
  - `I`: `[(0, 0), (0, 1), (0, 2), (0, 3)]` (Cyan)
  - `O`: `[(0, 0), (0, 1), (1, 0), (1, 1)]` (Yellow)
  - `T`: `[(0, 1), (1, 0), (1, 1), (1, 2)]` (Purple)
  - `S`: `[(0, 1), (0, 2), (1, 0), (1, 1)]` (Green)
  - `Z`: `[(0, 0), (0, 1), (1, 1), (1, 2)]` (Red)
  - `J`: `[(0, 0), (1, 0), (1, 1), (1, 2)]` (Blue)
  - `L`: `[(0, 2), (1, 0), (1, 1), (1, 2)]` (Orange)
- **Req-6:** The game MUST NOT support piece rotation. Active pieces remain in their initial orientation throughout their descent.
- **Req-7:** When a new game is created or restarted, a new random active piece MUST spawn at the top of the grid.
- **Req-8:** The spawn origin of the active piece MUST be set such that the shape fits within the top rows of the board. The default spawn origin for all pieces is `(0, 3)`.

### Group C: Legal Movements
- **Req-9:** The user MUST be able to command the active piece to shift left by one column. This decreases the column indices of all piece cells by 1.
- **Req-10:** The user MUST be able to command the active piece to shift right by one column. This increases the column indices of all piece cells by 1.
- **Req-11:** The user/timer MUST be able to command the active piece to descend by one row (tick/soft-drop). This increases the row indices of all piece cells by 1.
- **Req-12:** A movement command MUST only be applied if the resulting coordinates are legal. If the move is illegal, the active piece's coordinates MUST NOT change.

### Group D: Collision Handling
- **Req-13:** A position is ILLEGAL if any of the active piece's absolute cells lie outside the horizontal boundaries of the grid (col < 0 or col > 9).
- **Req-14:** A position is ILLEGAL if any of the active piece's absolute cells lie below the bottom boundary of the grid (row > 19).
- **Req-15:** A position is ILLEGAL if any of the active piece's absolute cells overlap with a cell on the board that is already settled (not `null`).
- **Req-16:** A left or right movement command that would result in an ILLEGAL position MUST be ignored (reverted).
- **Req-17:** A downward movement command (via tick or down move) that would result in an ILLEGAL position MUST trigger the locking sequence.

### Group E: Locking Mechanism
- **Req-18:** When a downward move is illegal, the active piece MUST lock into place at its current position immediately.
- **Req-19:** Locking MUST copy the coordinates and type of the active piece cells onto the board's grid, replacing `null` cells with the piece type/color string.
- **Req-20:** Once a piece is locked, the `active_piece` field MUST be cleared (set to `null`) in the state.
- **Req-21:** Immediately after locking and line clearing, the system MUST spawn a new random active piece at the spawn origin `(0, 3)`.

### Group F: Line Clearing
- **Req-22:** The system MUST detect any completed horizontal rows (where all 10 columns are filled with non-`null` settled blocks) immediately after locking.
- **Req-23:** Completed rows MUST be removed from the board, and all rows above the cleared row MUST shift downward by the number of cleared rows.
- **Req-24:** Empty rows (all cells filled with `null`) MUST be inserted at the top of the board to maintain the 20-row height.

### Group G: Game Over State
- **Req-25:** The game status MUST transition from `"playing"` to `"game_over"` if, immediately after a new piece is spawned, its initial position is ILLEGAL (overlaps with any existing settled blocks on the board).
- **Req-26:** The game status MUST transition from `"playing"` to `"game_over"` if, at the time of a gravity tick, the active piece is already locked at row 0 and cannot move down.
- **Req-27:** While the game is in `"game_over"` status, any tick or movement commands MUST be ignored, and the API must return the current state with `"game_over"` status.

### Group H: API and System Management
- **Req-28:** The API MUST keep all game states in-memory only (e.g., in an active games dict), identified by a unique UUID string per game session.
- **Req-29:** The HTTP controller MUST provide the following endpoints:
  - `POST /api/games`: Creates/restarts a game session, initializes an empty 20x10 board, spawns the first piece, and returns the generated UUID and initial state.
  - `GET /api/games/{id}`: Retrieves the current game state by ID.
  - `POST /api/games/{id}/tick`: Advances gravity by one tick, moving the active piece down or locking it.
  - `POST /api/games/{id}/move`: Moves the active piece with payload `{"direction": "left" | "right" | "down"}`.
- **Req-30:** The JSON payload returned by all game endpoints MUST conform to this schema structure:
  ```json
  {
    "id": "string-uuid",
    "board": [ [null, null, ...], ... ],
    "active_piece": {
      "type": "I" | "O" | "T" | "S" | "Z" | "J" | "L",
      "origin": [row, col],
      "cells": [ [row, col], ... ]
    } | null,
    "status": "playing" | "game_over"
  }
  ```

### Group I: Frontend Integration & Gameplay Timer
- **Req-31:** The frontend application MUST run a game tick loop that triggers a gravity `tick` command via `POST /api/games/{id}/tick` at a fixed interval of exactly 500 ms while the game status is `"playing"`.
- **Req-32:** The frontend application MUST map the following keyboard keys to their corresponding backend movements when pressed:
  - `ArrowLeft`: Shift left (`POST /api/games/{id}/move` with direction `"left"`).
  - `ArrowRight`: Shift right (`POST /api/games/{id}/move` with direction `"right"`).
  - `ArrowDown`: Soft drop / Shift down (`POST /api/games/{id}/move` with direction `"down"`).
- **Req-33:** To prevent out-of-order execution and race conditions from rapid concurrent user inputs or rapid interval events, the client-side game engine MUST implement input throttling / request serialization ensuring that no new API requests are dispatched if an API call is currently in-flight.
- **Req-34:** The frontend application MUST dynamically render the combined board grid, overlaying the active piece's coordinates and block type onto the underlying 20x10 settled cells of the board.

---

## 2. Acceptance Criteria

| ID | Description | Acceptance Criteria |
| --- | --- | --- |
| AC-1 | Board initialization | `POST /api/games` returns a 20x10 list of nulls, a non-null `active_piece` at origin `[0, 3]`, and status `"playing"`. |
| AC-2 | Left/Right Boundaries | Left shift at col 0 or right shift at right boundary keeps the coordinates unchanged. |
| AC-3 | Gravity and Locking | A `tick` with a piece at row 19 (or directly above settled block) locks it into the board, clears any full lines, and spawns a new piece at `[0, 3]`. |
| AC-4 | Line Clearing | Full rows (10 cells filled) are cleared, rows above shift down, and empty row inserted at index 0. |
| AC-5 | Game Over | Spawning a new piece onto a cell containing a settled block sets status to `"game_over"`. |
| AC-6 | Game Loop Interval | The client triggers automatic game ticks exactly every 500 ms when the status is `"playing"`. |
| AC-7 | Keyboard Mapping | Only the left, right, and down arrow keys dispatch the corresponding moves. |
| AC-8 | Race Condition Prevention | Rapid keyboard inputs during pending network requests are safely ignored/buffered and do not lead to overlapping operations. |
| AC-9 | Visual Board Overlay | The 20x10 UI board shows a combination of already settled blocks and the currently active piece at its correct absolute coordinates. |

---

## 3. Run and Test Commands

### Backend:
- **Run:** `fastapi dev app/main.py --port 8000`
- **Test:** `pytest -v`

### Frontend:
- **Build/Lint/Run:**
  - Build: `npm run build`
  - Lint/Type-check: `npm run lint` or `tsc --noEmit`
  - Run dev server: `npm run dev`
