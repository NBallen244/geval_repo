# Data Model Specification

## 1. Core Game Entities

### 1.1 `HighScoreEntry` (SQLite Persistent Storage)
High Scores are persisted inside a local SQLite database for **Solo play only**. Duel results do NOT populate this database.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `game_id` | TEXT | PRIMARY KEY, UNIQUE, NOT NULL | UUID of the finalized solo game session |
| `score` | INTEGER | >= 0, NOT NULL | Cumulative final score |
| `total_lines` | INTEGER | >= 0, NOT NULL | Total number of lines cleared |
| `level` | INTEGER | >= 1, NOT NULL | Final level reached |
| `completed_at` | TEXT | ISO-8601, NOT NULL | UTC timestamp of finalization (e.g. `YYYY-MM-DDTHH:MM:SSZ`) |

### 1.2 `TetrominoSchema` (In-Memory Active Piece Representation)
The structure of a falling piece, serialized within both Solo game state and Duel player board updates.

| Field | Type | Validation Rules | Description |
|-------|------|------------------|-------------|
| `type` | string | `I`, `O`, `T`, `S`, `Z`, `J`, `L` | Tetromino type |
| `cells` | array | Exactly 4 coordinate pairs: `[[r, c], [r, c], [r, c], [r, c]]` where `0 <= r <= 19` and `0 <= c <= 9` | Board indexes currently occupied by the piece |
| `origin` | array | Exactly 1 coordinate pair: `[r, c]` where `0 <= r <= 19` and `0 <= c <= 9` | The pivot coordinate used for rotation computations |

### 1.3 `GameSessionSchema` (In-Memory Solo Game State)
Maintains the state of an active single-player session.

| Field | Type | Validation Rules | Description |
|-------|------|------------------|-------------|
| `id` | string | Valid UUID string | Unique session identifier |
| `board` | array | 20x10 matrix. Values `0-7` | Board layout. `0` is empty, `1-7` map to settled block colors |
| `active_piece` | object | Optional `TetrominoSchema` | Current falling piece (null if game over) |
| `status` | string | `playing`, `game_over` | Lifecycle state of the session |
| `score` | int | >= 0 | Player's score |
| `total_lines` | int | >= 0 | Lines cleared |
| `level` | int | >= 1 | Current level |
| `gravity_interval_ms`| int | 100 to 500 | Current gravity loop interval in milliseconds |
| `next_piece` | string | `I`, `O`, `T`, `S`, `Z`, `J`, `L` | Pre-drawn type of the next piece |
| `hold_piece` | string | Optional `I`, `O`, `T`, `S`, `Z`, `J`, `L` | Held piece type (null if empty) |
| `can_hold` | boolean | | Tracks whether Hold can be triggered in the current turn |
| `is_persisted` | boolean | Excluded from JSON API | In-memory flag to ensure once-only SQLite finalization |

---

## 2. Multi-Player Duel Entities (In-Memory)

### 2.1 `PlayerState` (Seat State in a Duel)
Tracks the state of a single player within a duel room.

| Field | Type | Validation / Constraints | Description |
|-------|------|--------------------------|-------------|
| `player_id` | string | UUID string | Unique identifier for the player's connection |
| `board` | array | 20x10 matrix of `0-7` | Authoritative board matrix for this seat |
| `active_piece` | object | Optional `TetrominoSchema` | Authoritative active falling piece for this seat |
| `active_piece_generation`| integer| >= 0, starts at 0 | Server-owned generation count. Increments ONLY on spawn or Hold swap, not on gravity/horizontal movement. |
| `last_processed_seq_num` | integer| Bounded safe-integer, starts at 0 | Stores the highest sequence number processed for this seat to prevent duplicate or out-of-order action replay. |
| `next_piece_index`| integer| >= 0 | Pointer tracking the piece index in the room's seed sequence |
| `hold_piece` | string | Optional `I`, `O`, `T`, `S`, `Z`, `J`, `L` | Type of held piece |
| `can_hold` | boolean | | Whether the player can swap with Hold this turn |
| `score` | integer | >= 0 | Current accumulated score |
| `total_lines` | integer | >= 0 | Current cleared lines |
| `level` | integer | >= 1 | Current level (dictating gravity interval) |
| `status` | string | `playing`, `game_over`, `disconnected` | Status of the player's seat |

### 2.2 `DuelRoom` (Room State Container)
Encapsulates a duel match between two players. Bounded and managed in-memory on the backend server.

| Field | Type | Validation / Constraints | Description |
|-------|------|--------------------------|-------------|
| `room_id` | string | UUID string | Unique identifier of the duel room |
| `status` | string | `waiting`, `active`, `finished` | Room lifecycle status |
| `players` | dict | Exactly two keys: `seat_1` and `seat_2` mapping to `PlayerState` models | Seat mappings (values are null if seat is vacant) |
| `piece_sequence` | array | Pre-generated list of 1000 type strings (`I`, `O`, etc.) | Identical seed sequence supplied to both boards |
| `last_action_seat` | string | `"seat_1"`, `"seat_2"`, or null | Tracks which seat triggered the latest accepted action |
| `last_action_seq` | integer | Bounded safe-integer, or null | Sequence number of the latest accepted action for correlation |
| `last_action_observable_change` | boolean | | True if the latest action resulted in an observable state change |
| `created_at` | string | UTC ISO-8601 | Room creation timestamp |
| `last_activity` | string | UTC ISO-8601 | Tracks last command or state tick to guide garbage collection |

---

## 3. State Transitions

### 3.1 Solo Game Status Transitions
Solo sessions are transient in-memory models that transition sequentially:
```text
[Create Game API] ──> Status: "playing"
                          │
                          │ (Gravity tick/Obstructed hold overlap)
                          ▼
                      Status: "game_over" ──> [Trigger SQLite Insert Once]
```

### 3.2 Duel Room Status Transitions
Rooms are managed thread-safely in-memory, transitioning across three lifecycle states:
```text
[Init Room] ──> Status: "waiting"
                     │
                     │ (Two players join: Seat 1 and Seat 2 filled)
                     ▼
                Status: "active" (Starts server gravity loops & input routing)
                     │
                     │ (Case A: Both players top out in same server update tick -> DRAW)
                     │ (Case B: Player A tops out first -> Player B WINS)
                     │ (Case C: Player A disconnects/forfeits -> Player B WINS)
                     ▼
                Status: "finished" (Releases timers, and cleans up room within 5 mins)
```

### 3.3 Seat (PlayerState) Status Transitions
The status of a single seat within an active room transitions as follows:
```text
[Player Joins] ──> Status: "playing"
                       │
                       ├─ (Spawns overlap settled cells) ──> Status: "game_over"
                       │
                       └─ (WebSocket disconnected) ──> Status: "disconnected" (Forfeit)
```
- A disconnect transitions the seat status immediately to `"disconnected"`.
- This triggers a transition of the parent `DuelRoom` to `"finished"`, reporting a forfeit win to the surviving player.
- Reconnections are not supported; any connection drop results in an immediate forfeit.
