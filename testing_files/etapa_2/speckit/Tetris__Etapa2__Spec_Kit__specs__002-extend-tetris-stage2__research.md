# Implementation Research: Extend Tetris to Stage 2

This document records the research and domain analysis completed for the Stage 2 Tetris extension. It forms the solid engineering foundation for the design of the scoring, leveling, piece-holding, and next piece preview subsystems.

---

## Technical Research & Key Subsystems

### 1. Progressive Gravity Timer & Dynamic Intervals (Frontend)

To make Tetris progressively challenging, gravity ticks must execute faster as the player levels up. 

- **Decision**: Implement a custom React hook `useGame.ts` that dynamically schedules a `useEffect`-driven ticking loop. The tick interval is bound directly to the `gravity_interval_ms` property returned by the backend. When `gravity_interval_ms` changes, the current active timer is automatically cancelled and rescheduled with the new interval.
- **Rationale**: Standard `setInterval` cannot easily change its interval on the fly without being cleared and re-created. Wrapping standard `setTimeout` or a resettable `useEffect` interval loop ensures that changes in gravity interval are immediately applied without waiting for the previous long interval to expire or causing double-ticking.
- **Alternatives Considered**: 
  - *Fixed timer with skip frames*: Keeping a constant 100ms interval and skipping ticks based on level. This is complex to coordinate and introduces visual sluggishness.
  - *Full Frontend-Authoritative ticking*: Discarding backend interval and computing it locally. Rejected because the backend is the single source of truth for the game state machine.

### 2. State Synchronization and Filtering Out-of-Order Responses

In a web application with network latency, rapid key inputs (e.g. holding down arrow keys or spamming soft-drops and Hold commands) can lead to multiple concurrent HTTP requests in flight. If an older request's response arrives *after* a newer request's response, it could overwrite the newer state, causing the game state to "jump backward" or flicker.

- **Decision**: Introduce a client-side transaction/sequence tracker in `useGame.ts`. The client maintains a monotonically increasing `requestSequenceNumber` on the client, or uses a simple locking mechanism (`isRequestInFlight` boolean) that prevents new network commands from being dispatched until the pending server request completes. Specifically, to keep gameplay fluid, we will use a request-locking mechanism where movements or hold triggers are ignored or queued, OR we will track the latest sent request ID and only apply state updates that correspond to the latest request. Given standard Tetris, a lightweight request sequence number combined with disabling/ignoring keyboard events while a request is in flight (`isLoading`) is the most robust way to prevent state desynchronization.
- **Rationale**: A client-side request lock guarantees that actions are executed sequentially on the authoritative backend, keeping the client and server states in lockstep.
- **Alternatives Considered**:
  - *Optimistic UI Updates*: Updating the board state locally before backend confirmation. Rejected because collision, row-clearing, and line-locking rules are extremely complex and authoritatively held on the backend. Optimistic updates would cause visual flickering if the backend disagreed (e.g., due to a late lock collision).

### 3. Hold and Swapping Piece State Machine (Backend)

The "Hold" action swaps the current falling piece with a stored piece. The player can only do this once per spawned piece.

- **Decision**: Maintain two new state variables in the in-memory backend session: `hold_piece: Optional[str]` and `can_hold: bool`.
  - When the game starts or restarts, `hold_piece` is `None` and `can_hold` is `True`.
  - On a `POST /api/games/{id}/hold` request:
    - If `can_hold` is `False`, ignore the command and return the current state.
    - If `hold_piece` is empty (`None`):
      1. Store the active piece's *type* in `hold_piece`.
      2. Set the `active_piece` to a new tetromino spawned at the top-center using the current `next_piece` type.
      3. Generate a new random piece type for `next_piece`.
      4. Set `can_hold` to `False`.
    - If `hold_piece` is already occupied (not `None`):
      1. Swap the active piece's type with `hold_piece` (the current active piece's type is saved in `hold_piece`, and the previously held piece type is spawned as the new `active_piece` at the top-center in its initial unrotated orientation).
      2. Leave the `next_piece` queue completely unchanged.
      3. Set `can_hold` to `False`.
  - When an active piece collision locks onto the board (during normal gravity ticks), reset `can_hold` to `True`.
- **Rationale**: This matches the classic Tetris hold rule exactly, preventing continuous swapping of the same piece and resetting the swap ability only once a piece locks.
- **Alternatives Considered**:
  - *Client-side hold handling*: Checking `can_hold` only in the frontend. Rejected because the backend is the authoritative state machine; a client could bypass validation and spam the swap command.

### 4. Line Clearing, Leveling, and Scoring Formula (Backend)

Line clearing requires counting rows cleared, adding them to the running total, and updating the level and gravity interval accordingly.

- **Decision**: Perform state calculations inside the locking phase of `tick_session`:
  1. Determine the number of rows cleared (`cleared_count`).
  2. If `cleared_count > 0`:
     - Calculate score: `score += bonus[cleared_count] * level` (using the level active *prior* to line clearing).
     - Update lines: `total_lines += cleared_count`.
     - Update level: `level = 1 + floor(total_lines / 10)`.
     - Update gravity: `gravity_interval_ms = max(100, 500 - 50 * (level - 1))`.
  - The scoring multipliers are:
    - 1 row: 100
    - 2 rows: 300
    - 3 rows: 500
    - 4 rows: 800
- **Rationale**: Leveling up is based on cumulative cleared lines (`total_lines`), where each 10 lines completed increases the level by 1. Basing the scoring multiplier on the level prior to line clearing prevents unfair scoring inflation at transition boundaries and aligns with standard Tetris scoring conventions.
- **Alternatives Considered**:
  - *Level-up on every 10 lines individually*: Checking if `total_lines % 10` crossed a boundary. This is less robust than using `1 + floor(total_lines / 10)`, which is self-correcting and handle multi-line clears that cross multiple boundaries.

### 5. Extended Schema Validation (Pydantic v2)

With several new numeric and string properties, the backend schema must enforce strict validation constraints to prevent illegal states.

- **Decision**: Define Pydantic fields in `GameSessionSchema` with the following rules:
  - `score`: integer, must be `>= 0` (default 0).
  - `total_lines`: integer, must be `>= 0` (default 0).
  - `level`: integer, must be `>= 1` (default 1).
  - `gravity_interval_ms`: integer, must be between `100` and `500` (default 500).
  - `next_piece`: string, must be one of `{"I", "O", "T", "S", "Z", "J", "L"}`.
  - `hold_piece`: string or null, must be one of `{"I", "O", "T", "S", "Z", "J", "L"}` or `None` (default null).
  - `can_hold`: boolean (default true).
- **Rationale**: Pydantic's automated field-level validation guarantees that malformed session states cannot be initialized or persisted, maintaining structural integrity across serialization boundaries.
- **Alternatives Considered**:
  - *Manual validation checks*: Checking fields in endpoints or service functions. Pydantic is already integrated into FastAPI and is more performant and declarative.
