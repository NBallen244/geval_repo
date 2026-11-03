# REST API Contract Specification: build-tetris-core

This document details the interface contracts exposed by the Python FastAPI backend to the React client.

## Endpoint Overview

All endpoints consume and return `application/json`. Game session states are managed in-memory on the server and mapped to a unique UUID.

| Method | Endpoint | Request Body | Response Body | Description |
|--------|----------|--------------|---------------|-------------|
| `POST` | `/api/games` | *None* | `GameSession` | Creates a new game session with an empty board and initial random piece. |
| `GET` | `/api/games/{id}` | *None* | `GameSession` | Retrieves the current state of an existing game session. |
| `POST` | `/api/games/{id}/tick` | *None* | `GameSession` | Advances the game by one gravity tick (shifts piece down or locks/spawns next). |
| `POST` | `/api/games/{id}/move` | `MoveRequest` | `GameSession` | Executes manual movements: left, right, or down (soft drop). |

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
      "type": "O",
      "cells": [[0,4], [0,5], [1,4], [1,5]],
      "origin": [0,4]
    },
    "status": "playing"
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
Advances the active piece downward by one cell, checking for contact, locking, and line clears.

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
  *Allowed Directions*: `"left"`, `"right"`, `"down"`.
- **Success Response (200 OK)**: Returns the updated `GameSession` JSON.
- **Error Response (422 Unprocessable Entity)**: Returned if request body fails schema validation.
