# Feature Specification: Reverse Polish Notation (RPN) Engine and UI Migration

**Feature Branch**: `004-rpn-calculator-refactor`

**Created**: 2026-10-25

**Status**: Draft

**Input**: User description: "Following the information described in @docs/SEED-4, lets start with the refactoring of the web calculator app."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - RPN Mode Stack Operations (Priority: P1)

As a power user who prefers stack-based calculations, I want to use the calculator in a dedicated RPN input mode so that I can perform complex formulas with fewer keystrokes and see the stack levels shift in real-time.

**Why this priority**: RPN stack-based input and calculation is the core requirement of Stage 4. Delivering this provides the absolute MVP of the new RPN-centric product vision.

**Independent Test**: Can be fully tested by selecting "RPN Mode" on the UI, pushing numbers onto the stack using the `ENTER` key (e.g., entering `12.5`, pressing `ENTER`, entering `3`, pressing `ENTER`, and then pressing `*` to multiply them to get `37.5`). The stack levels (X, Y, Z, T) and final result must reflect this state independently of Standard mode.

**Acceptance Scenarios**:

1. **Given** the calculator is in RPN Mode with an empty stack, **When** the user inputs `12.5` and clicks `ENTER`, **Then** the value `12.5` is pushed onto the stack and displayed as the active level X, and the input display is cleared for the next entry.
2. **Given** the calculator is in RPN Mode with `12.5` in stack level X, **When** the user inputs `3` and clicks `ENTER`, **Then** `3` is pushed to level X, and `12.5` shifts up to level Y.
3. **Given** the calculator is in RPN Mode with `3` in level X and `12.5` in level Y, **When** the user clicks the `*` operator, **Then** `3` and `12.5` are popped, multiplied precisely via high-precision decimal arithmetic to yield `37.5`, which is pushed onto level X of the stack, and level Y becomes empty.
4. **Given** the calculator is in RPN Mode with only one value `5` in level X, **When** the user clicks the `+` operator, **Then** a "Stack Underflow" error is gracefully shown to the user, and the stack remains unchanged.

---

### User Story 2 - Standard Mode Infix-to-RPN Conversion (Priority: P1)

As a standard user, I want to type traditional infix mathematical expressions (e.g. `12.5 + 3 * (4 - 1.5) / 2`) and have the backend parse and evaluate them using Shunting Yard conversion so that I get exact, standard-precedence decimal results without learning RPN syntax.

**Why this priority**: Standard infix calculations represent the backward-compatibility layer. It guarantees standard PEMDAS compliance while internally leveraging the new stack-based RPN engine.

**Independent Test**: Can be tested by typing `12.5 + 3 * (4 - 1.5) / 2` in Standard Mode and clicking `=`. The backend converts this infix string to postfix tokens, evaluates them on the stack, and returns the mathematically correct and precise result `16.25`.

**Acceptance Scenarios**:

1. **Given** the calculator is in Standard Mode, **When** the user inputs `12.5 + 3 * (4 - 1.5) / 2` and clicks `=`, **Then** the display shows the high-precision result `16.25`.
2. **Given** the calculator is in Standard Mode, **When** the user inputs `1 / 3 * 3` and clicks `=`, **Then** the display shows the exact high-precision decimal value `1` (avoiding float precision issues like `0.99999999999999`).
3. **Given** the calculator is in Standard Mode, **When** the user inputs an unclosed parenthesis like `(2 + 3`, **Then** a "Syntax Error: Unclosed parentheses" is displayed.

---

### User Story 3 - Real-Time Stack Visualizer UI (Priority: P2)

As a visual-focused user, I want to see a graphical stack display showing the values currently stored in stack levels X, Y, Z, and T so that I always know the exact operational state of the calculator.

**Why this priority**: This directly satisfies the requirement for a real-time stack visualizer. It enhances user confidence and provides crucial visual feedback in RPN Mode.

**Independent Test**: Can be tested by switching to RPN Mode and executing operations, verifying that the on-screen levels change immediately as numbers are pushed or operations are performed.

**Acceptance Scenarios**:

1. **Given** the calculator is in RPN Mode, **When** no values have been entered, **Then** the stack visualizer displays empty levels for `T:`, `Z:`, `Y:`, and `X:`.
2. **Given** the calculator is in RPN Mode, **When** the user pushes `42` onto the stack, **Then`X:` immediately displays `42.0` (or `42`), and `Y:`, `Z:`, `T:` are empty.
3. **Given** the stack has four values (e.g. `10` in X, `20` in Y, `30` in Z, `40` in T), **When** a fifth value `50` is pushed, **Then** the stack grows dynamically to hold all five values, with `50` occupying the new active level X, `10` shifting to Y, `20` to Z, `30` to T, and the old level T value `40` shifting to level T+1 (hidden from the 4-level display but preserved in the underlying evaluation array).

---

### Edge Cases

- **Stack Underflow**: When a binary operator (e.g., `+`, `-`, `*`, `/`) is applied with fewer than 2 operands on the stack, or a unary operator (e.g., `sin`, `sqrt`) is applied with an empty stack. The system must raise a clear `STACK_UNDERFLOW` error and not crash.
- **Division by Zero in Stack**: When the top stack value (X) is `0` and a division `/` operator is clicked. The system must raise a `DIVISION_BY_ZERO` error and preserve the original stack state.
- **Fractional Power of Negative Numbers**: Performing powers like `-8` raised to `1/3` (cube root) via RPN. The system must handle exact root functions and raise a `DOMAIN_ERROR` only for truly undefined operations (such as even roots of negative numbers).
- **Infinite Stack Overflow**: Pushing a large number of values onto the stack. The stack display should limit levels, or the stack size should be bounded to prevent memory leakage.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The backend mathematical evaluation engine MUST perform all numerical operations using a stack-based execution pattern.
- **FR-002**: The backend MUST implement the Shunting Yard Algorithm to parse infix expressions (e.g. standard mathematical input string), translate them into an equivalent postfix (RPN) token sequence, and evaluate them via the stack engine.
- **FR-003**: The backend MUST preserve high-precision decimal math (`Decimal` logic) for all stack-based operations (push, pop, unary and binary calculations), preventing any float-based representation or approximation errors.
- **FR-004**: The backend API `/api/v1/evaluate` MUST accept an optional `mode` parameter in the request payload containing values `"standard"` or `"rpn"`, defaulting to `"standard"`.
- **FR-005**: In RPN mode, the backend evaluator MUST process space-separated postfix tokens (e.g. `3 4 +` or `pi 2 / sin`) using the stack execution engine, returning the final stack top value.
- **FR-006**: The backend evaluator MUST support all scientific functions and constants (e.g., `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sqrt`, `ln`, `log10`, `root`, `pi`, `e`) as unary or binary operators operating on the evaluation stack.
- **FR-007**: The frontend UI MUST support switching between Standard Infix Input ("Standard Mode") and RPN Stack-Based Input ("RPN Mode") via a clearly marked mode selector toggle.
- **FR-008**: In RPN Mode, the frontend UI MUST provide an `ENTER` button (and bind the physical keyboard `Enter` key) to push the current input display value onto the RPN evaluation stack.
- **FR-009**: In RPN Mode, clicking any operator or scientific function key MUST immediately trigger the evaluation of that operator on the stack, popping the required arguments, computing the result, pushing it back, and displaying it.
- **FR-010**: The frontend UI MUST include a real-time visual stack display showing the active levels (X, Y, Z, T) of the RPN evaluation stack when in RPN Mode.
- **FR-011**: All features MUST maintain accessibility (a11y) compliance, providing clear focus styles, screen reader announcements via ARIA live regions, and full keyboard control (numbers, operators, enter/evaluate, backspace, escape) for both Standard and RPN modes.
- **FR-012**: Total test coverage (backend statement and branch coverage, frontend test coverage) MUST remain strictly at or above 80%.

### Key Entities *(include if feature involves data)*

- **Evaluation Stack**: A Last-In-First-Out (LIFO) collection of High-Precision Decimals representing the current state of RPN evaluation.
- **Infix Expression**: A string representation of mathematical formulas following algebraic notation (e.g., `a + b * c`), parsed using operators and parentheses.
- **Postfix Token Sequence**: An ordered list of numerical operands, constants, and operators arranged in Reverse Polish Notation (e.g., `a b c * +`), ready for direct stack evaluation.
- **Calculator State**: The persistent structure representing the current active mode (Standard vs RPN), the current stack, the active display expression, and the angle measurement unit (radians vs degrees).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of infix math expressions evaluated in Standard Mode must produce identical numerical results to standard algebraic calculators, adhering to strict PEMDAS precedence.
- **SC-002**: All RPN stack calculations must run with absolute precision using Python's `Decimal` type, guaranteeing that `0.1 0.2 +` evaluates to exactly `0.3`.
- **SC-003**: The real-time stack visualizer in the React frontend must update its displayed X, Y, Z, T levels in under 100ms after any push or operator event.
- **SC-004**: Users must be able to switch between Standard Mode and RPN Mode with 0% data loss of their current inputs or stored memory register.

## Assumptions

- **Target Users**: Users are either standard users expecting algebraic PEMDAS calculations or power/technical users expecting stack-based postfix execution.
- **Scope Boundaries**: Standard desktop/mobile web viewports are supported. Complex graphing or programming RPN functions (such as matrix operations or custom RPN macros) are out of scope for this stage.
- **Data/Environment**: The pre-existing memory register operations (`M+`, `M-`, `MR`, `MC`) and history drawer remain fully integrated and will save the final computed result of both Standard and RPN modes.
- **Physical Keyboard Integration**: Keyboard keys `+`, `-`, `*`, `/` and `Enter` are automatically mapped to their respective operations based on the active mode (e.g., `Enter` evaluates in Standard Mode, but acts as stack `ENTER` push in RPN Mode).
