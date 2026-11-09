# Implementation Plan: Reverse Polish Notation (RPN) Engine and UI Migration

**Branch**: `004-rpn-calculator-refactor` | **Date**: 2026-10-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-rpn-calculator-refactor/spec.md`

## Summary
The goal of this feature is to refactor the core evaluation engine of the web calculator app to use a stack-based Reverse Polish Notation (RPN) evaluator. To support standard algebraic input, we will implement the Shunting Yard Algorithm on the backend, which converts infix expressions into postfix (RPN) tokens and evaluates them using the new stack engine. On the frontend, we will implement an RPN Dual Mode that allows direct RPN entry (displaying levels X, Y, Z, T, and providing an `ENTER` key) alongside the traditional Standard Mode.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.x / React 18+ (Frontend)

**Primary Dependencies**: FastAPI, Pydantic (Backend), React, Vite (Frontend)

**Storage**: N/A (Session-based calculation history and evaluation stack in-memory)

**Testing**: Pytest for backend unit and API testing, Vitest/Jest for frontend unit and component testing

**Target Platform**: Modern Web Browsers, Docker Containers

**Project Type**: Split Full-Stack Web Application (Frontend client + Backend REST API)

**Performance Goals**:
- Infix-to-postfix conversion and evaluation under 10ms.
- API roundtrip time under 50ms (excluding network latency).
- Frontend UI updates and RPN stack display transitions in under 100ms.

**Constraints**:
- Strict adherence to exact decimal precision (Python `Decimal` module) for all mathematical calculations.
- Strict WCAG 2.1 AA accessibility (a11y) standards (keyboard shortcuts, ARIA attributes, screen reader announcements).
- Total repository statement and branch code coverage must strictly remain at or above 80%.

**Scale/Scope**: 
- Standard algebraic infix expressions up to 1000 characters.
- Evaluation stack containing arbitrary numbers of elements (visualized up to 4 levels: X, Y, Z, T).
- Support for all Stage 2 scientific functions and constants (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sqrt`, `ln`, `log10`, `root`, `pi`, `e`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Gate I: Exact Decimal Precision**: **PASSED**. The backend RPN evaluator will utilize `Decimal` push/pop and evaluation, converting floats back to Decimal immediately and preventing float errors.
- **Gate II: PEMDAS Precedence**: **PASSED**. Standard mode will utilize the Shunting Yard Algorithm, which mathematically preserves strict PEMDAS precedence through operator precedence weights during infix-to-postfix translation.
- **Gate III: Accessibility & UX**: **PASSED**. The UI layout will preserve keyboard shortcuts, add RPN-specific shortcut mapping (such as `Enter` for pushing to stack and operator mappings), and maintain proper ARIA live announcement triggers.
- **Gate IV: RESTful Clean Architecture**: **PASSED**. Strict separation remains. The React client delegates evaluation to FastAPI `/api/v1/evaluate` with appropriate mode structures, keeping core computation on the backend.
- **Gate V: Test-Driven Validation**: **PASSED**. Pytest math tests will be created and verified before frontend UI component wiring is finalized.

## Project Structure

### Documentation (this feature)

```text
specs/004-rpn-calculator-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── contracts/           # Phase 1 output
    └── evaluation-api.json
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── v1/
│   │       ├── errors.py
│   │       ├── router.py
│   │       └── schemas.py
│   └── core/
│       ├── config.py
│       └── evaluator.py   # To be refactored to Shunting Yard + Stack-based engine
└── tests/
    └── unit/              # pytest math and API test suite

frontend/
├── src/
│   ├── components/
│   │   ├── ButtonGrid.tsx
│   │   ├── Calculator.tsx  # To support Standard/RPN dual modes and enter buttons
│   │   ├── Display.tsx
│   │   └── StackVisualizer.tsx # New visual stack component
│   ├── services/
│   │   └── api.ts
│   ├── types/
│   │   └── calculator.ts
│   └── App.tsx
└── src/tests/             # Frontend component and unit tests
```

**Structure Decision**: Option 2: Web application (Frontend + Backend split). The backend contains calculation and parsing routines, and the frontend handles the visual keyboard interactions, mode toggling, and the new visual RPN stack component.

## Complexity Tracking

*No violations of the Constitution are planned; hence no entries are required here.*
