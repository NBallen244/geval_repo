# Feature Specification: build-tetris-core

**Feature Branch**: `001-build-tetris-core`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "Build Stage 1, option A, of a browser-based Tetris study as a greenfield project. Create the tool's native specification artifacts first, then use those artifacts to implement a decoupled Python FastAPI backend and React with TypeScript frontend. Use English for all specifications, application text, code comments, tests and interactions. Keep generated source in `backend/` and `frontend/` and do not create or edit files outside this tool directory."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Falling Block Gameplay (Priority: P1)

As a Tetris player, I want to start a new game and see a 10x20 grid with a random tetromino starting at the top, descending automatically every 500 ms, so that I can control its movement to position it before it reaches the bottom and locks in place.

**Why this priority**: This is the fundamental, indispensable gameplay engine of Tetris. Without automatic falling, piece spawning, and basic collision, the application is not playable.

**Independent Test**: Can be fully tested with a blank board where a single piece spawns at the top, descends, accepts user moves (left, right, down), and locks at the bottom, delivering the visual confirmation of a basic game loop.

**Acceptance Scenarios**:

1. **Given** a new game session is created, **When** the board is initialized, **Then** the grid must measure exactly 10 columns by 20 rows, all cells must be empty, and a random standard tetromino (from the standard 7 shapes) must spawn in its initial orientation at the top center.
2. **Given** an active falling tetromino, **When** a gravity tick occurs, **Then** the piece must shift down by exactly one grid row.
3. **Given** an active falling tetromino adjacent to the left boundary of the board, **When** a command to move left is received, **Then** the tetromino's horizontal position must remain unchanged.
4. **Given** an active falling tetromino adjacent to the right boundary of the board, **When** a command to move right is received, **Then** the tetromino's horizontal position must remain unchanged.
5. **Given** an active falling tetromino resting immediately on the bottom boundary of the board, **When** a gravity tick occurs, **Then** the piece must lock permanently into the board, its cells must become filled blocks in the settled board state, and a new random tetromino must spawn at the top center.

---

### User Story 2 - Clearing Completed Horizontal Lines (Priority: P2)

As a Tetris player, I want completed horizontal rows of blocks to be automatically cleared from the grid and the rows above to shift down, so that I can keep playing and prevent the block stack from reaching the top of the board.

**Why this priority**: Line clearing is the primary mechanic of game progression and survival in Tetris. It prevents the board from filling up too quickly and provides the core goal of the game.

**Independent Test**: Set up a settled board state with a single empty hole in a row, place a piece to fill that hole, and verify the row is cleared and the cells above shift down correctly.

**Acceptance Scenarios**:

1. **Given** a board state with row 19 completely filled with settled blocks except for column 0, **When** a tetromino cell is locked into column 0 of row 19, **Then** row 19 must be completely cleared, and all settled blocks in rows 0 through 18 must shift downward by exactly one row.
2. **Given** a board state with rows 18 and 19 completely filled with settled blocks except for columns 0 and 1, **When** an O tetromino is locked and fills columns 0 and 1 in both rows, **Then** both rows 18 and 19 must be cleared, and all settled blocks above them must shift downward by exactly two rows.

---

### User Story 3 - Game Over & Replayability (Priority: P3)

As a Tetris player, I want the game to detect when the stack of blocks reaches the top and blocks new pieces from spawning, display a clear game-over message, disable movement controls, and allow me to restart a new game.

**Why this priority**: Defines the natural end of a game loop and allows players to try again, establishing a complete and replayable game cycle.

**Independent Test**: Can be tested by filling the center columns up to the spawn area, spawning a new piece, checking that game status changes to `"game_over"` and controls are disabled, then pressing restart to reset.

**Acceptance Scenarios**:

1. **Given** the settled blocks stack up to row 0 in the spawning column, **When** a new tetromino is spawned and immediately overlaps with any settled blocks, **Then** the game status must transition to `"game_over"`.
2. **Given** the game has entered the `"game_over"` status, **When** gravity ticks or movement controls are received, **Then** the game state must remain unchanged and no movements must be executed.
3. **Given** the game is in `"game_over"` status, **When** the restart control is activated, **Then** all settled blocks on the board must be cleared, the status must transition to `"playing"`, and a new tetromino must spawn at the top center.

### Edge Cases

- **Simultaneous Inputs**: What happens when a manual movement command is processed simultaneously with an automatic gravity tick? Since the backend processes API requests sequentially, the commands will be serialized. If a manual move is processed first, the piece moves; if it lands, the subsequent gravity tick locks it in place.
- **Immediate Game Over**: If a tetromino spawns and immediately overlaps with a settled block, the status must change to `"game_over"` immediately, and the overlapping piece must not be allowed to move.

## Requirements *(mandatory)*

### Functional Requirements

#### Board & Game State Requirements
- **FR-001**: The game board MUST be represented as a grid of exactly 10 columns (width) and 20 rows (height).
- **FR-002**: Each cell in the 10x20 grid MUST exist in either an empty state or a settled filled block state.
- **FR-003**: A game session MUST track a status flag indicating either `"playing"` or `"game_over"`.
- **FR-004**: The system MUST support the seven standard tetromino shapes (I, O, T, S, Z, J, L) in their predefined initial orientations.
- **FR-005**: All tetromino pieces spawned MUST be selected randomly from the seven standard shapes with equal probability.
- **FR-006**: A newly spawned tetromino MUST appear at the top-center of the grid in its initial orientation.
- **FR-007**: The game state MUST track the active falling piece, its shape type, its current cell coordinates, and its origin position.

#### Movement & Collision Requirements
- **FR-008**: The system MUST shift the active tetromino downward by exactly one grid row on every automatic gravity tick if no downward collision is detected.
- **FR-009**: The system MUST shift the active tetromino downward by exactly one grid row on receiving a manual `"down"` move command (soft drop) if no downward collision is detected.
- **FR-010**: The system MUST shift the active tetromino leftward by exactly one grid column on receiving a manual `"left"` move command if no left-side collision is detected.
- **FR-011**: The system MUST shift the active tetromino rightward by exactly one grid column on receiving a manual `"right"` move command if no right-side collision is detected.
- **FR-012**: The system MUST detect collision with the left grid boundary and prevent the active piece from moving left of column index 0.
- **FR-013**: The system MUST detect collision with the right grid boundary and prevent the active piece from moving right of column index 9.
- **FR-014**: The system MUST detect collision with the bottom grid boundary and prevent the active piece from moving below row index 19.
- **FR-015**: The system MUST detect collision with already settled filled blocks on the board and prevent the active piece from moving into occupied cells.
- **FR-016**: If any movement command (left, right, manual down) results in a collision, the system MUST preserve the active piece's existing position with no state change.

#### Locking & Line Clear Requirements
- **FR-017**: If the active piece is in contact with the bottom boundary or a settled filled block directly below it, and a gravity tick occurs, the piece MUST lock in its current position.
- **FR-018**: Upon locking, the cells occupied by the active tetromino MUST be converted into settled filled blocks on the game board.
- **FR-019**: Immediately after locking, the system MUST check all 20 rows of the board for fully completed horizontal lines (all 10 cells in a row filled).
- **FR-020**: The system MUST remove all fully completed lines from the board.
- **FR-021**: The system MUST shift all settled filled blocks above the cleared lines downward by the exact number of cleared lines.
- **FR-022**: The system MUST insert empty rows at the top of the board to replace the cleared lines.

#### Spawning, Game Over & Reset Requirements
- **FR-023**: Immediately after completing any line clears (or confirming none exist) following a piece lock, the system MUST spawn a new random tetromino at the top-center of the board.
- **FR-024**: If a newly spawned tetromino overlaps with any settled filled blocks at its starting position, the game status MUST immediately change to `"game_over"`.
- **FR-025**: When the game status is `"game_over"`, all gravity ticks and movement commands MUST be ignored, and no state changes must be made to the board or active piece.
- **FR-026**: The system MUST support a restart command that clears all settled blocks from the grid, sets the game status to `"playing"`, and spawns a new random tetromino at the top-center.

#### Backend Interface Requirements
- **FR-027**: The backend MUST own the authoritative game state and rules, running entirely in-memory without database persistence or authentication.
- **FR-028**: The backend MUST expose a `POST /api/games` endpoint to create a new game session or restart, returning a unique game ID and the initial game state.
- **FR-029**: The backend MUST expose a `GET /api/games/{id}` endpoint to retrieve the current state of the game session by its ID.
- **FR-030**: The backend MUST expose a `POST /api/games/{id}/tick` endpoint to advance the game by one gravity tick.
- **FR-031**: The backend MUST expose a `POST /api/games/{id}/move` endpoint accepting `{ "direction": "left" | "right" | "down" }` to execute manual movements.
- **FR-032**: All game state responses from the backend MUST be returned as JSON containing the 20x10 settled board grid, active piece coordinates and origin, and the status flag (`"playing"` or `"game_over"`).

#### Frontend Interface Requirements
- **FR-033**: The frontend MUST visually render the 10x20 board grid, depicting both empty cells and settled filled blocks.
- **FR-034**: The frontend MUST superimpose the active falling tetromino on the board, rendering its cells in a visually distinct style.
- **FR-035**: The frontend MUST invoke the backend's gravity tick endpoint (`POST /api/games/{id}/tick`) at a fixed interval of exactly 500 ms while the game status is `"playing"`.
- **FR-036**: The frontend MUST capture keyboard events and map Left Arrow to `"left"`, Right Arrow to `"right"`, and Down Arrow to `"down"`, triggering `POST /api/games/{id}/move` requests to the backend.
- **FR-037**: The frontend MUST render a prominent game-over overlay or modal in English when the status transitions to `"game_over"`.
- **FR-038**: The frontend MUST provide a "Restart" button that sends a `POST /api/games` request and resets the frontend state to start a new game.

### Key Entities

- **Game**: Represents the authoritative state of a single Tetris game session.
  - *Attributes*:
    - `id`: A unique string identifier.
    - `board`: A 20x10 grid of cell states (empty or filled).
    - `activePiece`: The current falling tetromino, storing its shape type, absolute coordinates, and origin coordinate.
    - `status`: A string indicator (`"playing"` or `"game_over"`).
- **Tetromino**: Represents the shape, coordinates, and behavior of a falling piece.
  - *Attributes*:
    - `type`: One of the seven standard shapes (I, O, T, S, Z, J, L).
    - `cells`: An array of four cell coordinates (row, col) currently occupied by the piece.
    - `origin`: The rotation/positional pivot coordinate (row, col) of the piece on the grid.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Gravity ticks MUST execute at a reliable interval of exactly 500 ms while the game is playing, with any timing drift not exceeding 10 ms.
- **SC-002**: Backend endpoints MUST respond to all movement and tick requests within 50 ms under local environment conditions, ensuring zero noticeable lag.
- **SC-003**: 100% of fully completed rows MUST be cleared immediately upon piece locking, with upper rows shifted down correctly and zero orphaned blocks.
- **SC-004**: 100% of game-over overlaps MUST be detected immediately upon piece spawn, locking the gameplay controls and rendering the game-over screen in English within 100 ms of the state change.

## Assumptions

- **Single User Focus**: The application is intended for single-player study; user accounts, authentication, leaderboards, and persistent high scores are out of scope.
- **No Rotation**: Piece rotation, wall kicks, hold queues, ghost pieces, and next-piece previews are explicitly out of scope for this stage.
- **In-Memory Storage**: The backend will store game sessions in memory, and sessions will be cleared if the server restarts.
- **Target Environment**: The application runs locally as a decoupled system: Python FastAPI for the API server and React/TypeScript for the SPA web interface.

## Execution & Validation Requirements

- **VR-001 (Reproducible Build Command)**: The frontend MUST compile and build successfully without any TypeScript or compile-time warnings/errors using the exact reproducible command:
  ```bash
  cd frontend
  npm run build
  ```
- **VR-002 (Reproducible Test Command)**: The backend tests MUST execute and pass successfully from the `backend/` directory using:
  ```bash
  cd backend
  pytest
  ```
  And also from the root directory using:
  ```bash
  python -m pytest backend/tests
  ```
