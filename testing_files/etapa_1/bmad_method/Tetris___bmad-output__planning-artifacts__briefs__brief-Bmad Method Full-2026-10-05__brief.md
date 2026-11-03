---
title: "Product Brief: Stage 1 Tetris Study"
status: approved
created: 2026-10-05T22:54
updated: 2026-10-05T23:54
---

# Product Brief: Stage 1 Tetris Study

## Executive Summary
The Stage 1 Tetris Study is a browser-based, greenfield implementation of the classic Tetris game, structured to demonstrate the design of a decoupled application. The project serves as an architectural study focusing on a strict separation of concerns, featuring an authoritative Python FastAPI backend and a React with TypeScript frontend. This greenfield development will implement a minimal, fully functional, and highly polished core gameplay experience.

Rather than building a complex game with a plethora of features, this stage focuses on technical execution and robust foundations. By implementing an in-memory game state on the backend and a lightweight, responsive client on the frontend, the study provides a robust blueprint for future client-server interactive applications. All communications, code artifacts, and specifications will be written in English.

## The Problem
Developing highly interactive applications like Tetris often leads to bloated client-side code where game rules, UI rendering, user input handling, and temporal progression (gravity) are tightly coupled. This tight coupling makes the code difficult to maintain, test, and scale. Furthermore, trusting the client to maintain the game state introduces vulnerabilities, security risks, and divergence issues. There is a need for a clear, educational study of a decoupled architecture that demonstrates how to implement a real-time, tick-based game where the backend remains the sole source of truth while the client remains thin, responsive, and easily testable.

## The Solution
We are building a browser-based Tetris study as a decoupled client-server application:
1. **Authoritative Backend (Python FastAPI):** Owns the complete game state, grid definition, and rule engine. It exposes HTTP REST APIs to create games, retrieve state, and apply ticks and movements. All calculations (collision, line clearing, locking, game over) are executed authoritatively on the backend.
2. **Thin Frontend (React + TypeScript):** Subscribes to the backend's state and displays the 10-column by 20-row game grid and active piece cells. It manages a fixed 500ms client-side gravity timer that ticks the game forward, and captures left, right, and soft-drop (down) controls to trigger corresponding moves on the API.

This design ensures the backend acts as a pure state-machine, while the frontend functions as a stateless renderer and input-capturer.

## What Makes This Different
This implementation prioritizes a strict architectural separation of concerns over typical client-side-only game development.
- **Strict Single Source of Truth:** Unlike most web-based Tetris games, there is zero game logic or state manipulation on the frontend. The game cannot progress, shift, or lock pieces without backend authorization.
- **High Testability:** Separating the HTTP controller layer from the core domain models and game rules on the backend allows robust unit test coverage of game mechanics (collision, line clearing, piece locking) without mocking HTTP requests or running a browser.
- **Extreme Simplicity:** No database, no user authentication, and no complex state persistence. The game state is held entirely in memory on the backend, ensuring a lightweight and extremely fast local setup.

## Who This Serves
- **Software Architects & Engineers:** Developers looking for a concrete, clean, and real-world example of decoupled tick-based game architectures using modern stacks (FastAPI and React/TypeScript).
- **Study Reviewers:** Evaluators of this study who require a flawless, robust, and highly predictable gameplay system backed by comprehensive unit tests and clean, self-documenting code.

## Success Criteria
- **Strict Decoupling:** The frontend must not compute collisions, piece locks, line clears, or game-over logic. It must rely entirely on the API responses.
- **Flawless Gameplay Loop:** Smooth movement, consistent gravity ticks at 500ms intervals, robust collision detection on borders and settled blocks, correct locking, line clearing, and game-over state.
- **High Test Coverage:** The game rules, piece movements, line clears, and collision edge-cases are robustly verified with automated unit tests in the backend.
- **Technical Hygiene:** Pure TypeScript on the frontend, clean type definitions, type safety throughout, and separation of controllers, domain models, and game rules on the Python backend.

## Scope & Functional Requirements

The fixed functional scope has been broken down into 30 atomic, testable requirements:

### General & Setup
- **REQ-01:** The application shall be built as a greenfield project with a completely decoupled architecture, consisting of a Python FastAPI backend and a React with TypeScript frontend.
- **REQ-02:** The backend and frontend source files shall be completely contained within the `backend/` and `frontend/` directories, respectively.
- **REQ-03:** All application text, API contracts, specifications, code comments, tests, and user interfaces shall be written exclusively in English.
- **REQ-04:** The backend shall maintain the authoritative game state and rules in memory, without requiring a database or authentication.

### Board & Grid Properties
- **REQ-05:** The game grid shall have a fixed, unconfigurable size of 10 columns by 20 rows.
- **REQ-06:** Grid coordinates shall be represented using a standard 0-indexed coordinate system, with column indices from 0 to 9 (left-to-right) and row indices from 0 to 19 (top-to-bottom, where 0 is the top row and 19 is the bottom row).

### Tetromino Pieces & Spawning
- **REQ-07:** The game shall support the seven standard Tetromino shapes: I, J, L, O, S, T, and Z.
- **REQ-08:** Each Tetromino shall spawn at the top of the grid, centered horizontally, in its initial standard orientation.
- **REQ-09:** The active piece coordinates and shape type shall be part of the game state sent by the backend.
- **REQ-10:** No piece rotation controls or systems (such as SRS/wall kicks) shall be implemented in this stage; pieces shall remain in their initial spawned orientation throughout their lifetime.

### Gravity & Movement Controls
- **REQ-11:** The active piece shall automatically move downward by one grid row on each gravity tick.
- **REQ-12:** The game shall accept manual input for left movement, shifting the active piece one column to the left.
- **REQ-13:** The game shall accept manual input for right movement, shifting the active piece one column to the right.
- **REQ-14:** The game shall accept manual input for soft drop (downward movement), shifting the active piece one row down immediately.

### Collision Handling & Movement Legality
- **REQ-15:** A movement (left, right, down, or gravity tick) shall be blocked if any part of the active piece would cross the left grid boundary (column < 0) or the right grid boundary (column > 9).
- **REQ-16:** A movement (left, right, down, or gravity tick) shall be blocked if any part of the active piece would cross the bottom grid boundary (row > 19).
- **REQ-17:** A movement (left, right, down, or gravity tick) shall be blocked if any part of the active piece would overlap with any already settled blocks on the board.
- **REQ-18:** If a manual movement (left or right) is blocked by a boundary or settled block, the active piece shall remain in its current position without moving.

### Locking & Subsequent Spawning
- **REQ-19:** The active piece shall lock in place and become part of the settled board state when it can no longer descend (i.e., its next downward movement would result in a bottom boundary collision or a collision with a settled block).
- **REQ-20:** Locking shall occur immediately upon a downward movement or gravity tick being blocked.
- **REQ-21:** Immediately after an active piece locks, the backend shall check for completed rows, resolve line clears, and then spawn a new active piece at the top of the grid.
- **REQ-22:** Spawned pieces shall be chosen from the standard shapes using a random selection mechanism on the backend.

### Line Clearing
- **REQ-23:** A horizontal row on the grid is considered complete when all 10 columns in that row are occupied by settled blocks.
- **REQ-24:** Completed rows shall be cleared from the grid immediately upon piece locking, and any settled blocks above the cleared rows shall shift down by the number of cleared rows.
- **REQ-25:** The grid shall be capable of clearing one, two, three, or four lines simultaneously in a single tick.

### Game-Over State
- **REQ-26:** A game-over state shall trigger if a newly spawned active piece immediately collides with existing settled blocks at its spawn position.
- **REQ-27:** When a game-over state triggers, the game status shall change to `game_over` and all automatic gravity ticks and player movement inputs (except restart) shall be ignored.
- **REQ-28:** The API and frontend shall clearly convey whether the game is currently `playing` or is in a `game_over` state.

### Restart Control
- **REQ-29:** The user shall be able to trigger a restart at any time (during gameplay or after game over), which shall reset the game board to empty, clear all settled blocks, reset status to `playing`, and spawn a new active piece.
- **REQ-30:** Triggering a restart must send a `POST /api/games` request (or `POST /api/games/{id}`) to initialize the fresh game on the backend.

---

### Explicit Acceptance Criteria (AC)

- **AC-1 (Board Size):** The backend must enforce and the frontend must render a board that is exactly 10 columns by 20 rows. Grid cells outside this boundary are illegal and raise a validation error.
- **AC-2 (Piece Spawning):** Spawning centers the tetromino horizontally on row 0. Standard initial orientations must match standard Tetris pieces exactly.
- **AC-3 (Legal Movement):** Manual and automatic moves (left, right, down) only succeed if no boundary/settled block collisions occur.
- **AC-4 (Side/Bottom/Stack Collisions):** Left/right boundaries stop sideways moves. Bottom boundary and settled blocks stop downward moves and trigger locking.
- **AC-5 (Locking):** When a piece's downward movement is blocked, it is baked into the settled board grid, and a new piece is spawned.
- **AC-6 (Clearing Full Lines):** Completed rows are deleted, and all occupied cells above them drop down.
- **AC-7 (Subsequent Spawning):** Spawning happens automatically in the same tick as a lock/clear sequence.
- **AC-8 (Game Over):** If the spawning area is occupied, status is set to `game_over` and gameplay stops.

---

### Backend API Specifications
The backend is a lightweight FastAPI web application that owns all gameplay rules and validation.

#### Endpoints Contract:
- **POST `/api/games`**
  - **Description:** Creates a new game instance (or restarts) with an empty grid and a spawned active piece.
  - **Response (200 OK):**
    ```json
    {
      "id": "uuid-string",
      "status": "playing",
      "board": [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ... (20 rows of 10 elements; 0 for empty, non-zero/color-index for settled blocks)
      ],
      "active_piece": {
        "shape": "I",
        "origin": {"row": 0, "col": 3},
        "cells": [
          {"row": 0, "col": 3},
          {"row": 0, "col": 4},
          {"row": 0, "col": 5},
          {"row": 0, "col": 6}
        ]
      }
    }
    ```
- **GET `/api/games/{id}`**
  - **Description:** Retrieves the current game state for the given session ID.
  - **Response (200 OK):** Game state JSON structure (same as above).
- **POST `/api/games/{id}/tick`**
  - **Description:** Advances the game state by one gravity tick (moving active piece down 1 row, checking collision, locking, clearing completed rows, and spawning next piece if needed).
  - **Response (200 OK):** Game state JSON structure (same as above).
- **POST `/api/games/{id}/move`**
  - **Description:** Moves the active piece manually in the specified direction.
  - **Request Body:**
    ```json
    {
      "direction": "left" | "right" | "down"
    }
    ```
  - **Response (200 OK):** Game state JSON structure (same as above).

---

### Frontend Technical Requirements
The frontend is a lightweight React and TypeScript application.
- **Client-Side Gravity Timer:** Runs a standard `setInterval` or `setTimeout` loop that triggers a `/api/games/{id}/tick` call every 500ms when the game status is `playing`.
- **Stateless Grid Rendering:** Renders the 20x10 board from the backend response. Renders the active piece cells layered on top of the grid. Empty cells, settled blocks, and active cells should be styled distinctively.
- **Keyboard Event Listener:** Listens to keyboard events to dispatch API requests:
  - ArrowLeft -> Move left
  - ArrowRight -> Move right
  - ArrowDown -> Move down (soft drop)
- **Restart Button:** Displays a prominent button to start or reset the game, sending a POST request to `/api/games` to create a fresh session.
- **Game-Over Screen:** When the game status becomes `game_over`, displays an overlay or text warning the user of game over in clear English, along with a button to restart.

---

### Explicit Exclusions (Out of Scope for Stage 1)
- **Piece Rotation & Wall Kicks:** Completely excluded. Pieces only move down, left, and right in their initial spawned orientation.
- **Hold & Preview Piece:** No holding slot, no preview of the next piece.
- **Ghost Piece:** No ghost piece silhouette at the bottom of the column.
- **Configurable Controls:** Controls are hardcoded to standard arrow keys (ArrowLeft, ArrowRight, ArrowDown).
- **Line Counter, Score, Speed Progression:** No scoring system, no line counters, and gravity remains fixed at 500ms (no speed increase over time).
- **Multiplayer & Networking:** Strictly single-player.
- **Database & Authentication:** Strictly in-memory game state, no user accounts, no login, no persistent leaderboard.

---

## Vision
The project forms a highly extensible base for future phases of Tetris features:
- **Phase 2:** Introducing piece rotation, Super Rotation System (SRS), wall kicks, and responsive keyboard controls.
- **Phase 3:** Adding hold piece slots, next-piece previews, line/level counters, score calculations, speed increments, and sound effects.
- **Phase 4:** Adding persistence via a lightweight DB, global leaderboards, and user accounts.
