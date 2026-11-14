# REST API Contract Specification: Tetris Stage 3 Persistent High Scores

This document defines the REST API contracts exposed by the Python FastAPI backend to the React/TypeScript frontend client for the Stage 3 Tetris features, ensuring strict compatibility with Stage 2 endpoints while defining the high scores, strict validation, and error-handling requirements.

---

## 1. Request Body Safety and Global Constraints

- **Extra Key Validation**: Every POST endpoint with a defined JSON body MUST validate that no unexpected/extraneous parameters are submitted. Any request violating this rule MUST be rejected with a documented `4xx` error (such as `422 Unprocessable Entity` or `400 Bad Request`).
- **Bodyless POST Compatibility**: Endpoint `POST /api/games` (game creation/restart) accepts optional empty requests (`{}` or bodyless) but rejects any payload containing parameters (e.g. attempting to submit forged metadata).
- **Read-Only GET Operations**: Under no circumstances shall a `GET` endpoint mutate game sessions, create database rows, or trigger database write retries.
- **Sanitized Errors**: Database locks, disk failures, or write timeout exceptions must NOT propagate raw traces to the client. They must return a controlled JSON error payload with HTTP Status `503 Service Unavailable`.

---

## 2. API Endpoints Reference

### 2.1. GET /api/high-scores
Retrieves the read-only global leaderboard consisting of the top 10 highest-scoring completed games.

- **Method**: `GET`
- **Request Parameters**: None
- **Response Format**: `application/json`
- **Success Response (200 OK)**:
  ```json
  {
    "scores": [
      {
        "game_id": "8f3956bf-e9db-484c-be88-d698fdf7e3a9",
        "score": 4800,
        "total_lines": 24,
        "level": 3,
        "completed_at": "2026-10-29T16:15:30Z"
      },
      {
        "game_id": "c1387d89-8d77-49f3-8b7a-8fbc38da64c8",
        "score": 1200,
        "total_lines": 10,
        "level": 2,
        "completed_at": "2026-10-29T12:00:00Z"
      }
    ]
  }
  ```
  *Sorting Rules*: Ordered by `score` descending, then `completed_at` ascending (UTC time), then `game_id` lexicographically ascending.
- **Error Response (503 Service Unavailable)**: Returned if the SQLite database is locked, missing, or corrupted.
  ```json
  {
    "detail": "Leaderboard service is temporarily unavailable due to storage lock or connection failure."
  }
  ```
  *(Crucial: Internal stack traces, raw SQL queries, and local directory file paths MUST be omitted).*

---

### 2.2. POST /api/games
Spawns or resets an authoritative in-memory game session.

- **Method**: `POST`
- **Request Body**: Empty or optional object with no properties.
- **Expected Success Response (201 Created)**:
  ```json
  {
    "id": "e5c706d3-2f88-466d-9276-8f3b2361bdf1",
    "board": [
      [0,0,0,0,0,0,0,0,0,0],
      ...
    ],
    "activePiece": {
      "type": "T",
      "cells": [[0,3],[1,3],[1,2],[1,4]],
      "origin": [0,3]
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
- **Error Response (422 Unprocessable Entity / 400 Bad Request)**: Returned if any keys (e.g. `{"score": 9999}`) are submitted in the request body.
  ```json
  {
    "detail": "Extra fields are not permitted in game creation requests."
  }
  ```

---

### 2.3. GET /api/games/{id}
Inspects the current state of an active or terminal game session.

- **Method**: `GET`
- **Path Parameter**: `id` (string, UUID format)
- **Success Response (200 OK)**: Returns the current `GameSessionSchema` JSON representation (same schema as 2.2).
- **Error Response (404 Not Found)**: Returned if the game session ID is invalid or has expired from memory.
  ```json
  {
    "detail": "Game session e5c706d3-2f88-466d-9276-8f3b2361bdf1 not found."
  }
  ```

---

### 2.4. POST /api/games/{id}/tick
Forces a progressive gravity tick downward for the active falling piece.

- **Method**: `POST`
- **Path Parameter**: `id` (string, UUID format)
- **Request Body**: Empty
- **Success Response (200 OK)**: Returns the updated `GameSessionSchema` JSON representation.
- **Behavior on Game Over**: If the gravity tick results in a locked block overlap at the spawn origin, the state transitions to `"game_over"`. This immediately schedules an atomic transaction to write the final metrics to SQLite within the thread-synchronized context.
- **Error Response (404 Not Found)**: Session not found.
- **Error Response (503 Service Unavailable)**: Storage layer write error during game-over finalization.

---

### 2.5. POST /api/games/{id}/move
Slides or soft-drops the active falling piece.

- **Method**: `POST`
- **Path Parameter**: `id` (string, UUID format)
- **Request Body (Strict JSON)**:
  ```json
  {
    "direction": "left"
  }
  ```
  *Allowed values*: `"left"`, `"right"`, `"down"`.
- **Success Response (200 OK)**: Returns the updated `GameSessionSchema` JSON representation.
- **Error Response (422 Unprocessable Entity / 400 Bad Request)**:
  - If `direction` is malformed, missing, or spelling is incorrect.
  - If any extra key (e.g. `{"direction": "left", "cheat": true}`) is passed in the JSON body.
- **Error Response (404 Not Found)**: Session not found.
- **Error Response (503 Service Unavailable)**: Storage layer write error during game-over finalization (e.g. if a soft-drop results in game-over and the SQLite database write fails).
  ```json
  {
    "detail": "Finalization service is temporarily unavailable due to storage failure."
  }
  ```

---

### 2.6. POST /api/games/{id}/hold
Swaps the active piece with the held piece in the hold buffer.

- **Method**: `POST`
- **Path Parameter**: `id` (string, UUID format)
- **Request Body**: Empty
- **Success Response (200 OK)**: Returns the updated `GameSessionSchema` JSON representation.
- **Behavior on Obstructed Hold**: If swapping the piece results in an immediate collision at the spawn origin (covering empty firstHold or occupied swap), the status immediately transitions to `"game_over"`. The final metrics are written immediately to SQLite under thread-synchronized locks.
- **Error Response (404 Not Found)**: Session not found.
- **Error Response (503 Service Unavailable)**: Storage layer write error during game-over finalization.
