# Implementation Plan: Scientific Web Calculator & Extended State Management

**Branch**: `002-scientific-calculator` | **Date**: 2026-10-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-scientific-calculator/spec.md`

## Summary

This feature expands the existing basic arithmetic calculator into a fully-functional scientific web calculator. The backend AST evaluator is updated to securely whitelist and evaluate trigonometric, logarithmic, root, and power functions and constants, supporting instant degree/radian angle toggles via stateless payload extensions. Memory (M+, M-, MR, MC) and a side-drawer session calculation history are fully implemented on the frontend client-side to maintain a responsive tactile feel and respect strict API statelessness.

## Technical Context

**Language/Version**: Python 3.11+, TypeScript, React 18

**Primary Dependencies**: FastAPI, Pydantic, Vite

**Storage**: N/A (In-memory client state for history and memory register)

**Testing**: pytest (backend), React Testing Library / Vitest (frontend)

**Target Platform**: Modern Web Browsers (Desktop & Mobile viewports >= 320px)

**Project Type**: Web application (frontend + backend)

**Performance Goals**: p95 response time <100ms, instantaneous UI state updates (<50ms)

**Constraints**: Strict separation of concerns, high-precision decimal arithmetic (28-digit precision limit on transcendental operations), safe AST execution.

**Scale/Scope**: Standard single-page scientific calculator layout, lightweight in-memory session logging.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I: Exact Decimal Precision**: Compliant. All computations are handled via python's `decimal` module; transcendental evaluations are converted back to `Decimal` and normalized to prevent representation errors.
- [x] **Principle II: Strict PEMDAS Parsing**: Compliant. AST-based operator hierarchy ensures mathematically rigorous expression order.
- [x] **Principle III: Comprehensive Accessibility**: Compliant. ARIA-live regions, proper focus styling, explicit descriptive labels, and keyboard mapping are defined in design.
- [x] **Principle IV: RESTful Clean Architecture**: Compliant. The backend API is completely stateless. History, memory state, and angle variables are owned by the client React components, with evaluations delegated via POST requests.
- [x] **Principle V: Test-Driven Validation**: Compliant. Development plan dictates implementing backend evaluation updates and unit/contract test validation first, before modifying frontend code.

## Project Structure

### Documentation (this feature)

```text
specs/002-scientific-calculator/
├── plan.md              # This file
├── research.md          # Technical research and choices
├── data-model.md        # Explicit data interfaces & models
├── quickstart.md        # Verification and validation guide
└── contracts/
    └── v1-evaluate-post.json # API Request/Response schema contract
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       └── schemas.py
│   └── core/
│       └── evaluator.py
└── tests/
    ├── contract/
    └── unit/

frontend/
├── src/
│   ├── components/
│   │   └── Calculator.tsx
│   ├── services/
│   │   └── api.ts
│   ├── types/
│   │   └── index.ts
│   └── tests/
```

**Structure Decision**: The project follows a decoupled structure with a separate `backend` (FastAPI) and `frontend` (React + TS) to ensure clean separation of concerns.

## Complexity Tracking

> **No violations of the Basic Web Calculator Constitution were introduced. The system maintains a simple, stateless backend with all interactive session states managed elegantly on the client.**
