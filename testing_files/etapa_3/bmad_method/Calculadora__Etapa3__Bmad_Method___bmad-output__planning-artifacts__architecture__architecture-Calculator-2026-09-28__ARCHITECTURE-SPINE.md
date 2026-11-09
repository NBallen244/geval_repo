---
name: Calculator Architecture Spine
type: architecture-spine
purpose: build-substrate
altitude: system
paradigm: Client-Server (Layered Architecture)
scope: Governs the frontend React client and the backend FastAPI service of the Scientific Web Calculator.
status: active
created: 2026-09-28
updated: 2026-10-23
binds:
  - FR-1
  - FR-2
  - FR-3
  - FR-4
  - FR-5
  - FR-6
  - FR-7
  - FR-8
  - FR-9
  - FR-10
  - FR-11
  - FR-12
sources:
  - {planning_artifacts}/prds/prd-Calculator-2026-09-28/prd.md
  - {planning_artifacts}/ux-designs/ux-Calculator-2026-09-28/DESIGN.md
  - {planning_artifacts}/ux-designs/ux-Calculator-2026-09-28/EXPERIENCE.md
companions:
  - ../../../specs/spec-calculator/code-inspection-report-stage-3.md
---

# Architecture Spine — Scientific Web Calculator

This document establishes the binding architectural invariants, boundaries, state mutation paths, and technical stacks for the Scientific Web Calculator. It is the definitive design substrate ensuring consistent, secure, and precise implementation.

---

## Design Paradigm

The system follows a strict **Layered Client-Server Paradigm** isolated in containerized environments:

```
+─────────────────────────────────────────────────────────────+
│ FRONTEND CONTAINER (Nginx Static Serve - Port 3000)        │
│   ┌──────────────────────────┐   ┌────────────────────────┐ │
│   │        View/UI           │   │    State Controller    │ │
│   │    (React Components)    │◄──┼───   (Event Hooks)     │ │
│   └────────────┬─────────────┘   └───────────▲────────────┘ │
+────────────────┼─────────────────────────────┼──────────────+
                 │ POST /api/v1/evaluate       │
                 ▼                             │ JSON Response
+──────────────────────────────────────────────┼──────────────+
│ BACKEND CONTAINER (FastAPI Server - Port 8000)             │
│   ┌──────────────────────────┐   ┌───────────┴────────────┐ │
│   │       API Router         │──►│       AST Engine       │ │
│   │    (REST Endpoints)      │   │  (Safe custom parsing) │ │
│   └──────────────────────────┘   └────────────────────────┘ │
+─────────────────────────────────────────────────────────────+
```

1. **Frontend Client Layer:** Manages physical grid components, custom state controllers (Idle, Active, Preview, Evaluated, Error), memory registers, and captures global keyboard events. It communicates via REST API payloads.
2. **Backend Service Layer:** A stateless, high-performance API service. It acts as the single source of mathematical truth, housing the Abstract Syntax Tree (AST) parsing and arbitrary-precision evaluation routines.

---

## Invariants & Rules

### AD-1 — Safe AST-Based Evaluation with High-Precision Decimals
- **Rule:** The calculation engine must parse mathematical expression strings into an Abstract Syntax Tree using Python's standard `ast` compiler and traverse nodes utilizing a custom `NodeVisitor` subclass. Operations must be evaluated strictly using Python's standard `decimal` module. Whitelisted nodes are strictly limited to `ast.Expression`, `ast.BinOp` (Add, Sub, Mult, Div, Pow), `ast.UnaryOp` (UAdd, USub), `ast.Constant`, `ast.Name` (constants pi and e), and `ast.Call` (functions sin, cos, tan, asin, acos, atan, sqrt, ln, log, log10). Raw string evaluations are strictly forbidden.

### AD-2 — Stateless HTTP API Communication
- **Rule:** The `POST /api/v1/evaluate` endpoint must remain completely stateless. All parameters (such as `expression` and `angle_unit`) must be passed in the request JSON payload, and the evaluated response must be returned in the immediate HTTP exchange.

### AD-3 — Global Keyboard Interception and Focus Trapping
- **Rule:** The Frontend Client must bind a global keydown event listener to the page window, trapping keys (`0-9`, `.`, operators, brackets, Backspace, Escape, and Enter). Default browser actions (e.g. Firefox Quick Find) must be intercepted using `event.preventDefault()`. Grid buttons have `tabIndex="-1"` to block focus leakage.

### AD-4 — Standardized JSON Error Payload Format
- **Rule:** All backend and frontend mathematical errors must be serialized into a consistent JSON payload structure returning status `error`, an `error_type` token, and a readable, user-facing error message starting exactly with `Error: <detail>`.

### AD-5 — Debounced Live Calculation Previews
- **Rule:** Active expression typing must debounce the REST API evaluation call by `300ms` for live previews. A preview query is only sent to the server if the parenthesizing within the expression is balanced.

### AD-6 — Secure Production Multi-Stage Containerization
- **Rule:** Both frontend and backend layers must be containerized using multi-stage `Dockerfile` definitions. The backend container must execute under a non-root system user (`appuser:appgroup` with UID `10001`). The frontend container must compile assets into raw static directories and serve them via high-performance, lightweight alpine-based Nginx servers configured with asset gzip compression and pushState routing configurations.

### AD-7 — Continuous Integration Quality Gates
- **Rule:** Statement and branch code coverage must meet or exceed **80%** across both the backend (`pytest-cov`) and frontend (`vitest`) codebases. Automated tests must execute and pass completely prior to continuous integration deployment runs.

---

## Stack

The following verified stacks form the core architectural foundation:

| Name | Version | Role |
| :--- | :--- | :--- |
| **Python** | 3.13 | Backend Runtime |
| **FastAPI** | ^0.110.0 | Backend REST API Framework |
| **Pytest / Pytest-cov** | ^8.0.0 | Backend Unit Testing & Coverage |
| **Node.js** | 20+ | Frontend Runtime |
| **React** | ^18.2.0 | Frontend UI Library |
| **TypeScript** | ^5.0.0 | Frontend Static Typing |
| **Vite** | ^4.4.5 | Frontend Build System and Bundler |
| **Vitest / jsdom / RTL** | ^1.6.0 | Frontend Unit & Integration Testing |
| **Nginx** | alpine | Production Static Frontend Server |
| **Docker / Docker Compose** | 3.8+ | Containerization & Orchestration |

---

## Structural Seed

```text
{project-root}/
  docker-compose.yml         # Unified local orchestration
  backend/
    Dockerfile               # Secure multi-stage FastAPI containerizer
    requirements.txt         # Runtime and test dependencies
    app/
      __init__.py
      main.py                # FastAPI initialization and global config
      routers/
        evaluate.py          # API route /api/v1/evaluate
      engine/
        parser.py            # AST mathematical syntax parser
        evaluator.py         # Custom SafeMathEvaluator (AST visitor)
    tests/
      test_api.py            # Integration tests for API endpoint
      test_engine.py         # Unit tests covering PEMDAS, constants, and trig bounds
  frontend/
    Dockerfile               # Secure multi-stage asset compiler and Nginx builder
    nginx.conf               # Lightweight static serve & pushState config
    package.json             # Dev dependencies including Vitest and RTL
    vite.config.ts           # Bundler and Vitest configuration
    src/
      main.tsx               # Client entry point
      App.tsx                # Layout shell centering the Calculator
      components/
        CalculatorFrame.tsx  # Outermost physical box frame & side drawer
        DisplayPanel.tsx     # Display screen wrapper containing active inputs/results
        ButtonGrid.tsx       # Standard and scientific layouts
        CalculatorButton.tsx # Tactical interactive buttons
      hooks/
        useKeyboard.ts       # Global keyboard event interception hook
        useEvaluate.ts       # Custom debounced API and memory state hook
      tests/
        useEvaluate.test.ts  # State transition, debounces, and memory unit tests
        CalculatorFrame.test.tsx # Keyboard capture, drawer, and UI integration tests
```

---

## Capability → Architecture Map

| Capability / Area | Lives in | Governed by |
| :--- | :--- | :--- |
| **AST Evaluation (CAP-1)** | `backend/app/engine/evaluator.py` | AD-1 (Safe AST-Based Evaluation) |
| **Arbitrary Precision (CAP-2)** | `backend/app/engine/evaluator.py` | AD-1 (Safe AST-Based Evaluation) |
| **Tactile Grid Layout (CAP-3)** | `frontend/src/components/ButtonGrid.tsx` | DESIGN.md.Layout |
| **Keyboard Interception (CAP-4)** | `frontend/src/hooks/useKeyboard.ts` | AD-3 (Global Keyboard Interception) |
| **Accessibility (CAP-5)** | `frontend/src/components/` | EXPERIENCE.md.Accessibility |
| **Error Handling (CAP-6)** | `backend/app/engine/parser.py` | AD-4 (Standardized JSON Error Payload) |
| **Scientific Operations (CAP-7)**| `backend/app/engine/evaluator.py` | AD-1 (AST whitelisted Call & Pow nodes) |
| **Memory register (CAP-8)** | `frontend/src/hooks/useEvaluate.ts` | FR-10 (High-Precision Memory Registers) |
| **Session History (CAP-9)** | `frontend/src/components/CalculatorFrame.tsx` | FR-11 (Side Drawer Panel Cache) |
| **Thorough Verification (CAP-10)**| `backend/tests/`, `frontend/src/tests/`| AD-7 (Test Coverage Quality Gates) |
| **Orchestrated Deploy (CAP-11)** | `docker-compose.yml`, `Dockerfile`s | AD-6 (Secure Containerization) |
