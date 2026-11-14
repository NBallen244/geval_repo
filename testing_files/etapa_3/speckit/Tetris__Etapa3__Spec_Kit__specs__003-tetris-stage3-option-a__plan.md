# Implementation Plan: Persistent High Scores, Dockerization, Playwright Benchmarking, and CI

**Branch**: `003-tetris-stage3-option-a` | **Date**: Thursday, October 29, 2026 | **Spec**: [specs/003-tetris-stage3-option-a/spec.md](spec.md)

**Input**: Feature specification from `/specs/003-tetris-stage3-option-a/spec.md`

## Summary
Extend our Stage 2 option A Tetris application to Stage 3 option A. This brownfield change adds:
1. **Persistent High Scores**: Local SQLite database using standard Python `sqlite3`, thread-safe locks, retry capabilities, and 503 error handling.
2. **REST API validation**: Leaderboard sorting descending by score, then ascending by time, then game_id; and strict payload key forbid-validation (4xx rejections).
3. **Frontend Leaderboard UI**: Visual panel showing ranks, score, lines, and level with loading, empty, and error fallback states.
4. **Docker Packaging**: Non-root multi-stage containers for backend and frontend with proxying and persistent volumes.
5. **Playwright Performance Benchmark**: Rendering cadence testing in foreground Chromium (1280x900 viewport) tracking frames scheduling, DOM updates, and API timings separately.
6. **Secret-Free GitHub Actions CI**: Workflow pinning Node/Python major versions and auditing dependencies.
7. **Playwright Sandbox and Timeline Correction**: Explicitly set `chromiumSandbox: true` in every browser launch branch (installed and fallback, never using `--no-sandbox`), enforce a single in-page declared timeline (`warmupStart = now`, `warmupEnd = warmupStart + 5000`, `measurementStart = warmupEnd`, `declaredEnd = measurementStart + 30000`), preserve crossing/boundary intervals, capture focus/visibility snapshot immediately after each collector reset, and log complete auditable launch metadata.

---

## Technical Context

**Language/Version**: Python `3.11` (Backend), TypeScript `5.x` with React `18.x` and Node `24LTS` (Frontend)

**Primary Dependencies**: 
- Backend Production (pinned from container reference): `fastapi==0.162.0`, `pydantic==2.14.1`, `uvicorn==0.54.0`, `anyio==4.15.1`, `starlette==1.10.0`, `pydantic_core==2.50.1`, `typing_extensions==4.16.0`, `click==8.5.0`, `h11==0.16.0`, `idna==3.20`
- Backend Dev/Audit (pinned for Linux/CI): `pytest==9.1.1`, `pytest-cov==7.1.0`, `requests==2.34.2`, `coverage==7.16.2`, `pip-audit==2.10.1`, `pip-api==0.0.35`, `pip-requirements-parser==32.0.1`, `packageurl-python==0.17.6`, `cyclonedx-python-lib==11.12.0`, `license-expression==30.4.4`, `boolean.py==5.0`, `rich==15.0.0`, `shellingham==1.5.4`, `CacheControl==0.14.4`, `msgpack==1.2.4`, `filelock==4.2.6`
- Frontend: `vite`, `tailwindcss` (or Vanilla CSS per seed standard), `lucide-react`
- Testing/QA: `pytest`, `requests`, `@testing-library/react`, `playwright`

**Storage**: Local file-system SQLite database (`high_scores` table). File path defined by `TETRIS_DB_PATH` with a local default of `./data/high-scores.sqlite3`.

**Testing**: `pytest` with code coverage reports (Backend), Vitest or Jest (Frontend), Playwright (End-to-End Performance)

**Target Platform**: Linux server Docker environment, modern browsers (Chrome/Firefox/Edge)

**Project Type**: Containerized multi-tier Web Service (Frontend static bundle + FastAPI API)

**Performance Goals**: 
- Playwright Chromium foreground scheduler cadence: mean frame rate >= 55 FPS and p95 frame intervals <= 25 ms.
- Atomic SQL execution: WAL mode enabled for near-zero lock contention.

**Constraints**:
- Strict API payload verification (`extra="forbid"` on POST requests, returning documented 4xx).
- Controlled, sanitized JSON errors on 503 Service Unavailable (zero database file path or traceback leaks).
- Restrictive CORS policy (credentials disallowed when wildcard is configured).
- 10-by-20 React DOM board, seven unrotated pieces, in-memory games, and single-worker backend remain preserved.
- Unsuppressed Security Audits: Running `pip-audit` without any suppressed vulnerabilities (unsuppressed GHSA-vv3r-rc64-8847).
- Fully Pinned Inputs: Fully pinned production and development dependencies suitable for Python 3.11 to guarantee reproducible builds in Docker and GitHub Actions.

**Scale/Scope**: Top 10 persistent leaderboard entries. Complete game over writes (including zero scores) once per UUID. Single-process, single-worker design with thread locks to eliminate race conditions.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Constitution Status**: Unconfigured / Not-Applicable. The inherited `.specify/memory/constitution.md` is still an unconfigured placeholder template, not an adopted constitution.
- **Controlling Requirements**: We adhere strictly to the frozen seed's controlling requirements for Stage 3 Option A (Persistent High Scores, Dockerization, Playwright performance testing, and secret-free GHA CI) as the source of truth, preserving all existing Stage 1/2 functionality and APIs without alteration.

---

## Project Structure

The project conforms to a two-tier Web Application architecture.

### Documentation (this feature)

```text
specs/003-tetris-stage3-option-a/
├── spec.md              # Completed Feature Specification
├── plan.md              # This file (Detailed execution blueprint)
├── research.md          # Phase 0 Research (Decisions, rationales, and alternatives)
├── data-model.md        # Phase 1 Data Model (SQLite columns, Pydantic validations, transitions)
├── quickstart.md        # Phase 1 Quickstart (Reproducible run commands and acceptance verifications)
├── checklists/
│   └── requirements.md  # Native quality checklist
└── contracts/
    ├── api-contract.md  # Detailed endpoint contract specification
    └── openapi.json     # Standard OpenAPI 3.0 specification file
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── endpoints.py
│   ├── models/
│   │   └── schemas.py
│   └── services/
│       ├── database.py   # NEW: SQLite helper and schema initialization
│       └── game_engine.py
├── requirements.txt
└── tests/
    ├── integration/
    └── unit/

frontend/
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── Board.tsx
│   │   ├── GameControls.tsx
│   │   └── HighScoresPanel.tsx # NEW: Leaderboard display panel
│   └── hooks/
│       └── useGame.ts
├── tests/
│   └── performance-benchmark.ts # NEW: Playwright performance benchmark script
├── package.json
└── vite.config.ts
```

**Structure Decision**: 
Standard Web Application layout with a decoupled React frontend and FastAPI backend, matching the Stage 1 and Stage 2 codebase structure precisely.

---

## Phase Status and Next Steps

1. **Phase 0 (Research)**: Completed.
   - Database choices, connection lock patterns, non-root multi-stage containers, Playwright traces, and CORS safety are researched and documented in [research.md](research.md).
2. **Phase 1 (Design & Contracts)**: Completed.
   - The database schemas and validation parameters are detailed in [data-model.md](data-model.md).
   - API endpoints and JSON contract signatures are specified in [contracts/api-contract.md](contracts/api-contract.md) and [contracts/openapi.json](contracts/openapi.json).
   - Validation scripts and CLI commands are mapped out in [quickstart.md](quickstart.md).
3. **Phase 2 (Implementation Tasks)**:
   - To be executed in the next stage of the Spec Kit workflow.
   - Standard tasks will cover database initialization, thread-safe endpoint mutation, High Scores frontend panel rendering, Docker packaging, Playwright perform-script creation, and GHA setup.
