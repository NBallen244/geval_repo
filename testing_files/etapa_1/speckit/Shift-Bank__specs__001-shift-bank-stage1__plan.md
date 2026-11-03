# Implementation Plan: Shift Bank Stage 1 (Revised)

**Branch**: `001-shift-bank-stage1` | **Date**: 2026-09-30 | **Spec**: [specs/001-shift-bank-stage1/spec.md](spec.md)

**Input**: Feature specification from `/specs/001-shift-bank-stage1/spec.md`

## Summary
Develop Stage 1 of Shift Bank, a secure, tool-neutral web application allowing an authenticated mock user to view balances, transfer funds strictly between Checking and Savings accounts, and execute mock MFA for sensitive transfers (COP 1,000,000 or greater). The technical approach uses a lightweight Python 3.13 FastAPI backend with native SQLite persistence (without ORMs) and a Vanilla CSS React + TypeScript frontend built with Vite.

## Technical Context

**Language/Version**: Python 3.13 (Backend), TypeScript / React 18+ (Frontend)

**Primary Dependencies**: `fastapi`, `uvicorn` (Backend); `react`, `react-dom`, `vite` (Frontend)

**Storage**: SQLite using Python's built-in `sqlite3` module (ORMs like SQLAlchemy are strictly excluded)

**Testing**: `pytest` and `httpx` (Backend); `vitest` / React Testing Library (Frontend)

**Target Platform**: Modern Web Browsers (Chrome, Firefox, Safari) and Python 3.13+ runtime environment

**Project Type**: web-service / web-app

**Performance Goals**: N/A (replaces arbitrary performance thresholds with correctness, data consistency, and transactional atomic validation)

**Constraints**: Precise decimal math using Python `decimal.Decimal` (string representation in APIs), vanilla CSS layouts only (no Tailwind or CSS frameworks)

**Scale/Scope**: Pre-authenticated mock user with exactly 2 accounts and 2 pre-seeded history items

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Specification Authority (Principle I)**: PASS. No out-of-scope features are planned. External bank transfers, card payments, and loans are fully excluded.
- **Specification-First Changes (Principle II)**: PASS. Requirements and scope revisions were fully committed to `spec.md` before starting this plan.
- **Proportional Implementation (Principle III)**: PASS. No complex authentication, relational databases, or ORMs are introduced. Native SQLite and vanilla React styling keep implementation lightweight and stage-proportional.
- **Requirement-Driven Validation (Principle IV)**: PASS. Verification scenarios mapped to the specifications.
- **Strict Scope Compliance (Principle V)**: PASS. No UI display of internal database IDs, only friendly checking/savings labels.
- **Workflow & Tool Neutrality**: PASS. The plan outlines manual verification scenarios and lightweight testing compatible with experimental and tool-neutral standards.

## Project Structure

### Documentation (this feature)

```text
specs/001-shift-bank-stage1/
├── spec.md              # Feature specification
├── plan.md              # This file (Implementation Plan)
├── research.md          # Technical decisions and rationale
├── data-model.md        # SQLite database tables & state machine schema
├── quickstart.md        # Runnable verification scenario guide
└── contracts/
    └── api.md           # FastAPI REST API endpoint contract definitions
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api.py           # FastAPI REST endpoint routers
│   ├── database.py      # sqlite3 connection, migrations, and seed scripts
│   ├── main.py          # FastAPI application bootstrapper
│   ├── models.py        # Pydantic schemas utilizing string-decimal conversion
│   └── services.py      # Account balance and MFA state machine logic
├── requirements.txt     # Backend dependencies (fastapi, uvicorn, pytest)
└── tests/
    └── test_api.py      # Backend unit and integration tests

frontend/
├── src/
│   ├── App.css          # Vanilla CSS layout and component styling
│   ├── App.tsx          # Main React layout & state control
│   ├── main.tsx         # React DOM bootstrapper
│   ├── types.ts         # TypeScript interfaces for API integration
│   └── services.ts      # Fetch client for backend API communication
├── index.html           # HTML template
├── package.json         # Frontend dependencies (react, typescript, vite, vitest)
└── vite.config.ts       # Vite build configuration
```

**Structure Decision**: Selected a clear **Web Application Multi-project (Option 2)** directory separating `backend/` and `frontend/` as the project baseline to ensure clear domain logic and clean boundary separation.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*(No violations. 100% compliant with Shift Bank Constitution v1.2.0).*
