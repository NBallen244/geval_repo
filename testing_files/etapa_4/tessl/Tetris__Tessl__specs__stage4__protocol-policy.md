# M3 Real-Time WebSocket Duel Protocol Policy

This document defines the authoritative compact protocol and operational policy for the two-player real-time duel mode. All implementations, tests, and configurations must strictly adhere to these rules.

## 1. Action/Revision Lifecycle & Highwater Policy

The server maintains a monotonic highwater action ID `highwater_action_id` per seat (initialized to `0`).

### 1.1 Action ID Monotonicity
- **New Actions (`action_id > highwater_action_id`):** Every new client action with an ID strictly greater than the current highwater ID consumes that ID (i.e., `highwater_action_id` is updated to `action_id`). This occurs regardless of whether the action is accepted, no-op, or rejected.
  - **Every NEW valid action gets an ACK.** Only actions that are new (exceed the highwater ID) and schema-valid are processed and acknowledged.
- **Duplicate Actions (`action_id <= highwater_action_id`):** Any action message with an ID less than or equal to the highwater ID is recognized as a duplicate/old message and is **completely ignored**. The server does not re-apply the action, does not perform side effects, and **does not send any ACK or broadcast reply**, even if the payload differs from the originally processed action.

### 1.2 Handshake & Start Gating Actions
- **Before-Start Actions:** If a client sends an action before both players have joined and the game status has transitioned to `"playing"`, the action is rejected:
  - `highwater_action_id` is updated to `action_id` (consuming the ID).
  - The server returns a `server_ack` with:
    - `status`: `"rejected"`
    - `reason`: `"not_started"`
    - `authoritative_board`: Current own board state (nonterminal, awaiting start).
- **Start Notification:** Both players receive a `"playing"` start notification (`server_state_update` with status `"playing"`) automatically upon the second player's successful join. No client input is required to trigger the start.

### 1.3 Revision Matching Rules
For any new, schema-valid action (`action_id > highwater_action_id`) received when game status is `"playing"`:
- **Stale or Future Revision (`expected_revision != current_board_revision`):**
  - `highwater_action_id` is updated to `action_id`.
  - The action is rejected without mutation.
  - The server returns a `server_ack` with:
    - `status`: `"rejected"`
    - `reason`: `"stale revision"` (if `expected_revision < current_board_revision`) or `"future revision"` (if `expected_revision > current_board_revision`).
    - `authoritative_board`: Current board state.
- **Matched Revision & Legal Block (`expected_revision == current_board_revision`):**
  - If the action is a legal movement or rotation that is blocked by board boundaries or locked cells (or if it is an `'O'` piece rotation, which is a strict no-op):
    - `highwater_action_id` is updated to `action_id`.
    - No state mutation or revision advancement occurs.
    - The server returns a `server_ack` with:
      - `status`: `"noop"`
      - `reason`: `"blocked"` or `"no-op rotation"`
      - `authoritative_board`: Current board state (unchanged).
  - If the action is legal and successful:
    - `highwater_action_id` is updated to `action_id`.
    - State is mutated, `board_revision` increments by 1, and the room-wide `room_revision` increments.
    - The server returns a `server_ack` with:
      - `status`: `"accepted"`
      - `reason`: `"success"`
      - `authoritative_board`: Newly updated board state.
      - A room-wide `server_state_update` broadcast is scheduled.

### 1.4 Invalid Messages & Connection Binding
- **Schema Violations:** Messages that fail JSON schema validation do not produce any ACK. Instead, they trigger a canonical WebSocket error or close.
- **Seat to Socket Binding:** Each player seat (`player1` and `player2`) is strictly bound to its verified, active WebSocket connection. A socket cannot submit actions for the opponent's seat.

### 1.5 Outcome Delivery
- **Single Outcome Transition:** The state transition to `"finished"` and its corresponding broadcast occur exactly once.
- **Explicit Readback Policy:** Subsequent connection retries, late messages, or readback queries on a retained room return the final cached room snapshot. No second outcome transition is ever executed, and finished rooms cannot be resurrected.

---

## 2. Shared Deterministic Tetromino Sequence

To guarantee perfect fairness without precomputed limits or heavy memory caching, both player engines consume tetrominoes from an infinite deterministic shared sequence.

### 2.1 Seeded Hash Algorithm
- The room is initialized with a shared seed integer `seed` (nonnegative).
- The tetromino type at a given sequence index `idx` is computed using a deterministic O(1) mathematical function:
  - The input message is the UTF-8 encoded string representation of the nonnegative decimal seed, followed by an underscore `_`, followed by the nonnegative decimal index (with no padding), i.e., `str(seed) + "_" + str(idx)`.
  - The SHA-256 digest of this UTF-8 string is interpreted as a big-endian unsigned integer.
  - The tetromino type is resolved by taking this big-endian integer modulo 7, indexing into the exact piece order: `["I", "O", "T", "S", "Z", "J", "L"]`.
  - Mathematically, let $val$ be the big-endian integer of the 32-byte digest, then the piece is $\text{PIECES}[val \pmod 7]$.
- **Independent Consumption:** Each board maintains its own separate sequence index pointer. Boards consume pieces independently as they spawn or use Hold, ensuring no finite precomputed array constraints.
- **Server Authority:** While clients may display upcoming previews based on the shared seed, they have no authority over the sequence. The server alone evaluates all board states, advances piece index pointers, and decides the spawning tetrominoes.

---

## 3. Operational Limits & WebSocket Policy

### 3.1 Room & Resource Limits
- **Maximum Active/Retained Rooms:** Exactly `100`.
  - Creation of any room beyond 100 is capped and rejected.
  - Joining an existing available room is permitted even if the active room count is at the cap.
- **Monotonic Revision Exhaustion:** If the room revision or any board revision reaches `9007199254740991` (scalar overflow boundary), the room is aborted operationally with `"operational-abort"` reason and winner `"draw"`.

### 3.2 Timeouts & Deadlines
- **Handshake Hello Deadline:** Exactly `10` seconds. The first valid handshake message (`client_handshake`) must be received within 10 seconds of establishing the socket connection. Failure to do so results in connection termination. This is not a deadline for the second player to arrive.
- **Waiting Peer Timeout:** Exactly `120` seconds. If a room remains in `"waiting"` status with only one player for more than 120 seconds, the room is aborted with outcome reason `"waiting-peer-timeout"` and winner seat null.
- **Playing Idle Timeout:** Exactly `120` seconds. If no action is received from either player in `"playing"` status for more than 120 seconds, the room is aborted.
- **Finished Room Retention:** Exactly `300` seconds of inactivity taking precedence. Once a game finishes, the final state is preserved for exactly 300 seconds of inactivity before deletion.
- **Active Sweeper Task:** A background sweeper executes once every `60` seconds (with a maximum sweep slack of `60` seconds) to purge inactive or retained finished rooms, closing open sockets and cancelling background gravity tasks.

### 3.3 Network Bandwidth & Queueing
- **Inbound Message Rate Limit:** At most `50` messages per fixed monotonic `1.0` second window per socket, including duplicates. Excess messages immediately close the socket with code `1008` (Policy Violation).
- **Maximum Inbound Message Size:** Exactly `4096` bytes. Any message exceeding this limit immediately closes the socket with code `1009` (Message Too Big).
- **Outbound Broadcast Queue Limit:** Exactly `100` messages.
- **Outbound Write Timeout:** Exactly `200` milliseconds. Outbound socket transmissions are performed asynchronously outside of state locks, and must complete within 200ms. If a socket's send buffer overflows or a write times out, it is cancelled with a specific numeric grace of `50` milliseconds, and the connection is closed.

### 3.4 Disconnects & Forfeits
- **Disconnect in PLAYING:** If a connection drops, a queue overflows, or a write fails for a player during `playing` status, that player is declared to have forfeited, and the survivor is immediately awarded a forfeit win.
- **Abort in WAITING:** If a connection drops, queue full, send failure, or server shutdown occurs during `"waiting"`, the room is aborted with no winner declared (winner seat null) and outcome reason `"waiting-aborted"` (player1 board playing, player2 null).
- **Survivor Completion:** The surviving player is notified immediately of the forfeit, receives the final `"finished"` state update, and the socket is closed gracefully with code `1000` (Normal Closure) once the final state is drained.

### 3.5 WebSocket Implementation and Dependencies
- **Production WebSocket Engine Pin:** The backend production deployment explicitly targets the concrete library dependency `websockets==14.1` (compatible with Python >= 3.12). This represents the chosen strict runtime version pin. No installation is performed now to preserve existing workspace lock states.

---

## 4. Error and Close Code Mapping

The following exact numeric close codes are used at the transport layer:
- **`1000` (Normal Closure):** Normal game completion, clean shutdown, or graceful survivor closeout.
- **`1003` (Unsupported Data):** Binary messages ONLY.
- **`1007` (Invalid Frame Payload Data):** Invalid text (bad UTF-8) framing received before ASGI dispatch (no guaranteed JSON reply).
- **`1008` (Policy Violation):** Message rate limit exceeded, seat guard violation, or invalid handshake after connecting.
- **`1009` (Message Too Big):** Inbound message exceeds exactly `4096` bytes.

If a client sends valid JSON that fails schema validation, the server does not produce a fake ACK, but instead sends a JSON-formatted server error message and closes the socket with code `1008` (Policy Violation).

---

## 5. Serialization and Concurrency

- **Room Locking:** Every state mutation inside a room is serialized under an independent `asyncio.Lock` per room.
- **Asynchronous I/O Outside Locks:** To maximize throughput and prevent slow socket writers from blocking the room's gravity loops or the other player's actions, snapshots of board states are written under a short lock, but the actual broadcast writes are executed strictly **outside** of the room lock.
- **Independent Gravity Evaluation:** Server-side gravity updates evaluate all due boards in a single tick cycle before checking outcomes, ensuring simultaneous topouts are cleanly captured as draws.
