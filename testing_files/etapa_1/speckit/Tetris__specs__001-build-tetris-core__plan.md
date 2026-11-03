# Implementation Plan: build-tetris-core

**Branch**: `001-build-tetris-core` | **Date**: 2026-09-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-build-tetris-core/spec.md`

## Summary
The goal is to implement Stage 1, Option A of a browser-based Tetris game core. The game will be built as a decoupled, greenfield project consisting of a Python FastAPI backend and a React with TypeScript frontend. The backend owns the authoritative game state and rules entirely in-memory, while the frontend is a visual renderer that runs gravity ticks at a 500 ms interval and handles keyboard inputs. No database persistence, authentication, or rotation mechanics are included in this stage.

## Technical Context

**Language/Version**: Python 3.11+, TypeScript 5.0+, Node 18+

**Primary Dependencies**: FastAPI, Uvicorn, Pydantic (Backend); React 18, Vite (Frontend); Vanilla CSS for interface styling and grid presentation (TailwindCSS avoided).

**Storage**: In-memory Python dictionaries (keyed by unique game IDs) on the backend server; transient state loaded on the React client.

**Testing**: pytest (Backend unit & integration testing); Vitest or Jest/React Testing Library (Frontend unit & rendering testing).

**Target Platform**: Modern standard desktop web browsers (Chrome, Firefox, Edge, Safari).

**Project Type**: Decoupled Web Application (FastAPI REST backend and React client-side SPA).

**Performance Goals**: API response latencies <50 ms under local network conditions; stable frontend game loop ticks running at 500 ms (drift <10 ms).

**Constraints**: Stateless server execution with in-memory active session stores. No rotation, no hold mechanics, no piece preview, no database, single-player focus.

**Scale/Scope**: Local developer study environment with up to 10 concurrent active local game sessions.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Decoupled Architecture**: Verified. The backend is a completely independent REST API server, and the frontend is an independent visual client that consumes the API.
- **Principle II: English and Standards**: Verified. All code, comments, specs, interface text, and logs are written in English.
- **Principle III: No Unwanted Scope**: Verified. Piece rotation, hold queue, next-piece preview, and user accounts are explicitly listed as out of scope.
- **Principle IV: Test-First Readiness**: Verified. The specification is fully testable with measurable Success Criteria (SC-001 through SC-004), enabling unit and contract tests on both backend and frontend.

All quality gates are successfully passed.

## Project Structure

### Documentation (this feature)

```text
specs/001-build-tetris-core/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    └── openapi.json     # OpenAPI specification
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   └── endpoints.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   └── game_engine.py
│   └── main.py
└── tests/
    ├── unit/
    └── integration/

frontend/
├── src/
│   ├── components/
│   │   ├── Board.tsx
│   │   ├── GameOverModal.tsx
│   │   └── GameControls.tsx
│   ├── hooks/
│   │   └── useGame.ts
│   ├── App.tsx
│   ├── index.css
│   └── main.tsx
└── tests/
```

**Structure Decision**: Option 2 (Web application) was selected. The project is split into a standalone backend API in `backend/` and a React front-end application in `frontend/`.

## Testing & Verification Plan

### Frontend Build Validation
The frontend must compile and build cleanly (no warnings or typescript errors) with:
```bash
cd frontend
npm run build
```

### Backend Test Validation
The backend tests must pass cleanly in both of these execution modes:
- Run from `backend/` directory:
  ```bash
  cd backend
  pytest
  ```
- Run from root directory:
  ```bash
  python -m pytest backend/tests
  ```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None      | N/A        | N/A                                 |
