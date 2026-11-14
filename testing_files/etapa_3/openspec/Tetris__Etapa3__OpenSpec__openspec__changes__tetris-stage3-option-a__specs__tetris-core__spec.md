# Spec Delta

## MODIFIED Requirements

### Requirement: REQ-026 Game Over Condition
The game status MUST transition to `game_over` if a newly spawned piece overlaps any settled blocks. This transition MUST trigger authoritative, synchronized persistent recording of the final game state (conforming to REQ-046). Any subsequent state mutation or duplication of this finalization MUST be rejected.

#### Scenario: Game over trigger
- **GIVEN** settled blocks are present at row 0, column 3 (i.e. cell `[0, 3]`)
- **WHEN** a new piece attempts to spawn at origin `[0, 3]`
- **THEN** the game status transitions to `game_over`

#### Scenario: Game over trigger and immutability
- **GIVEN** settled blocks are present at row 0, column 3 (i.e. cell `[0, 3]`)
- **WHEN** a new piece attempts to spawn at origin `[0, 3]`
- **THEN** the game status transitions to `game_over` and persistent recording is triggered
- **AND** the original persisted result remains immutable on subsequent request attempts

### Requirement: REQ-028 Reset Game Control
Restart control MUST reset the settled grid and generate a new game with status `playing`. It MUST reset all Stage 2 counters (score=0, total_lines=0, level=1, gravity_interval_ms=500), clear the Hold slot (hold_piece=null, can_hold=true), spawn a new active piece, and queue a new next piece. Restarting, abandoning, or refreshing an active game session MUST NOT write a high score to persistent storage (no high score is recorded for games that do not naturally reach the terminal `game_over` status).

#### Scenario: Restart game from game over
- **GIVEN** a game session with status `game_over` and populated board matrix
- **WHEN** the frontend restarts by sending POST `/api/games` to create a new session
- **THEN** the new session has a different ID, an empty board, an active piece at origin `[0, 3]`, status `playing`, and all Stage 2 metrics and Hold variables at their initial values, and no new database row is created for the restarted session

### Requirement: REQ-029 Authority of Backend
The backend API MUST own the authoritative coordinate grid, validation, and collision states. Read-only endpoints (GET requests) MUST NOT mutate any game state or create any database records (GET idempotency). In-memory active game mutations (move, tick, hold) and finalization writes MUST be synchronized to prevent race conditions within the single-process backend. Active games exist only in-memory and are not resumed after backend restart.

#### Scenario: Authoritative state retrieval
- **GIVEN** a movement is processed on the backend
- **WHEN** the client requests `/api/games/{id}`
- **THEN** the response contains the authoritative board matrix, active piece coordinates, and game status

#### Scenario: Idempotency of state retrieval
- **GIVEN** a movement is processed on the backend
- **WHEN** the client requests GET `/api/games/{id}`
- **THEN** the response contains the authoritative board matrix and state, and no database writes or state mutations occur

### Requirement: REQ-041 Hold Spawn Collision
The backend MUST handle hold operations and transition immediately to `game_over` if spawning a piece from Hold (either on first-Hold when the hold slot is empty, or on occupied-Hold when swapping pieces) at the spawn origin `[0, 3]` overlaps any settled blocks. This transition MUST trigger persistent recording of the final game state.

#### Scenario: Overlap collision during hold swap
- **GIVEN** settled blocks exist at cell `[1, 4]` and a swapped held piece of type "T" overlaps it on spawn
- **WHEN** POST `/api/games/{id}/hold` is executed
- **THEN** the game status transitions to `game_over`

#### Scenario: Overlap collision during first-time empty hold obstruction path
- **GIVEN** an empty Hold slot and settled blocks at cell `[0, 3]` or overlapping spawn coordinates for the queued next piece
- **WHEN** POST `/api/games/{id}/hold` is executed (first-Hold path)
- **THEN** the game status transitions immediately to `game_over` and high-score recording is triggered

#### Scenario: Overlap collision during occupied-Hold swap obstruction path
- **GIVEN** settled blocks exist at cell `[1, 4]` and a swapped held piece of type "T" overlaps it on spawn at `[0, 3]`
- **WHEN** POST `/api/games/{id}/hold` is executed (occupied-Hold path)
- **THEN** the game status transitions immediately to `game_over` and high-score recording is triggered

## ADDED Requirements

### Requirement: REQ-056 Request Body Strictness
The backend MUST strictly validate request bodies for game creation and move/hold requests. Any extra or unexpected fields present in the request body (such as client-supplied score, level, or completed_at parameters) MUST be rejected with a 422 Unprocessable Entity error (or similar 4xx validation error), leaving the game state unchanged. Valid bodyless game creation (POST `/api/games` with an empty body) and valid movement bodies MUST be fully preserved.

#### Scenario: Reject move request with extra metadata fields
- **GIVEN** a game is playing
- **WHEN** a client sends POST `/api/games/{id}/move` with a body containing direction "left" and an injected field "score": 99999
- **THEN** the request is rejected with a 422 error, the game state and board remain completely unchanged, and no persistent record is created
