# Requirements Document

## Introduction

This document defines the fixed functional scope for Stage 1, Option A, of a browser-based Tetris study, implemented as a greenfield project. The backend (Python FastAPI) owns the authoritative game state and rules. The frontend (React with TypeScript) renders game state obtained from the backend HTTP API and issues control commands.

The scope is deliberately limited. The playfield is a 10-column by 20-row grid. Pieces are the seven standard tetrominoes in their initial orientations only. Gravity moves the active piece down automatically. The player may move the active piece left, right, or soft drop (down), and may restart the game. Full horizontal lines are cleared. The game ends when a newly spawned piece cannot be placed.

The following are explicitly out of scope for this stage: rotation, wall kicks, line counter, score, speed progression, hold, next-piece preview, ghost piece, configurable controls, persistence, multiplayer, database, and authentication. All game state is held in memory only.

### Coordinate and Data Conventions

- The board is a grid of 20 rows by 10 columns. Row index `0` is the top row; row index `19` is the bottom row. Column index `0` is the leftmost column; column index `9` is the rightmost column.
- A board cell is empty (`null`/`0`) or occupied by a settled block (a piece type identifier).
- An active piece is described by its type, an origin (row, column), and the set of absolute board cells it currently occupies.
- Cell coordinates are expressed as `[row, column]` pairs.
- Piece "cells" in API responses are the absolute occupied board coordinates of the active piece.

### Standard Tetromino Definitions (initial orientation)

Cells are given relative to the piece origin (the top-left corner of the piece's bounding box), as `[row, column]` offsets:

- `I`: `[0,0] [0,1] [0,2] [0,3]`
- `O`: `[0,0] [0,1] [1,0] [1,1]`
- `T`: `[0,1] [1,0] [1,1] [1,2]`
- `S`: `[0,1] [0,2] [1,0] [1,1]`
- `Z`: `[0,0] [0,1] [1,1] [1,2]`
- `J`: `[0,0] [1,0] [1,1] [1,2]`
- `L`: `[0,2] [1,0] [1,1] [1,2]`

### Spawn Rule

Each piece spawns with its origin at row `0`, horizontally centered by placing the origin at column `3` (for the shared 4-wide bounding box convention used here), so pieces enter near the top-center of the board.

## Requirements

### Requirement 1: Board dimensions

**User Story:** As a player, I want a standard-sized playfield, so that the game behaves like classic Tetris.

#### Acceptance Criteria

1. WHEN a game is created THEN the system SHALL represent the settled board as exactly 20 rows.
2. WHEN a game is created THEN the system SHALL represent each board row as exactly 10 columns.
3. WHEN a game is created THEN the system SHALL initialize every settled board cell as empty.

### Requirement 2: Game creation and identity

**User Story:** As a player, I want to start a game, so that I can begin playing.

#### Acceptance Criteria

1. WHEN a client sends `POST /api/games` THEN the system SHALL create a new game and return its state.
2. WHEN a game is created THEN the system SHALL assign it a unique identifier.
3. WHEN a game is created THEN the system SHALL set its status to `playing`.
4. WHEN a game is created THEN the system SHALL spawn one active piece.

### Requirement 3: Piece set

**User Story:** As a player, I want the seven standard tetrominoes, so that gameplay matches classic Tetris.

#### Acceptance Criteria

1. WHEN the system spawns a piece THEN the piece type SHALL be one of `I`, `O`, `T`, `S`, `Z`, `J`, `L`.
2. WHEN the system spawns a piece THEN the piece SHALL use its defined initial orientation only.
3. WHEN the system selects pieces across a game THEN it SHALL be capable of producing all seven types.

### Requirement 4: Deterministic piece sequence under a fixed seed

**User Story:** As a researcher, I want a reproducible piece sequence, so that runs are comparable.

#### Acceptance Criteria

1. WHEN a game is created with a fixed seed THEN the sequence of spawned piece types SHALL be deterministic.
2. WHEN two games are created with the same fixed seed THEN they SHALL produce identical piece-type sequences.

### Requirement 5: Piece spawning position

**User Story:** As a player, I want pieces to appear at the top center, so that play starts predictably.

#### Acceptance Criteria

1. WHEN a piece spawns THEN its origin row SHALL be `0`.
2. WHEN a piece spawns THEN its origin column SHALL place the piece near the horizontal center of the board.
3. WHEN a piece spawns THEN all of its occupied cells SHALL lie within the board bounds.

### Requirement 6: Active piece representation

**User Story:** As a frontend developer, I want the active piece cells and origin, so that I can render it.

#### Acceptance Criteria

1. WHEN the system returns game state THEN it SHALL include the active piece type while status is `playing`.
2. WHEN the system returns game state THEN it SHALL include the active piece origin as `[row, column]` while status is `playing`.
3. WHEN the system returns game state THEN it SHALL include the active piece's absolute occupied cells while status is `playing`.

### Requirement 7: Read game state

**User Story:** As a player, I want to read the current game state, so that the UI can display it.

#### Acceptance Criteria

1. WHEN a client sends `GET /api/games/{id}` for an existing game THEN the system SHALL return its current state.
2. WHEN a client sends `GET /api/games/{id}` for an unknown id THEN the system SHALL respond with HTTP 404.

### Requirement 8: Gravity tick moves the piece down

**User Story:** As a player, I want the piece to fall over time, so that the game progresses.

#### Acceptance Criteria

1. WHEN a client sends `POST /api/games/{id}/tick` AND the active piece can move down THEN the system SHALL move the active piece down by one row.
2. WHEN the active piece moves down THEN its occupied cells SHALL each increase in row index by one.

### Requirement 9: Move left

**User Story:** As a player, I want to move the piece left, so that I can position it.

#### Acceptance Criteria

1. WHEN a client sends `POST /api/games/{id}/move` with `{ "direction": "left" }` AND the move is legal THEN the system SHALL decrease the active piece's column index by one.
2. WHEN a left move would place any cell at column index less than `0` THEN the system SHALL reject the move and leave the piece unchanged.

### Requirement 10: Move right

**User Story:** As a player, I want to move the piece right, so that I can position it.

#### Acceptance Criteria

1. WHEN a client sends `POST /api/games/{id}/move` with `{ "direction": "right" }` AND the move is legal THEN the system SHALL increase the active piece's column index by one.
2. WHEN a right move would place any cell at column index greater than `9` THEN the system SHALL reject the move and leave the piece unchanged.

### Requirement 11: Soft drop (move down)

**User Story:** As a player, I want to soft drop the piece, so that I can speed up placement.

#### Acceptance Criteria

1. WHEN a client sends `POST /api/games/{id}/move` with `{ "direction": "down" }` AND the piece can move down THEN the system SHALL move the active piece down by one row.
2. WHEN a client sends `POST /api/games/{id}/move` with `{ "direction": "down" }` AND the piece cannot move down THEN the system SHALL lock the piece.

### Requirement 12: Left/right wall collision

**User Story:** As a player, I want the walls to stop the piece, so that it stays on the board.

#### Acceptance Criteria

1. WHEN any horizontal move would move a cell beyond the left wall THEN the system SHALL treat the move as illegal.
2. WHEN any horizontal move would move a cell beyond the right wall THEN the system SHALL treat the move as illegal.
3. WHEN a horizontal move is illegal THEN the settled board SHALL remain unchanged.

### Requirement 13: Stack collision on horizontal move

**User Story:** As a player, I want pieces to respect settled blocks, so that movement is fair.

#### Acceptance Criteria

1. WHEN a horizontal move would place any active cell onto a settled block THEN the system SHALL treat the move as illegal.
2. WHEN a horizontal move is illegal due to a settled block THEN the piece SHALL remain unchanged.

### Requirement 14: Bottom collision detection

**User Story:** As a player, I want the floor to stop the piece, so that it can lock.

#### Acceptance Criteria

1. WHEN the active piece has any cell in the bottom row THEN the system SHALL treat a downward move as blocked.
2. WHEN a downward move would place any cell at row index greater than `19` THEN the system SHALL treat the downward move as blocked.

### Requirement 15: Stack collision below

**User Story:** As a player, I want pieces to rest on the stack, so that they build up.

#### Acceptance Criteria

1. WHEN the cell directly below any active cell is a settled block THEN the system SHALL treat a downward move as blocked.

### Requirement 16: Locking on blocked gravity tick

**User Story:** As a player, I want a resting piece to lock, so that a new piece can appear.

#### Acceptance Criteria

1. WHEN a gravity tick occurs AND the active piece cannot move down THEN the system SHALL lock the active piece into the settled board.
2. WHEN a piece locks THEN each of its occupied cells SHALL become a settled block of that piece's type.

### Requirement 17: Spawn after locking

**User Story:** As a player, I want a new piece after one locks, so that play continues.

#### Acceptance Criteria

1. WHEN a piece locks AND at least one line is not being cleared into a game-over condition THEN the system SHALL spawn the next piece.
2. WHEN a new piece spawns after locking THEN it SHALL follow the deterministic sequence order.

### Requirement 18: Clearing a single full line

**User Story:** As a player, I want full lines removed, so that the board frees up.

#### Acceptance Criteria

1. WHEN a piece locks AND exactly one row is completely filled THEN the system SHALL remove that row.
2. WHEN a row is removed THEN all rows above it SHALL shift down by one.
3. WHEN a row is removed THEN a new empty row SHALL be inserted at the top.

### Requirement 19: Clearing multiple full lines

**User Story:** As a player, I want several full lines removed at once, so that clears work correctly.

#### Acceptance Criteria

1. WHEN a piece locks AND two or more rows are completely filled THEN the system SHALL remove all such rows in the same operation.
2. WHEN multiple rows are removed THEN the number of new empty rows inserted at the top SHALL equal the number of removed rows.
3. WHEN multiple rows are removed THEN remaining rows SHALL preserve their relative vertical order.

### Requirement 20: No clear when no line is full

**User Story:** As a player, I want partial rows preserved, so that the board is accurate.

#### Acceptance Criteria

1. WHEN a piece locks AND no row is completely filled THEN the system SHALL leave all rows unchanged in count.
2. WHEN no line clears THEN previously settled blocks SHALL remain in place.

### Requirement 21: Line clearing precedes next spawn

**User Story:** As a player, I want clears resolved before the next piece, so that ordering is correct.

#### Acceptance Criteria

1. WHEN a piece locks THEN the system SHALL clear completed lines BEFORE spawning the next piece.

### Requirement 22: Game-over on spawn collision

**User Story:** As a player, I want the game to end when pieces cannot fit, so that there is a clear conclusion.

#### Acceptance Criteria

1. WHEN a new piece is spawned AND any of its cells overlaps a settled block THEN the system SHALL set the status to `game_over`.
2. WHEN the status becomes `game_over` THEN the system SHALL NOT spawn a new active piece.

### Requirement 23: No gameplay after game over

**User Story:** As a player, I want inputs ignored after game over, so that state stays consistent.

#### Acceptance Criteria

1. WHEN the status is `game_over` AND a client sends a tick THEN the system SHALL leave the board and status unchanged.
2. WHEN the status is `game_over` AND a client sends a move THEN the system SHALL leave the board and status unchanged.

### Requirement 24: Restart via game creation

**User Story:** As a player, I want to restart, so that I can play again.

#### Acceptance Criteria

1. WHEN a client sends `POST /api/games` after a game over THEN the system SHALL create a fresh game with an empty board.
2. WHEN a fresh game is created THEN its status SHALL be `playing` with a newly spawned piece.

### Requirement 25: State payload shape

**User Story:** As a frontend developer, I want a predictable JSON shape, so that rendering is straightforward.

#### Acceptance Criteria

1. WHEN the system returns game state THEN it SHALL include an `id` string field.
2. WHEN the system returns game state THEN it SHALL include a `status` field of `playing` or `game_over`.
3. WHEN the system returns game state THEN it SHALL include a `board` field of 20 rows by 10 columns.
4. WHEN the status is `playing` THEN the system SHALL include an `active_piece` object with `type`, `origin`, and `cells`.
5. WHEN the status is `game_over` THEN the `active_piece` field SHALL be `null`.

### Requirement 26: Move request validation

**User Story:** As a client, I want invalid requests rejected, so that errors are clear.

#### Acceptance Criteria

1. WHEN a move request omits `direction` OR uses a value other than `left`, `right`, `down` THEN the system SHALL respond with HTTP 422.
2. WHEN a move request targets an unknown game id THEN the system SHALL respond with HTTP 404.

### Requirement 27: In-memory state only

**User Story:** As an operator, I want no external storage, so that the study stays simple.

#### Acceptance Criteria

1. WHEN the backend runs THEN it SHALL hold all game state in memory only.
2. WHEN the backend process restarts THEN previously created games SHALL no longer exist.

### Requirement 28: Separation of concerns

**User Story:** As a maintainer, I want layered code, so that rules are testable in isolation.

#### Acceptance Criteria

1. WHEN the backend is structured THEN HTTP controllers, domain models, and game rules SHALL reside in separate modules.
2. WHEN game rules are tested THEN they SHALL be exercisable without the HTTP layer.

### Requirement 29: Frontend renders authoritative state

**User Story:** As a player, I want the UI to reflect the backend, so that display is accurate.

#### Acceptance Criteria

1. WHEN the frontend receives game state THEN it SHALL render the 20x10 grid from the `board` field.
2. WHEN the status is `playing` THEN the frontend SHALL render the active piece from `active_piece.cells`.
3. WHEN the frontend renders THEN it SHALL NOT compute game rules locally.

### Requirement 30: Fixed gravity interval

**User Story:** As a player, I want steady falling, so that pacing is consistent.

#### Acceptance Criteria

1. WHEN the status is `playing` THEN the frontend SHALL send a tick every 500 milliseconds.
2. WHEN the status is `game_over` THEN the frontend SHALL stop sending ticks.

### Requirement 31: Movement controls

**User Story:** As a player, I want keyboard controls, so that I can play.

#### Acceptance Criteria

1. WHEN the player presses the Left control THEN the frontend SHALL send a `left` move.
2. WHEN the player presses the Right control THEN the frontend SHALL send a `right` move.
3. WHEN the player presses the Down control THEN the frontend SHALL send a `down` move.

### Requirement 32: Restart control

**User Story:** As a player, I want a restart button, so that I can begin again.

#### Acceptance Criteria

1. WHEN the player activates the Restart control THEN the frontend SHALL create a new game via `POST /api/games`.
2. WHEN a new game is created THEN the frontend SHALL render the fresh state.

### Requirement 33: Game-over message

**User Story:** As a player, I want to know when the game ends, so that I understand the state.

#### Acceptance Criteria

1. WHEN the status is `game_over` THEN the frontend SHALL display a clear English game-over message.
2. WHEN the status is `playing` THEN the frontend SHALL NOT display the game-over message.

### Requirement 34: English labels

**User Story:** As a player, I want English UI text, so that the interface is understandable.

#### Acceptance Criteria

1. WHEN the frontend renders controls and status THEN all visible labels SHALL be in English.

### Requirement 35: Reproducible build and tests

**User Story:** As a researcher, I want documented commands, so that the study is reproducible.

#### Acceptance Criteria

1. WHEN backend tests are run with the documented command THEN they SHALL execute the rule tests.
2. WHEN the frontend build is run with the documented command THEN it SHALL produce a production build without errors.
