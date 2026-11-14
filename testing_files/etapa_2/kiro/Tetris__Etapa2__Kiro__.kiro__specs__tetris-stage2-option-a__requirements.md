# Requirements Document

## Introduction

This document defines the functional scope for Stage 2, Option A, of a browser-based Tetris study. It is a brownfield extension of the existing Stage 1, Option A implementation that lives in this same tool's workspace (`backend/` FastAPI service and `frontend/` React + TypeScript client, with the Stage 1 native specification under `.kiro/specs/tetris-stage1-option-a/`). The Stage 1 behavior and contracts are the baseline and must be preserved; Stage 2 only adds the features described below.

Stage 2 adds a **score**, a **cumulative cleared-line count**, a **level**, **progressive gravity**, a **one-piece Hold**, and a **one-piece next-piece preview**. The backend remains the single authoritative owner of game state and rules; the frontend renders backend state and forwards controls. There is no database and no authentication; all state remains in memory only.

The following remain explicitly out of scope for this stage and must not be introduced: rotation, wall kicks, T-Spins, ghost piece, time attack, achievements, persistence, database, authentication, multiplayer, and high-score storage.

### Relationship to Stage 1 (preserved baseline)

The following Stage 1 facts are inputs and must not be changed by Stage 2. They are reproduced here so Stage 2 acceptance criteria can reference them precisely.

- **Board:** 20 rows by 10 columns. Row `0` is the top, row `19` is the bottom; column `0` is leftmost, column `9` is rightmost.
- **Pieces:** the seven standard tetrominoes `I`, `O`, `T`, `S`, `Z`, `J`, `L` in their initial (unrotated) orientation only. The canonical relative offsets are:
  - `I`: `[0,0] [0,1] [0,2] [0,3]`
  - `O`: `[0,0] [0,1] [1,0] [1,1]`
  - `T`: `[0,1] [1,0] [1,1] [1,2]`
  - `S`: `[0,1] [0,2] [1,0] [1,1]`
  - `Z`: `[0,0] [0,1] [1,1] [1,2]`
  - `J`: `[0,0] [1,0] [1,1] [1,2]`
  - `L`: `[0,2] [1,0] [1,1] [1,2]`
- **Shape height:** every canonical shape above spans at most two rows. This remains true in Stage 2 and bounds what is reachable in ordinary play (see Requirement 5).
- **Spawn origin:** `(row 0, column 3)`. A piece whose spawn cells overlap a settled block or leave the board ends the game.
- **Piece generator:** a seeded deterministic shuffled 7-bag. The same seed produces the same type sequence. This behavior is retained unchanged; the only change is that Stage 2 exposes one previewed next piece and must draw exactly one new preview on the events defined below. The queued/spawn/Hold rules, canonical shapes, and 7-bag behavior are exactly as in the frozen seed and this tool's own baseline.
- **Board serialization:** JSON board is a 20x10 array of integer codes, `0` = empty and `1..7` = settled block type codes (`I=1, O=2, T=3, S=4, Z=5, J=6, L=7`). Integer codes, not letters, are used for board cells.
- **Legacy response key:** the active piece is exposed under the key `active_piece` (with `type`, `origin`, `cells`). This key name is retained.
- **Endpoints:** `POST /api/games`, `GET /api/games/{id}`, `POST /api/games/{id}/tick`, `POST /api/games/{id}/move` keep their existing request/response compatibility. `POST /api/games` returns HTTP 200 (not 201).
- **Status values:** `playing` and `game_over`.
- **Lock / clear / spawn ordering:** on a lock, the active piece settles into the board, completed lines are cleared, and only then is the next piece spawned. This tool's own ordering is the baseline; no terminal ordering from any other implementation is an input.
- **Regression tests:** the 39 existing backend test functions (27 in `backend/tests/test_rules.py`, 12 in `backend/tests/test_api.py`) are regression assertions and must continue to pass. One single assertion is a necessary exception: `test_state_payload_shape` asserts an exact top-level key set `{"id","status","board","active_piece"}`, which is logically incompatible with Requirement 6.1 (every state response must also expose the seven Stage 2 fields). That one top-level key-set equality is therefore widened to include the Stage 2 keys; the test's active-piece sub-shape assertion (`{"type","origin","cells"}`) and all other behavioral assertions of the 39 functions are preserved unchanged. No behavioral regression assertion is weakened.

### New data and coordinate conventions

- **Score:** a non-negative integer, initially `0`.
- **Total lines:** a non-negative integer counting all rows cleared since the game started, initially `0`.
- **Level:** a positive integer, initially `1`, derived as `1 + floor(total_lines / 10)`.
- **Gravity interval (ms):** a positive integer, initially `500`, derived as `max(100, 500 - 50 * (level - 1))`.
- **Next piece (`next_piece`):** the single piece type that will spawn next; always present (non-null) while the game is readable, and it remains a valid queued type after game over.
- **Hold piece (`hold_piece`):** the single piece type currently held, or `null` when the hold slot is empty.
- **Can hold (`can_hold`):** a boolean; `true` when a Hold is allowed for the current active piece, `false` once Hold has been used for the current active piece and until the next piece locks.

## Glossary

- **Consume the preview:** take the current `next_piece` as the piece to bring into play, then draw exactly one new preview from the seeded 7-bag so `next_piece` is refilled.
- **Spawn origin / initial orientation:** `(0, 3)` with the canonical unrotated offsets for the piece type.
- **Pre-lock level:** the value of `level` immediately before the lock currently being resolved, i.e. the level used to multiply the line-clear score for that lock.
- **Study controls:** the exact numeric scoring, leveling, and gravity formulas below are fixed experimental controls. They do not authorize rotation or any other out-of-scope feature.

## Requirements

### Requirement 1: New game initial counters

**User Story:** As a player, I want a new game to start from a known baseline, so that scoring and pacing are predictable.

#### Acceptance Criteria

1. WHEN a game is created via `POST /api/games` THEN the system SHALL set `score` to `0`.
2. WHEN a game is created THEN the system SHALL set `total_lines` to `0`.
3. WHEN a game is created THEN the system SHALL set `level` to `1`.
4. WHEN a game is created THEN the system SHALL set `gravity_interval_ms` to `500`.
5. WHEN a game is created THEN the system SHALL set `hold_piece` to `null`.
6. WHEN a game is created THEN the system SHALL set `can_hold` to `true`.
7. WHEN a game is created THEN the system SHALL set `next_piece` to a non-null piece type.

### Requirement 2: Score awarded per lock by cleared-row count and pre-lock level

**User Story:** As a player, I want points for clearing lines, so that I am rewarded for play.

#### Acceptance Criteria

1. WHEN a lock clears exactly 1 row THEN the system SHALL add `100 * pre_lock_level` to `score`.
2. WHEN a lock clears exactly 2 rows THEN the system SHALL add `300 * pre_lock_level` to `score`.
3. WHEN a lock clears exactly 3 rows THEN the system SHALL add `500 * pre_lock_level` to `score`.
4. WHEN a lock clears exactly 4 rows THEN the system SHALL add `800 * pre_lock_level` to `score`.
5. WHEN a lock clears 0 rows THEN the system SHALL add `0` to `score`.
6. WHEN computing the line-clear award for a lock THEN the system SHALL multiply by the level value in effect immediately before that lock (the pre-lock level), not the level after any resulting level increase.

### Requirement 3: Cumulative line count and level derivation

**User Story:** As a player, I want levels to rise as I clear lines, so that the game gets harder.

#### Acceptance Criteria

1. WHEN a lock clears `n` rows (`n` in `0..4`) THEN the system SHALL increase `total_lines` by `n` after computing that lock's score.
2. WHEN `total_lines` changes THEN the system SHALL set `level` to `1 + floor(total_lines / 10)`.
3. WHEN `total_lines` is `0` through `9` THEN `level` SHALL equal `1`.
4. WHEN `total_lines` is `10` through `19` THEN `level` SHALL equal `2`.
5. WHEN a lock clears no rows THEN `total_lines` and `level` SHALL remain unchanged.
6. WHEN the pre-lock state is `level` `1` and `total_lines` `9`, AND a lock clears exactly 1 row THEN the system SHALL add `100` to `score` (pre-lock level 1), set `total_lines` to `10`, set `level` to `2`, and set `gravity_interval_ms` to `450` (this is the primary TOTAL LINES 9 -> 10 threshold scenario).

### Requirement 4: Progressive gravity interval derivation

**User Story:** As a player, I want pieces to fall faster at higher levels, so that difficulty scales.

#### Acceptance Criteria

1. WHEN `level` changes THEN the system SHALL set `gravity_interval_ms` to `max(100, 500 - 50 * (level - 1))`.
2. WHEN `level` is `1` THEN `gravity_interval_ms` SHALL equal `500`.
3. WHEN `level` is `2` THEN `gravity_interval_ms` SHALL equal `450`.
4. WHEN `level` is `9` THEN `gravity_interval_ms` SHALL equal `100`.
5. WHEN `level` is `10` or greater THEN `gravity_interval_ms` SHALL equal `100` (the floor), never less than `100`.
6. WHEN the pre-lock state is `level` `9` and `total_lines` `89`, AND a lock clears exactly 1 row THEN the system SHALL compute that lock's score with the pre-lock level `9` (adding `900`), set `total_lines` to `90`, set `level` to `10`, AND set `gravity_interval_ms` to `100` after the level update (the correct level-9-to-10 crossing; no one-row clear moves `total_lines` from `9` directly into level `10`).

### Requirement 5: Four-, three-, and two-row clears validated as isolated domain rules

**User Story:** As a researcher, I want the multi-row scoring rules verified even though ordinary unrotated play cannot reach them, so that the scoring table is trustworthy without introducing rotation.

#### Acceptance Criteria

1. WHEN the scoring rule for 3 simultaneously cleared rows is verified THEN it SHALL be exercised through the real production clear-and-score path using an explicitly labeled isolated domain fixture (for example a crafted board with prefilled complete rows), not by presenting a rotated piece as valid UI play.
2. WHEN the scoring rule for 4 simultaneously cleared rows is verified THEN it SHALL be exercised through the real production clear-and-score path using an explicitly labeled isolated domain fixture, not by rotation.
3. WHEN verifying 3- and 4-row clears THEN the system SHALL NOT mutate the canonical unrotated shapes, SHALL NOT invent rotated or custom gameplay pieces, and SHALL NOT present artificially rotated pieces as valid gameplay in the UI.
4. WHEN verifying 0-, 1-, and 2-row clears THEN these cases MAY be reached either through ordinary play or through the same isolated domain fixtures, and SHALL use the real production clear-and-score path.
5. WHEN documenting verification THEN isolated-domain evidence SHALL be distinguished from user-visible / browser evidence.

### Requirement 6: State response exposes Stage 2 fields without consuming the queue

**User Story:** As a frontend developer, I want every state response to carry the Stage 2 fields, so that I can render them, and I want reads to be side-effect free.

#### Acceptance Criteria

1. WHEN the system returns game state THEN it SHALL include `score`, `total_lines`, `level`, `gravity_interval_ms`, `next_piece`, `hold_piece`, and `can_hold` in addition to the existing `id`, `status`, `board`, and `active_piece`.
2. WHEN the system returns game state THEN `next_piece` SHALL be a piece-type string (`I`,`O`,`T`,`S`,`Z`,`J`,`L`).
3. WHEN the system returns game state THEN `hold_piece` SHALL be a piece-type string or `null`.
4. WHEN the system returns game state THEN `can_hold` SHALL be a boolean.
5. WHEN a client sends `GET /api/games/{id}` THEN the response SHALL NOT change `score`, `total_lines`, `level`, `gravity_interval_ms`, `next_piece`, `hold_piece`, `can_hold`, the board, the active piece, the queued next piece, or the seeded generator / 7-bag state, and SHALL perform no generator draw.
6. WHEN any number of consecutive state reads are issued THEN `next_piece` SHALL be identical across them until an event defined in Requirement 7 consumes it.
7. WHEN the status is `game_over` THEN `next_piece` SHALL remain a valid queued piece type (it is not nulled and no further draw occurs).

### Requirement 7: Preview queue consumption counts

**User Story:** As a researcher, I want to know exactly when the previewed piece is drawn, so that the generator advances deterministically.

#### Acceptance Criteria

1. WHEN a piece spawns normally (new game, after a lock, or a restart's first spawn) THEN the system SHALL consume the previewed piece as the piece that enters play AND SHALL draw exactly one new preview (exactly one generator draw for the preview on that event).
2. WHEN the first Hold for an active piece occurs AND the hold slot was empty THEN the system SHALL move the current active piece into the hold slot, consume the previewed piece to become the new active piece, AND draw exactly one new preview (exactly one generator draw).
3. WHEN a Hold swaps with an already-occupied hold slot THEN the system SHALL exchange the active piece with the held piece AND SHALL NOT consume the preview or draw any new preview (zero generator draws).
4. WHEN a Hold is rejected (because `can_hold` is `false`) THEN the system SHALL NOT change the board, active piece, hold piece, preview, counters, or generator state (zero generator draws).
5. WHEN a state read, a rejected action, or any move after game over occurs THEN the system SHALL perform zero generator draws and SHALL NOT advance the 7-bag.

### Requirement 8: Hold mechanics

**User Story:** As a player, I want to hold a piece for later, so that I can plan placements.

#### Acceptance Criteria

1. WHEN `POST /api/games/{id}/hold` is called while `status` is `playing` AND `can_hold` is `true` AND the hold slot is empty THEN the system SHALL place the current active piece type into `hold_piece`, bring the previewed piece into play as the new active piece at the spawn origin `(0,3)` in its initial orientation, draw one new preview, and set `can_hold` to `false`.
2. WHEN `POST /api/games/{id}/hold` is called while `status` is `playing` AND `can_hold` is `true` AND the hold slot is occupied THEN the system SHALL swap the active piece type with `hold_piece`, place the swapped-in piece at the spawn origin `(0,3)` in its initial orientation, NOT consume the preview, and set `can_hold` to `false`.
3. WHEN a held or swapped-in piece is placed at the canonical spawn origin AND its cells overlap a settled block or leave the board THEN the system SHALL set `status` to `game_over` and clear the active piece, consistent with the seed-frozen Stage 1 spawn-collision behavior.
4. WHEN `POST /api/games/{id}/hold` is called while `can_hold` is `false` THEN the system SHALL reject the Hold and leave all state unchanged, with no generator draw.
5. WHEN an active piece locks THEN the system SHALL set `can_hold` to `true` for the next active piece, re-enabling Hold once per active piece.
6. WHEN `POST /api/games/{id}/hold` targets an unknown game id THEN the system SHALL respond with HTTP 404.
7. WHEN `POST /api/games/{id}/hold` is called while `status` is `game_over` THEN the system SHALL leave all state unchanged, with no generator draw.
8. WHEN the Hold endpoint returns THEN its response body SHALL use the same game-state shape as the other endpoints (Requirement 6).

### Requirement 9: Soft drop grants no points

**User Story:** As a player, I want soft drop to speed placement without inflating the score, so that scoring reflects line clears only.

#### Acceptance Criteria

1. WHEN a soft drop (`move` with `direction: "down"`) moves the active piece down THEN the system SHALL NOT change `score`.
2. WHEN a soft drop causes a lock THEN `score` SHALL change only according to the line-clear award rules in Requirement 2.

### Requirement 10: Rejected and post-game-over actions do not mutate state

**User Story:** As a player, I want invalid inputs ignored, so that game state stays consistent.

#### Acceptance Criteria

1. WHEN the status is `game_over` AND a tick, move, or hold is sent THEN the system SHALL leave the board, active piece, counters, hold state, preview, and generator unchanged, with no generator draw.
2. WHEN a Hold is rejected THEN the system SHALL leave all Stage 2 fields and generator state unchanged.
3. WHEN repeated state reads are issued THEN the system SHALL leave all Stage 2 fields and generator state unchanged.

### Requirement 11: Restart resets all Stage 2 state

**User Story:** As a player, I want restart to fully reset, so that a new game is clean.

#### Acceptance Criteria

1. WHEN a client sends `POST /api/games` (restart) THEN the system SHALL reset `score` to `0`, `total_lines` to `0`, `level` to `1`, and `gravity_interval_ms` to `500`.
2. WHEN a restart occurs THEN the system SHALL clear `hold_piece` to `null` and set `can_hold` to `true`.
3. WHEN a restart occurs THEN the system SHALL produce a fresh active piece and a fresh non-null `next_piece` preview.
4. WHEN a restart occurs THEN the new game SHALL have a new unique id distinct from the previous game.

### Requirement 12: Existing endpoint compatibility preserved

**User Story:** As an integrator, I want the Stage 1 endpoints to keep working, so that existing clients and the 39 regression tests pass.

#### Acceptance Criteria

1. WHEN `POST /api/games` is called THEN the system SHALL respond with HTTP 200 and a game-state body.
2. WHEN `GET /api/games/{id}` is called for an existing game THEN the system SHALL return its current state; for an unknown id it SHALL respond HTTP 404.
3. WHEN `POST /api/games/{id}/tick` is called THEN the system SHALL advance one gravity tick (move down or lock) exactly as in Stage 1, now also applying Stage 2 scoring/leveling on any resulting clear.
4. WHEN `POST /api/games/{id}/move` is called with `left`, `right`, or `down` THEN the system SHALL behave as in Stage 1; a missing or invalid `direction` SHALL yield HTTP 422 and an unknown id SHALL yield HTTP 404.
5. WHEN the board is serialized THEN cells SHALL remain integer codes (`0` empty, `1..7` types), the active piece SHALL remain under the `active_piece` key with `type`, `origin`, `cells`, and the spawn origin SHALL remain `(0,3)`.
6. WHEN Stage 2 is implemented THEN all 39 existing backend regression test functions SHALL continue to pass; the only permitted change is widening the single top-level key-set equality in `test_state_payload_shape` to include the Stage 2 fields mandated by Requirement 6.1 (its active-piece sub-shape assertion and every other behavioral assertion remain unmodified, and no behavioral assertion is weakened).

### Requirement 13: Frontend renders Stage 2 state

**User Story:** As a player, I want to see score, lines, level, hold, and next piece, so that I can follow my progress.

#### Acceptance Criteria

1. WHEN the frontend receives game state THEN it SHALL display the current `score`, `total_lines`, and `level` from backend state.
2. WHEN the frontend receives game state THEN it SHALL display the `next_piece` preview from backend state.
3. WHEN `hold_piece` is non-null THEN the frontend SHALL display the held piece; WHEN it is `null` the frontend SHALL show an empty / no-hold indication.
4. WHEN `can_hold` is `false` THEN the frontend SHALL disable the Hold button; WHEN it is `true` and the game is playing THEN the Hold button SHALL be enabled.
5. WHEN the frontend renders THEN it SHALL NOT compute scoring, leveling, gravity, hold, or preview rules locally; these values come only from backend state.

### Requirement 14: Frontend Hold controls

**User Story:** As a player, I want to trigger Hold by button or key, so that holding is convenient.

#### Acceptance Criteria

1. WHEN the player clicks the Hold button while the game is playing AND Hold is allowed THEN the frontend SHALL send `POST /api/games/{id}/hold`.
2. WHEN the player presses the `C` key or the `c` key while the game is playing AND Hold is allowed THEN the frontend SHALL send `POST /api/games/{id}/hold`.
3. WHEN the existing controls are used (Left, Right, Soft Drop arrows and buttons, Restart) THEN they SHALL continue to function as in Stage 1.

### Requirement 15: Dynamic gravity scheduling on the frontend

**User Story:** As a player, I want the fall speed to match the backend level, so that pacing reflects progress.

#### Acceptance Criteria

1. WHEN the status is `playing` THEN the frontend SHALL schedule automatic ticks using the current `gravity_interval_ms` from backend state rather than a fixed 500 ms constant.
2. WHEN `gravity_interval_ms` changes in backend state THEN the frontend SHALL reschedule its automatic tick to the new interval.
3. WHEN the status is `game_over` THEN the frontend SHALL stop sending automatic ticks.

### Requirement 16: Frontend request ordering and lifecycle safety

**User Story:** As a player, I want the UI to stay consistent even with slow or overlapping requests, so that the board never jumps backward.

#### Acceptance Criteria

1. WHEN overlapping or out-of-order responses arrive THEN the frontend SHALL NOT apply a stale response that would reverse the visible game state.
2. WHEN the current game is replaced by create, restart, or disposal THEN a response belonging to the previous game generation SHALL NOT be applied to the new game, SHALL NOT use the new game's id, and SHALL NOT block the new game's request queue.
3. WHEN manual mutating requests are issued for the same game generation THEN the frontend SHALL serialize them in FIFO order.
4. WHEN a response is received THEN the frontend SHALL validate that it still belongs to the current game generation both after `fetch` resolves AND after `response.json()` resolves, including on the create / restart paths and in error and finally completions.
5. WHEN a stale request from a previous generation completes (including its error or finally handler) THEN it SHALL NOT clear the current generation's scheduling guard or pending timer.
6. WHEN a new game's Hold is triggered while a previous game's Hold response is still pending THEN the new game's Hold SHALL be able to proceed.
7. WHEN automatic ticks are scheduled THEN they SHALL be owned per game generation and coalesced to at most one queued or in-flight tick at a time, so that ticks do not burst after a slow network call.
8. WHEN manual input, restart, an interval change, game over, or component unmount occurs THEN the frontend SHALL cancel the exact pending tick timeout and, where applicable, reschedule using the latest authoritative interval.
9. WHEN the component passes through React StrictMode setup / cleanup / re-setup and through restart THEN the controls and scheduling SHALL remain correct.

The following criteria (16.10 through 16.24) make explicit and testable the three specific production request-ordering / lifecycle guarantees required by the authorized correction. They were discovered by independent production-hook acceptance that drives the real `frontend/src/useGame.ts` and `frontend/src/api.ts` transport boundary with independently deferred `fetch` headers and `response.json()` bodies and fake timers, with no mocking of the hook itself. They strengthen, and do not weaken, criteria 16.1 through 16.9.

**R1 — Restart / stale identity (immediate invalidation of the old game).**

10. WHEN a restart or create begins THEN the frontend SHALL invalidate the previous game identity immediately at the start of the restart or create (before the create request resolves), so that the previous game id is no longer a valid dispatch target while creation is in flight.
11. WHILE a restart or create for game `B` is in flight after game `A` was loaded, IF a mutating action (for example Hold, Left, Right, or Soft Drop) is triggered THEN the frontend SHALL NOT dispatch that action against game `A`'s id under the new generation.
12. WHILE a restart or create for game `B` is in flight, IF a delayed response belonging to game `A` resolves its `fetch` headers THEN the frontend SHALL NOT apply that response and SHALL NOT overwrite the visible state for game `B`.
13. WHILE a restart or create for game `B` is in flight, IF a delayed response belonging to game `A` resolves its `response.json()` body THEN the frontend SHALL NOT apply that body and SHALL NOT overwrite the visible state for game `B`.
14. WHEN a new generation begins at restart or create THEN the frontend SHALL isolate the new generation's request queue from the previous generation's queue, so that a pending previous-generation request SHALL NOT block or clear the new generation's queue, guard, or pending timer.
15. IF a restart or create request fails THEN the frontend SHALL surface the error for the current generation only, SHALL leave no orphaned timer or scheduling guard from the failed attempt, and SHALL NOT apply a failed previous-generation attempt to the current generation.

**R2 — Automatic ticks share serialization with manual work.**

16. WHILE a manual mutating request's `response.json()` body is still pending, IF the gravity timeout expires THEN the frontend SHALL NOT allow the resulting automatic tick to bypass the manual FIFO ordering for that generation.
17. IF a later automatic tick response (for example a snapshot at board row 2) resolves before an earlier manual mutation response (for example a snapshot at board row 1) THEN the frontend SHALL NOT visibly reverse authoritative state by applying the earlier manual snapshot after the later tick snapshot.
18. WHEN a mutation of any kind, including an automatic tick, is processed THEN the frontend SHALL serialize and order it under the same per-generation ownership rules, so that automatic ticks and manual actions share one consistent ordering discipline.
19. WHEN manual input is introduced THEN the frontend SHALL cancel the exact pending automatic-tick timeout at dispatch time (when the manual input is introduced), not after the manual request completes.
20. WHEN a mutation completes for the current generation THEN the frontend SHALL reschedule the next automatic tick using fresh timing from the latest authoritative `gravity_interval_ms`, with no duplicate timers and no stale state updates, across the interval transitions `500` to `450` and down to the `100` floor.

**R3 — Automatic-tick coalescing guard ownership.**

21. WHEN a manual mutating request completes WHILE an automatic tick still owns the coalescing guard THEN the frontend SHALL NOT clear that automatic-tick guard; guard ownership SHALL remain with the queued or in-flight automatic operation that holds it.
22. WHILE a given generation is active THEN the frontend SHALL keep at most one automatic tick queued or in flight, with no catch-up bursts of automatic ticks.
23. WHEN game over, component unmount, or React StrictMode cleanup occurs THEN the frontend SHALL release the automatic-tick guard and cancel the pending timer for that generation, and SHALL remain correct through StrictMode setup / cleanup / re-setup.
24. WHEN a response from a previous generation completes (including its error or finally handler) THEN the frontend SHALL NOT clear the current generation's coalescing guard or pending timer.

The following criteria (16.25 through 16.31) make explicit and testable two additional production request-ordering / lifecycle defects (labeled R4 and R5) reproduced by independent production-hook acceptance that drives the real `frontend/src/useGame.ts` and `frontend/src/api.ts` transport boundary with independently deferred `fetch` headers and `response.json()` bodies and fake timers, with no mocking of the hook (stable hook SHA256 `B75EA8B864F8890B1531B71367EF9410ED138F6A15E5E75B6523A02903667479`). In the shared scenario for both defects, two manual mutating operations are already queued in FIFO order before either completes; the first (predecessor) completes at `t0` with a `gravity_interval_ms` of `500` and schedules a gravity timeout, and the second completes at `t100`. These criteria strengthen, and do not weaken, criteria 16.1 through 16.24 or any R1/R2/R3 guarantee.

**R4 — reconcile the predecessor-created gravity timeout against each fresh authoritative interval.**

25. WHEN a current-generation authoritative manual result is applied THEN the frontend SHALL reconcile the exact pending gravity timeout by cancelling it and rescheduling it against that result's fresh `gravity_interval_ms`, INCLUDING a timeout that was created by a queued predecessor completion, while preserving FIFO ordering and the one-owned-tick coalescing guard.
26. WHILE two manual mutating operations are already queued in FIFO order before either completes, WHEN the predecessor completes at `t0` with `gravity_interval_ms` `500` AND the second manual completion at `t100` returns a fresh `level` `2` state with `gravity_interval_ms` `450` THEN after the second completion the frontend SHALL measure the next automatic tick period as the fresh `450` ms from `t100`, so that advancing `449` ms after the second completion produces zero `POST /api/games/{id}/tick` requests.
27. WHILE the R4 level-up scenario in criterion 16.26 holds, WHEN `450` ms have elapsed after the second completion at `t100` THEN the frontend SHALL dispatch exactly one `POST /api/games/{id}/tick` request (advancing one additional millisecond past `449` ms yields exactly one `/tick`).

**R5 — a terminal manual result cancels the predecessor-created gravity timeout.**

28. WHEN a current-generation authoritative manual result reports a non-playing status (`game_over`) THEN the frontend SHALL cancel the exact pending gravity timeout, INCLUDING a timeout created by a queued predecessor completion, and SHALL NOT schedule a new automatic tick.
29. WHILE two manual mutating operations are already queued in FIFO order before either completes, WHEN the predecessor completes at `t0` with `gravity_interval_ms` `500` AND the second manual completion at `t100` returns status `game_over` THEN advancing `1000` ms after the second completion SHALL produce zero `POST /api/games/{id}/tick` requests.

**R4/R5 — preserved invariants.**

30. WHEN a current-generation manual result reconciles or cancels the pending gravity timeout (criteria 16.25 through 16.29) THEN the frontend SHALL NOT clear a coalescing guard owned by an in-flight or queued automatic tick (preserving 16.21 and 16.24), and a stale previous-generation completion SHALL remain isolated and SHALL NOT touch the current generation's queue, guard, or pending timer (preserving the R1 isolation of 16.10 through 16.15).
31. WHEN the R4/R5 reconciliation is implemented THEN the frontend SHALL cancel the exact pending gravity timeout both at manual dispatch time AND after each current-generation authoritative manual result, each under a generation check, preserving FIFO ordering and one-owned-tick coalescing, without removing or weakening any existing timer expectation or assertion in criteria 16.1 through 16.24.

### Requirement 17: English text and preserved boundaries

**User Story:** As a player, I want consistent English UI and no scope creep, so that the study stays controlled.

#### Acceptance Criteria

1. WHEN the frontend renders any label, status, or message (including the Hold control and the C-key affordance) THEN the visible text SHALL be in English.
2. WHEN Stage 2 is implemented THEN rotation, wall kicks, T-Spins, ghost piece, time attack, achievements, persistence, database, authentication, multiplayer, and high-score storage SHALL NOT be added.
3. WHEN Stage 2 is implemented THEN all game state SHALL remain in memory only.
4. WHEN the frontend HTML document loads THEN the document title SHALL be updated from the inherited Stage 1 title to a Stage 2 title that matches the implemented page, without a broad redesign or any additional gameplay feature.

### Requirement 18: Reproducible build, tests, and quality evidence

**User Story:** As a researcher, I want documented, reproducible verification, so that results are trustworthy.

#### Acceptance Criteria

1. WHEN backend tests are run with the documented command THEN they SHALL execute the Stage 1 regression tests plus new Stage 2 tests and pass.
2. WHEN backend coverage is emitted THEN it SHALL use a documented, compatible dev dependency (a `pytest-cov` pin added in `backend/requirements-dev.txt`, installed before use) rather than assuming a `--cov` flag is available in the baseline runtime pins, and SHALL produce `docs/coverage.xml`; the original runtime pins in `backend/requirements.txt` SHALL be preserved unless an explicit compatible remediation is justified.
3. WHEN the frontend production build is run with the documented command THEN it SHALL type-check and bundle without errors.
4. WHEN frontend tests are run with the documented command THEN they SHALL exercise production frontend paths and emit a full production-src LCOV report at `frontend/coverage/lcov.info` that includes all production files under `frontend/src`, with no coverage exclusions of production files.
5. WHEN `npm audit` is run THEN the result SHALL be recorded honestly, including exact exit status, with the known baseline of 3 vulnerabilities (1 moderate, 2 high) and any applied compatible remediation, with no suppression.
6. WHEN the controlled quality gate is evaluated THEN new code coverage SHALL be at least 80%, new duplication at most 3%, and new violations zero, with no threshold weakening, no unjustified finding suppression, no exclusion of uncovered production files, no weakening of tests, no alteration of legacy regression assertions, and no claim of a passing gate without actual verification.
7. WHEN security is assessed THEN the full-tree `npm audit --json` (NOT `--omit=dev`) SHALL be the authoritative result, because the baseline full-tree audit reports 7 findings (3 moderate, 2 high, 2 critical) and `npm audit --omit=dev` reporting `0` SHALL NOT be treated as proof that the Vite build / dev-server toolchain is safe, given that Vite is a `devDependency`.
8. WHEN security remediation is performed THEN it MAY upgrade Vite, Vitest, and the Vite React plugin to mutually compatible, patched, explicitly pinned versions appropriate for the installed Node 25.6.1 environment, since there is no authorized hard restriction to preserve Vite 5, while preserving React 18 and TypeScript behavior unless a documented compatible upgrade is required.
9. WHEN security remediation is completed THEN the system SHALL produce, with the documented commands, an actual clean dependency install, a successful production build, the full generated frontend tests with coverage, and a full-tree `npm audit --json`, targeting `0` full-tree findings.
10. WHEN recording the audit result THEN the system SHALL NOT suppress advisories, SHALL NOT remove required test tooling, SHALL NOT use fake or nonexistent versions, SHALL NOT exclude packages from the audit scope, and SHALL NOT rely on an unpatched override to hide a finding.
11. IF a real vulnerability blocker remains after reasonable compatible remediation THEN the system SHALL retain the exact audit evidence and SHALL state the remaining blocker precisely, including its severity and the reason remediation is blocked.
12. WHEN the frontend coverage configuration is defined THEN it SHALL NOT exclude `frontend/src/main.tsx` from coverage, because `main.tsx` is an executable production bootstrap rather than test glue.
13. WHEN the LCOV report is emitted THEN it SHALL include all executable production source under `frontend/src`, including `frontend/src/main.tsx`, and a meaningful bootstrap / mount test SHALL be provided when needed to cover the bootstrap rather than hiding uncovered lines.
14. WHERE a file is a test, a test setup module, or a declaration-only environment type (for example `frontend/src/vite-env.d.ts`) THEN it MAY be classified as non-production and excluded from the production coverage denominator.
15. WHEN coverage scope is reported THEN any README or result statement that previously overstated coverage scope SHALL be corrected, and the final coverage denominator and scope SHALL be reported explicitly.
16. WHEN Stage 2 frontend tests are authored THEN the generated test suite under `frontend/src` SHALL include meaningful tests for the R1, R2, and R3 production paths (Requirements 16.10 through 16.24) that drive the real `useGame` hook and `api` transport boundary with independently deferred `fetch` headers and `response.json()` bodies and fake timers, without mocking the hook, and the researcher harness, its config, its report files, and shared helpers SHALL remain unchanged.
17. WHEN Stage 2 frontend tests are authored THEN the generated test suite under `frontend/src` SHALL include meaningful tests for the R4 and R5 production paths (Requirements 16.25 through 16.31) that drive the real `useGame` hook and `api` transport boundary with independently deferred `fetch` headers and `response.json()` bodies and fake timers, without mocking the hook, covering BOTH already-queued manual cases: the R4 level-up case asserting that advancing `449` ms after the second completion at `t100` produces zero `/tick` requests and advancing one additional millisecond produces exactly one `/tick` request, and the R5 game-over case asserting that advancing `1000` ms after the terminal second completion produces zero `/tick` requests. WHEN these tests are added THEN existing frontend and backend test instances and their assertions SHALL be preserved (parametrization MAY change instance counts only with documented equivalent coverage), every executable frontend production module including `frontend/src/main.tsx` SHALL remain in the LCOV report with no production exclusions, and the researcher harnesses, fixtures, reports, their config, and shared helpers SHALL remain unchanged.

## Material Ambiguities and Assumptions

These are recorded for transparency. The items previously flagged as open are now resolved by the frozen seed and this tool's own baseline, as noted.

1. **Hold-swap spawn-collision outcome (RESOLVED by seed).** An incoming held or swapped-in piece that is blocked at the canonical spawn origin ends the game (`game_over`, active cleared), consistent with the seed-frozen Stage 1 spawn-collision handling (Requirement 8.3). No confirmation remains outstanding.
2. **`next_piece` after game over (RESOLVED by seed).** `next_piece` remains a valid queued type after `game_over`; it is not nulled and no further draw occurs (Requirement 6.7). No confirmation remains outstanding.
3. **Scoring rule naming.** The 100/300/500/800 values follow the classic single/double/triple/tetris table; the spec fixes the exact integers, so no external table is assumed as an input.
4. **Level boundary interpretation.** Requirements 3.6 and 4.6 fix the interpretation: the pre-lock level scores the clear and gravity updates after the level change. The primary boundary this stage makes explicit is TOTAL LINES 9 -> 10 (level 1 -> 2, gravity 500 -> 450). The level-9-to-10 crossing is exercised separately at TOTAL LINES 89 -> 90 (pre-lock level 9, award 900, gravity -> 100).
5. **Backend coverage tooling (RESOLVED).** The baseline `backend/requirements.txt` does not include `pytest-cov`, so the `--cov` flag is unavailable by default. Coverage uses a documented, compatible dev dependency installed before use (Requirement 18.2); runtime pins are preserved.
6. **Frontend test framework (RESOLVED).** Stage 1 has no frontend test framework. Vitest + Testing Library with `@vitest/coverage-v8` is specified in design and installed only in the implementation phase; it is not added in the specification-only phase.
7. **Frontend security remediation and Vite pinning (RESOLVED).** There is no authorized hard restriction to preserve Vite 5. The authoritative security signal is the full-tree `npm audit --json` (7 findings: 3 moderate, 2 high, 2 critical), not `npm audit --omit=dev`, because Vite is a `devDependency`. Remediation may upgrade Vite / Vitest / the Vite React plugin to mutually compatible, patched, explicitly pinned versions for the installed Node 25.6.1 environment, preserving React 18 and TypeScript behavior, and targets `0` full-tree findings with honest evidence (Requirement 18.7 through 18.11).
8. **Frontend coverage denominator (RESOLVED).** `frontend/src/main.tsx` is an executable production bootstrap and SHALL remain in the coverage denominator; only tests, test setup, and declaration-only environment types (for example `frontend/src/vite-env.d.ts`) are classified as non-production (Requirement 18.12 through 18.15).
9. **Production request-ordering races (RESOLVED by correction).** The R1 (stale identity on restart), R2 (automatic tick bypassing the manual FIFO and reversing state), and R3 (manual completion clearing an automatic tick's coalescing guard) races observed against the production `useGame` hash `67F340FC713072C81F3A744292D708FA3C290F01EE489D6E3D22EF774184269B` are required correctness fixes captured in Requirement 16.10 through 16.24; they strengthen Requirement 16 without weakening any earlier criterion.
10. **Queued-predecessor gravity-timeout reconciliation (RESOLVED by correction).** Two additional races, R4 and R5, were reproduced against the production `useGame` hash `B75EA8B864F8890B1531B71367EF9410ED138F6A15E5E75B6523A02903667479` in the shared scenario where two manual mutating operations are already queued in FIFO order, the predecessor completes at `t0` with `gravity_interval_ms` `500`, and the second completes at `t100`. In R4, the second completion returns a fresh `level` `2` / `gravity_interval_ms` `450` state but the scheduler leaves the predecessor's `t500` deadline alive instead of reconciling it against the fresh `450` ms interval, so a tick fires `49` ms early; the fix requires every current-generation authoritative manual result to cancel and reschedule the exact pending gravity timeout against its fresh interval (normative boundary: `449` ms after `t100` yields zero `/tick`, the full `450` ms yields exactly one `/tick`). In R5, the second completion returns `game_over` and correctly skips scheduling but fails to cancel the predecessor's timeout, so one `/tick` fires after terminal state; the fix requires a terminal current-generation manual result to also cancel the exact pending gravity timeout (normative boundary: advancing `1000` ms after the `game_over` completion yields zero `/tick`). Both corrections are captured in Requirement 16.25 through 16.31 and verified by Requirement 18.17; they strengthen Requirement 16 and preserve R1 isolation, FIFO ordering, the one-owned-tick coalescing guard (R3), and every earlier criterion without weakening any of them.

