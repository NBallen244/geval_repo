## Purpose

Enables scientific mathematical operations, constants, and memory register management on the Web Calculator with local session state persistence.

## Requirements

### Requirement: Advanced Scientific Math Evaluation
The backend and stack evaluation engine SHALL support evaluating trigonometric functions (sin, cos, tan, asin, acos, atan), logarithms (ln, log10), powers (**, square, base-10 power), and roots (square root, n-th root) with high precision. In RPN Mode, applying a unary scientific function (e.g., sin, ln, sqrt) SHALL pop the top value (X) from the stack, apply the function, and push the result back onto the stack. Applying a binary scientific operator (e.g., **, root) SHALL pop the top two values (X and Y), apply the function, and push the result back onto the stack.

#### Scenario: RPN scientific exponentiation evaluation
- **WHEN** user pushes "2", pushes "4", and applies power "**"
- **THEN** system evaluates operation and top of stack X displays "16"

#### Scenario: RPN scientific square root evaluation
- **WHEN** user pushes "9" and applies square root "sqrt"
- **THEN** system evaluates operation and top of stack X displays "3"

#### Scenario: RPN scientific domain error handling
- **WHEN** user pushes "-1" and applies square root "sqrt"
- **THEN** system returns an HTTP 400 Bad Request error stating "Math domain error"

### Requirement: Trigonometric Units (Radians and Degrees Toggle)
The calculator SHALL support toggling between Radians and Degrees modes, applying the selected mode to all trigonometric and inverse trigonometric computations.

#### Scenario: Sine evaluation in Radians
- **WHEN** user toggles angle unit to Radians and evaluates `sin(pi / 2)`
- **THEN** system returns exactly `1`

#### Scenario: Sine evaluation in Degrees
- **WHEN** user toggles angle unit to Degrees and evaluates `sin(90)`
- **THEN** system returns exactly `1`

### Requirement: Scientific Mathematical Constants
The calculator SHALL support quick input and evaluation of standard mathematical constants `pi` and `e`.

#### Scenario: Expression containing pi constant
- **WHEN** user evaluates `pi * 2`
- **THEN** system replaces `pi` with its high-precision value and returns the product

### Requirement: Local Memory Register System
The calculator SHALL provide a memory register supporting standard memory operations: M+ (add current display to memory), M- (subtract current display from memory), MR (recall memory), and MC (clear memory), displaying a visual "M" badge on screen whenever the stored value is non-zero.

#### Scenario: Memory add and recall operations
- **WHEN** user adds `5` to memory using `M+`, clears display, and presses `MR`
- **THEN** display displays `5` and active visual indicator shows "M" badge

### Requirement: Interactive Session Calculation History
The frontend SHALL provide an interactive history panel displaying previously evaluated expressions in the current active session. Users can click any historical entry to reload either the historical expression or its final result into the input display.

#### Scenario: Reloading historical expression
- **WHEN** user clicks on a historical calculation `10 + 20` in the history panel and selects expression reuse
- **THEN** the active input display is loaded with `10 + 20`

### Requirement: Enhanced Responsive Layout and Keyboard Mapping
The scientific calculator layout SHALL adapt to support RPN controls in scientific mode. In RPN Mode, pressing scientific keys on the virtual or physical keyboard (e.g., pressing "p" for pi, "e" for e constant) SHALL immediately push their respective values onto the stack. Unary and binary scientific keys (e.g., sqrt, ln) SHALL immediately execute on the stack's top values.

#### Scenario: Keyboard input of scientific constants in RPN Mode
- **WHEN** user is in RPN Mode and presses keyboard key "p"
- **THEN** high-precision value of pi is pushed onto the stack
