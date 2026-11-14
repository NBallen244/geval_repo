# WebSocket API Contract (Duel Mode)

This document specifies the bidirectional real-time communication protocol for Two-Player Duel over WebSockets.

---

## 1. Connection and Upgrade Handshake

### 1.1 Connection URL
- **Endpoint**: `ws://<domain>/api/duel/ws` (and proxies correctly on production under same-origin paths).

### 1.2 Handshake Origin Validation
To prevent Cross-Site WebSocket Hijacking (CSWSH), the server MUST authoritatively validate the client's upgrade request.
- The `Origin` header sent by the browser is checked against a list of authorized domains.
- If the upgrade request fails validation, the server immediately responds with `403 Forbidden` and terminates the handshake, before establishing any WebSocket worker or resource state.

### 1.3 Room Assignment Gating
- Clients join a duel by providing an optional room query parameter: `ws://<domain>/api/duel/ws?room_id=<room_uuid>`.
- If no `room_id` is supplied, the server authoritatively generates a fresh room UUID.
- If a `room_id` is supplied but the room is full (already contains 2 players) or is in a finished state, the server MUST NOT silently allocate a new random room. Instead, it MUST fail deterministically, closing the WebSocket connection with custom close code `4001 Room Full` or `4004 Room Invalid/Finished`.
- Playloads must remain completely free of any client-provided player identity. Player identifiers are assigned authoritatively by the server.

---

## 2. Message Envelope & Schema Versioning

All messages sent over the WebSocket link must be encoded as JSON strings and conform to the versioned envelopes specified below. Payloads are strictly bounded; individual incoming message payloads exceeding **1 KB** will be discarded and lead to connection close.

### 2.1 General Envelope Format
All JSON messages contain a top-level schema version parameter `"v": 1` and an event category:
```json
{
  "v": 1,
  "event": "EVENT_NAME",
  "payload": {}
}
```

---

## 3. Client-to-Server Message Schemas

Clients send movement, rotation, hold, or join requests. The server verifies the caller's session seat token, ensuring players can never control the other seat or forge game state metrics.

### 3.1 Player Action Command (`action`)
- **Event Name**: `action`
- **Payload Schema**:
  - `seq_num` (integer, monotonic, strictly increasing sequence number in bounded safe-integer range `[1, 9007199254740991]`)
  - `generation` (integer, echoing the last received `active_piece_generation` value for this player's seat)
  - `action_type` (string: `"left"`, `"right"`, `"down"`, `"cw"`, `"ccw"`, `"hold"`)
- **Example Payload**:
  ```json
  {
    "v": 1,
    "event": "action",
    "payload": {
      "seq_num": 104,
      "generation": 3,
      "action_type": "cw"
    }
  }
  ```

### 3.2 Stale Action Semantics & Deduplication
To enforce strict latency correctness and prevent double-execution, the server applies the following rules:
1. **Deduplication / Order Check**: If the incoming `seq_num` is less than or equal to the seat's stored `last_processed_seq_num`, the action is discarded as duplicate or out-of-order without applying any state mutations.
2. **Generation/Stale Check**: The incoming action `generation` must match the server's current `active_piece_generation` for that seat. If they do not match, the action is discarded as stale (e.g., if a gravity tick or Hold swap has already replaced or advanced the active piece, the action was meant for a previous piece generation and must be rejected).
3. **Rejection Outcome**: Rejected actions trigger an `error` frame with code `409 Conflict/Stale Action`, returning the current authoritative snapshot without applying any board changes.

---

## 4. Server-to-Client Message Schemas

The server broadcasts state snapshots and outcome messages to both clients concurrently.

### 4.1 Room Join Confirmation (`joined`)
Emitted immediately to the connecting player upon successful handshake and seat assignment.
- **Event Name**: `joined`
- **Payload Schema**:
  - `room_id` (string, UUID)
  - `assigned_seat` (string: `"seat_1"` or `"seat_2"`)
- **Example Payload**:
  ```json
  {
    "v": 1,
    "event": "joined",
    "payload": {
      "room_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "assigned_seat": "seat_1"
    }
  }
  ```

### 4.2 Real-Time Duel State Broadcast (`state_update`)
Broadcasted to both players upon connection state updates, action processing, and server-side gravity loops.
- **Event Name**: `state_update`
- **Payload Schema**:
  - `revision` (integer, monotonic increasing state revision sequence)
  - `status` (string: `"waiting"`, `"active"`, `"finished"`)
  - `last_action_seat` (string or null, identifies which seat performed the action that caused this state update)
  - `last_action_seq` (integer or null, identifies the action seq_num that caused this update)
  - `last_action_observable_change` (boolean, true if the action altered the board/piece state, false if it was a valid but unmutated move such as hitting a wall)
  - `seat_1` (object, matching player board state or null if vacant)
  - `seat_2` (object, matching player board state or null if vacant)
- **Seat State Format**:
  - Contains standard properties from `PlayerState`, specifically including `active_piece_generation` and `last_processed_seq_num`.
- **State Update Example**:
  ```json
  {
    "v": 1,
    "event": "state_update",
    "payload": {
      "revision": 420,
      "status": "active",
      "last_action_seat": "seat_1",
      "last_action_seq": 104,
      "last_action_observable_change": true,
      "seat_1": {
        "player_id": "78fa1b43-3456-42d4-a82f-bf6544a0e987",
        "board": [
          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
          ...
          [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        ],
        "active_piece": {
          "type": "T",
          "cells": [[10, 4], [11, 3], [11, 4], [11, 5]],
          "origin": [11, 4]
        },
        "active_piece_generation": 3,
        "last_processed_seq_num": 104,
        "score": 450,
        "total_lines": 4,
        "level": 1,
        "status": "playing"
      },
      "seat_2": {
        "player_id": "98124b89-23ef-4f1b-a5d6-0982348efca2",
        "board": [
          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
          ...
          [0, 0, 0, 0, 0, 0, 0, 0, 2, 2]
        ],
        "active_piece": {
          "type": "I",
          "cells": [[8, 3], [8, 4], [8, 5], [8, 6]],
          "origin": [8, 4]
        },
        "active_piece_generation": 1,
        "last_processed_seq_num": 12,
        "score": 100,
        "total_lines": 1,
        "level": 1,
        "status": "playing"
      }
    }
  }
  ```

### 4.3 Match Conclusion & Duel Result (`game_over`)
Broadcasted immediately when the duel finishes. This is the **one-and-only terminal outcome message** emitted for the room session.
- **Event Name**: `game_over`
- **Payload Schema**:
  - `outcome` (string: `"seat_1_win"`, `"seat_2_win"`, `"draw"`)
  - `reason` (string, explaining the top-out or forfeit/disconnect)
- **Example Payload**:
  ```json
  {
    "v": 1,
    "event": "game_over",
    "payload": {
      "outcome": "seat_1_win",
      "reason": "seat_2 topped out under gravity"
    }
  }
  ```

---

## 5. Control and Error Frames

### 5.1 Invalid Payload Error (`error`)
Emitted to a client when sending malformed JSON, out-of-order sequence numbers, or cross-seat actions.
- **Event Name**: `error`
- **Example Payload**:
  ```json
  {
    "v": 1,
    "event": "error",
    "payload": {
      "code": 401,
      "message": "Unauthorized: Cannot control opponent's seat"
    }
  }
  ```

### 5.2 Close Connection Codes
The server employs standard RFC 6455 close codes and custom room-specific close codes when closing connections:
- `1000 Normal Closure`: Used when the room finishes naturally or players exit.
- `4000 Bad Request / Handshake Failure`: Handshake parameter checks fail, or an oversized incoming payload (exceeding the 1 KB boundary) triggers a policy close. Note that missing or foreign Origin headers fail the handshake with HTTP 403 Forbidden before the WebSocket upgrade occurs, rather than a socket close code.
- `4001 Room Full`: Client connected to a room that already holds two active players.
- `4004 Room Invalid/Finished`: Client attempted to connect with a room ID that is unknown or already concluded.
- `4008 Idle Timeout`: Connection terminated after 5 minutes of inactivity.
