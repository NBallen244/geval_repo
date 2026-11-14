# Implementation Plan: Extend Tetris to Stage 2 - Score, Level, Hold, Next Preview

**Branch**: `002-extend-tetris-stage2` | **Date**: 2026-10-20 | **Spec**: [specs/002-extend-tetris-stage2/spec.md](spec.md)

**Input**: Feature specification from `/specs/002-extend-tetris-stage2/spec.md`

## Summary

This feature extends the browser-based single-player Tetris Core implementation (Stage 1, Option A) to Stage 2, Option A, introducing scoring, leveling, progressive gravity speed, a single-piece Hold slot, a Next Piece preview queue, and real-time frontend dashboard displays. 

Our technical approach centers on extending the existing in-memory backend Python state-machine (`GameSessionSchema` via FastAPI) to maintain and validate the newly added scoring variables, next piece generation, and hold state. The React frontend will receive these state values dynamically and reschedule its automatic tick-gravity timers based on `gravity_interval_ms`, keeping inputs snappy and synchronized while avoiding race conditions or visual jumps when handling out-of-order API responses.

## Technical Context

**Language/Version**: Python 3.12, TypeScript 5.0+

**Primary Dependencies**: FastAPI, Pydantic v2 (backend); React 18, Vite (frontend)

**Storage**: In-memory Python `active_sessions` dict mapping UUID strings to Pydantic objects.

**Testing**: Pytest (backend unit & integration tests), Vitest with `@testing-library/react` and JSDOM (frontend hooks & UI tests)

**Target Platform**: Modern standard browsers (frontend) and Windows (`win32`) Python FastAPI server (backend)

**Project Type**: Decoupled Web Application (Frontend + Backend REST API)

**Performance Goals**:
- Dynamic tick intervals rescheduling immediately upon receiving changed `gravity_interval_ms` from backend.
- Frame-rate level responsive player controls (keyboard key listeners for 'C' and UI hold action).

**Constraints**:
- Keep board size exactly 10-by-20.
- No piece rotation (preserved from Stage 1).
- No soft-drop manual movement scoring.
- Exact scoring formula: `1 row: 100 * level`, `2 rows: 300 * level`, `3 rows: 500 * level`, `4 rows: 800 * level` (where level is evaluated prior to line clearing).
- Reset all state variables on game restart.

**Scale/Scope**: Single-player local session, temporary in-memory session lifetime.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Rule 1: Library-First / Core Isolation**: The backend game state logic is fully isolated in `game_engine.py` and schema-enforced with Pydantic. No UI or networking logic leaks into the core engine. (**Passed**)
- **Rule 2: Interface-Driven Contract**: Exposes clean JSON REST endpoints. Stage 2 retains the exact snake_case JSON schemas for new properties while mapping legacy camelCase `activePiece` correctly for compatibility. (**Passed**)
- **Rule 3: Test-First (Non-Negotiable)**: Detailed unit tests will be formulated to isolate and verify the scoring formula, hold operations, line count, levels progression, and edge cases (such as immediate overlap game over upon hold) before implementation changes. (**Passed**)
- **Rule 4: Low-Complexity Architecture**: All new states are stored directly within the single in-memory `GameSessionSchema`. There is no introduction of databases, web sockets, or other heavy infrastructure, keeping system complexity to an absolute minimum. (**Passed**)

## Project Structure

### Documentation (this feature)

```text
specs/002-extend-tetris-stage2/
├── plan.md              # This file (Implementation Plan)
├── research.md          # Phase 0 output (Implementation Research)
├── data-model.md        # Phase 1 output (Data Model & State Transitions)
├── quickstart.md        # Phase 1 output (Quickstart & E2E Validation Guide)
├── contracts/
│   ├── api-contract.md  # Phase 1 output (REST API Contract Specification)
│   └── openapi.json     # Phase 1 output (OpenAPI Specification file)
└── checklists/
    └── requirements.md  # Revise checklist
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py      # REST endpoints (adds POST /api/games/{id}/hold)
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py        # Schema models (extended with Stage 2 fields)
│   ├── services/
│   │   ├── __init__.py
│   │   └── game_engine.py    # Game rules, scoring, gravity & hold mechanics
│   ├── __init__.py
│   └── main.py               # Fast API App instantiation
├── tests/
│   ├── integration/
│   │   ├── test_api_us1.py
│   │   ├── test_api_us2.py   # Adds hold, score & leveling API tests
│   │   └── test_api_us3.py   # Adds UI sync & interval tests
│   └── unit/
│       ├── test_game_engine_us1.py
│       ├── test_game_engine_us2.py # Adds engine unit tests for Hold, level & score
│       └── test_game_engine_us3.py # Adds engine unit tests for edge cases (Immediate overlap)
├── conftest.py
└── requirements.txt

frontend/
├── src/
│   ├── components/
│   │   ├── Board.tsx
│   │   ├── GameControls.tsx  # Game controls panel with Hold button
│   │   └── GameOverModal.tsx # Reset & restart modal
│   ├── hooks/
│   │   └── useGame.ts        # Dynamic interval ticking, key binds & stale responses filtering
│   ├── App.tsx               # Main UI rendering panels (Hold, Statistics, Next, Board)
│   ├── index.css
│   ├── main.tsx
│   └── types.ts              # Stage 2 TypeScript interfaces
├── tests/
│   ├── GameOverModal.test.tsx
│   └── useGame.test.ts       # Tests for useGame (Hold keys, speed timers, out-of-order responses)
├── package.json
├── tsconfig.json
└── vite.config.ts
```

**Structure Decision**: Web application layout (Option 2) matching the existing frontend and backend project structure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*(No violations. The proposed design is 100% compliant with the project constitution and constraints.)*
