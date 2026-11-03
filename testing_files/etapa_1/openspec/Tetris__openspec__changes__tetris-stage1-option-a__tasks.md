# OpenSpec Task Roadmap: Stage 1 Setup, Engine, and Tests

## Phase 1: Greenfield Scaffolding
- [x] **Task 1.1:** Scaffold empty folders `backend/` and `frontend/`.
- [x] **Task 1.2:** Configure Python backend virtual environment, install `fastapi`, `uvicorn`, and `pytest`.
- [x] **Task 1.3:** Setup React, Vite, and TypeScript inside `frontend/` directory.
- [x] **Task 1.4:** Setup GitHub actions or simple scripts to run backend tests and build the frontend.

## Phase 2: Authoritative Backend Engine
- [x] **Task 2.1:** Implement Pydantic data models in `backend/models.py` (REQ-001, REQ-002, REQ-003).
- [x] **Task 2.2:** Build standard 7 tetromino generators in `backend/engine.py` (REQ-004, REQ-005, REQ-006).
- [x] **Task 2.3:** Implement collision detection logic (borders and settled blocks) in `backend/engine.py` (REQ-011, REQ-012, REQ-013, REQ-014, REQ-015, REQ-016).
- [x] **Task 2.4:** Write the active piece movement handlers: shift left, shift right, and soft drop (REQ-008, REQ-009, REQ-010).
- [x] **Task 2.5:** Implement the lock-down handler (REQ-017, REQ-018, REQ-019).
- [x] **Task 2.6:** Write row-clearing logic: identify, remove full lines, drop upper blocks, prepend new rows (REQ-020, REQ-021, REQ-022, REQ-023, REQ-024).
- [x] **Task 2.7:** Implement game-over overlap verification on spawn (REQ-025, REQ-026, REQ-027).

## Phase 3: REST API Controllers
- [x] **Task 3.1:** Implement `POST /api/games` creating a new game session (REQ-028, REQ-029).
- [x] **Task 3.2:** Implement `GET /api/games/{id}` retrieving session data (REQ-030).
- [x] **Task 3.3:** Implement `POST /api/games/{id}/move` validating and moving the piece.
- [x] **Task 3.4:** Implement `POST /api/games/{id}/tick` advancing gravity.

## Phase 4: Frontend Development
- [x] **Task 4.1:** Establish HTTP fetch services to communicate with FastAPI endpoints.
- [x] **Task 4.2:** Implement `GridBoard` component rendering 10x20 cells (REQ-001, REQ-002).
- [x] **Task 4.3:** Setup keyboard controls hook forwarding events to `/move` endpoint (REQ-008, REQ-009, REQ-010).
- [x] **Task 4.4:** Configure 500 ms gravity tick hook sending calls to `/tick` (REQ-030).
- [x] **Task 4.5:** Design clear `GameOverModal` (REQ-026).

## Phase 5: Verification & Runnable Tests
- [x] **Task 5.1:** Write unit tests in `backend/test_engine.py` using `pytest` verifying spawning, movements, collisions, locking, clearing, and game-over rules.
- [x] **Task 5.2:** Test API controllers using FastAPI's `TestClient`.
- [x] **Task 5.3:** Build frontend completely without errors or type warnings using `npm run build`.
- [x] **Task 5.4:** Document running instructions in README files.
