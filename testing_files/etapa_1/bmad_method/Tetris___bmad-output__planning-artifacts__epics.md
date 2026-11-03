---
title: "Greenfield Epics and Stories list: Stage 1 Decoupled Tetris Study"
status: final
created: 2026-10-05T22:54
updated: 2026-10-05T23:54
---

# Greenfield Epics & Stories: Stage 1 Decoupled Tetris Study

This document breaks the Product Requirements Document (PRD) for Stage 1 (Option A) of the Tetris study into development epics and actionable stories with complete acceptance criteria.

## NonFunctional Requirements

- **NFR-1: Fixed Gravity Timer** - The frontend client-side gravity ticks must execute approximately every 500ms using standard timer APIs during the "playing" state.
- **NFR-2: UI Refresh and Animation Frame** - The frontend must render grid changes immediately upon receiving responses from the backend without visible lag or layout shifting.

### Additional Requirements

- **AD-1: Core Domain Decoupling** - Keep domain rules decoupled from FastAPI HTTP controllers (no HTTP imports in `backend/app/core/domain.py`).
- **AD-2: Directory Structures** - Conform exactly to the structural seed:
  - `backend/app/main.py`
  - `backend/app/core/domain.py`
  - `backend/app/tests/test_domain.py`
  - `frontend/src/main.tsx`
  - `frontend/src/App.tsx`
  - `frontend/src/styles.css`
- **AD-3: CORS Configuration** - Configure CORS in FastAPI for local React development (`http://localhost:5173`).
- **AD-4: Ephemeral In-Memory Sessions** - Game states must be mapped to UUID keys in an ephemeral dictionary. No automatic idle session cleanup is required.

### UX Design Requirements

No external UX Design Contract was present in the inputs, but Section 11 of the PRD defines explicit UX parameters that have been integrated as first-class requirements:
- **UX-DR-1: Centered Dark Grid Frame** - The 10x20 board must be rendered centered on the page with a clean, dark, minimalist aesthetic (charcoal background `#121212`, grid borders `#2A2A2A`).
- **UX-DR-2: Neon Block Styling** - Settled blocks must be rendered as solid, modern neon colors mapped to shape indices:
  - 1: Cyan (I)
  - 2: Blue (J)
  - 3: Orange (L)
  - 4: Yellow (O)
  - 5: Green (S)
  - 6: Purple (T)
  - 7: Red (Z)
- **UX-DR-3: Active Piece Glow/Pulse Effect** - Active piece cells must be rendered in the same neon color as their shape but with a glowing/pulsing border to distinguish them from static settled blocks.
- **UX-DR-4: Controls Reference Panel** - A visible side panel must explicitly display the following bindings:
  - `ArrowLeft`: Move Left
  - `ArrowRight`: Move Right
  - `ArrowDown`: Soft Drop
  - Restart Button: Click to Restart (no keyboard shortcut bound)
- **UX-DR-5: English Screen Overlays** - The overlay shown upon game-over must be written exclusively in English, displaying "Game Over" and a clear restart button.

### FR Coverage Map

- FR-1: Epic 1 - Story 1.1, Story 1.2
- FR-2: Epic 1 - Story 1.3
- FR-3: Epic 1 - Story 1.1, Story 1.2, Story 1.4
- FR-4: Epic 1 - Story 1.2, Story 1.3
- FR-5: Epic 1 - Story 1.2, Story 1.3
- FR-6: Epic 2 - Story 2.1
- FR-7: Epic 2 - Story 2.1
- FR-8: Epic 2 - Story 2.1
- FR-9: Epic 2 - Story 2.1
- FR-10: Epic 2 - Story 2.1
- FR-11: Epic 3 - Story 3.1, Story 3.2
- FR-12: Epic 3 - Story 3.1, Story 3.2
- FR-13: Epic 3 - Story 3.1, Story 3.2
- FR-14: Epic 3 - Story 3.1, Story 3.2
- FR-15: Epic 4 - Story 4.1
- FR-16: Epic 4 - Story 4.1
- FR-17: Epic 4 - Story 4.2
- FR-18: Epic 4 - Story 4.1, Story 4.4
- FR-19: Epic 4 - Story 4.1, Story 4.2, Story 4.3
- FR-20: Epic 4 - Story 4.2
- FR-21: Epic 4 - Story 4.2
- FR-22: Epic 4 - Story 4.3
- FR-23: Epic 4 - Story 4.3
- FR-24: Epic 4 - Story 4.3
- FR-25: Epic 4 - Story 4.3
- FR-26: Epic 5 - Story 5.1
- FR-27: Epic 5 - Story 5.1
- FR-28: Epic 5 - Story 5.2
- FR-29: Epic 5 - Story 5.3
- FR-30: Epic 5 - Story 5.3

## Epic List

### Epic 1: Greenfield Decoupled Setup & Session Initialization
Establish the Python FastAPI backend and React/TypeScript frontend scaffolding. Set up ephemeral, in-memory session structures and expose the session creation API.
**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5

### Epic 2: Active Tetromino Piece Spawning & State Delivery
Build the backend representation of the seven standard Tetromino shapes, their horizontal centering on spawn, and the authoritative GameState payload format. Display the active piece cells in the frontend renderer.
**FRs covered:** FR-6, FR-7, FR-8, FR-9, FR-10

### Epic 3: Keyboard Controls, Manual Movement & Gravity Ticks
Expose the manual move and gravity tick endpoints. Bind manual inputs to arrow keys on the frontend and drive automatic gravity via a 500ms timer.
**FRs covered:** FR-11, FR-12, FR-13, FR-14

### Epic 4: Authoritative Backend Collisions, Locking & Line Clear Engine
Implement authoritative backend collision logic for board borders and settled blocks. Implement immediate locking, post-lock spawn sequences, completed row clearing, board gravity shifts, and multi-row clears.
**FRs covered:** FR-15, FR-16, FR-17, FR-18, FR-19, FR-20, FR-21, FR-22, FR-23, FR-24, FR-25

### Epic 5: Game-Over, Restart Lifecycle & UX Polish
Build spawning-collision game-over detection, frontend lockout, a centered Game Over screen overlay, a reset API, a restart control button, side shortcuts panel, and standard controls.
**FRs covered:** FR-26, FR-27, FR-28, FR-29, FR-30

---

## Epic 1: Greenfield Decoupled Setup & Session Initialization

Set up the project scaffolding, define the basic data schemas, and establish the session creation endpoint.

### Story 1.1: FastAPI Greenfield Scaffolding

As a Developer,
I want a clean, greenfield Python FastAPI project setup in the `backend/` directory,
So that I can write core authoritative game mechanics in a testable environment.

**Acceptance Criteria:**

**Given** no existing backend code,
**When** the developer creates `backend/app/main.py`, a `backend/requirements.txt`, and initializes a virtual environment,
**Then** running FastAPI with uvicorn on port 8000 succeeds and basic CORS is configured.
**And** a baseline `pytest` configuration is set up in `backend/tests/` to run unit tests.

### Story 1.2: React TypeScript Scaffolding & Canvas Layout

As a Developer,
I want a clean Vite + React + TypeScript scaffolding in the `frontend/` directory with a modern dark aesthetic,
So that I have a baseline stateless renderer workspace.

**Acceptance Criteria:**

**Given** no existing frontend code,
**When** the developer scaffolds Vite with React/TypeScript and installs standard packages under `frontend/`,
**Then** running `npm run dev` starts a local server on port 5173.
**And** `frontend/src/App.tsx` contains a centered dark layout container (`#121212`) and links to `frontend/src/styles.css` with a basic grid frame of 10 columns by 20 rows.

### Story 1.3: Game Session Initialization API (`POST /api/games`)

As a Player,
I want to request a new game session on the backend,
So that a fresh in-memory board state is created and uniquely identified.

**Acceptance Criteria:**

**Given** an empty in-memory backend session dictionary,
**When** a `POST /api/games` request is received,
**Then** the backend must generate a unique UUID and create a new game session.
**And** the game session status must be initialized to `"playing"`.
**And** the session board must represent a 10x20 matrix filled with 0s.
**And** the response must return a 201 status with the complete GameState JSON schema.

### Story 1.4: Frontend Start Game Integration

As a Player,
I want a prominent "Start Game" button,
So that I can initialize a new gameplay session and see the empty board grid.

**Acceptance Criteria:**

**Given** a player on the landing page with no active game session,
**When** the player clicks the "Start Game" button,
**Then** the frontend dispatches a `POST /api/games` request to the backend.
**And** the frontend receives the UUID and board representation and renders a centered empty 10x20 grid (charcoal background `#121212` with subtle borders `#2A2A2A`).

---

## Epic 2: Active Tetromino Piece Spawning & State Delivery

Define the Tetromino shapes, horizontally center them on spawn, and render the active piece coordinates.

### Story 2.1: Backend Tetromino Definitions & Random Spawning

As a Developer,
I want the backend to define the seven standard Tetromino shapes (I, J, L, O, S, T, Z) with horizontal centering on spawn and pick one randomly on game creation,
So that active pieces spawn correctly according to standard Tetris properties.

**Acceptance Criteria:**

**Given** a new game session is being initialized via `POST /api/games`,
**When** the backend computes the active piece,
**Then** it must randomly choose one of the seven shapes: I, J, L, O, S, T, or Z.
**And** the piece coordinates (4 blocks) must be calculated centered horizontally at row 0 (or rows 0 and 1, depending on shape).
**And** the returned GameState payload must include `active_piece` with its shape, origin row/column, and the absolute board coordinates of its four blocks.

### Story 2.2: Frontend Active Piece Rendering

As a Player,
I want to see the falling Tetromino piece rendered in a distinct color on the board grid,
So that I can easily identify the active piece from empty cells.

**Acceptance Criteria:**

**Given** the frontend receives a GameState containing a valid `active_piece` payload,
**When** rendering the grid,
**Then** cells corresponding to the active piece block coordinates must be colored with modern neon-style solid colors (e.g., I: Cyan, O: Yellow, T: Purple, S: Green, Z: Red, J: Blue, L: Orange).
**And** active piece cells must render with a pulsing or glowing border effect to differentiate them from settled blocks.

---

## Epic 3: Keyboard Controls, Manual Movement & Gravity Ticks

Implement the controls and automatic ticks that advance the active piece.

### Story 3.1: Backend Movement & Tick Endpoints

As a Developer,
I want the backend to expose movement and gravity tick API endpoints that adjust the active piece's row or column coordinates,
So that the active piece can progress through the board.

**Acceptance Criteria:**

**Given** a valid active session in `"playing"` status,
**When** a `POST /api/games/{id}/move` request with `{"direction": "left"}` is received,
**Then** the active piece column coordinates must decrease by 1 (without considering collisions yet).
**And** when the direction is `"right"`, column coordinates must increase by 1.
**And** when the direction is `"down"`, row coordinates must increase by 1.
**And** when a `POST /api/games/{id}/tick` request is received, row coordinates must increase by 1 (representing a gravity tick).
**And** the API response must return 200 OK with the updated GameState payload in snake_case.

### Story 3.2: Keyboard Event Listeners & Client-Side Gravity Timer

As a Player,
I want my keyboard arrow presses to dispatch movement API requests and a background timer to trigger gravity ticks automatically,
So that the game feels interactive and progresses on its own.

**Acceptance Criteria:**

**Given** an active game session in `"playing"` status,
**When** the player presses standard keyboard keys `ArrowLeft`, `ArrowRight`, or `ArrowDown`,
**Then** the frontend dispatches the corresponding movement API request (`left`, `right`, or `down`).
**And** when the game starts, a client-side timer must be initialized to dispatch a `POST /api/games/{id}/tick` precisely every 500ms.
**And** when keys are pressed, the timer must not double-tick or accelerate.

---

## Epic 4: Authoritative Backend Collisions, Locking & Line Clear Engine

Build border and settled block collisions, immediate piece locking, post-lock spawn sequences, row clearing, and row shifts.

### Story 4.1: Backend Border & Settled Block Collision Validation

As a Developer,
I want the backend to validate all movement requests against grid boundaries and settled blocks,
So that illegal moves are blocked.

**Acceptance Criteria:**

**Given** an active game,
**When** a move left would result in any active piece cell column index < 0,
**Then** the movement is blocked and the active piece position remains unchanged.
**And** when a move right would result in column index > 9, the movement is blocked.
**And** when any movement would overlap with any settled block (cell value > 0) on the board grid, the movement is blocked.

### Story 4.2: Authoritative Piece Locking & Post-Lock Spawning

As a Developer,
I want downward movement collisions with the bottom border or settled blocks to immediately lock the piece and spawn a new random one,
So that pieces stack on the board.

**Acceptance Criteria:**

**Given** an active game in `"playing"` status,
**When** a soft drop (`"down"` move) or gravity tick would result in any active piece cell row index > 19, or overlap with a settled block,
**Then** the downward movement is blocked and the active piece's cells are immediately baked into the board grid as settled blocks (the board grid cells at those coordinates transition from 0 to the piece's color index).
**And** immediately after locking, the backend spawns a new random active piece at the top of the grid and returns the updated state containing the locked board and new piece in a single API roundtrip.

### Story 4.3: Line Clearing & Shifting Gravity Engine

As a Player,
I want completed rows of settled blocks to be cleared automatically and rows above to shift downward,
So that I can clear space and continue playing.

**Acceptance Criteria:**

**Given** a piece has just locked into the grid,
**When** one or more rows have all 10 columns occupied by settled blocks (value > 0),
**Then** the backend must immediately clear those completed rows during the locking sequence.
**And** all settled blocks above the cleared rows must shift down by the exact number of cleared rows, and row 0 must be filled with 0s.
**And** the engine must support clearing 1, 2, 3, or 4 completed rows simultaneously in a single locking tick.

### Story 4.4: Frontend Synchronized Grid Rendering

As a Player,
I want the frontend board to render settled blocks and cleared lines immediately without lag,
So that the visual representation is always perfectly synchronized with the authoritative state.

**Acceptance Criteria:**

**Given** the frontend receives the updated GameState,
**When** rendering,
**Then** settled blocks (values 1-7) must render as static solid neon blocks matching their index.
**And** UI changes are rendered immediately without visible lag or layout shifting.

---

## Epic 5: Game-Over, Restart Lifecycle & UX Polish

Trigger game-overs, lockout controls, overlay messaging, a game reset API, and restart controls.

### Story 5.1: Spawning Collision Game-Over Detection

As a Developer,
I want the backend to trigger a game-over state if a newly spawned active piece immediately collides with existing settled blocks,
So that the game terminates when the board is full.

**Acceptance Criteria:**

**Given** a post-lock spawn sequence is triggered,
**When** the newly spawned random piece's coordinates overlap with any settled blocks (cell value > 0),
**Then** the backend must set the session status field to `"game_over"`.
**And** all subsequent move or tick API calls on that session must return the `"game_over"` status without advancing any pieces.

### Story 5.2: Frontend Game-Over Overlay & Input Lockout

As a Player,
I want a clear visual overlay showing "Game Over" and all keyboard controls to be disabled when the game is over,
So that I know the session has ended and cannot trigger redundant API requests.

**Acceptance Criteria:**

**Given** the frontend receives a GameState with status `"game_over"`,
**When** this state is received,
**Then** the frontend must immediately stop the 500ms client-side gravity timer.
**And** keyboard movement event listeners must ignore all manual inputs (`ArrowLeft`, `ArrowRight`, `ArrowDown`).
**And** a prominent English visual overlay reading "Game Over" must cover the center of the grid.

### Story 5.3: Game Reset API & Frontend Restart Control

As a Player,
I want a prominent Restart button to clear the board and start a new game,
So that I can play again instantly after a game over or during gameplay.

**Acceptance Criteria:**

**Given** a session is in `"playing"` or `"game_over"` status,
**When** the player clicks the Restart button,
**Then** the frontend dispatches a reset request (or a new session request `POST /api/games`).
**And** the backend resets the board grid to empty (all cells 0), status to `"playing"`, spawns a new random active piece, and returns the fresh GameState payload.
**And** the frontend resumes the 500ms gravity timer ticks.

### Story 5.4: Keyboard Reference Panel

As a Player,
I want a side panel showing the controls reference,
So that I have helpful instructions.

**Acceptance Criteria:**

**Given** the frontend dashboard,
**When** rendered,
**Then** a clean side panel must clearly list standard controls: `ArrowLeft`: Move Left, `ArrowRight`: Move Right, `ArrowDown`: Soft Drop, and a Restart Button.
