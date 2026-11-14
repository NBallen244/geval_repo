---
title: "PRD Addendum: Stage 2 Technical Contracts & Strategy"
status: final
created: 2026-10-25T20:12
updated: 2026-10-25T20:12
---

# PRD Addendum: Stage 2 Technical Contracts & Strategy

This addendum records the API schema shifts, endpoints, frontend reactivity design, and automated testing architecture for Stage 2.

## 1. Updated API Contract (GameState Schema)

The state returned by all endpoints (and serialized by the backend) is extended to include Stage 2 fields.

### JSON State Payload (`GameState` model):
```json
{
  "id": "string (UUID)",
  "status": "playing" | "game_over",
  "board": [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ... (20 rows of 10 columns; 0 = empty, 1-7 = settled block color indices)
  ],
  "active_piece": {
    "shape": "I" | "J" | "L" | "O" | "S" | "T" | "Z",
    "origin": {"row": 0, "col": 3},
    "cells": [
      {"row": 0, "col": 3},
      {"row": 0, "col": 4},
      {"row": 0, "col": 5},
      {"row": 0, "col": 6}
    ]
  } | null,
  "score": 0,
  "total_lines": 0,
  "level": 1,
  "gravity_interval_ms": 500,
  "next_piece": "I" | "J" | "L" | "O" | "S" | "T" | "Z",
  "hold_piece": "I" | "J" | "L" | "O" | "S" | "T" | "Z" | null,
  "can_hold": true
}
```
*Note on Nullable Active Piece:* Under the `"game_over"` status, particularly due to an obstructed spawn (either from a normal piece spawn or retrieved hold piece), the `active_piece` field is set to `null` to avoid returning illegal overlapping cells. During active play (`"playing"`), `active_piece` is always populated and strictly follows the coordinate structure defined in `SHAPE_TEMPLATES`.

### Endpoints
1. **`POST /api/games`**
   - **Status Code:** 201 Created
   - **Behavior:** Initializes score to 0, lines to 0, level to 1, gravity_interval_ms to 500, select active and next piece randomly (exactly 2 RNG draws). Returns GameState.
2. **`GET /api/games/{id}`**
   - **Status Code:** 200 OK (or 404 Not Found if missing ID)
   - **Behavior:** Returns current GameState. Does NOT consume next_piece and makes exactly zero (0) RNG draws.
3. **`POST /api/games/{id}/tick`**
   - **Status Code:** 200 OK (or 404 Not Found)
   - **Behavior:** Performs gravity tick. If `status` is already `"game_over"`, returns state unmodified with zero (0) RNG draws.
4. **`POST /api/games/{id}/move`**
   - **Status Code:** 200 OK (or 404 / 422 for move validation errors)
   - **Behavior:** Moves piece. If `status` is already `"game_over"`, returns state unmodified with zero (0) RNG draws.
5. **`POST /api/games/{id}/hold`**
   - **Status Code:** 200 OK (or 404 Not Found)
   - **Behavior:** Performs Hold swap.
     - If game `status` is already `"game_over"` or `can_hold` is `false`, it behaves as a valid no-op, returning `200 OK` and the unmodified `GameState` with zero (0) RNG draws.
     - If `hold_piece` is empty (`null`), it bakes the current active piece into `hold_piece`, spawns `next_piece` at its template origin coordinates, generates exactly one new `next_piece` (1 RNG draw), sets `can_hold` to `false`, and returns `200 OK` and the updated `GameState`.
     - If `hold_piece` is occupied, it swaps the current active piece with `hold_piece`, spawns the retrieved piece at its template origin coordinates, keeps `next_piece` unchanged with zero (0) RNG draws, sets `can_hold` to `false`, and returns `200 OK` and the updated `GameState`.

---

## 2. Frontend Reactivity & Timing

To ensure robust synchronizations under React StrictMode:
- **Timer Management:** At any idle state, there must be exactly one active automatic timer driving gravity.
- **Immediate Cancellation:** When any mutation (arrow move, Hold button/C-key, Restart, gravity tick) is enqueued, the automatic timer is immediately canceled.
- **FIFO Mutation Queue:** All mutations must be processed in a strict FIFO queue. No overlapping or concurrent fetch/JSON requests are allowed.
- **Rescheduling Timer:** After the last queued response completes, schedule exactly one full gravity interval matching the newly updated `gravity_interval_ms` (e.g., waiting 450ms after completing execution when crossing to level 2; none at 449ms). If the final state returned has status `"game_over"`, the timer is completely cleared and no timer remains.
- **Preemption on Restart:** Clicking Restart must immediately preempt and discard the old mutation queue, clearing any pending timer, without waiting for any prior pending fetch/JSON requests to finish.
- **Monotonically Unique Generations:** The client must track monotonically unique generation tokens to verify ownership after every `fetch`, after every `.json()`, in all `catch`/`finally` blocks, and inside all timer callbacks. Obsolete or unmounted component callbacks are discarded and cannot mutate component state, loading, error, guard, or timer variables. Falsy rejected values are ignored and do not mutate state.
- **Hold Queueing:** Hold triggers are queueable and usable even while older requests are pending in the FIFO queue.
- **Interactive Control Elements:** Explicit Start/Restart interaction, Arrow controls, C key, and Hold buttons are preserved.

---

## 3. Automated Test Strategy

To verify Stage 2 features rigorously, we will introduce automated tests covering:
1. **Scoring Scenarios (with Mock Fixtures):**
   - We will write isolated domain unit tests using board fixtures pre-completed at the bottom rows.
   - We must NOT invent vertical "I" shapes, rotate "O", edit templates, or use arbitrary one-cell new pieces for testing.
   - For 3 and 4 completed rows, we isolate genuine canonical "O" pieces above precompleted bottom rows:
     - **3-Row Clear Test (N=3):**
       - Precompleted full rows: rows 17, 18, and 19 (filled with settled blocks, columns 0..9).
       - Row 16 is completely empty.
       - Place the canonical `"O"` piece at origin `(15,4)` with cells `(15,4), (15,5), (16,4), (16,5)`.
       - Execute a downward move or tick. Since row 17 is completely filled, the `"O"` piece collides and locks at origin `(15,4)`.
       - This results in clearing exactly 3 completed rows (rows 17, 18, and 19), with the `"O"` piece remaining baked at row 15 and 16.
     - **4-Row Clear Test (N=4):**
       - Precompleted full rows: rows 16, 17, 18, and 19 (filled with settled blocks, columns 0..9).
       - Row 15 is completely empty.
       - Place the canonical `"O"` piece at origin `(14,4)` with cells `(14,4), (14,5), (15,4), (15,5)`.
       - Execute a downward move or tick. Since row 16 is completely filled, the `"O"` piece collides and locks at origin `(14,4)`.
       - This results in clearing exactly 4 completed rows (rows 16, 17, 18, and 19), with the `"O"` piece remaining baked at row 14 and 15.
   - Verify that Level 1 awards 100, 300, 500, or 800 points.
   - Verify that Level 2 awards 200, 600, 1000, or 1600 points (using pre-lock level).
2. **Progression Calculations:**
   - Validate that level formula `1 + floor(total_lines / 10)` works under different values (e.g. 9 lines -> level 1, 10 lines -> level 2, 11 lines -> level 2, 20 lines -> level 3).
   - Validate that gravity interval formula computes correctly down to 100ms.
3. **Hold State Machine Transitions:**
   - Empty Hold swap: active piece gets stored in hold, next piece spawned, next piece generated. `can_hold` is set to false.
   - Occupied Hold swap: active piece swapped with hold, former hold spawns at standard origin, next piece preview is untouched. `can_hold` is set to false.
   - Lock reset: locking resets `can_hold` to true.
   - Double hold rejection / no-op: hold request returns the unchanged state if `can_hold` is false before lock.
4. **Obstructed Spawn Game Over:**
   - Validate that if standard spawn coordinates are filled by settled blocks, any spawn (normal or hold retrieval) immediately triggers a `"game_over"` status, and `active_piece` is set to `null` to ensure the final settled board is safe and clean.
5. **Regression Preservation:**
   - The original 13 regression tests are preserved completely unchanged and must continue passing. The historical one-cell test fixture remains untouched as an isolated regression, but will not be used to represent new canonical gameplays.
