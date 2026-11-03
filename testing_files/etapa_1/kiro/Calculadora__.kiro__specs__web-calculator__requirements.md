# Requirements Document

## Introduction

This document defines the requirements for a modern, daily-use, responsive web calculator. The application evaluates chained arithmetic expressions while strictly adhering to standard order of operations (PEMDAS) and maintaining high decimal precision. The system is composed of a Python/FastAPI backend that parses, validates, and calculates expressions, and a React/TypeScript frontend that mimics a physical desktop calculator with full keyboard and accessibility support. A strict separation is maintained between the frontend UI rendering state and the backend math evaluation engine.

## Glossary

- **System**: The complete web calculator application, comprising the Backend_Service and the Frontend_Client.
- **Backend_Service**: The Python 3.11+ FastAPI application that exposes a REST API for expression evaluation.
- **Frontend_Client**: The React with TypeScript application (built with Vite) that renders the calculator interface and communicates with the Backend_Service.
- **Evaluation_Engine**: The component within the Backend_Service responsible for parsing, validating, and calculating arithmetic expressions.
- **Parser**: The subcomponent of the Evaluation_Engine that transforms an expression string into an evaluable structure according to the arithmetic grammar.
- **Expression**: A string of arithmetic operators, decimal operands, and parentheses submitted for evaluation (e.g., `12.5 + 3 * (4 - 1.5) / 2`).
- **PEMDAS**: The standard order of operations: Parentheses, Exponents, Multiplication, Division, Addition, Subtraction.
- **Evaluate_Endpoint**: The REST endpoint `POST /api/v1/evaluate` exposed by the Backend_Service.
- **Expression_Display**: The Frontend_Client area that shows the full input Expression entered by the User.
- **Result_Display**: The Frontend_Client area that shows the live or final calculated result.
- **User**: A person interacting with the Frontend_Client via mouse, touch, or keyboard.
- **Decimal_Precision**: Exact decimal arithmetic performed using Python's `decimal` module (or equivalent AST-based exact evaluation) that avoids binary floating-point representation errors.
- **Error_Response**: A structured JSON payload returned by the Backend_Service describing a failed evaluation, including a descriptive error message.

## Requirements

### Requirement 1: Chained Expression Evaluation

**User Story:** As a User, I want to evaluate chained arithmetic expressions, so that I can perform multi-operator calculations in a single entry.

#### Acceptance Criteria

1. WHEN a valid Expression containing two or more arithmetic operators and no more than 256 characters is submitted to the Evaluate_Endpoint, THE Backend_Service SHALL return a numeric result equal to the value obtained by evaluating the Expression under PEMDAS with Decimal_Precision.
2. WHEN an Expression contains any combination of addition, subtraction, multiplication, and division operators, THE Evaluation_Engine SHALL compute a result equal to the value produced by conventional arithmetic evaluation of those operators under PEMDAS.
3. WHEN an Expression contains decimal operands, THE Evaluation_Engine SHALL compute the result using the exact decimal values of those operands with Decimal_Precision.
4. WHEN an Expression contains parentheses, THE Evaluation_Engine SHALL evaluate the innermost parenthesized subexpressions before any operators outside those parentheses.
5. IF an Expression submitted to the Evaluate_Endpoint exceeds 256 characters, THEN THE Backend_Service SHALL reject the Expression with an Error_Response containing a descriptive message identifying that the maximum Expression length was exceeded, and SHALL NOT return a calculated result.

### Requirement 2: PEMDAS Precedence

**User Story:** As a User, I want expressions evaluated using standard order of operations, so that results match conventional arithmetic.

#### Acceptance Criteria

1. WHEN an Expression contains both multiplication or division and addition or subtraction operators, THE Evaluation_Engine SHALL apply multiplication and division before addition and subtraction.
2. WHEN an Expression contains nested parenthesized subexpressions, THE Evaluation_Engine SHALL evaluate the innermost parenthesized subexpressions first and proceed outward before applying operators outside those parentheses.
3. WHEN an Expression contains exponentiation, THE Evaluation_Engine SHALL apply exponentiation before multiplication, division, addition, and subtraction.
4. WHEN an Expression contains a chain of exponentiation operators, THE Evaluation_Engine SHALL evaluate the exponentiation operators from right to left.
5. WHEN an Expression contains operators of equal precedence for addition, subtraction, multiplication, or division, THE Evaluation_Engine SHALL evaluate those operators from left to right.
6. WHEN an Expression contains a unary minus applied to an operand that is also raised to an exponent, THE Evaluation_Engine SHALL apply the exponentiation before the unary minus.

### Requirement 3: Decimal Precision

**User Story:** As a User, I want calculations to preserve exact decimal precision, so that results are free of floating-point representation errors.

#### Acceptance Criteria

1. WHEN the Expression `0.1 + 0.2` is submitted to the Evaluate_Endpoint, THE Evaluation_Engine SHALL return `0.3`.
2. WHEN an Expression whose exact mathematical result is representable as a terminating decimal is submitted to the Evaluate_Endpoint, THE Evaluation_Engine SHALL return that exact decimal value with no binary floating-point representation error.
3. WHEN an Expression is evaluated using Decimal_Precision, THE Evaluation_Engine SHALL compute all intermediate and final arithmetic operations using exact decimal arithmetic rather than binary floating-point arithmetic.
4. IF a division produces a non-terminating decimal result, THEN THE Evaluation_Engine SHALL return the result rounded to a minimum of 10 significant decimal digits using round-half-to-even rounding.

### Requirement 4: Error Handling

**User Story:** As a User, I want descriptive error messages for invalid input, so that I understand why an expression could not be evaluated.

#### Acceptance Criteria

1. IF an Expression contains a division by zero, THEN THE Backend_Service SHALL return an Error_Response with a descriptive message identifying division by zero.
2. IF an Expression contains an invalid operator sequence, THEN THE Backend_Service SHALL return an Error_Response with a descriptive message identifying the invalid sequence.
3. IF an Expression contains unclosed parentheses, THEN THE Backend_Service SHALL return an Error_Response with a descriptive message identifying the unclosed parentheses.
4. IF an Expression contains characters that are not operators, digits, decimal points, or parentheses, THEN THE Backend_Service SHALL return an Error_Response with a descriptive message identifying the invalid characters.
5. IF an Expression is empty or contains only whitespace, THEN THE Backend_Service SHALL return an Error_Response with a descriptive message identifying that no expression was provided.
6. WHEN the Backend_Service returns an Error_Response for any input-validation failure defined in this requirement, THE Backend_Service SHALL include an HTTP status code in the 4xx range and SHALL NOT include a calculated result.

### Requirement 5: Evaluate REST Endpoint

**User Story:** As a Frontend_Client developer, I want a well-defined REST endpoint, so that I can submit expressions and receive structured results.

#### Acceptance Criteria

1. THE Backend_Service SHALL expose the Evaluate_Endpoint at `POST /api/v1/evaluate`.
2. WHEN a request is received at the Evaluate_Endpoint with a JSON request body containing an Expression string of 1 to 256 characters, THE Backend_Service SHALL accept the request and submit the Expression string for evaluation.
3. WHEN an Expression is evaluated successfully, THE Backend_Service SHALL return a JSON response with a `Content-Type` of `application/json`, containing the calculated result value, and an HTTP status code of 200.
4. IF an Expression cannot be evaluated, THEN THE Backend_Service SHALL return an Error_Response in JSON format with a `Content-Type` of `application/json` and an HTTP status code in the 4xx range.
5. WHEN the Backend_Service returns a success response, THE Backend_Service SHALL include a result field and omit any error field, and WHEN the Backend_Service returns an Error_Response, THE Backend_Service SHALL include an error message field and omit any result field, such that the presence of these fields unambiguously distinguishes a success response from an Error_Response.
6. IF a request is received at the Evaluate_Endpoint whose body is not valid JSON, is missing the Expression string, or contains an Expression string exceeding 256 characters, THEN THE Backend_Service SHALL return an Error_Response in JSON format with an HTTP status code in the 4xx range and a descriptive message identifying the malformed or missing request body.

### Requirement 6: Expression Parsing and Round-Trip Integrity

**User Story:** As a User, I want the calculator to parse expressions reliably, so that valid input is consistently interpreted.

#### Acceptance Criteria

1. WHEN an Expression composed only of digits, decimal points, the addition, subtraction, multiplication, division, and exponentiation operators, and balanced parentheses is submitted, THE Parser SHALL transform the Expression into an evaluable structure that conforms to PEMDAS precedence.
2. IF an Expression violates the arithmetic grammar, THEN THE Parser SHALL NOT produce an evaluable structure and THE Backend_Service SHALL return an Error_Response with a descriptive message identifying the grammar violation.
3. WHEN the Parser produces an evaluable structure and that structure is rendered back into an Expression string and parsed again, THE Parser SHALL produce a structure that conforms to the same PEMDAS precedence as the original structure.
4. WHEN a round-trip re-parse is evaluated, THE Evaluation_Engine SHALL produce a result equal to the original Expression's result to at least 10 significant decimal digits under Decimal_Precision.

### Requirement 7: Calculator Display

**User Story:** As a User, I want to see both my full input and the result, so that I can verify what I am calculating.

#### Acceptance Criteria

1. THE Frontend_Client SHALL render an Expression_Display showing the full input Expression, and SHALL show an empty Expression_Display in the initial state before any input is entered.
2. THE Frontend_Client SHALL render a Result_Display showing the calculated result, and SHALL show an empty Result_Display in the initial state before any result is returned.
3. WHEN the User modifies the Expression, THE Frontend_Client SHALL update the Expression_Display to reflect the current input on each modification.
4. WHEN the Backend_Service returns a calculated result, THE Frontend_Client SHALL display the result in the Result_Display.
5. WHEN the Backend_Service returns an Error_Response, THE Frontend_Client SHALL display the error message text contained in the Error_Response to the User.
6. WHEN the Frontend_Client displays a calculated result in the Result_Display, THE Frontend_Client SHALL clear any previously displayed error message, and WHEN the Frontend_Client displays an error message, THE Frontend_Client SHALL clear any previously displayed result in the Result_Display.

### Requirement 8: Physical Calculator Layout

**User Story:** As a User, I want an interface resembling a standard desktop calculator, so that it feels familiar to use daily.

#### Acceptance Criteria

1. THE Frontend_Client SHALL render buttons for digits 0 through 9, a decimal point, the operators addition, subtraction, multiplication, and division, parentheses, an evaluate control, and a reset control.
2. THE Frontend_Client SHALL arrange digit buttons 1 through 9 in a three-column-by-three-row keypad grid ordered with 7, 8, 9 in the top row, 4, 5, 6 in the middle row, and 1, 2, 3 in the bottom row, with the 0 button positioned in a row below the 1 through 9 keypad.
3. THE Frontend_Client SHALL position the addition, subtraction, multiplication, and division operator buttons in a dedicated column or row region separated from the digit keypad.
4. WHEN the calculator interface is rendered, THE Frontend_Client SHALL display every control listed in criterion 1 as visible and clickable within the visible viewport without requiring scrolling.

### Requirement 9: Responsive Layout

**User Story:** As a User, I want the calculator to adapt to my device, so that it is usable on mobile, tablet, and desktop.

#### Acceptance Criteria

1. WHILE the viewport width is between 320 and 767 pixels (mobile), THE Frontend_Client SHALL render the calculator without horizontal overflow and with all calculator buttons fully visible without clipping.
2. WHILE the viewport width is between 768 and 1023 pixels (tablet), THE Frontend_Client SHALL render the calculator without horizontal overflow and with all calculator buttons fully visible without clipping.
3. WHILE the viewport width is between 1024 and 2560 pixels (desktop), THE Frontend_Client SHALL render the calculator without horizontal overflow and with all calculator buttons fully visible without clipping.
4. WHILE the viewport width is between 320 and 767 pixels (mobile), THE Frontend_Client SHALL render each interactive calculator control with a touch target of at least 44 by 44 CSS pixels.

### Requirement 10: Keyboard Support

**User Story:** As a User, I want full keyboard control, so that I can operate the calculator without a mouse.

#### Acceptance Criteria

1. WHEN the User presses a digit key from `0` to `9`, THE Frontend_Client SHALL append the corresponding digit to the Expression.
2. WHEN the User presses the `+`, `-`, `*`, or `/` key, THE Frontend_Client SHALL append the corresponding operator to the Expression.
3. WHEN the User presses the `.` key or a parenthesis key, THE Frontend_Client SHALL append the corresponding decimal point or parenthesis character to the Expression.
4. WHEN the User presses the `Enter` key or the `=` key, THE Frontend_Client SHALL submit the current Expression for evaluation.
5. WHEN the User presses the `Backspace` key and the Expression is non-empty, THE Frontend_Client SHALL remove the most recently entered character from the Expression.
6. WHEN the User presses the `Backspace` key and the Expression is empty, THE Frontend_Client SHALL leave the Expression unchanged.
7. WHEN the User presses the `Escape` key, THE Frontend_Client SHALL reset the Expression to empty and clear the Result_Display.
8. WHEN the User presses a key that is not mapped to a calculator function, THE Frontend_Client SHALL leave the Expression and Result_Display unchanged.

### Requirement 11: Visual Accessibility

**User Story:** As a User, I want a readable, high-contrast interface, so that I can use the calculator comfortably.

#### Acceptance Criteria

1. THE Frontend_Client SHALL render body text and control labels with a contrast ratio of at least 4.5 to 1 against their background.
2. THE Frontend_Client SHALL render large-scale text (at least 18 point, or 14 point bold) with a contrast ratio of at least 3 to 1 against its background.
3. THE Frontend_Client SHALL render user interface component boundaries and graphical indicators with a contrast ratio of at least 3 to 1 against adjacent colors.
4. WHILE a control has keyboard focus, THE Frontend_Client SHALL render a visible focus indicator on that control with a contrast ratio of at least 3 to 1 against adjacent colors.
5. WHILE a control is in the pressed or active state, THE Frontend_Client SHALL render a visible active-state indication distinguishing it from its resting state.
6. THE Frontend_Client SHALL label each calculator button with visible text identifying the button function.

### Requirement 12: Screen Reader Support

**User Story:** As a User relying on assistive technology, I want accessible markup, so that a screen reader can convey the calculator state.

#### Acceptance Criteria

1. THE Frontend_Client SHALL provide an `aria-label` attribute on each digit, decimal point, operator, parenthesis, evaluate, and reset control, and each `aria-label` SHALL match the visible function of that control.
2. WHERE an interactive calculator control is not a native button element, THE Frontend_Client SHALL assign the `role="button"` attribute to that control.
3. WHEN the Expression_Display or Result_Display content changes, THE Frontend_Client SHALL announce the updated content through an `aria-live` region with a politeness setting of `polite`.
4. WHEN the Frontend_Client displays an Error_Response message, THE Frontend_Client SHALL announce the error message through an `aria-live` region with a politeness setting of `assertive`.
5. WHEN the Expression and Result_Display are reset to their empty state, THE Frontend_Client SHALL announce the reset through an `aria-live` region.

### Requirement 13: Type-Safe API Contract

**User Story:** As a Frontend_Client developer, I want strict TypeScript interfaces for the API, so that request and response handling is type-safe.

#### Acceptance Criteria

1. THE Frontend_Client SHALL define a TypeScript interface for the Evaluate_Endpoint request payload that types the Expression string field.
2. THE Frontend_Client SHALL define a TypeScript interface for the Evaluate_Endpoint success response that types the calculated result field.
3. THE Frontend_Client SHALL define a TypeScript interface for the Error_Response structure that types the error message field.
4. WHEN the Frontend_Client calls the Evaluate_Endpoint, THE Frontend_Client SHALL construct the request payload conforming to the request payload interface without using the `any` type.
5. IF a response from the Evaluate_Endpoint does not conform to the success response interface or the Error_Response interface, THEN THE Frontend_Client SHALL treat the response as an error and display an error message to the User.

### Requirement 14: Separation of Concerns

**User Story:** As a developer, I want a clean separation between UI state and math evaluation, so that the system is maintainable and testable.

#### Acceptance Criteria

1. THE Frontend_Client SHALL manage Expression input state and UI rendering state without computing any numeric arithmetic result of an Expression.
2. THE Backend_Service SHALL perform all arithmetic evaluation of Expressions.
3. WHEN the User submits an Expression for evaluation, THE Frontend_Client SHALL obtain the calculated result exclusively by sending the Expression to the Backend_Service through the Evaluate_Endpoint.
4. IF the Frontend_Client cannot reach the Backend_Service through the Evaluate_Endpoint, THEN THE Frontend_Client SHALL display an error message indicating the evaluation service is unavailable and SHALL NOT display a locally computed result.

### Requirement 15: Backend Test Coverage

**User Story:** As a developer, I want automated backend tests, so that PEMDAS correctness and error handling are verified.

#### Acceptance Criteria

1. THE Backend_Service SHALL include pytest unit tests that verify PEMDAS precedence correctness for expressions combining at least three different operator precedence levels, each asserting the returned result equals the expected value.
2. THE Backend_Service SHALL include pytest unit tests that verify each Error_Response case defined in Requirement 4, each asserting that the response is an Error_Response with a 4xx status code.
3. THE Backend_Service SHALL include a pytest test verifying the round-trip parsing property defined in Requirement 6 across multiple sample expressions.
4. WHEN the backend test suite is executed, THE Backend_Service test suite SHALL pass all defined tests.
