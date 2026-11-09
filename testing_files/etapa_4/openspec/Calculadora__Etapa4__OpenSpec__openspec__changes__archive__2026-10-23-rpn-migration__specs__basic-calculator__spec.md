## MODIFIED Requirements

### Requirement: Expression Evaluation with PEMDAS Precedence
The backend evaluation service SHALL support both Standard infix expression evaluation and stack-based Reverse Polish Notation (RPN) evaluation. Standard expressions containing addition, subtraction, multiplication, division, decimal points, and parenthesized sub-expressions SHALL be parsed using the Shunting Yard Algorithm to convert infix inputs into Postfix/RPN tokens, which are then evaluated via a dedicated stack-based execution engine. In RPN Mode, postfix/RPN expressions SHALL be processed directly by the stack-based evaluator.

#### Scenario: RPN stack-based evaluation
- **WHEN** user requests evaluation of RPN expression "3 4 2 * + 1 1 + -"
- **THEN** system evaluates expression and returns "9"

#### Scenario: Conversion of infix to RPN via Shunting Yard
- **WHEN** standard mode expression "3 + 4 * 2 - (1 + 1)" is converted and evaluated
- **THEN** system converts it to postfix tokens "3 4 2 * + 1 1 + -" and returns "9"

### Requirement: Dual-Display Responsive UI
The frontend interface SHALL support standard infix and RPN mode layouts, featuring a screen area with a real-time stack visualizer showing the active evaluation stack levels (X, Y, Z, T) when in RPN Mode. The UI SHALL dynamically adjust to desktop, tablet, and mobile viewport sizes without clipping content or causing horizontal overflow.

#### Scenario: Viewing responsive dual display in RPN Mode
- **WHEN** user toggles to RPN Mode on a mobile screen width of 375px
- **THEN** interface displays the active stack levels (X, Y, Z, T) and calculator grid without layout overflow

### Requirement: Comprehensive Keyboard Integration
The frontend application SHALL support complete physical keyboard input. In Standard Mode, pressing Enter or = evaluates the expression. In RPN Mode, pressing Enter SHALL push the current input value onto the stack, and pressing operator keys (+, -, *, /) SHALL immediately execute the operator on the stack's top values.

#### Scenario: Keyboard input and evaluation in RPN Mode
- **WHEN** user is in RPN Mode and presses keys "2", "Enter", "3", "Enter", "+"
- **THEN** the active stack level X displays "5"
