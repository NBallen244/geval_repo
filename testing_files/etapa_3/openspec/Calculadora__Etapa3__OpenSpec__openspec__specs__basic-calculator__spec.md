## Purpose

Provides a responsive, highly accessible web calculator that accurately processes chained arithmetic expressions with exact decimal precision via a FastAPI backend and interactive React frontend.

## Requirements

### Requirement: Expression Evaluation with PEMDAS Precedence
The backend evaluation service SHALL parse and evaluate chained arithmetic expressions containing addition, subtraction, multiplication, division, decimal points, and parenthesized sub-expressions, strictly adhering to the standard order of operations (PEMDAS).

#### Scenario: Basic chained evaluation with order of operations
- **WHEN** user requests evaluation of expression `3 + 4 * 2 - (1 + 1)`
- **THEN** system evaluates expression and returns `9`

### Requirement: High Decimal Precision
The arithmetic engine SHALL compute all results using exact decimal arithmetic to completely avoid standard binary floating-point representation errors.

#### Scenario: Exact decimal evaluation
- **WHEN** user requests evaluation of expression `0.1 + 0.2`
- **THEN** system evaluates expression and returns exactly `0.3` without floating-point inaccuracies

### Requirement: API Error Handling
The backend REST API SHALL validate all input expressions and return clear, descriptive error responses for malformed syntax or invalid mathematical operations.

#### Scenario: Division by zero handling
- **WHEN** user requests evaluation of expression `5 / 0`
- **THEN** system returns an HTTP 400 Bad Request error response stating "Division by zero"

#### Scenario: Mismatched parentheses handling
- **WHEN** user requests evaluation of expression `(3 + 2`
- **THEN** system returns an HTTP 400 Bad Request error response stating "Mismatched parentheses"

### Requirement: Dual-Display Responsive UI
The frontend interface SHALL mimic a physical desktop calculator layout, featuring a screen area with two clear display lines—one for the full current input expression and one for the result (live or final)—and SHALL dynamically adjust to desktop, tablet, and mobile viewport sizes without clipping content or causing horizontal overflow.

#### Scenario: Viewing responsive dual display
- **WHEN** user loads application on a mobile screen width of 375px
- **THEN** interface displays full calculator grid and dual-line screen without clipping buttons or layout overflow

### Requirement: Comprehensive Keyboard Integration
The frontend application SHALL support complete physical keyboard input, letting users type digits (0-9), arithmetic operators (+, -, *, /), parentheses, execute evaluation (Enter or =), delete the last character (Backspace), and completely reset/clear the display (Escape).

#### Scenario: Keyboard input and evaluation
- **WHEN** user presses keyboard keys `2`, `+`, `3`, and `Enter`
- **THEN** input display shows `2+3` and result display shows `5`

### Requirement: Visual and Screen Reader Accessibility
The UI SHALL meet high accessibility standards by providing visual focus and active states, high contrast, and proper ARIA labels and live regions so that a screen reader can announce expression updates and evaluation results.

#### Scenario: Screen reader announcement of evaluation
- **WHEN** result area is updated via user input or evaluation
- **THEN** an `aria-live` region containing the result is updated, allowing screen readers to immediately announce the result
