# Feature Specification: Scientific Web Calculator & Extended State Management

**Feature Branch**: `002-scientific-calculator`

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: "Following the indications and instructions described in @"C:\Users\nicol\OneDrive\Documents\Proyecto de Grado\sdd-comparative-study\Calculadora\Etapa 1\Spec Kit\docs\SEED-2.md" , expand the functionality of the current Web Calculator app."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Advanced Mathematical Evaluation with Angle Toggle (Priority: P1)

As a student or scientific user, I want to evaluate advanced mathematical expressions (trigonometric, logs, powers, roots, and constants) using degrees or radians, so that I can perform scientific calculations with high decimal precision.

**Why this priority**: Essential scientific operations form the foundation of a scientific calculator; without these core math features, the app cannot serve scientific calculation needs.

**Independent Test**: Can be fully tested by evaluating standard scientific math expressions (e.g., `sin(pi/2)`, `3^3`, `sqrt(25)`, `ln(e)`) and toggling the angle unit mode (Radians vs. Degrees) to verify correct results and error handling without using memory or history features.

**Acceptance Scenarios**:

1. **Given** the calculator is in Radians mode, **When** the expression `sin(pi / 2)` is evaluated, **Then** the result displays `1`.
2. **Given** the calculator is in Degrees mode, **When** the expression `sin(90)` is evaluated, **Then** the result displays `1`.
3. **Given** the calculator is in Radians mode, **When** the expression `cos(pi)` is evaluated, **Then** the result displays `-1`.
4. **Given** the calculator is in Degrees mode, **When** the expression `cos(180)` is evaluated, **Then** the result displays `-1`.
5. **Given** the expression `3 ^ 2` is evaluated, **Then** the result displays `9`.
6. **Given** the expression `sqrt(16)` is evaluated, **Then** the result displays `4`.
7. **Given** the expression `ln(e)` is evaluated, **Then** the result displays `1`.
8. **Given** the expression `sqrt(-4)` is evaluated, **When** the user clicks evaluate, **Then** a friendly error message "Domain Error: Square root of a negative number" is shown.
9. **Given** the expression `log10(0)` is evaluated, **When** the user clicks evaluate, **Then** a friendly error message "Domain Error: Logarithm of zero or negative number" is shown.

---

### User Story 2 - Memory Register System (Priority: P2)

As a frequent calculator user, I want to store intermediate results in a memory register using standard operations (M+, M-, MR, MC) and see a visual indicator of stored values, so that I can reuse calculated figures across multiple steps.

**Why this priority**: Memory operations are high value for multi-step calculations but operate independently of the core mathematical parsing engine.

**Independent Test**: Can be fully tested by entering numeric values, triggering `M+`/`M-` operations, verifying the appearance of the "M" badge on screen, recalling the stored value using `MR`, and clearing it using `MC` to verify the "M" badge disappears.

**Acceptance Scenarios**:

1. **Given** the active display is showing `25`, **When** the user clicks the `M+` button, **Then** the internal memory register value increases by `25` and a visual "M" badge/indicator is displayed on screen.
2. **Given** the active display is showing `10`, the memory register has `25`, and the "M" badge is visible, **When** the user clicks the `M-` button, **Then** the internal memory register value is reduced to `15` and the "M" badge remains visible.
3. **Given** the active expression input is empty, the memory register contains `15`, and the "M" badge is visible, **When** the user clicks the `MR` button, **Then** the value `15` is loaded back into the active expression display.
4. **Given** the memory register contains `15` and the "M" badge is visible, **When** the user clicks the `MC` button, **Then** the memory register is reset to zero and the "M" badge disappears from the screen.

---

### User Story 3 - Interactive Session Calculation History (Priority: P3)

As an analytical user, I want to see a history of all calculations performed during my session in a collapsible panel, and reload past expressions or results back into my active workspace, so that I don't have to retype complex formulas.

**Why this priority**: History panel provides significant convenience and enhances user experience but is non-blocking for executing calculations or managing memory.

**Independent Test**: Can be fully tested by performing multiple evaluations, checking that they populate the sidebar panel, clicking on either the formula or result of a historical item to load it into the input, and clearing the history log with a button.

**Acceptance Scenarios**:

1. **Given** the user has evaluated `5 + 5` (resulting in `10`), **When** they look at the session history panel, **Then** they see an entry displaying `5 + 5 = 10`.
2. **Given** the history panel has the entry `5 + 5 = 10` and the input expression is empty, **When** the user clicks on the expression part `5 + 5` in the history, **Then** `5 + 5` is loaded back into the active input expression display.
3. **Given** the history panel has the entry `5 + 5 = 10` and the input expression is empty, **When** the user clicks on the result part `10` in the history, **Then** `10` is loaded back into the active input expression display as a number.
4. **Given** multiple entries exist in the history panel, **When** the user clicks the "Clear History" button, **Then** all history records are deleted and the history panel becomes empty.

---

### Edge Cases

- **Exponentiation with fractional/negative powers**: For operations like `(-2) ^ 0.5`, the system must catch complex/imaginary number results and return a clean math domain error.
- **Out of range inverse trigonometric inputs**: For calculations like `asin(2)` or `acos(-1.5)`, the system must return a clean "Domain Error: Input must be between -1 and 1."
- **Division by zero in scientific formulas**: In nested structures like `sin(pi) / (5 - 5)`, the system must correctly evaluate the denominator first, identify the zero-divisor, and raise a `DIVISION_BY_ZERO` error.
- **Nested trigonometric operations**: Evaluating nested functions like `sin(cos(tan(0.5)))` must adhere strictly to inner-to-outer evaluation rules and maintain high decimal precision.
- **Extremely large outputs (Overflow)**: Very large numerical inputs or power operations like `10 ^ 100000` must raise an arithmetic overflow error gracefully instead of crashing the backend server.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: **Advanced Math Evaluation Engine**: The mathematical engine MUST support trigonometric functions (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`), power operations ($x^y$, $x^2$, $10^x$), root operations ($\sqrt{x}$, $\sqrt[y]{x}$), logarithmic operations ($\ln$, $\log_{10}$), and standard constants ($\pi$, $e$).
- **FR-002**: **Angle Units Mode**: The system MUST support toggling between Degrees and Radians modes. Trigonometric functions MUST evaluate expressions using the selected angle unit mode.
- **FR-003**: **Mathematical Sandbox Security**: The backend mathematical engine MUST strictly validate mathematical expression syntax via safe AST parsing and whitelist allowed functions, operators, and constants, blocking any unsupported or unsafe operations.
- **FR-004**: **Precision and Normalization**: Calculations MUST utilize Python's `decimal` module for high precision (at least 28 decimal digits) and avoid floating-point representation errors. Chained operations MUST be normalized to strip redundant trailing zeros from results.
- **FR-005**: **Graceful Domain Error Handling**: Mathematical domain errors (e.g., division by zero, square root of negative numbers, logarithms of non-positive numbers, inverse trigonometric functions of out-of-range values) MUST be caught and returned as user-friendly error payloads.
- **FR-006**: **Memory Register Operations**: The UI MUST provide memory buttons: `M+` (adds current display value to memory register), `M-` (subtracts current display value from memory register), `MR` (recalls the memory register value into the expression), and `MC` (clears the memory register to zero).
- **FR-007**: **Visual Memory Indicator**: The display MUST show a distinct, accessible "M" badge/indicator whenever the memory register contains a non-zero value.
- **FR-008**: **Session Calculation History**: The UI MUST feature an interactive history panel/drawer listing all expressions evaluated in the current session alongside their final results.
- **FR-009**: **Interactive History Recall**: Users MUST be able to click on any history item to reload either the full evaluated expression or the final result back into the main input expression field.
- **FR-010**: **History Lifespan & Clearing**: Session history MUST persist in-memory across normal calculations within the active session, and a "Clear History" button MUST be provided to clear all historical records.
- **FR-011**: **Keyboard Shortcuts Mapping**: Keyboard support MUST be expanded to include hotkeys/shortcuts for scientific operations (e.g., `^` or `**` for power, keys/combinations for trig/log functions, memory recall/clear, and constants).
- **FR-012**: **Responsive Scientific Layout Grid**: The layout MUST automatically scale to display a standard 4-column keypad on mobile screens with a collapsible scientific keypad option (via a "Scientific" toggle button), and show a full expanded scientific grid on desktop screens without overcrowding or clipping.

### Key Entities *(include if feature involves data)*

- **CalculationSession**: Represents the current in-memory state of the user's interaction.
  - Attributes:
    - `history`: List of evaluated expressions and results.
    - `memory_register`: Highly precise numeric decimal value.
    - `angle_unit`: Enum (`radians` or `degrees`).
    - `current_expression`: The active expression string input.
- **HistoryItem**: Individual calculation record in the session history.
  - Attributes:
    - `id`: Unique identifier for tracking and interaction.
    - `expression`: String representing the evaluated math expression.
    - `result`: String representing the final precise computed result.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Standard and scientific expressions (e.g., `sin(pi/6)` or `2^10`) are evaluated with exact precision (verified via test assertions matching exact Decimal values) in under 200ms.
- **SC-002**: Toggling the angle mode between Degrees and Radians adjusts trigonometric evaluations instantly (within 100ms on screen) without page reload.
- **SC-003**: 100% of mathematical domain errors (e.g., log of negative, sqrt of negative, div by zero) display a user-friendly error message rather than a raw server stack trace or crash.
- **SC-004**: Memory operations (`M+`, `M-`, `MR`, `MC`) and history drawer updates occur with zero layout clipping or responsive breakdown on mobile (width >= 320px) and desktop (width >= 1024px) screens.

## Assumptions

- **Target Platform**: Modern, evergreen web browsers (Chrome, Firefox, Safari, Edge).
- **Session Lifespan**: Session history and memory are managed entirely in frontend client-side memory (React state) and do not persist across page reloads (browser refreshes), which aligns with the stateless backend service.
- **API Statelessness**: The backend `POST /api/v1/evaluate` API remains stateless. To evaluate trigonometric expressions, the frontend passes both the `expression` and the current `angle_unit` (e.g., `radians` or `degrees`) in the request payload.
- **Keyboard Shortcuts Accessibility**: Focus outlines and keyboard event handlers are defined to support full ARIA standards and keyboard-only operation, enabling complete accessibility.
