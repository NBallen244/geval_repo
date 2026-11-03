---
title: "Product Requirements Document: Stage 1 Tetris Study (Option A)"
status: final
created: 2026-10-05T22:54
updated: 2026-10-05T23:54
---

# PRD: Stage 1 Tetris Study (Option A)

## 0. Document Purpose
This Product Requirements Document (PRD) outlines the behavioral, functional, and technical requirements for Stage 1 (Option A) of the Tetris Study. This is a browser-based, greenfield implementation of a classic Tetris game that serves as an architectural study. The primary focus is demonstrating a strictly decoupled client-server architecture with an authoritative backend and a thin, responsive, stateless frontend. The PRD is structured with Glossary-anchored vocabulary, globally numbered and testable Functional Requirements (FRs), explicit user journeys, and concrete acceptance criteria.

This document builds directly on the approved Product Brief located in `_bmad-output/planning-artifacts/briefs/brief-Bmad Method Full-2026-10-05/brief.md`.

## 1. Vision
The Stage 1 Tetris Study is an educational study demonstrating how to design highly interactive, tick-based web games without bloat or client-side game state duplication. Most web-based Tetris games suffer from tightly coupled UI, physics, and gravity loops, leading to vulnerable and hard-to-test frontends.

To address this, our solution enforces a strict separation of concerns:
1. **Authoritative Backend (FastAPI):** Acts as a pure, tick-based state machine. It owns all board and piece grids, collision logic, lock detection, line clearing, and game-over states. It holds sessions in-memory.
2. **Thin Frontend (React + TypeScript):** Subscribes to the backend's state, renders cells, runs a fixed 500ms gravity ticker, and translates keyboard presses directly into API commands.

This decoupling allows the game's rules and movement physics to be robustly verified with backend unit tests, while the frontend acts as a pure, testable, and stateless renderer.

## 2. Target User

### 2.1 Jobs To Be Done (JTBD)
- **Architectural Reference (Functional):** As a Software Architect, I want to review a clean, real-world prototype of a decoupled tick-based game, so that I can understand and apply state-machine decoupling principles to complex client-server applications.
- **Rigor & Compliance Evaluation (Contextual):** As a Study Reviewer, I want to inspect a perfectly separated client-server application with comprehensive backend tests verifying all edge cases, so that I can confirm its technical hygiene.
- **Development Blueprint (Emotional/Social):** As a Developer, I want a lightweight, local, database-free greenfield codebase that is easy to start and experiment with, so that I feel confident extending it in subsequent phases.

### 2.2 Non-Users (v1)
- **Casual Gamer:** A consumer seeking a feature-rich, customizable Tetris client with smooth rotation, next-piece queues, scoring, leaderboards, and high-fidelity graphics. This project is strictly a minimal, decoupled architectural study.

### 2.3 Key User Journeys
- **UJ-1: Player Starts and Plays a Gameplay Loop**
  - **Persona + context:** Winston, a senior software architect reviewing the decoupled design.
  - **Entry state:** Winston opens the application in his browser on a local server. No previous active game.
  - **Path:**
    1. Winston clicks the prominent "Start Game" button. The frontend dispatches a `POST /api/games` request.
    2. The backend generates a game ID, creates an empty 10x20 in-memory grid, spawns a random Tetromino centered horizontally at row 0, and returns the full JSON state.
    3. The frontend renders the blank grid with the active piece cells colored at the top. The frontend's client-side gravity timer starts, ticking every 500ms.
    4. Every 500ms, the timer dispatches a `POST /api/games/{id}/tick` request. The backend moves the active piece down 1 row, calculates collision legality, updates the state, and responds with the new coordinates.
    5. Winston presses the "ArrowLeft" or "ArrowRight" keys. The frontend dispatches `POST /api/games/{id}/move` with direction "left" or "right". The backend moves the piece and responds with the updated board.
  - **Climax:** Winston soft-drops the piece by pressing "ArrowDown" (direction "down"). The piece reaches the bottom of the grid (row 19). On the next gravity tick, the backend detects that downward movement is blocked. It immediately locks the active piece cells into the grid, clears any fully completed lines, spawns a new random active piece at the top, and returns the updated state to the frontend in a single tick.
  - **Resolution:** Winston sees the previous piece turn into a settled color, and a new active piece appears at the top.
- **UJ-2: Player Suffers Game Over and Restarts**
  - **Persona + context:** Amelia, a developer testing boundary conditions.
  - **Entry state:** The board has settled blocks piled up to row 1.
  - **Path:**
    1. Amelia allows pieces to pile up vertically without shifting them.
    2. The active piece locks in place. The backend attempts to spawn a new Tetromino, but its standard spawning cells are already occupied by settled blocks.
    3. The backend detects the collision at spawn, sets the game status to "game_over", and returns the state.
    4. The frontend receives the "game_over" status, immediately stops its 500ms client-side gravity timer, disables keyboard movement controls, and displays a prominent English overlay reading "Game Over".
  - **Climax:** Amelia clicks the "Restart" button on the overlay, which dispatches a `POST /api/games` request.
  - **Resolution:** The board resets to an empty 10x20 grid, a new active piece spawns at the top, and the client timer resumes the 500ms gravity ticks.

## 3. Glossary
- **Tetromino (or Piece)** — A geometric shape composed of four square blocks (cells) connected orthogonal-wise. The seven standard shapes are: I, J, L, O, S, T, and Z.
- **Grid (or Board)** — A fixed-size matrix of cells, strictly 10 columns wide by 20 rows high, where all game interactions occur.
- **Cell** — An individual grid coordinate, represented by a 0-indexed row index (0 to 19, top-to-bottom) and column index (0 to 9, left-to-right). Holds a value of 0 (empty) or a non-zero color index representing a settled block.
- **Active Piece** — The currently falling Tetromino that is subject to player controls and automatic gravity ticks.
- **Settled Block** — A block from a previously locked Tetromino that has become part of the static board grid.
- **Gravity Tick** — An automatic temporal progression, triggered by a 500ms frontend timer, that advances the active piece down by one row on the backend.
- **Collision** — An intersection condition where any block of the active piece would occupy an out-of-bounds grid coordinate or overlap with an already settled block.
- **Locking** — The immediate transition of an active piece into settled blocks when its downward movement is blocked by a collision with the bottom boundary or settled blocks.
- **Line Clear** — The automatic removal of a fully completed row (all 10 cells occupied by settled blocks) on the backend immediately after a piece locks, which shifts all rows above it downward.
- **Game Over** — The state where a newly spawned piece immediately collides with existing settled blocks, terminating the current game session.
- **Restart** — A control that resets the board grid to empty, clears settled blocks, resets status to `playing`, and spawns a new active piece.

## 4. Features

### 4.1 System & Platform Setup (Decoupled Greenfield)
**Description:** The study must be built from scratch as a completely decoupled system containing an authoritative backend and a stateless frontend, using only English for specifications, application text, comments, and tests. Realizes UJ-1.

**Functional Requirements:**
- **FR-1: Greenfield Decoupled Setup**
  The application shall be structured with a Python FastAPI backend and a React/TypeScript frontend as separate components.
  - *Consequence:* Backend code resides in `backend/` and frontend in `frontend/`. No shared runtime or direct file-system dependencies.
- **FR-2: In-Memory Game State**
  The backend shall maintain all active game sessions entirely in-memory without requiring a physical database or authentication.
  - *Consequence:* Session state is ephemeral; restarting the FastAPI process clears all active games.
- **FR-3: English Language Uniformity**
  All application specifications, user interfaces, API JSON keys, logs, code comments, and automated test names shall be written exclusively in English.
  - *Consequence:* Frontend UI texts and backend error responses must be standard English.

### 4.2 Grid Properties and Board Dimensions
**Description:** Enforces standard grid properties and coordinates for gameplay. Realizes UJ-1.

**Functional Requirements:**
- **FR-4: Fixed Grid Size**
  The board grid shall have a fixed, unconfigurable size of exactly 10 columns by 20 rows.
  - *Consequence:* Valid column coordinates are `[0-9]` and rows are `[0-19]`. Any index outside this raises a validation error.
- **FR-5: Standard 0-Indexed Coordinate System**
  The coordinate system must represent row 0 as the top-most row and row 19 as the bottom-most row, and column 0 as the left-most column and column 9 as the right-most column.
  - *Consequence:* Left shift decreases column index, right shift increases column index, and soft drop/gravity increases row index.

### 4.3 Tetromino Piece Definitions & Spawning
**Description:** Spawns and manages Tetromino shapes on the backend and transmits their state. Realizes UJ-1.

**Functional Requirements:**
- **FR-6: Supported Tetromino Shapes**
  The system shall support exactly the seven standard Tetromino shapes: I, J, L, O, S, T, and Z.
  - *Consequence:* The backend must map each shape to its standard 4-cell coordinate block.
- **FR-7: Horizontal Centering on Spawn**
  Newly spawned pieces shall spawn centered horizontally on row 0 (or row 0 and 1, depending on shape) at the top of the grid.
  - *Consequence:* For example, the "I" piece spawns horizontally occupying rows 0, columns 3, 4, 5, and 6.
- **FR-8: Authoritative State Payload**
  The backend shall include the active piece's shape, its origin cell, and the absolute board coordinates of its four blocks in the game state JSON response.
  - *Consequence:* The frontend only reads the `active_piece` block coordinates from the API and never computes them.
- **FR-9: Random Backend Spawning**
  The selection of which Tetromino shape to spawn must be computed randomly on the backend during initialization and post-lock sequences.
  - *Consequence:* Standard random libraries on the backend must be used to ensure a non-deterministic distribution of pieces.

### 4.4 Piece Orientation (No Rotation)
**Description:** Eliminates the complexity of piece rotation in this stage to focus entirely on decoupled physics and movement. Realizes UJ-1.

**Functional Requirements:**
- **FR-10: Fixed Lifetime Orientation**
  Active pieces shall remain locked in their initial spawned orientation for their entire lifetime.
  - *Consequence:* No rotation endpoints or keyboard mapping (UP, spacebar) shall be implemented. Any upward move commands are ignored.

### 4.5 Movement Controls & Gravity Progression
**Description:** Captures manual input and timer ticks to advance the active piece. Realizes UJ-1.

**Functional Requirements:**
- **FR-11: Manual Left Move**
  The game shall process left-move commands from the frontend to shift the active piece exactly one column to the left.
  - *Consequence:* Keyboard 'ArrowLeft' dispatches `POST /api/games/{id}/move` with body `{"direction": "left"}`.
- **FR-12: Manual Right Move**
  The game shall process right-move commands from the frontend to shift the active piece exactly one column to the right.
  - *Consequence:* Keyboard 'ArrowRight' dispatches `POST /api/games/{id}/move` with body `{"direction": "right"}`.
- **FR-13: Manual Soft Drop**
  The game shall process manual down-move commands from the frontend to shift the active piece exactly one row down.
  - *Consequence:* Keyboard 'ArrowDown' dispatches `POST /api/games/{id}/move` with body `{"direction": "down"}`.
- **FR-14: Automatic Gravity Progression**
  The game shall advance the active piece down by one row automatically at regular, fixed gravity tick intervals.
  - *Consequence:* The frontend dispatches `POST /api/games/{id}/tick` on a fixed 500ms browser timer when game status is `playing`.

### 4.6 Collision Handling & Legality
**Description:** Authoritative backend validation of all movements against board boundaries and settled blocks. Realizes UJ-1.

**Functional Requirements:**
- **FR-15: Left Grid Border Block**
  A movement (left shift) must be blocked if any cell of the resulting active piece would have a column index less than 0.
  - *Consequence:* The active piece remains in its current position, and the API returns the unmodified coordinates.
- **FR-16: Right Grid Border Block**
  A movement (right shift) must be blocked if any cell of the resulting active piece would have a column index greater than 9.
  - *Consequence:* The active piece remains in its current position, and the API returns the unmodified coordinates.
- **FR-17: Bottom Grid Border Block**
  A downward movement (soft drop or gravity tick) must be blocked if any cell of the resulting active piece would have a row index greater than 19.
  - *Consequence:* The piece does not move out-of-bounds, and the locking routine is immediately triggered on the backend.
- **FR-18: Settled Block Intersection Collision**
  Any movement (left, right, down, or gravity tick) must be blocked if any cell of the resulting active piece would overlap with any settled blocks (value > 0) on the grid.
  - *Consequence:* Overlaps are illegal. A sideways overlap results in no movement. A downward overlap triggers immediate locking.
- **FR-19: Authoritative Decoupled Validation**
  The backend must serve as the sole validator for movement legality, collision check, and boundary checks.
  - *Consequence:* The frontend shall never execute collision code or attempt to override cell coordinates sent by the backend.

### 4.7 Locking Mechanism
**Description:** Bakes the falling piece into static board state. Realizes UJ-1.

**Functional Requirements:**
- **FR-20: Immediate Piece Locking**
  When a downward movement (soft drop or gravity tick) is blocked by the bottom border or a settled block, the active piece cells must be baked immediately into the static board grid.
  - *Consequence:* Grid cells matching the active piece's final coordinates transition from 0 (empty) to non-zero values.
- **FR-21: Post-Lock Spawn Sequence**
  Immediately after baking a locked piece, the backend must resolve line clears and spawn a new random active piece at the top row.
  - *Consequence:* The backend processes locking, clears lines, and generates a new active piece coordinates in a single API roundtrip.

### 4.8 Line Clearing Engine
**Description:** Detects and clears completed rows. Realizes UJ-1.

**Functional Requirements:**
- **FR-22: Full Row Completion Detection**
  A grid row is completed when all 10 columns in that row have a settled block value greater than 0.
  - *Consequence:* Empty cells (0) are not counted.
- **FR-23: Immediate Completed Line Removal**
  All completed rows must be removed from the grid immediately during the locking sequence.
  - *Consequence:* Occupied cells on completed rows are deleted from memory.
- **FR-24: Grid Shift Gravity**
  When one or more completed rows are cleared, all settled blocks above those rows must shift downward by the exact number of cleared rows.
  - *Consequence:* Row indices of blocks above the clear increase by the cleared row count. Rows at the top of the grid (index 0 upward) are filled with empty rows of 0s.
- **FR-25: Multi-Line Clear Support**
  The clearing engine must correctly support clearing 1, 2, 3, or 4 rows simultaneously in a single locking tick.
  - *Consequence:* The board shifts down smoothly.

### 4.9 Game-Over State Detection
**Description:** Detects and handles the end of a game session. Realizes UJ-2.

**Functional Requirements:**
- **FR-26: Spawning Collision Game-Over**
  A game-over state must trigger if a newly spawned active piece immediately collides with existing settled blocks at its standard spawning coordinates.
  - *Consequence:* The session status field changes to `"game_over"`.
- **FR-27: Status Field Transmission**
  The backend API and frontend client must clearly indicate whether the game is currently `"playing"` or in a `"game_over"` state.
  - *Consequence:* The status field is sent in all HTTP responses.
- **FR-28: Frontend Lockout in Game-Over**
  When the game status is `"game_over"`, the frontend client must stop its client-side gravity timer and ignore all keyboard movement inputs (left, right, down).
  - *Consequence:* No movement API requests or automated ticks are dispatched by the frontend in game-over state.

### 4.10 Restart Lifecycle & Board Reset
**Description:** Resets the game board back to a fresh state. Realizes UJ-2.

**Functional Requirements:**
- **FR-29: Game Reset API**
  Receiving a restart request must clear the in-memory board grid (set all cells to 0), reset game status to `"playing"`, and spawn a new active piece.
  - *Consequence:* Endpoint `POST /api/games` or `POST /api/games/{id}` returns the fresh state.
- **FR-30: Frontend Reset Control**
  The frontend shall display a prominent reset button available during both gameplay and game-over states that triggers the backend game reset immediately.
  - *Consequence:* Clicking the button dispatches the reset API call and restarts the gravity timer.

---

### Cross-Cutting NFRs
- **NFR-1: Fixed Gravity Timer**
  The frontend client-side gravity ticks must execute approximately every 500ms using standard timer APIs during the `"playing"` state.
- **NFR-2: UI Refresh and Animation Frame**
  The frontend must render grid changes immediately upon receiving responses from the backend without visible lag or layout shifting.

---

## 5. Non-Goals (Explicit)
- **Piece Rotation & SRS:** No rotation controls or wall kicks. Tetrominos stay in spawning orientation.
- **Hold & Next Queue:** No piece holding slots or next piece preview panels.
- **Ghost Piece:** No preview silhouette at the bottom of the column.
- **Dynamic Gravity & Scoring:** No speed increase over time, no scoring engine, and no line counter.
- **Leaderboards & Accounts:** No user registration, login, profiles, databases, or online leaderboards.

---

## 6. MVP Scope

### 6.1 In Scope
- GREENFIELD Python FastAPI backend in `backend/` utilizing in-memory session dictionaries.
- GREENFIELD React with TypeScript frontend in `frontend/` utilizing Vanilla CSS.
- Exactly 10 columns by 20 rows board size.
- Standard 0-indexed coordinate model.
- 7 Tetromino shapes spawning centered at the top in fixed initial orientation (no rotation).
- 500ms frontend gravity ticker driving `/tick` endpoint.
- Left, right, and soft-drop (down) API movements mapped to standard keyboard arrows (ArrowLeft, ArrowRight, ArrowDown).
- Authoritative backend collision, immediate locking, immediate line clears (1 to 4 lines), and game-over state.
- Local restart control.

### 6.2 Out of Scope for MVP
- Upward piece movement or movement-based speed modifiers.
- Custom keybindings (hardcoded keys only).
- Theme switchers or sound engines (strictly standard CSS/HTML visual styles).
- Persistent state across backend process restarts.

---

## 7. Success Metrics
- **SM-1 (Decoupling Verification):** 100% of game-loop decisions (collisions, locks, clears, game-overs) are evaluated on the backend. Zero piece collision calculations on the frontend.
  - *Validates:* FR-19, FR-15, FR-16, FR-17, FR-18.
- **SM-2 (Responsive Feel):** Time from keyboard keypress to UI rendering of successful move is less than 60ms locally.
  - *Validates:* FR-11, FR-12, FR-13.
- **SM-C1 (Robustness):** Gravity tick interval remains strictly at 500ms on the client and is not skipped or accelerated by concurrent player movements.
  - *Counterbalances:* SM-2.

---

## 8. Open Questions
1. **Color Indices:** Should the backend return standard color string values or integer color-indices?
   *Decision:* Backend will return integer indices (1-7), and the React frontend will map these indices to CSS classes representing specific colors.
2. **Session Cleanup:** How does the backend prevent memory leaks from abandoned game sessions?
   *Decision:* No automatic idle session cleanup/eviction is required.

---

## 9. Assumptions Index
- **[ASSUMPTION-1]:** The backend will run on `http://localhost:8000` and the frontend on `http://localhost:5173` or similar standard development ports, with CORS enabled on the FastAPI backend for development.
- **[ASSUMPTION-2]:** A simple random shape generation using Python's standard `random.choice` is sufficient and fair for Stage 1. No advanced bag randomized algorithms (like 7-bag generator) are required.

---

## 10. Adapt-In: API Contracts (Developer Product Addition)

The FastAPI backend exposes the following endpoints.

### 10.1 Data Models (JSON Schemas)

#### GameState State Schema:
```json
{
  "id": "string (UUID)",
  "status": "playing" | "game_over",
  "board": [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ... (20 rows of 10 elements. 0 = empty, 1-7 = color/shape indices of settled blocks)
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
  }
}
```

### 10.2 Endpoints Contract

- **POST `/api/games`**
  - **Description:** Initializes a brand new game session in memory and spawns the first piece.
  - **Request Body:** None (or optional session request)
  - **Response (201 Created):** `GameState` payload.

- **GET `/api/games/{id}`**
  - **Description:** Retrieves the current game state of the given game session ID.
  - **Response (200 OK):** `GameState` payload.
  - **Response (404 Not Found):** `{"detail": "Game session not found"}`

- **POST `/api/games/{id}/tick`**
  - **Description:** Moves the active piece down by one row automatically (gravity tick). If downward collision occurs, locks the piece, clears rows, spawns a new one, and checks for game-over.
  - **Response (200 OK):** `GameState` payload.
  - **Response (404 Not Found):** `{"detail": "Game session not found"}`

- **POST `/api/games/{id}/move`**
  - **Description:** Performs a manual shift in the specified direction if legal.
  - **Request Body:**
    ```json
    {
      "direction": "left" | "right" | "down"
    }
    ```
  - **Response (200 OK):** `GameState` payload.
  - **Response (400 Bad Request):** `{"detail": "Invalid direction"}`
  - **Response (404 Not Found):** `{"detail": "Game session not found"}`

---

## 11. Adapt-In: Aesthetic and Tone

To ensure the greenfield study is modern, engaging, and visually polished:
- **UI Language:** Standard, precise technical English.
- **Grid Layout:** The 10x20 board must be rendered centered on the page with a clean, dark, minimalist aesthetic (e.g., charcoal background `#121212`, grid borders `#2A2A2A`).
- **Cell Styling:**
  - Empty cells: Subtle grid borders with a slightly transparent color.
  - Settled blocks: Solid, vibrant, neon-style modern blocks matching their Tetromino shape index (e.g., I: Cyan, O: Yellow, T: Purple, S: Green, Z: Red, J: Blue, L: Orange) to offer excellent feedback.
  - Active piece cells: Rendered with the same vibrant color but with a glowing border or subtle pulsing effect to differentiate them from settled blocks.
- **Controls Reference Panel:** Side panel clearly showing standard controls:
  - `ArrowLeft`: Move Left
  - `ArrowRight`: Move Right
  - `ArrowDown`: Soft Drop
  - Restart Button: Click to Restart (no keyboard shortcut bound)
