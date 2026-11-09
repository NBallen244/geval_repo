---
title: Basic Web Calculator
status: draft
created: 2026-09-28
updated: 2026-09-28
---

# PRD: Basic Web Calculator

## 0. Document Purpose
This Product Requirements Document (PRD) establishes the single source of truth for the design, development, and testing of the Basic Web Calculator. It is structured for PMs, developers, and testers to ensure that the core principles of exact decimal precision, robust mathematical parsing, and excellent accessibility (a11y) are delivered consistently across the frontend (React/TypeScript) and backend (FastAPI/Python) services.

## 1. Vision
The Basic Web Calculator is a modern, high-precision, and highly accessible daily-use web application that mimics the layout of a physical desktop calculator. It addresses a common frustration with standard digital calculators: rounding errors in floating-point math (e.g., `0.1 + 0.2` yielding `0.30000000000000004`) and poor keyboard-only operation. By combining a robust, AST-based Python backend with an accessible and responsive React frontend, this calculator guarantees mathematically exact results for complex chained expressions while maintaining an elegant, physical-inspired, responsive layout.

## 2. Target User

### 2.1 Jobs To Be Done
- **Functional:** I need to perform daily financial, personal, and administrative arithmetic calculations (e.g., splitting a bill, calculating discounts, balancing a budget) quickly and with absolute confidence that the decimals are 100% exact.
- **Contextual/Interface:** I need to use the calculator seamlessly on my phone while on the go, or on my desktop computer using only my keyboard, without being slowed down by clicking with a mouse.
- **Emotional:** I want to feel confident that the system is executing standard mathematical precedence (PEMDAS) correctly without having to calculate sub-results individually.

### 2.2 Non-Users (v1)
- **Scientific/Engineering Users:** Users requiring advanced scientific functions (trigonometric functions, logarithms, matrix calculations, calculus, or complex number support).
- **Offline Desktop-only Users:** Users expecting a native, heavyweight desktop software package that works without any network connection (v1 requires API connectivity).

### 2.3 Key User Journeys

- **UJ-1: Elena calculates her weekly grocery share.**
  - **Persona + context:** Elena is a college student who splits grocery expenses with roomies and needs quick, precise calculations.
  - **Entry state:** She opens the calculator app on her phone; the screen shows `0` in the displays, with keyboard focus initialized on the calculator container.
  - **Path:**
    1. Elena taps the physical buttons on her phone screen or type on her keyboard to input: `(45.50 + 12.80 + 115) / 3`.
    2. As she inputs each token, the Primary Display updates to show `(45.50 + 12.80 + 115) / 3`.
    3. The Result Display shows a live preview of the calculation as she types.
    4. She taps the `=` button or hits the `Enter` key.
  - **Climax:** The Frontend Client sends a calculation request to the Backend Service, which evaluates the expression using exact decimal arithmetic. The Result Display updates to show the final exact value: `57.76666666666667` (or correctly formatted to standard high-precision, avoiding any float representation errors).
  - **Resolution:** The main display shifts the active expression into a secondary, small history line, and the value `57.76666666666667` remains on the display, ready to be cleared or used as the starting operand for her next calculation.
  - **Edge Case:** If Elena types `/ 0` by mistake, the Result Display immediately indicates `Error: Division by zero`, and the `=` button is disabled, prompting her to press `Backspace` or `Escape` to clear.

- **UJ-2: Marcus reconciles invoices using a keyboard.**
  - **Persona + context:** Marcus is an accountant who works exclusively with keyboard numeric pads for maximum data entry speed.
  - **Entry state:** Marcus opens the web calculator on his desktop monitor. The cursor is automatically focused on the calculator body.
  - **Path:**
    1. Without touching his mouse, Marcus uses his physical keyboard's numpad to type: `150.75 + 325.20 * 1.15`.
    2. The display updates immediately to match his keypresses, with high-contrast active styling indicating focus states.
    3. He presses `Enter` on his numpad.
  - **Climax:** The Backend Service processes the expression, strictly applying PEMDAS rules (`325.20 * 1.15` first, then adding `150.75`). The final evaluation of `524.73` is displayed instantly.
  - **Resolution:** He presses `Escape` to clear the displays and starts the next invoice calculation.

## 3. Glossary
- **Expression** — A mathematical string representing arithmetic operations to be evaluated (e.g., `12.5 + 3 * (4 - 1.5) / 2`).
- **Token** — The smallest individual unit of an Expression, representing either an Operand, an Operator, or a Parenthesis.
- **Operand** — A numeric value in an Expression, which can be an integer or a decimal number.
- **Operator** — A symbol representing an arithmetic operation (specifically `+`, `-`, `*`, `/`).
- **PEMDAS** — The standard order of operations: Parentheses, Exponents (not supported in v1), Multiplication, Division, Addition, Subtraction.
- **AST** — Abstract Syntax Tree, a tree representation of the syntactic structure of an Expression, used by the Backend Service for parsing and validation.
- **Primary Display** — The upper, larger display area of the calculator that shows the full, active Expression entered by the user.
- **Result Display** — The lower, dedicated display area of the calculator showing either the live calculation preview or the final exact Evaluation Result.
- **Evaluation Result** — The exact calculated decimal value of an Expression, produced by the Backend Service.

## 4. Features

### 4.1 Arithmetic & Logic Engine (Backend Service)
**Description:** The math evaluation core of the application must be written as a Python service. It is responsible for taking raw Expression strings, parsing them, validating that they conform to correct mathematical syntax, and evaluating them according to PEMDAS rules using exact decimal representation.

**Functional Requirements:**

#### FR-1: Expression Evaluation API Endpoint
The Backend Service must expose a RESTful HTTP endpoint `POST /api/v1/evaluate` accepting a JSON payload containing the mathematical Expression string. Realizes UJ-1, UJ-2.
**Consequences (testable):**
- System returns HTTP 200 with a JSON payload containing the exact result as a string/number when given a valid mathematical expression.
- System returns HTTP 422 with a JSON payload containing a clear error message when given an invalid mathematical expression.

#### FR-2: AST Parsing & PEMDAS Precedence
The evaluation engine must parse the Expression string into an Abstract Syntax Tree (AST) to validate and execute precedence rules strictly according to standard PEMDAS mathematical order.
**Consequences (testable):**
- Evaluating `10 + 2 * 5` must return exactly `20`.
- Evaluating `(10 + 2) * 5` must return exactly `60`.
- Parentheses nesting must be supported up to at least 10 levels deep.

#### FR-3: Exact Decimal Precision
All arithmetic operations within the Backend Service must be performed using arbitrary-precision decimals (e.g., Python's built-in `decimal` module) rather than standard IEEE-754 floating-point operations.
**Consequences (testable):**
- Evaluating `0.1 + 0.2` must return exactly `0.3`.
- Evaluating `1.0 - 0.9` must return exactly `0.1`.
- Trailing zeroes in decimal outputs must be preserved or handled consistently up to standard currency/desktop precision (e.g., user-configurable or reasonable default precision of 10+ digits).

#### FR-4: Safe Error and Edge Case Handling
The math engine must validate inputs and gracefully handle common mathematical errors, throwing descriptive messages rather than crashing.
**Consequences (testable):**
- Division by zero must return an error response: `Error: Division by zero`.
- Unbalanced parentheses must return an error response: `Error: Unbalanced parentheses`.
- Consecutive operators (e.g., `12 + * 3`) must return an error response: `Error: Invalid operator sequence`.

### 4.2 Physical-Style Responsive UI (Frontend Client)
**Description:** The user interface must mimic a physical, standard desktop calculator. It must fit perfectly on mobile, tablet, and desktop screens, presenting an intuitive grid of buttons along with clear screen readers and keyboard integration.

**Functional Requirements:**

#### FR-5: Physical-Inspired Grid Layout
The layout must feature a clean, physical-inspired visual grid representing a desktop calculator, with buttons for numbers (`0-9`), operators (`+`, `-`, `*`, `/`), brackets (`(`, `)`), decimals (`.`), clear (`C`/`AC`), delete (`Backspace`), and evaluate (`=`).
**Consequences (testable):**
- Grid adapts responsively using CSS grids/flexbox without layout breaking or clipped labels on viewport widths as small as 320px and as large as 3840px.
- Active states (hover, active, focus) must be visually distinct for all interactive grid buttons.

#### FR-6: Dual Display Outputs
The interface must feature two distinct display areas: the Primary Display (showing the active typed Expression) and the Result Display (showing the calculated Evaluation Result or live calculation preview). Realizes UJ-1.
**Consequences (testable):**
- Entering characters updates the Primary Display character-by-character in real-time.
- If the current Active Expression is mathematically complete, the Result Display must show a live grayed-out preview of the evaluation.
- Clicking `=` or pressing `Enter` updates the Result Display with high-contrast styling and pushes the evaluated Expression to a smaller, faded historical expression label above.

#### FR-7: Standard Keyboard Accessibility
The Frontend Client must listen to global keyboard events and bind corresponding actions to the physical keyboard keys, allowing keyboard-only users to operate the application without a mouse. Realizes UJ-2.
**Consequences (testable):**
- Pressing physical keys `0-9`, `.`, `+`, `-`, `*`, `/`, `(`, `)` must insert those characters into the Primary Display.
- Pressing `Enter` or `=` must trigger the REST API evaluation call.
- Pressing `Backspace` must delete the last character in the Primary Display.
- Pressing `Escape` must trigger an immediate reset (equivalent to clicking `AC`), clearing both displays.

#### FR-8: Screen Reader Integration (a11y)
The Frontend Client must include explicit accessibility attributes to support assistive technologies such as screen readers.
**Consequences (testable):**
- Every button on the grid has a descriptive `aria-label` (e.g., `aria-label="Add"` for `+`, `aria-label="Number 9"` for `9`).
- Display areas are wrapped in `aria-live="polite"` regions so changes to expressions and final results are read out automatically by screen readers.

## 5. Non-Goals (Explicit)
- **No Scientific Operations:** No scientific mathematical functions (trigonometry, logarithms, exponents, square roots) in v1.
- **No Local or Remote Persistence:** No user registration, authentication, database storage, or remote sync of calculation history.
- **No Multi-currency/Unit Conversions:** The calculator only processes raw numeric expressions and does not perform units, weights, or currency conversion.
- **No Local Execution Fallback:** The application requires an active connection to the Backend Service for math evaluation; offline standalone calculations are out of scope for v1.

## 6. MVP Scope

### 6.1 In Scope
- A responsive React + TypeScript frontend client running in modern web browsers (Chrome, Safari, Firefox, Edge).
- A Python + FastAPI backend service running mathematical parsing and arbitrary-precision calculations.
- Exact PEMDAS-compliant evaluation of chained expressions containing `0-9`, `.`, `+`, `-`, `*`, `/`, `(`, and `)`.
- Full physical keyboard integration and comprehensive WCAG-compliant screen reader support (ARIA tags).
- High decimal accuracy using Python's `decimal` module.
- 100% test coverage of mathematical precedence and decimal precision in backend unit tests (`pytest`).

### 6.2 Out of Scope for MVP
- Storing or displaying a persistent list of past calculation history (beyond the single active history slot).
- Keyboard shortcuts for clearing a single character versus resetting everything (using simple `Backspace` and `Escape` for now).
- Local mathematical parsing on the frontend via JavaScript (all validation and parsing is routed through the backend REST API).
- Custom UI theme switching (dark/light mode toggles are deferred to v2).

## 7. Success Metrics
- **SM-1 (Mathematical Accuracy):** 100% of arithmetic calculations in the test suite must return exact decimal values with zero floating-point rounding issues (e.g., `0.1 + 0.2` strictly evaluates to `0.3` under 100% of test runs). Validates FR-3.
- **SM-2 (Keyboard Usability):** 100% of mapped physical keys (`0-9`, standard operators, backspace, escape, enter) must trigger corresponding frontend state modifications within the application. Validates FR-7.
- **SM-3 (API Latency):** Backend API response latency for `POST /api/v1/evaluate` must be under 50ms for the 95th percentile under normal network conditions. Validates FR-1.
- **SM-C1 (Counter-Metric - Code Simplicity):** The math parsing code complexity must remain low and maintainable. We will avoid complex, handwritten lexical analysis tools if Python's built-in `ast` module or simple standard parsing libraries can solve the requirements safely, ensuring readability.

## 8. Open Questions
1. **Decimal Precision Limit:** Should we truncate results to a fixed number of decimal places (e.g., 10 or 15) to prevent infinite decimal representations (such as `1 / 3` giving `0.3333333333333333...`) from overflowing the responsive displays? We assume truncating to 12 decimal places with proper rounding is optimal for a standard desktop view.
2. **Dynamic Live Validation:** Should the frontend validate the expression as the user types before sending it to the backend, or should the backend perform all syntactical checks on each keypress (live evaluation preview)? We assume the frontend will send the expression to the backend for safe live preview evaluation only if it is structurally balanced.

## 9. Assumptions Index
- **[ASSUMPTION: Truncation]** We assume truncating evaluated decimals to 12 decimal places with standard mathematical rounding is acceptable to prevent UI overflow while maintaining superior accuracy.
- **[ASSUMPTION: REST for Live Preview]** We assume that sending the active expression to the `POST /api/v1/evaluate` endpoint on a debounced keypress is fast enough for the live preview feature, eliminating the need for a separate frontend parsing engine.
- **[ASSUMPTION: Single Active History Slot]** We assume that a single faded label showing the immediately preceding calculated expression is sufficient for daily use and fits within our physical desktop calculator aesthetic.
