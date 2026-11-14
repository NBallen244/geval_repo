# REST API Contract Specification: Extend Tetris to Stage 2

This document defines the REST API contract details exposed by the Python FastAPI backend to the React/TypeScript frontend client for the Stage 2 Tetris features.

---

## Endpoint Overview

All endpoints consume and return `application/json`. Game session states are managed server-side and mapped to a unique UUID.

| Method | Endpoint | Request Body | Response Body | Description |
|--------|----------|--------------|---------------|-------------|
| `POST` | `/api/games` | *None* | `GameSession` | Creates or restarts a game session, initializing all Stage 2 variables to default. |
| `GET` | `/api/games/{id}` | *None* | `GameSession` | Retrieves the current authoritative game state of a session. |
| `POST` | `/api/games/{id}/tick` | *None* | `GameSession` | Advances gravity down by 1 row, checking for locking, line clearing, scoring, leveling, and piece respawn. |
| `POST` | `/api/games/{id}/move` | `MoveRequest` | `GameSession` | Performs a manual left, right, or down shift. |
| `POST` | `/api/games/{id}/hold` | *None* | `GameSession` | Performs a piece swap with the Hold slot (or stores the active piece). |

---

## Detailed Endpoint Definitions

### 1. Create/Restart Game Session
Initializes or resets a game session.

- **URL**: `/api/games`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Success Response (201 Created)**:
  ```json
  {
    "id": "c1f7b764-9844-48f8-b3d2-c2cb72836245",
    "board": [
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0]
    ],
    "activePiece": {
      "type": "I",
      "cells": [[0,3], [0,4], [0,5], [0,6]],
      "origin": [0,4]
    },
    "status": "playing",
    "score": 0,
    "total_lines": 0,
    "level": 1,
    "gravity_interval_ms": 500,
    "next_piece": "O",
    "hold_piece": null,
    "can_hold": true
  }
  ```

---

### 2. Retrieve Game State
Fetches the current authoritative state of a game.

- **URL**: `/api/games/{id}`
- **Method**: `GET`
- **URL Path Parameters**: `id` (UUID string)
- **Success Response (200 OK)**: Returns the current `GameSession` JSON representation.
- **Error Response (404 Not Found)**:
  ```json
  {
    "detail": "Game session c1f7b764-9844-48f8-b3d2-c2cb72836245 not found"
  }
  ```

---

### 3. Gravity Tick
Advances the active piece downward by one cell, checking for contact, locking, line clears, leveling, and piece spawning.

- **URL**: `/api/games/{id}/tick`
- **Method**: `POST`
- **URL Path Parameters**: `id` (UUID string)
- **Success Response (200 OK)**: Returns the updated `GameSession` JSON.
- **Error Response (404 Not Found)**: Returned if session ID is invalid.

---

### 4. Manual Move Command
Executes horizontal shifting (left/right) or gravity speedup (soft drop down).

- **URL**: `/api/games/{id}/move`
- **Method**: `POST`
- **URL Path Parameters**: `id` (UUID string)
- **Request Body (application/json)**:
  ```json
  {
    "direction": "left"
  }
  ```
- **Success Response (200 OK)**: Returns the updated `GameSession` JSON.
- **Error Response (422 Unprocessable Entity)**:
  ```json
  {
    "detail": [
      {
        "loc": ["body", "direction"],
        "msg": "Input should be 'left', 'right' or 'down'",
        "type": "value_error"
      }
    ]
  }
  ```

---

### 5. Piece Hold Command
Swaps the active piece with the piece in the hold slot, spawning a new piece in its place.

- **URL**: `/api/games/{id}/hold`
- **Method**: `POST`
- **URL Path Parameters**: `id` (UUID string)
- **Success Response (200 OK)**: Returns the updated `GameSession` JSON.
  - *Example response showing active piece stored in Hold slot for the first time*:
    ```json
    {
      "id": "c1f7b764-9844-48f8-b3d2-c2cb72836245",
      "board": [ ... ],
      "activePiece": {
        "type": "O",
        "cells": [[0,4], [0,5], [1,4], [1,5]],
        "origin": [0,4]
      },
      "status": "playing",
      "score": 0,
      "total_lines": 0,
      "level": 1,
      "gravity_interval_ms": 500,
      "next_piece": "T",
      "hold_piece": "I",
      "can_hold": false
    }
    ```
- **Error Response (404 Not Found)**: Returned if session ID is invalid.
