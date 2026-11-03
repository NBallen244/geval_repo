# API Endpoints Usage Guide: Tetris Core

The FastAPI backend exposes the following REST API endpoints under `/api`. All bodies and responses consume and produce `application/json`.

## Endpoints Table

| Method | Endpoint | Request Body | Response Body | Description |
|--------|----------|--------------|---------------|-------------|
| `POST` | `/api/games` | *None* | `GameSession` | Creates a new game session with an empty board and initial random piece. |
| `GET` | `/api/games/{id}` | *None* | `GameSession` | Retrieves the current state of an existing game session. |
| `POST` | `/api/games/{id}/tick` | *None* | `GameSession` | Advances the game by one gravity tick (shifts piece down or locks/spawns next). |
| `POST` | `/api/games/{id}/move` | `MoveRequest` | `GameSession` | Executes manual movements: left, right, or down (soft drop). |

## Request and Response Schemas

### MoveRequest
```json
{
  "direction": "left" | "right" | "down"
}
```

### GameSession Response
```json
{
  "id": "a0f5060c-9cb4-4cc9-a097-d85b6fd4aeef",
  "board": [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ...
  ],
  "activePiece": {
    "type": "T",
    "cells": [[0, 4], [1, 3], [1, 4], [1, 5]],
    "origin": [1, 4]
  },
  "status": "playing"
}
```
