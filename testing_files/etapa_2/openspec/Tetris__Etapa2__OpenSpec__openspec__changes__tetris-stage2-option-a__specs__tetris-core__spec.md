# Spec Delta

## ADDED Requirements

### Requirement: REQ-031 Backend State Payload Expansion
The backend game state response MUST expose: `id` (string), `board` (20x10 matrix), `active_piece` (object or null), `status` (string), `score` (integer), `total_lines` (integer), `level` (integer), `gravity_interval_ms` (integer), `next_piece` (string), `hold_piece` (string or null), and `can_hold` (boolean).

#### Scenario: Validate expanded State payload
- **GIVEN** a request to fetch game state
- **WHEN** GET `/api/games/{id}` is executed
- **THEN** the response includes `id`, `board`, `active_piece`, `status`, `score`, `total_lines`, `level`, `gravity_interval_ms`, `next_piece`, `hold_piece`, and `can_hold` keys

### Requirement: REQ-032 Score Initialization
A new game session MUST start with `score` set to 0, `total_lines` set to 0, `level` set to 1, `gravity_interval_ms` set to 500 ms, `hold_piece` set to null, and `can_hold` set to true.

#### Scenario: Verify initial Stage 2 metrics on spawn
- **GIVEN** a request to create a new game session
- **WHEN** POST `/api/games` is executed
- **THEN** the returned payload has `score` = 0, `total_lines` = 0, `level` = 1, `gravity_interval_ms` = 500, `hold_piece` = null, and `can_hold` = true

### Requirement: REQ-033 Scoring Execution
Points MUST be awarded immediately upon locking a piece, based on the number of rows simultaneously cleared by that lock and the level *immediately before* that lock:
- 1 row cleared: 100 * level points
- 2 rows cleared: 300 * level points
- 3 rows cleared: 500 * level points
- 4 rows cleared: 800 * level points
- 0 rows cleared: 0 points
Soft drop and gravity ticks MUST NOT award any additional points.

#### Scenario: Single row clear scoring
- **GIVEN** a game at level 2 clears exactly one row upon locking a piece
- **WHEN** line clearing is processed
- **THEN** the game score is increased by exactly 200 points (100 * 2)

### Requirement: REQ-034 Line Count Accumulation
Cleared rows MUST be added to the cumulative `total_lines` count immediately after scoring.

#### Scenario: Accumulate cleared lines
- **GIVEN** cumulative lines is 8 and two lines are cleared by a lock
- **WHEN** line clearing is processed
- **THEN** `total_lines` becomes 10

### Requirement: REQ-035 Level Progression
The game level MUST be recalculated as `level = 1 + floor(total_lines / 10)` immediately after updating the line count.

#### Scenario: Level up threshold reached
- **GIVEN** `total_lines` increases from 9 to 10
- **WHEN** level calculation is executed
- **THEN** `level` becomes 2

### Requirement: REQ-036 Progressive Gravity
The progressive gravity interval MUST be recalculated as `gravity_interval_ms = max(100, 500 - 50 * (level - 1))` immediately after updating the level.

#### Scenario: Calculate dynamic gravity at level 2
- **GIVEN** `level` increases to 2
- **WHEN** progressive gravity is updated
- **THEN** `gravity_interval_ms` is reduced to exactly 450 ms

### Requirement: REQ-037 Next Piece Queue
The backend MUST maintain a queued next piece. Fetching game state MUST NOT consume or change this piece, but spawning or holds (first time) MUST consume the previewed piece and generate exactly one new random preview.

#### Scenario: Peek next piece without consuming
- **GIVEN** a game session with next piece as "I"
- **WHEN** GET `/api/games/{id}` is executed multiple times
- **THEN** the returned `next_piece` is always "I" and the queue is not consumed

### Requirement: REQ-038 First Hold Execution
When the hold slot is empty, requesting POST `/api/games/{id}/hold` MUST place the active piece type into the `hold_piece` slot, remove the active piece, spawn the queued `next_piece` at the normal spawn origin `[0, 3]` in its initial orientation, generate a new random `next_piece`, and set `can_hold` to false.

#### Scenario: Execute hold with empty slot
- **GIVEN** active piece is "T", `next_piece` is "I", and `hold_piece` is null
- **WHEN** POST `/api/games/{id}/hold` is executed
- **THEN** `hold_piece` becomes "T", active piece becomes "I" at origin `[0, 3]`, a new random piece is queued in `next_piece`, and `can_hold` becomes false

### Requirement: REQ-039 Swapping Hold Execution
When the hold slot is occupied, requesting POST `/api/games/{id}/hold` MUST swap the active piece type and the `hold_piece` type, spawn the held piece type at the normal spawn origin `[0, 3]` in its initial orientation, leave the queued `next_piece` unchanged, and set `can_hold` to false.

#### Scenario: Execute swap hold with occupied slot
- **GIVEN** active piece is "O", `next_piece` is "I", and `hold_piece` is "S"
- **WHEN** POST `/api/games/{id}/hold` is executed
- **THEN** `hold_piece` becomes "O", active piece becomes "S" at origin `[0, 3]`, `next_piece` remains "I", and `can_hold` becomes false

### Requirement: REQ-040 Hold Limitation
Hold can be used at most once per active piece, and MUST become available again (`can_hold` becomes true) only after that piece locks and a new active piece spawns. If the game status is `game_over`, `can_hold` MUST be false. If POST `/api/games/{id}/hold` is requested when `can_hold` is false or the game status is `game_over`, the request MUST be rejected without mutating any game state.

#### Scenario: Repeated hold request ignored
- **GIVEN** `can_hold` is false for the current active piece
- **WHEN** POST `/api/games/{id}/hold` is requested
- **THEN** the request has no effect, the state remains unmodified, and `can_hold` remains false

#### Scenario: Hold request during game over ignored
- **GIVEN** the game status is `game_over` and `can_hold` is false
- **WHEN** POST `/api/games/{id}/hold` is requested
- **THEN** the request is rejected, the state remains unmodified, and `can_hold` remains false

### Requirement: REQ-041 Hold Spawn Collision
If spawning a new piece (either from next_piece on first hold, or from hold_piece on swap) at the spawn origin `[0, 3]` overlaps any settled blocks, the game status MUST transition immediately to `game_over`.

#### Scenario: Overlap collision during hold swap
- **GIVEN** settled blocks exist at cell `[1, 4]` and a swapped held piece of type "T" overlaps it on spawn
- **WHEN** POST `/api/games/{id}/hold` is executed
- **THEN** the game status transitions to `game_over`

### Requirement: REQ-042 Dynamic Frontend Gravity Timing
The frontend MUST schedule gravity ticks dynamically based on the `gravity_interval_ms` value received from the latest backend state.

#### Scenario: Interval adjusts dynamically on level up
- **GIVEN** `gravity_interval_ms` changes from 500 ms to 450 ms in the state payload
- **WHEN** the frontend processes the state update
- **THEN** the active gravity timer is cleared and rescheduled to run at the new 450 ms interval

### Requirement: REQ-043 Frontend Inputs for Hold
The frontend MUST render score, total_lines, level, next_piece preview, hold_piece, and a visual cooldown indicator for `can_hold`. It MUST provide a clickable "Hold" button and capture keydown events for the "C" key to execute a Hold request.

#### Scenario: Trigger hold using C key
- **GIVEN** a game is playing
- **WHEN** the player presses the "C" key
- **THEN** a POST `/api/games/{id}/hold` request is dispatched to the backend

### Requirement: REQ-044 Stale Response Protection
The frontend MUST prevent overlapping network requests or stale out-of-order responses from reversing visible game state.

#### Scenario: Discard stale API response
- **GIVEN** multiple rapid move requests are dispatched to the backend
- **WHEN** a response from an older action returns after a newer response has already been received and rendered
- **THEN** the older response is discarded and the newer state remains visible

## MODIFIED Requirements

### Requirement: REQ-028 Reset Game Control
Restart control MUST reset the settled grid and generate a new game with status `playing`. It MUST reset all Stage 2 counters (score=0, total_lines=0, level=1, gravity_interval_ms=500), clear the Hold slot (hold_piece=null, can_hold=true), spawn a new active piece and queue a new next piece.

#### Scenario: Restart game from game over
- **GIVEN** a game session with status `game_over` and populated board matrix
- **WHEN** the frontend restarts by sending POST `/api/games` to create a new session
- **THEN** the new session has a different ID, an empty board, an active piece at origin `[0, 3]`, status `playing`, and all Stage 2 metrics and Hold variables at their initial values
