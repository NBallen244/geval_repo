# Spec Delta: Tetris Core

## ADDED Requirements

### Requirement: REQ-047 Clockwise Rotation (Milestone 1)
The system MUST support clockwise 90-degree rotation of the active tetromino in the authoritative backend engine and expose it to the single-player UI. Clockwise rotation SHALL be triggered via the `ArrowUp` key on the frontend (while retaining React DOM-based rendering in Milestone 1) or a movement request with direction `"clockwise"` on the backend REST API.

#### Scenario: Successful clockwise rotation
- **GIVEN** an active piece at coordinate origin `[row, col]` with orientation 0 and no rotation obstructions
- **WHEN** clockwise rotation is requested via POST `/api/games/{id}/move` with direction "clockwise"
- **THEN** the active piece's orientation is updated to 1
- **AND** its cells are rotated 90 degrees clockwise relative to its origin

### Requirement: REQ-048 Counterclockwise Rotation (Milestone 1)
The system MUST support counterclockwise 90-degree rotation of the active tetromino in the authoritative backend engine and expose it to the single-player UI. Counterclockwise rotation SHALL be triggered via the `Z` key on the frontend (while retaining React DOM-based rendering in Milestone 1) or a movement request with direction `"counterclockwise"` on the backend REST API.

#### Scenario: Successful counterclockwise rotation
- **GIVEN** an active piece at coordinate origin `[row, col]` with orientation 0 and no rotation obstructions
- **WHEN** counterclockwise rotation is requested via POST `/api/games/{id}/move` with direction "counterclockwise"
- **THEN** the active piece's orientation is updated to 3
- **AND** its cells are rotated 90 degrees counterclockwise relative to its origin

### Requirement: REQ-049 Deterministic Rotation Orientations (Milestone 1)
Each of the 7 standard tetrominoes MUST define exactly four discrete, deterministic orientations (0, 1, 2, 3) with exact local cell coordinates relative to the piece's origin. This layout is governed by a fixed central pivot `[2, 1]` for 3-row shapes (T, J, L, S, Z) and a half-cell pivot `[1.5, 1.5]` for the 4x4 shape (I).

An "O" piece rotation MUST be treated as a no-op, preserving its coordinates and orientation (0) unchanged. A piece spawning or being retrieved from the Hold slot MUST enter play in its default initial spawn orientation (0).

Spawning or Hold Swapping normalizes coordinates by placing the piece at the spawn origin `[0, 3]` and setting orientation to 0.

#### Exact Occupied-Cell Tables (Relative to local Origin):

1. **"I" Piece** (Half-cell pivot `[1.5, 1.5]`, CW formula `[r, c] -> [c, 3 - r]`, CCW formula `[r, c] -> [3 - c, r]`):
   - Orientation 0 (Spawn): `[[1, 0], [1, 1], [1, 2], [1, 3]]`
   - Orientation 1: `[[0, 2], [1, 2], [2, 2], [3, 2]]`
   - Orientation 2: `[[2, 0], [2, 1], [2, 2], [2, 3]]`
   - Orientation 3: `[[0, 1], [1, 1], [2, 1], [3, 1]]`

2. **"O" Piece** (Rotation no-op, always orientation 0):
   - Orientation 0/1/2/3: `[[1, 1], [1, 2], [2, 1], [2, 2]]`

3. **"T" Piece** (Fixed Pivot `[2, 1]`, CW formula `[r, c] -> [c + 1, 3 - r]`, CCW formula `[r, c] -> [2 - (c - 1), 1 + (r - 2)]`):
   - Orientation 0 (Spawn): `[[1, 1], [2, 0], [2, 1], [2, 2]]`
   - Orientation 1: `[[1, 1], [2, 1], [2, 2], [3, 1]]`
   - Orientation 2: `[[2, 0], [2, 1], [2, 2], [3, 1]]`
   - Orientation 3: `[[1, 1], [2, 0], [2, 1], [3, 1]]`

4. **"J" Piece** (Fixed Pivot `[2, 1]`, CW/CCW formulas same):
   - Orientation 0 (Spawn): `[[1, 0], [2, 0], [2, 1], [2, 2]]`
   - Orientation 1: `[[1, 1], [1, 2], [2, 1], [3, 1]]`
   - Orientation 2: `[[2, 0], [2, 1], [2, 2], [3, 2]]`
   - Orientation 3: `[[1, 1], [2, 1], [3, 0], [3, 1]]`

5. **"L" Piece** (Fixed Pivot `[2, 1]`, CW/CCW formulas same):
   - Orientation 0 (Spawn): `[[1, 2], [2, 0], [2, 1], [2, 2]]`
   - Orientation 1: `[[1, 1], [2, 1], [3, 1], [3, 2]]`
   - Orientation 2: `[[2, 0], [2, 1], [2, 2], [3, 0]]`
   - Orientation 3: `[[1, 0], [1, 1], [2, 1], [3, 1]]`

6. **"S" Piece** (Fixed Pivot `[2, 1]`, CW/CCW formulas same):
   - Orientation 0 (Spawn): `[[1, 1], [1, 2], [2, 0], [2, 1]]`
   - Orientation 1: `[[1, 1], [2, 1], [2, 2], [3, 2]]`
   - Orientation 2: `[[2, 1], [2, 2], [3, 0], [3, 1]]`
   - Orientation 3: `[[1, 0], [2, 0], [2, 1], [3, 1]]`

7. **"Z" Piece** (Fixed Pivot `[2, 1]`, CW/CCW formulas same):
   - Orientation 0 (Spawn): `[[1, 0], [1, 1], [2, 1], [2, 2]]`
   - Orientation 1: `[[1, 2], [2, 1], [2, 2], [3, 1]]`
   - Orientation 2: `[[2, 0], [2, 1], [3, 1], [3, 2]]`
   - Orientation 3: `[[1, 1], [2, 0], [2, 1], [3, 0]]`

These local matrices guarantee unobstructed four-turn closure, exact inverse CW/CCW mappings, and identical occupied cells for O. Spawning and Hold Swap entries MUST normalize to Orientation 0.

#### Scenario: Verify initial orientation from spawn and hold
- **GIVEN** a piece is spawned or retrieved from Hold
- **WHEN** the active piece state is retrieved
- **THEN** its orientation is exactly 0
- **AND** its local cells match Orientation 0

#### Scenario: Verify O piece rotation is a no-op
- **GIVEN** an active "O" piece is in play
- **WHEN** a rotation is requested
- **THEN** its orientation remains 0 and its cell coordinates are unchanged

### Requirement: REQ-050 Horizontal-Only Wall Kicks (Milestone 1)
When a rotation is requested and the rotated target cells would overlap the board boundaries (left, right, bottom) or settled blocks, the system MUST attempt to resolve the collision by applying horizontal column offsets to the origin in the exact priority order: `0, -1, +1, -2, +2`. The system SHALL apply the first offset candidate that yields a valid, non-colliding position on the board. Vertical kicks (adjusting the row position) MUST NOT be performed. If none of the candidates are valid, the entire rotation MUST be rejected, preserving the piece's original position and orientation.

#### Scenario: Wall kick resolves horizontal boundary collision
- **GIVEN** an active "I" piece is next to the right wall (column 9)
- **WHEN** clockwise rotation is requested
- **THEN** the candidate offset `0` is blocked by the wall
- **AND** the candidate offset `-1` is valid and applied, shifting the piece 1 column to the left

#### Scenario: Full rejection when no offsets fit
- **GIVEN** an active piece is trapped on both sides by settled blocks or walls
- **WHEN** a rotation is requested
- **THEN** all offsets in `[0, -1, +1, -2, +2]` are invalid
- **AND** the rotation is rejected, keeping original position and orientation

### Requirement: REQ-051 No Side-Effects on Rotation (Milestone 1)
Active piece rotation MUST NOT by itself lock the piece, advance gravity, modify scores, update level counters, or mutate the next or held piece queue.

- **Blocked-down vs Gravity-lock**: Rotation does not trigger lockdown or advance gravity. Gravity ticks are driven independently. Lock-down occurs only when gravity (or manual drop) attempts to shift the piece down and is blocked.
- **Terminal game no-op**: If the game status is `game_over`, any rotation requests are rejected as a terminal no-op.

#### Scenario: Rotation executes without score or gravity mutation
- **GIVEN** a rotation is successfully performed
- **WHEN** state is retrieved
- **THEN** the score, level, and lines counters remain unchanged
- **AND** gravity ticks are not advanced, and hold slot is not updated

### Requirement: REQ-052 HTML5 Canvas 2D Rendering Board (Milestone 2)
The frontend board grid rendering MUST be implemented using an HTML5 Canvas 2D context instead of individual React DOM cells. The Canvas element MUST accurately draw all settled blocks and the active piece in their correct coordinates, and MUST adjust its scaling using the browser's device pixel ratio (`window.devicePixelRatio`) to maintain sharp block edges and prevent blurring on high-DPI displays. The board grid MUST automatically redraw on state updates, window resize, game status changes, or restart events.

#### Scenario: Canvas redraws on active piece update
- **GIVEN** an active piece moves or rotates on the backend
- **WHEN** the updated state payload is fetched by the frontend
- **THEN** the Canvas redraws the grid, rendering the new active piece cells and settled blocks correctly

### Requirement: REQ-053 Canvas-Compatible Controls and State Protection (Milestone 2)
While rendering game boards on HTML5 Canvas 2D, the frontend MUST fully preserve and support all existing keyboard controls (ArrowLeft, ArrowRight, ArrowDown, C for hold), score, level, lines, Hold preview, piece preview, leaderboard panels, and network stale-response protection.

#### Scenario: Arrow keys trigger move during canvas rendering
- **GIVEN** a game is running and rendering via Canvas
- **WHEN** the player presses ArrowLeft
- **THEN** the move request is dispatched and the board redraws the updated position returned by the server
