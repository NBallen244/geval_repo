# Data Model Design: Tetris Stage 3 Persistent High Scores

This document specifies the SQLite database schema, the Pydantic v2 validation models, and the state-transition machinery governing persistent high scores, API payload verification, and thread-safe operations.

---

## 1. Relational Database Schema (SQLite)

Completed games are permanently stored in a single database table named `high_scores`. The path is configured via `TETRIS_DB_PATH` and defaults to `./data/high-scores.sqlite3`.

### Table: `high_scores`

| Column | SQL Type | Constraints | Description |
|---|---|---|---|
| `game_id` | TEXT | PRIMARY KEY, NOT NULL, UNIQUE | Monotonically generated UUIDv4 representing the authoritative game session. |
| `score` | INTEGER | NOT NULL, CHECK(`score` >= 0) | The final accumulated score. |
| `total_lines` | INTEGER | NOT NULL, CHECK(`total_lines` >= 0) | Total horizontal lines cleared during the game. |
| `level` | INTEGER | NOT NULL, CHECK(`level` >= 1) | The final level reached by the player. |
| `completed_at` | TEXT | NOT NULL | UTC timestamp in ISO-8601 string format: `YYYY-MM-DDTHH:MM:SSZ`. |

#### SQL Schema Definition
```sql
CREATE TABLE IF NOT EXISTS high_scores (
    game_id TEXT PRIMARY KEY NOT NULL,
    score INTEGER NOT NULL CHECK(score >= 0),
    total_lines INTEGER NOT NULL CHECK(total_lines >= 0),
    level INTEGER NOT NULL CHECK(level >= 1),
    completed_at TEXT NOT NULL
);

-- Index to optimize sorting on leaderboard reads (GET /api/high-scores)
CREATE INDEX IF NOT EXISTS idx_high_scores_leaderboard 
ON high_scores (score DESC, completed_at ASC, game_id ASC);
```

---

## 2. Pydantic v2 Request/Response Schemas

FastAPI utilizes Pydantic v2 to validate payload serialization. To prevent cheaters from forging records or injecting unauthorized score metadata, we rigorously validate all input requests and forbid extra fields.

### `CreateGameRequest` (Game Creation Payload Validation)
Excludes any client-submitted fields to prevent arbitrary game settings or preset scores.
```python
from pydantic import BaseModel

class CreateGameRequest(BaseModel):
    model_config = {
        "extra": "forbid"  # Strictly reject any keys inside the JSON request body
    }
```

### `MoveRequest` (Movement Payload Validation)
Enforces a restrictive allowed list of direction strings and forbids extra keys.
```python
from pydantic import BaseModel, Field, field_validator

class MoveRequest(BaseModel):
    direction: str = Field(..., description="The sliding direction. One of 'left', 'right', 'down'.")

    model_config = {
        "extra": "forbid"  # Strictly reject any extraneous keys like 'score' or 'level'
    }

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        allowed = {"left", "right", "down"}
        if v not in allowed:
            raise ValueError(f"Direction must be one of {allowed}")
        return v
```

### `HighScoreEntrySchema` (Database Record Model)
Represents a single verified row returned in the leaderboard array.
```python
from pydantic import BaseModel, Field

class HighScoreEntrySchema(BaseModel):
    game_id: str = Field(..., description="UUID of the completed game session")
    score: int = Field(..., ge=0, description="The final game score")
    total_lines: int = Field(..., ge=0, description="Number of lines cleared")
    level: int = Field(..., ge=1, description="Final level reached")
    completed_at: str = Field(..., description="UTC completion timestamp in ISO-8601 format")
```

### `LeaderboardResponseSchema` (Leaderboard API Output Model)
```python
from typing import List
from pydantic import BaseModel

class LeaderboardResponseSchema(BaseModel):
    scores: List[HighScoreEntrySchema]
```

---

## 3. Game State Machine & Database Finalization Transitions

The authoritative game state exists purely in-memory. Persistence only occurs at the transition boundary to `"game_over"`.

```text
       +---------------------------------------------+
       |                  PLAYING                    |
       |  (Active piece falling, user input, tick)   |
       +---------------------+-----------------------+
                             |
                             | Game Over event:
                             | - Falling block overlaps on spawn origin (Gravity/Soft Drop)
                             | - Exceeded boundary on Hold piece swap (Obstructed Hold)
                             v
       +---------------------------------------------+
       |                 GAME_OVER                   |
       |  (Status="game_over", active_piece=None)    |
       +---------------------+-----------------------+
                             |
                             | Atomic Finalization (with threading.Lock):
                             | 1. Acquire mutex
                             | 2. Parameterized SQL insert of metrics
                             | 3. Set 'is_persisted = True' on session
                             | 4. Release mutex
                             v
       +---------------------------------------------+
       |                 PERSISTED                   |
       | (Database record exists, immutable state)   |
       +---------------------------------------------+
```

### Core Logic for State Mutation & Finalization Race Protection

To prevent concurrent requests from triggering multiple writes or corrupting in-memory game state, the backend wraps all mutating requests inside a synchronized block using a global/per-session `threading.Lock`.

1. **State Mutation (Tick, Move, Hold)**:
   - Acquire thread lock.
   - If `status == "game_over"`, skip calculations and skip finalization write (or retry persistence if `is_persisted == False`).
   - Run movement / tick collision calculations.
   - If collision locks piece:
     - Check rows to clear, update score, lines, level, and next piece.
     - Check if newly spawned piece collides with settled blocks:
       - If yes, transition `status = "game_over"`, set `active_piece = None`.
       - If no, keep `status = "playing"`.
   - If state has transitioned to `"game_over"` during this action:
     - Execute the Database Finalization routine immediately (within the same synchronized block).
   - Release thread lock.

2. **Database Finalization Routine**:
   - Query if `game_id` already exists in `high_scores` or if the in-memory session is already marked `is_persisted`.
   - If yes, abort writing (idempotent no-op).
   - If no, write a parameterized transaction:
     ```sql
     INSERT INTO high_scores (game_id, score, total_lines, level, completed_at)
     VALUES (?, ?, ?, ?, ?);
     ```
   - Mark `is_persisted = True` in the session.
   - If SQLite throws a locked or writing exception, catch it, log it securely without leaking paths/SQL, raise a controlled 503, and leave `is_persisted = False` so that subsequent mutating requests on this dead game session can safely retry persistence.

3. Read-only Commands (GET State / Leaderboard):
   - Read-only operations (GET State) obtain the thread-safe lock briefly to perform a deep-copy/snapshot of the in-memory game state (`.model_copy(deep=True)`), ensuring that GET operations do not inspect mutable live state outside protection or read a torn/partially-updated state.
   - GET operations do NOT perform any state mutation, do NOT attempt database inserts, and do NOT retry failed persistence. They do not hold the lock during long I/O or network responses, avoiding nested non-reentrant-lock deadlocks. Leaderboard database reads (GET /api/high-scores) also execute outside the state-mutation lock and do not mutate state.
