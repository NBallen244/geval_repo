---
title: Scientific Web Calculator
status: active
created: 2026-09-28
updated: 2026-10-23
---

# PRD: Scientific Web Calculator

## 0. Document Purpose
This Product Requirements Document (PRD) establishes the single source of truth for the design, development, testing, and deployment of the Scientific Web Calculator (expanded from the Basic Web Calculator MVP). It ensures that core mathematical exactness, advanced scientific functions, accessible design standards (WCAG 2.1 AA), and production containerization are delivered and maintained continuously.

## 1. Vision
The Scientific Web Calculator is a high-precision, highly accessible daily-use web application that mimics the layout and ergonomics of a physical desktop calculator. It addresses a common frustration with standard digital calculators: rounding errors in floating-point math (e.g., `0.1 + 0.2` yielding `0.30000000000000004`) and poor keyboard-only operation. By combining a secure AST-based arbitrary-precision Python backend with a responsive, accessible React frontend, this calculator guarantees mathematically exact results for standard arithmetic and complex scientific expressions alike.

## 2. Target User

### 2.1 Jobs To Be Done
- **Functional:** I need to perform daily financial, personal, and scientific calculations (e.g. compound interest, trigonometric angles, logarithms) quickly and with absolute confidence that the decimals are 100% exact.
- **Contextual/Interface:** I need to use the calculator seamlessly on my mobile screen while on the go, or on my desktop computer using only my keyboard, without being slowed down by clicking with a mouse.
- **Emotional:** I want to feel confident that the system is executing standard mathematical precedence (PEMDAS) and domain boundaries correctly, providing elegant warnings for impossible calculations.

### 2.2 Non-Users (v1)
- **Symbolic Math Users:** Users requiring symbolic algebra, calculus integrations, matrix solver tools, or graphing layouts (which are out of scope).
- **Offline Desktop-only Users:** Users expecting a native, heavyweight desktop software package that works without any network connection (this app operates under a client-server architecture).

### 2.3 Key User Journeys

- **UJ-1: Elena calculates her weekly grocery share.**
  - **Persona + context:** Elena is a college student who splits grocery expenses with roomies and needs quick, precise calculations.
  - **Path:** Elena opens the calculator app on her phone, inputs `(45.50 + 12.80 + 115) / 3`, and presses `=`.
  - **Climax:** The backend evaluates the expression using exact decimal arithmetic and returns `57.76666666666667`, avoiding any floating-point representation errors.

- **UJ-2: Marcus reconciles invoices using a keyboard.**
  - **Persona + context:** Marcus is an accountant who works exclusively with keyboard numeric pads for maximum data entry speed.
  - **Path:** Marcus uses his physical keyboard's numpad to type: `150.75 + 325.20 * 1.15` and presses `Enter`.
  - **Climax:** The system processes the expression applying PEMDAS rules strictly, displaying `524.73` instantly.

- **UJ-3: Physics student Sofia evaluates trigonometry in degrees.**
  - **Persona + context:** Sofia needs to calculate physical trigonometric bounds of waves in both radians and degrees quickly.
  - **Path:** Sofia opens the scientific keypad panel, toggles the unit mode from "RAD" to "DEG", enters `sin(90)`, and hits `=`.
  - **Climax:** The system correctly evaluates standard angles, returning `1` with exact decimal representation.

---

## 3. Glossary
*   **Expression** — A mathematical string representing arithmetic or scientific operations to be evaluated (e.g., `sin(pi / 2) + 2 ** 3`).
*   **Token** — The smallest individual unit of an Expression, representing either an Operand, an Operator, a Function Call, or a Parenthesis.
*   **Operand** — A numeric value in an Expression, representing an integer or an arbitrary-precision decimal number.
*   **Operator** — A symbol representing an arithmetic operation (specifically `+`, `-`, `*`, `/`, `**`).
*   **PEMDAS** — The standard order of operations: Parentheses, Exponents, Multiplication, Division, Addition, Subtraction.
*   **AST** — Abstract Syntax Tree, a tree representation of the syntactic structure of an Expression, used by the Backend Service for safe parsing and validation.
*   **Primary Display** — The upper, larger display area of the calculator screen that shows the full, active Expression constructed by the user.
*   **Result Display** — The lower, dedicated display area of the calculator screen showing either the live, debounced calculation preview or the final exact Evaluation Result.
*   **Evaluation Result** — The exact calculated decimal value of an Expression, produced by the Backend Service using the `decimal` module.
*   **Memory Register** — A client-side precision-preserving decimal register backing accumulation operations (`MC`, `MR`, `M+`, `M-`).

---

## 4. Features

### 4.1 Arithmetic, Scientific & Logic Engine (Backend Service)
**Description:** The math evaluation core of the application written as a stateless Python FastAPI service. It is responsible for taking raw Expression strings, parsing them securely using AST, validating mathematical boundaries, and evaluating them with absolute decimal precision.

**Functional Requirements:**
*   **FR-1: Expression Evaluation API Endpoint** - Expose `POST /api/v1/evaluate` accepting a JSON payload containing the mathematical Expression string and an optional `angle_unit` parameter.
*   **FR-2: AST Parsing & PEMDAS Precedence** - Parse the Expression into an AST using Python's standard `ast` compiler, resolving precedence strictly according to PEMDAS rules.
*   **FR-3: Exact Decimal Precision** - Perform all calculations via Python's standard `decimal` module; raw floating-point calculations are banned.
*   **FR-4: Safe Error and Edge Case Handling** - Validate inputs and gracefully handle common mathematical errors, throwing descriptive messages prefixed with `"Error: "`.
*   **FR-9: Advanced Scientific Functionality** - Securely whitelist and process scientific functions (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sqrt`, `ln`, `log10`) and constants (`pi`, `e`) inside the AST visitor without exposing RCE vectors.
*   **FR-10: High-Precision Client-Side Memory Accumulator** - Support precision-preserving addition and subtraction operations (`memory +/- displayed_number`) via the backend API.

### 4.2 Responsive & Accessible Scientific UI (Frontend Client)
**Description:** The user interface mimicking a physical, standard desktop calculator. It must fit perfectly on mobile, tablet, and desktop screens, presenting an intuitive dual-grid layout, visual indicators, active history drawer, and keyboard event mappings.

**Functional Requirements:**
*   **FR-5: Physical-Inspired Grid Layout** - Centered, tactile 4x5 standard grid that expands to include a scientific functions grid when toggled.
*   **FR-6: Dual Display Outputs** - Present a Primary Display (showing active character-by-character expressions) and a Result Display (showing live previews or final results).
*   **FR-7: Standard Keyboard Accessibility** - Capture global keydown events to operate standard digits, decimals, operators, Backspace, Escape, and Enter keys.
*   **FR-8: Screen Reader Integration (a11y)** - Provide WCAG 2.1 AA compliant descriptive `aria-label` tags, block button tab focus traversal (`tabIndex="-1"`), and configure polite `aria-live` announcement regions on displays.
*   **FR-11: Slide-Out Session Calculation History Drawer** - Cache successfully evaluated expressions in local memory, showing them in a sliding side drawer with quick actions to reload expressions or results back into the input display.

### 4.3 Containerization & Quality gates
*   **FR-12: Multi-Container Secure Packaging & Orchestration** - Package frontend and backend services into isolated, secure multi-stage Docker runtimes and orchestrate them using Docker Compose.

---

## 5. Non-Goals (Explicit)
*   **No Symbolic Math Solving:** No symbolic algebra or equation solver tools.
*   **No Multi-currency/Unit Conversions:** Conversions are strictly limited to Trigonometric Degrees/Radians.
*   **No Standalone Offline Operation:** The application requires active REST API connectivity; offline local evaluations are out of scope.

---

## 6. Success Metrics
*   **SM-1 (Mathematical Accuracy):** 100% of calculations in the test suite must return exact decimal values with zero floating-point rounding issues (e.g. `0.1 + 0.2` strictly evaluates to `0.3`).
*   **SM-2 (Keyboard Usability):** 100% of mapped physical keys must trigger corresponding state modifications.
*   **SM-3 (API Latency):** Backend API response latency for `POST /api/v1/evaluate` must be under 50ms for the 95th percentile under normal network conditions.
*   **SM-4 (Code Quality & Coverage Threshold):** Statement and branch code coverage must strictly meet or exceed **80%** across both the FastAPI backend (`pytest`) and React frontend (`vitest`) layers.
*   **SM-5 (Container Security & Portability):** Multi-stage production container deployment passes standard Docker Compose health check diagnostics and runs under non-privileged system accounts.
