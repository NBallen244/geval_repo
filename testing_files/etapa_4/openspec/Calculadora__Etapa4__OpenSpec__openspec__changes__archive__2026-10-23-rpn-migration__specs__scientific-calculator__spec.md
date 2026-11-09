## MODIFIED Requirements

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

### Requirement: Enhanced Responsive Layout and Keyboard Mapping
The scientific calculator layout SHALL adapt to support RPN controls in scientific mode. In RPN Mode, pressing scientific keys on the virtual or physical keyboard (e.g., pressing "p" for pi, "e" for e constant) SHALL immediately push their respective values onto the stack. Unary and binary scientific keys (e.g., sqrt, ln) SHALL immediately execute on the stack's top values.

#### Scenario: Keyboard input of scientific constants in RPN Mode
- **WHEN** user is in RPN Mode and presses keyboard key "p"
- **THEN** high-precision value of pi is pushed onto the stack
