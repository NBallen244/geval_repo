---
name: Calculator Architecture Spine
type: architecture-spine
purpose: build-substrate
altitude: system
paradigm: Client-Server (Layered Architecture)
scope: Governs the frontend React client and the backend FastAPI service of the Basic Web Calculator.
status: draft
created: 2026-09-28
updated: 2026-09-28
binds:
  - FR-1
  - FR-2
  - FR-3
  - FR-4
  - FR-5
  - FR-6
  - FR-7
  - FR-8
sources:
  - {planning_artifacts}/prds/prd-Calculator-2026-09-28/prd.md
  - {planning_artifacts}/ux-designs/ux-Calculator-2026-09-28/DESIGN.md
  - {planning_artifacts}/ux-designs/ux-Calculator-2026-09-28/EXPERIENCE.md
companions: []
---

# Architecture Spine — Basic Web Calculator

This document establishes the binding architectural invariants, boundaries, state mutation paths, and technical stacks for the Basic Web Calculator. It is the definitive design substrate for developers and subagents to ensure consistent, secure, and precise implementation.

---

## Design Paradigm

The system follows a strict **Layered Client-Server Paradigm** with clearly separated frontend and backend responsibilities:

```
+─────────────────────────────────────────────────────────────+
│ FRONTEND CLIENT (React/TypeScript)                          │
│   ┌──────────────────────────┐   ┌────────────────────────┐ │
│   │        View/UI           │   │    State Controller    │ │
│   │    (React Components)    │◄──┼───   (Event Hooks)     │ │
│   └────────────┬─────────────┘   └───────────▲────────────┘ │
+────────────────┼─────────────────────────────┼──────────────+
                 │ POST /api/v1/evaluate       │
                 ▼                             │ JSON Response
+──────────────────────────────────────────────┼──────────────+
│ BACKEND SERVICE (FastAPI/Python)             │              │
│   ┌──────────────────────────┐   ┌───────────┴────────────┐ │
│   │       API Router         │──►│       AST Engine       │ │
│   │    (REST Endpoints)      │   │  (Safe custom parsing) │ │
│   └──────────────────────────┘   └────────────────────────┘ │
+─────────────────────────────────────────────────────────────+
```

1. **Frontend Client Layer:** Manages physical grid components, UI state (Idle vs Active Input vs Error states), and captures global keyboard events. It communicates exclusively via REST API payloads and remains visually and behaviorally decoupled from mathematical parsing.
2. **Backend Service Layer:** A stateless, high-performance API service. It acts as the single source of mathematical truth, housing the Abstract Syntax Tree (AST) parsing and arbitrary-precision evaluation routines.

---

## Invariants & Rules

The invariants below represent non-negotiable structural and behavioral limits.

### AD-1 — Safe AST-Based Evaluation with High-Precision Decimals
- **Binds:** Backend Service Math Engine, FR-2, FR-3, FR-4
- **Prevents:** Execution of unsafe code via standard Python `eval()` (Remote Code Execution vulnerability) and floating-point approximation inaccuracies (e.g., `0.1 + 0.2` rounding issues).
- **Rule:** The calculation engine must parse mathematical expression strings into an Abstract Syntax Tree using Python's standard `ast` compiler and traverse nodes utilizing a custom `NodeVisitor` subclass. Operations must be evaluated strictly using Python's standard `decimal` module, returning values serialized as high-precision strings (e.g. `"16.25"`). Standard float-based division is prohibited in calculation paths.

### AD-2 — Stateless HTTP API Communication
- **Binds:** Backend Service API Router, FR-1
- **Prevents:** State mismatches, memory overhead, or persistent user sessions on the server.
- **Rule:** The `POST /api/v1/evaluate` endpoint must remain completely stateless. All parameters necessary to process an expression must be passed in the request JSON payload, and the evaluated response must be returned in the immediate HTTP exchange without maintaining server-side memory or storage.

### AD-3 — Global Keyboard Interception and Focus Trapping
- **Binds:** Frontend Client Event Handlers, FR-7
- **Prevents:** Latency, focus shifting out of the application container, and standard browser shortcuts overriding calculator controls.
- **Rule:** The Frontend Client must bind a global keydown event listener to the page window, trapping and capturing keys (`0-9`, `.`, `+`, `-`, `*`, `/`, `(`, `)`, `Enter`, `Backspace`, `Escape`). Default browser actions (e.g. Firefox Quick Find) must be intercepted using `event.preventDefault()` to maintain keyboard-only focus on the calculator.

### AD-4 — Standardized JSON Error Payload Format
- **Binds:** API Error Responses, FR-4, FR-6
- **Prevents:** Cryptic system trace leaks and inconsistent UI error banners.
- **Rule:** All backend and frontend mathematical errors must be serialized into a consistent JSON payload structure. The server must return a structured response with status `error`, a specific `error_type` token (e.g. `division_by_zero`, `unbalanced_parentheses`), and a readable, user-facing error message starting exactly with `Error: <detail>`.

### AD-5 — Debounced Live Calculation Previews
- **Binds:** Frontend Client Live Preview Hook, FR-6
- **Prevents:** Network flood/spam on every single keystroke.
- **Rule:** Active expression typing must debounce the REST API evaluation call by `300ms` for live previews. A preview query is only sent to the server if the parenthesizing within the expression is balanced (e.g., matching open/close bracket counts).

---

## Consistency Conventions

These conventions govern the development layers to prevent code design drift:

| Concern | Convention |
| :--- | :--- |
| **Naming Conventions** | • Backend API files and endpoint routers: `snake_case` (e.g. `main.py`, `/api/v1/evaluate`).<br>• Custom AST classes and visitors: `PascalCase` (e.g. `DecimalEvaluator`).<br>• Frontend component directories and React hooks: `PascalCase` components, `camelCase` hooks (e.g. `useKeyboardInterception.ts`). |
| **Data & Formats** | • API payloads: Exact matching keys (request `"expression"`; response `"result"`).<br>• Decimal string format: Decimals are serialized as strings in JSON payloads to prevent browsers from corrupting float representations during browser-side parsing. |
| **State & Cross-Cutting** | • Error handling: Catch specific mathematical and parsing exceptions in a dedicated exception handler and convert them into standard HTTP 422 responses.<br>• Theme toggling: Automatic preference styling based strictly on `@media (prefers-color-scheme: dark)`. |

---

## Stack

The following verified stacks form the core architectural foundation:

| Name | Version | Role |
| :--- | :--- | :--- |
| **Python** | 3.11+ | Backend Runtime |
| **FastAPI** | ^0.100.0 | Backend REST API Framework |
| **Pytest** | ^7.4.0 | Backend Unit Testing Suite |
| **Node.js** | 18+ / 20+ | Frontend Runtime |
| **React** | ^18.2.0 | Frontend UI Library |
| **TypeScript** | ^5.0.0 | Frontend Static Typing |
| **Vite** | ^5.0.0 | Frontend Build System and Bundler |

---

## Structural Seed

```text
{project-root}/
  backend/
    app/
      __init__.py
      main.py                # FastAPI initialization and global config
      routers/
        __init__.py
        evaluate.py          # API route /api/v1/evaluate
      engine/
        __init__.py
        parser.py            # AST mathematical syntax parser
        evaluator.py         # Custom DecimalEvaluator (AST visitor)
    tests/
      test_api.py            # Integration tests for endpoint payloads
      test_engine.py         # Unit tests covering PEMDAS and decimals
  frontend/
    public/                  # Static assets and icons
    src/
      main.tsx               # Client entry point
      App.tsx                # Layout shell centering the Calculator frame
      components/
        CalculatorFrame.tsx  # Outermost physical box frame
        DisplayPanel.tsx     # Display screen wrapper containing active inputs/results
        ButtonGrid.tsx       # 4x5 layout container for interactive buttons
        CalculatorButton.tsx # Tactical interactive buttons
      hooks/
        useKeyboard.ts       # Global keyboard event interception hook
        useEvaluate.ts       # Debounced debounced API integration hook
      types/
        api.ts               # Shared TypeScript API contracts
      styles/
        index.css            # Responsive layouts and custom physical depths
```

---

## Capability → Architecture Map

| Capability / Area | Lives in | Governed by |
| :--- | :--- | :--- |
| **Expression Evaluation (FR-1)** | `backend/app/routers/evaluate.py` | AD-2 (Stateless HTTP API) |
| **Precedence & AST (FR-2)** | `backend/app/engine/evaluator.py` | AD-1 (Safe AST-Based Evaluation) |
| **Exact Decimal Math (FR-3)** | `backend/app/engine/evaluator.py` | AD-1 (Safe AST-Based Evaluation) |
| **Edge-Case Safety (FR-4)** | `backend/app/engine/parser.py` | AD-4 (Standardized JSON Error Payload) |
| **Numpad Grid View (FR-5)** | `frontend/src/components/ButtonGrid.tsx` | DESIGN.md.Layout |
| **Dual Displays (FR-6)** | `frontend/src/components/DisplayPanel.tsx` | AD-5 (Debounced Live Calculations) |
| **Keyboard Interception (FR-7)** | `frontend/src/hooks/useKeyboard.ts` | AD-3 (Global Keyboard Interception) |
| **Screen Reader Accessibility (FR-8)** | `frontend/src/components/` | EXPERIENCE.md.Accessibility |

---

## Deferred

The following decisions are deferred to the execution/development cycles:

1. **Server Host and Deployment Pipeline:** Pinned deployment parameters (Docker configurations, server providers like Fly.io, Vercel, or AWS, and CI workflows) are deferred until prototype validation is successful.
2. **Client-Side Fallback Parser:** Hand-rolling a local JavaScript math parser to evaluate math offline is deferred to v2. The MVP requires a network connection to perform backend operations.
3. **Manual Light/Dark Mode Selector:** UI manual overrides (a switch button) are deferred to v2. The system relies on native browser preferences in v1.
