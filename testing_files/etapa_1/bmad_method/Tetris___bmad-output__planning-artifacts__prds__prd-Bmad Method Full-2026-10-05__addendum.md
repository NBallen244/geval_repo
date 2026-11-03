---
title: "PRD Addendum: Technical Implementation Stack"
status: final
created: 2026-10-05T22:54
updated: 2026-10-05T22:54
---

# PRD Addendum: Technical Implementation Stack

This addendum records the technical choices and structures for Stage 1 of the Tetris study. 

## 1. Backend Architecture (Python FastAPI)
- **Framework:** FastAPI with Python >= 3.10.
- **Routing:** All endpoints grouped under `/api/games` using APIRouter.
- **Core Domain Models:** Core domain data models (e.g., `Board`, `Piece`, `GameState`) decoupled from FastAPI HTTP controllers. No HTTP import should leak into the domain layer to guarantee high testability of core game mechanics.
- **Session Management:** Standard dict structure mapping game UUIDs to domain states. No database will be configured.
- **Testing Structure:** High unit test coverage utilizing `pytest`. We will verify all 7 tetromino piece spawns, collisions on all 4 boundaries (row > 19, col < 0, col > 9, overlap with settled block), immediate locking on down-collision, multi-line clears (1, 2, 3, 4 lines), and game over trigger at spawning cell occupancy.

## 2. Frontend Architecture (React + TypeScript)
- **Build Tool:** Vite for fast, lightweight builds.
- **State Management:** Simple, centralized `useGame` or `useState` hook subscribing to the backend state API.
- **Gravity Loop:** Built using standard `setInterval` or standard React timer hooks. Care must be taken to clear the interval on component unmount or when the status changes to `"game_over"`.
- **Styling:** CSS Modules or Vanilla CSS files inside `frontend/src` directory. Avoid heavy UI frameworks or TailwindCSS to ensure lightweight and pure CSS performance.

## 3. Portability & Development Commands
- **Backend Setup:**
  - Virtual Environment: `.venv/`
  - Installation: `pip install fastapi uvicorn pytest`
  - Start command: `uvicorn main:app --reload --port 8000`
- **Frontend Setup:**
  - Installation: `npm install`
  - Start command: `npm run dev` (runs on default port 5173)
