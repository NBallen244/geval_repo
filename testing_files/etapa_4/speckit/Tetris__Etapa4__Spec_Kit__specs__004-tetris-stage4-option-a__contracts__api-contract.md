# REST API Contract (Solo Play - Extended)

This document specifies the REST HTTP endpoints for single-player Tetris, incorporating 90-degree clockwise and counterclockwise rotation commands under the existing move endpoint.

---

## 1. Game Creation

Creates an active, authoritative in-memory single-player game session.

- **Method**: `POST`
- **Path**: `/api/games`
- **Headers**:
  - `Content-Type: application/json`
- **Body Requirement**: 
  - Supports bodyless requests or an empty JSON object `{}`. 
  - Under the `CreateGameRequest` schema, any extra parameters inside the request body are strictly rejected with `422 Unprocessable Entity` (`extra="forbid"` rule).
- **Success Response (201 Created)**:
  ```json
  {
    "id": "e0bfa531-15c2-4822-8356-07718e873b2c",
    "board": [
      [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      ...
      [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ],
    "activePiece": {
      "type": "T",
      "cells": [[0, 4], [1, 3], [1, 4], [1, 5]],
      "origin": [1, 4]
    },
    "status": "playing",
    "score": 0,
    "total_lines": 0,
    "level": 1,
    "gravity_interval_ms": 500,
    "next_piece": "I",
    "hold_piece": null,
    "can_hold": true
  }
  ```

---

## 2. Retrieve Game State

Retrieves a non-mutating deep copy of the active session snapshot. This endpoint is strictly read-only; it must never perform database insertions, finalizations, or retries.

- **Method**: `GET`
- **Path**: `/api/games/{id}`
- **Success Response (200 OK)**:
  - Returns the JSON payload matching the `GameSessionSchema` structure shown in the Game Creation response.
- **Error Responses**:
  - `404 Not Found`: Returned when the session ID does not exist in the active memory store.
    ```json
    {
      "detail": "Game session e0bfa531-15c2-4822-8356-07718e873b2c not found"
    }
    ```

---

## 3. Execute Movement & Rotation

Controls the active tetromino's position or orientation.

- **Method**: `POST`
- **Path**: `/api/games/{id}/move`
- **Headers**:
  - `Content-Type: application/json`
- **Request Body (MoveRequest)**:
  - Supports strict schema validation with zero extra keys allowed.
  - Allowed values for `direction` are: `"left"`, `"right"`, `"down"`, `"cw"` (clockwise), `"ccw"` (counterclockwise).
  - Schema:
    ```json
    {
      "direction": "cw"
    }
    ```
- **Success Response (200 OK)**:
  - Returns the fully updated `GameSessionSchema` representing the state after the movement or rotation check.
- **Error Responses**:
  - `422 Unprocessable Entity`: Returned on schema validation failures (e.g., sending an invalid direction string like `"up"`, `"diagonal"`, or any other unrecognized value, or sending extra fields).
    ```json
    {
      "detail": [
        {
          "loc": ["body", "direction"],
          "msg": "value is not a valid enumeration member; permitted: 'left', 'right', 'down', 'cw', 'ccw'",
          "type": "type_error.enum"
        }
      ]
    }
    ```
  - `404 Not Found`: Session ID does not exist in memory.

---

## 4. Trigger Hold Slot

Swaps the active piece with the slot container.

- **Method**: `POST`
- **Path**: `/api/games/{id}/hold`
- **Success Response (200 OK)**:
  - Returns the updated `GameSessionSchema`.
- **Error Responses**:
  - `404 Not Found`

---

## 5. Fetch High Scores Leaderboard

Retrieves the persistent high score ranking table from the local SQLite database.

- **Method**: `GET`
- **Path**: `/api/high-scores`
- **Success Response (200 OK)**:
  - Returns a JSON payload containing up to 10 entries ordered by `score` descending, then `completed_at` ascending, then `game_id` lexicographically ascending.
  - Schema:
    ```json
    {
      "scores": [
        {
          "game_id": "e0bfa531-15c2-4822-8356-07718e873b2c",
          "score": 1200,
          "total_lines": 12,
          "level": 2,
          "completed_at": "2026-11-03T18:45:00Z"
        },
        ...
      ]
    }
    ```
- **Error Responses**:
  - `503 Service Unavailable`: Database storage failures or query issues. Hides database files and server paths.
    ```json
    {
      "detail": "Leaderboard database is temporarily unavailable"
    }
    ```
