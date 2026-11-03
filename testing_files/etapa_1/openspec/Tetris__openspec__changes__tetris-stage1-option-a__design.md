# OpenSpec Architectural Design: Browser-Based Tetris Study

## 1. Decoupled System Architecture
The application is structured into two completely independent service layers communicating over RESTful JSON:

- **Frontend SPA (React & TypeScript):** Handles UI, rendering the grid, tracking clock intervals (500 ms gravity), capturing player keyboard events, and sending action commands to the backend.
- **Backend API (FastAPI):** Stateless HTTP layer that maps session states inside an in-memory manager, executing core game-loop logic, gravity ticks, collision checks, line clears, and piece spawning.

## 2. Backend Design (Python FastAPI)

### 2.1. File Structure
- `backend/main.py`: Entry point for Uvicorn, API routes, CORS setup.
- `backend/models.py`: Pydantic data schemas representing GameState, ActivePiece, MoveRequest, and GameConfig.
- `backend/engine.py`: Domain rules representing Board, Tetromino shapes, and GameSession manager.

### 2.2. Class & Flow Specifications
- **GameSession Manager:** Maps `session_id` to game logic structures in memory using a Python dictionary. Handles automatic cleanup of stale sessions.
- **Tetromino Factory:** Handles generation of the standard 7 tetromino shapes randomly.
- **Collision Checker:** Pure function taking Board cells and ActivePiece coordinates, returning a boolean indicating if coordinates are invalid, out-of-bounds, or overlapping.

## 3. Frontend Design (React & TypeScript)

### 3.1. Component Hierarchy
- `GameApp`: Root component managing active session ID, fetching game state, and displaying components.
- `GridBoard`: Renders a 10x20 table representing empty cells, active piece blocks, and settled blocks.
- `GameControls`: Renders start/restart buttons and lists simple keyboard instructions (Left/Right Arrows, Down Arrow).
- `GameOverModal`: Overlay modal triggered when status changes to `game_over`, showing a restart button.

### 3.2. State & Hooks
- `useGameLoop`: Standard React hook wrapping `setInterval`. Dispatches a `POST /api/games/{id}/tick` request every 500 ms when status is `playing`.
- `useKeyboardInput`: Captures keydown events (`ArrowLeft`, `ArrowRight`, `ArrowDown`) and triggers calls to `/api/games/{id}/move`.
