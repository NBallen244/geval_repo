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
- **Decimal_Precision**: Exact decimal arithmetic performed using Python's `decimal` module (or equivalent AST-based exact evaluation) that avoids binary floating-point representation errors. For non-terminating results, values are rounded to a minimum of 10 significant decimal digits using round-half-to-even rounding.
- **Error_Response**: A structured JSON payload returned by the Backend_Service describing a failed evaluation, including a descriptive error message.
- **Scientific_Function**: A named mathematical operation beyond basic arithmetic supported by the Evaluation_Engine, comprising the trigonometric functions (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`), the logarithmic functions (`ln`, `log10`), the square root function (`sqrt`), and the n-th root function.
- **Angle_Mode**: The unit interpretation applied to the argument of trigonometric functions and to the result of inverse trigonometric functions, with the two permitted values `radians` and `degrees`.
- **Mathematical_Constant**: A predefined exact mathematical value that can be inserted into an Expression, comprising pi (the ratio of a circle's circumference to its diameter) and e (Euler's number).
- **Domain_Error**: A failure condition in which a Scientific_Function or arithmetic operation is applied to an operand outside its mathematical domain, including division by zero, square root of a negative operand, logarithm of a zero or negative operand, and tangent of an angle at which tangent is undefined.
- **Memory_Register**: A single stored numeric value maintained in the Frontend_Client state that the User can add to, subtract from, recall, and clear using memory controls.
- **Memory_Indicator**: A visual badge rendered by the Frontend_Client that signals a non-zero Memory_Register value.
- **Calculation_History**: An ordered collection of evaluated Expression entries accumulated during the current User session, where each entry records the submitted Expression and its returned result.
- **History_Entry**: A single record within the Calculation_History containing one submitted Expression and the corresponding returned result.
- **History_Panel**: The Frontend_Client side drawer or collapsible panel that renders the Calculation_History and the controls to interact with it.
- **Scientific_Keypad**: The region of the Frontend_Client interface that renders the controls for Scientific_Functions, Mathematical_Constants, powers, roots, and the Angle_Mode toggle.

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

---

## Stage 2 Requirements (Scientific Calculator Extension)

The following requirements extend the system into a scientific calculator. All Stage 1 requirements (Requirements 1 through 15) remain in force and unchanged. Stage 2 behavior SHALL NOT weaken, remove, or override any Stage 1 requirement.

### Requirement 16: Stage 1 Codebase Inspection and Defect Remediation

**User Story:** As a developer, I want the Stage 1 codebase inspected and its defects documented before Stage 2 work begins, so that pre-existing issues are fixed without regressing baseline behavior.

#### Acceptance Criteria

1. THE System SHALL produce a written inspection report of the Stage 1 codebase in which each of the four defect categories (bug, architectural flaw, decimal precision issue, and missing edge-case handler) is explicitly covered either by one or more documented defects or by an explicit record that no defect was found in that category.
2. WHEN a defect is documented in the inspection report, THE System SHALL record for that defect the affected component, the steps or input that trigger the defect, and the expected result contrasted with the actual result.
3. WHEN a documented defect is remediated, THE System SHALL preserve the behavior defined in Requirements 1 through 15 such that every Stage 1 acceptance criterion continues to hold after remediation.
4. THE Backend_Service SHALL include pytest tests that assert the corrected behavior for each remediated defect that affects the Evaluation_Engine.
5. IF a remediation of a documented defect introduces a regression against any acceptance criterion in Requirements 1 through 15, THEN THE System SHALL reject or correct that remediation before the inspection activity is considered complete.
6. WHEN the backend test suite is executed after defect remediation, THE Backend_Service test suite SHALL complete with zero test failures and zero errors across all Stage 1 tests defined in Requirement 15 together with the tests added in criterion 4.

### Requirement 17: Trigonometric Functions and Angle Mode

**User Story:** As a User, I want trigonometric functions with selectable angle units, so that I can perform trigonometry in radians or degrees.

#### Acceptance Criteria

1. WHEN an Expression containing a `sin`, `cos`, or `tan` function applied to an operand subexpression is submitted to the Evaluate_Endpoint, THE Evaluation_Engine SHALL return the value of that function evaluated at the operand interpreted in the active Angle_Mode, computed with Decimal_Precision.
2. WHEN an Expression containing an `asin`, `acos`, or `atan` function applied to an operand subexpression is submitted to the Evaluate_Endpoint, THE Evaluation_Engine SHALL return the principal value of that inverse function expressed in the active Angle_Mode and computed with Decimal_Precision, where the principal value lies in the closed interval from negative 90 to positive 90 degrees for `asin` and `atan`, and in the closed interval from 0 to positive 180 degrees for `acos`, with the equivalent intervals in radians when the active Angle_Mode is `radians`.
3. WHERE the active Angle_Mode is `degrees`, THE Evaluation_Engine SHALL interpret the argument of a trigonometric function as degrees and SHALL express the result of an inverse trigonometric function in degrees.
4. WHERE the active Angle_Mode is `radians`, THE Evaluation_Engine SHALL interpret the argument of a trigonometric function as radians and SHALL express the result of an inverse trigonometric function in radians.
5. WHEN the Evaluation_Engine converts an angle between degrees and radians, THE Evaluation_Engine SHALL perform the conversion using the Mathematical_Constant pi under Decimal_Precision.
6. WHEN a trigonometric or inverse trigonometric result is a non-terminating decimal, THE Evaluation_Engine SHALL return the result rounded to a minimum of 10 significant decimal digits using round-half-to-even rounding.
7. IF an Expression applies `asin` or `acos` to an operand whose value is outside the closed interval from negative one to positive one, THEN THE Backend_Service SHALL return an Error_Response with a descriptive message identifying the domain error and SHALL NOT return a calculated result.
8. IF an Expression applies `tan` to an argument equal to an odd integer multiple of 90 degrees when the active Angle_Mode is `degrees`, or to an argument equal to an odd integer multiple of pi divided by 2 radians when the active Angle_Mode is `radians`, THEN THE Backend_Service SHALL return an Error_Response with a descriptive message identifying the domain error and SHALL NOT return a calculated result.
9. WHEN an Expression is submitted to the Evaluate_Endpoint and no Angle_Mode has been explicitly selected for that request, THE Evaluation_Engine SHALL treat the active Angle_Mode as `radians`.
10. IF a request specifies an Angle_Mode value other than `radians` or `degrees`, THEN THE Backend_Service SHALL return an Error_Response with a descriptive message identifying the invalid Angle_Mode and SHALL NOT return a calculated result.

### Requirement 18: Powers, Roots, and Logarithms

**User Story:** As a User, I want powers, roots, and logarithms, so that I can perform scientific calculations beyond basic arithmetic.

#### Acceptance Criteria

1. WHEN an Expression contains an exponentiation of a base operand raised to an exponent operand, and the base operand is non-negative or the exponent operand is an integer, THE Evaluation_Engine SHALL return the base raised to the exponent computed with Decimal_Precision.
2. WHEN an Expression contains a square-root function applied to a non-negative operand, THE Evaluation_Engine SHALL return the non-negative square root of the operand computed with Decimal_Precision.
3. WHEN an Expression contains an n-th root of a radicand operand with a non-zero degree operand, and the degree operand is an odd integer or the radicand operand is non-negative, THE Evaluation_Engine SHALL return the real n-th root of the radicand computed with Decimal_Precision.
4. WHEN an Expression contains a natural logarithm function applied to a positive operand, THE Evaluation_Engine SHALL return the natural logarithm of the operand computed with Decimal_Precision.
5. WHEN an Expression contains a base-10 logarithm function applied to a positive operand, THE Evaluation_Engine SHALL return the base-10 logarithm of the operand computed with Decimal_Precision.
6. WHEN a power, root, or logarithm result is a non-terminating decimal, THE Evaluation_Engine SHALL return the result rounded to a minimum of 10 significant decimal digits using round-half-to-even rounding.
7. IF an Expression applies a square-root function to a negative operand, or applies an n-th root with an even-integer degree operand to a negative radicand operand, THEN THE Backend_Service SHALL return an Error_Response with a descriptive message identifying the Domain_Error and SHALL NOT return a calculated result.
8. IF an Expression applies a natural logarithm or base-10 logarithm function to a zero or negative operand, THEN THE Backend_Service SHALL return an Error_Response with a descriptive message identifying the Domain_Error and SHALL NOT return a calculated result.
9. IF an Expression applies an exponentiation of a negative base operand raised to a non-integer exponent operand, THEN THE Backend_Service SHALL return an Error_Response with a descriptive message identifying the Domain_Error for a non-real result and SHALL NOT return a calculated result.
10. IF an Expression applies an n-th root with a degree operand equal to zero, THEN THE Backend_Service SHALL return an Error_Response with a descriptive message identifying the Domain_Error for an undefined root degree and SHALL NOT return a calculated result.
11. IF an Expression applies a logarithm, root, or exponentiation that produces a non-finite result, THEN THE Backend_Service SHALL return an Error_Response with a descriptive message identifying the Domain_Error and SHALL NOT return a calculated result.

### Requirement 19: Mathematical Constants

**User Story:** As a User, I want quick input of pi and e, so that I can use mathematical constants without typing their decimal values.

#### Acceptance Criteria

1. WHEN an Expression contains the Mathematical_Constant pi, THE Evaluation_Engine SHALL substitute the value of pi bounded by Decimal_Precision to a minimum of 10 significant decimal digits.
2. WHEN an Expression contains the Mathematical_Constant e, THE Evaluation_Engine SHALL substitute the value of e bounded by Decimal_Precision to a minimum of 10 significant decimal digits.
3. WHEN the User activates the pi control on the Scientific_Keypad, THE Frontend_Client SHALL insert the pi constant token into the Expression at the current cursor position.
4. WHEN the User activates the e control on the Scientific_Keypad, THE Frontend_Client SHALL insert the e constant token into the Expression at the current cursor position.
5. THE Frontend_Client SHALL render each Mathematical_Constant token in the Expression using a deterministic display representation (the symbol `pi` for pi and the symbol `e` for e) that is identical for every insertion of the same Mathematical_Constant.

### Requirement 20: Memory Register System

**User Story:** As a User, I want calculator memory operations, so that I can store and reuse values across calculations.

#### Acceptance Criteria

1. THE Frontend_Client SHALL maintain a Memory_Register initialized to a value of zero in the initial state before any memory operation is performed.
2. WHEN the User activates the M+ control WHILE the Result_Display contains a numeric result, THE Frontend_Client SHALL set the Memory_Register to the sum of the current Memory_Register value and the current Result_Display value, retaining the full decimal value of the result with Decimal_Precision.
3. WHEN the User activates the M- control WHILE the Result_Display contains a numeric result, THE Frontend_Client SHALL set the Memory_Register to the difference obtained by subtracting the current Result_Display value from the current Memory_Register value, retaining the full decimal value of the result with Decimal_Precision.
4. WHEN the User activates the MR control, THE Frontend_Client SHALL insert the current Memory_Register value into the Expression at the current input position.
5. WHEN the User activates the MC control, THE Frontend_Client SHALL set the Memory_Register value to zero.
6. WHEN a memory operation changes the Memory_Register to a non-zero value, THE Frontend_Client SHALL render the Memory_Indicator within the same display update.
7. WHEN a memory operation changes the Memory_Register to a value of zero, THE Frontend_Client SHALL hide the Memory_Indicator within the same display update.
8. IF the User activates the M+ or M- control WHILE the Result_Display does not contain a numeric result, THEN THE Frontend_Client SHALL leave the Memory_Register value unchanged and SHALL present an error indication to the User identifying that no numeric result is available to store.
9. IF the User activates the MR control WHILE inserting the Memory_Register value would cause the Expression to exceed 256 characters, THEN THE Frontend_Client SHALL leave the Expression and the Memory_Register value unchanged and SHALL present an error indication to the User identifying that the maximum Expression length would be exceeded.

### Requirement 21: Session Calculation History

**User Story:** As a User, I want a history of my calculations in the current session, so that I can review and reuse previous expressions and results.

#### Acceptance Criteria

1. WHEN the Backend_Service returns a calculated result for a submitted Expression, THE Frontend_Client SHALL append a History_Entry recording that Expression and the returned result as the most recent entry of the Calculation_History, and WHERE appending would cause the Calculation_History to exceed 100 History_Entry items, THE Frontend_Client SHALL first remove the oldest History_Entry so that the Calculation_History never holds more than 100 History_Entry items.
2. THE Frontend_Client SHALL render the Calculation_History in a History_Panel with the most recently appended History_Entry displayed first and the oldest displayed last.
3. WHEN the User selects the expression portion of a History_Entry, THE Frontend_Client SHALL replace the entire current content of the Expression with the recorded Expression of that History_Entry.
4. WHEN the User selects the result portion of a History_Entry, THE Frontend_Client SHALL replace the entire current content of the Expression with the recorded result of that History_Entry.
5. WHILE the active User session continues, THE Frontend_Client SHALL retain in the Calculation_History state, in append order, the most recent 100 History_Entry items accumulated during that session.
6. WHEN the User activates the Clear History control, THE Frontend_Client SHALL remove every History_Entry from the Calculation_History.
7. WHEN the Backend_Service returns an Error_Response for a submitted Expression, THE Frontend_Client SHALL leave the Calculation_History unchanged.
8. WHILE the Calculation_History contains zero History_Entry items, THE Frontend_Client SHALL render an empty-state indication in the History_Panel indicating that no calculations are recorded.

### Requirement 22: Enhanced Responsive Scientific Layout

**User Story:** As a User, I want the scientific controls to fit my device, so that the expanded keypad remains usable on mobile, tablet, and desktop.

#### Acceptance Criteria

1. THE Frontend_Client SHALL render the Scientific_Keypad controls for trigonometric functions, inverse trigonometric functions, powers, roots, logarithms, Mathematical_Constants, the Angle_Mode toggle, and the memory controls.
2. WHILE the viewport width is between 320 and 767 pixels (mobile), THE Frontend_Client SHALL render the Scientific_Keypad and the Stage 1 keypad without horizontal overflow and with every rendered control fully visible without clipping, using either a collapsible Scientific_Keypad or a responsive grid arrangement.
3. WHILE the viewport width is between 768 and 1023 pixels (tablet), THE Frontend_Client SHALL render the Scientific_Keypad and the Stage 1 keypad without horizontal overflow and with every rendered control fully visible without clipping.
4. WHILE the viewport width is between 1024 and 2560 pixels (desktop), THE Frontend_Client SHALL render the Scientific_Keypad and the Stage 1 keypad without horizontal overflow and with every rendered control fully visible without clipping.
5. WHILE the viewport width is between 320 and 767 pixels (mobile), THE Frontend_Client SHALL render each interactive Scientific_Keypad and memory control with a touch target of at least 44 by 44 CSS pixels.
6. THE Frontend_Client SHALL render an Angle_Mode toggle control that displays the active Angle_Mode as either `radians` or `degrees`.
7. WHEN the User activates the Angle_Mode toggle control, THE Frontend_Client SHALL switch the active Angle_Mode to the other value between `radians` and `degrees` and update the displayed active Angle_Mode within 100 milliseconds.
8. WHERE the Scientific_Keypad is rendered as collapsible, WHEN the User activates the Scientific_Keypad collapse or expand control, THE Frontend_Client SHALL toggle the visibility of the Scientific_Keypad controls and indicate the current collapsed or expanded state through the control.
9. WHEN the viewport width changes across any of the 320-767, 768-1023, or 1024-2560 pixel ranges, THE Frontend_Client SHALL re-render the Scientific_Keypad and the Stage 1 keypad for the new range without horizontal overflow and with every rendered control fully visible without clipping.

### Requirement 23: Scientific Keyboard Mapping

**User Story:** As a User, I want keyboard shortcuts for scientific operations, so that I can enter scientific expressions without a mouse.

#### Acceptance Criteria

1. WHEN the User presses the `^` key, THE Frontend_Client SHALL append the exponentiation operator to the Expression.
2. WHEN the User presses a key bound to a Mathematical_Constant (the `p` key for pi and the `e` key for e), THE Frontend_Client SHALL append the corresponding constant token to the Expression.
3. WHEN the User completes a key sequence bound to a Scientific_Function within an inter-key timeout of 1000 milliseconds between consecutive keystrokes, THE Frontend_Client SHALL append the corresponding Scientific_Function token to the Expression.
4. WHEN the User presses a single key that is not mapped to a calculator function, is not bound to a Mathematical_Constant, and is not a valid prefix or completion of a Scientific_Function key sequence, THE Frontend_Client SHALL leave the Expression and Result_Display unchanged.
5. THE Frontend_Client SHALL preserve every Stage 1 keyboard mapping defined in Requirement 10 without alteration.
6. IF the User begins a Scientific_Function key sequence and the inter-key timeout of 1000 milliseconds elapses before the sequence is completed, or the User presses a key that cannot continue the in-progress sequence, THEN THE Frontend_Client SHALL discard the in-progress sequence and SHALL leave the Expression and Result_Display unchanged.

### Requirement 24: Scientific API Contract and State Serialization

**User Story:** As a Frontend_Client developer, I want the evaluation API and state models to support scientific features with strict typing, so that scientific requests, memory values, and history are type-safe.

#### Acceptance Criteria

1. WHEN the Frontend_Client submits an Expression containing one or more Scientific_Functions or Mathematical_Constants to the Evaluate_Endpoint, THE Backend_Service SHALL evaluate the Expression and return either a success response containing the calculated result or an Error_Response, using the response structure defined in Requirement 5 in which the presence of the result field or the error message field unambiguously distinguishes the two outcomes.
2. THE Evaluate_Endpoint request contract SHALL include an Angle_Mode field whose only permitted values are `radians` and `degrees`.
3. WHEN a request is received at the Evaluate_Endpoint without an Angle_Mode field, THE Backend_Service SHALL interpret the request using the `radians` Angle_Mode as the default.
4. IF a request is received at the Evaluate_Endpoint whose Angle_Mode field holds a value other than `radians` or `degrees`, THEN THE Backend_Service SHALL return an Error_Response with an HTTP status code in the 4xx range and a descriptive message identifying the invalid Angle_Mode, and SHALL NOT return a calculated result.
5. WHEN the Evaluation_Engine returns a Scientific_Function result or a result derived from a Mathematical_Constant, THE Backend_Service SHALL return the result as a decimal string computed with Decimal_Precision, rounding any non-terminating result to a minimum of 10 significant decimal digits using round-half-to-even rounding.
6. THE Frontend_Client SHALL define TypeScript interfaces for the scientific request payload, the Memory_Register value, the History_Entry, and the Calculation_History, each typed without using the `any` type, and the Angle_Mode field of the scientific request payload SHALL be typed as a union restricted to the literal values `radians` and `degrees`.
7. THE Frontend_Client SHALL compute no Scientific_Function, power, root, logarithm, or angle conversion locally and SHALL obtain every scientific result exclusively from the Backend_Service through the Evaluate_Endpoint.
8. IF an Expression submitted to the Evaluate_Endpoint applies a Scientific_Function, root, or logarithm to an operand outside its mathematical domain (a Domain_Error), THEN THE Backend_Service SHALL return an Error_Response with an HTTP status code in the 4xx range and a descriptive message identifying the Domain_Error, and SHALL NOT return a calculated result.

### Requirement 25: Scientific Backend Test Coverage

**User Story:** As a developer, I want automated backend tests for scientific features, so that scientific function correctness, angle conversions, and domain error handling are verified.

#### Acceptance Criteria

1. THE Backend_Service SHALL include pytest unit tests that verify each trigonometric and inverse trigonometric function defined in Requirement 17 in both the `radians` and `degrees` Angle_Modes, each asserting the returned result equals the expected value to at least 10 significant decimal digits.
2. THE Backend_Service SHALL include pytest unit tests that verify degrees-to-radians and radians-to-degrees angle conversions, each asserting the converted value equals the expected value to at least 10 significant decimal digits.
3. THE Backend_Service SHALL include pytest unit tests that verify each power, root, and logarithm function defined in Requirement 18, each asserting the returned result equals the expected value to at least 10 significant decimal digits.
4. THE Backend_Service SHALL include pytest unit tests that verify each Scientific_Function Domain_Error defined in Requirements 17 and 18 returns an Error_Response with a 4xx status code.
5. THE Backend_Service SHALL include pytest unit tests that verify the Mathematical_Constants pi and e are substituted to at least 10 significant decimal digits as defined in Requirement 19.
6. THE Backend_Service SHALL include pytest unit tests that verify boundary-value behavior for domain-valid inputs immediately adjacent to each Domain_Error boundary defined in Requirements 17 and 18, including `asin` and `acos` at operands of negative one and positive one, `sqrt` at an operand of zero, and natural logarithm and base-10 logarithm at an operand immediately greater than zero, each asserting the returned result equals the expected value to at least 10 significant decimal digits.
7. THE Backend_Service test suite SHALL achieve a measured line coverage of at least 90 percent across the scientific engine modules that implement Scientific_Functions, angle conversion, and Mathematical_Constant substitution.
8. WHEN the backend test suite is executed, THE Backend_Service test suite SHALL complete with zero test failures and zero errors, and IF any test fails or the coverage threshold defined in criterion 7 is not met, THEN THE Backend_Service test suite SHALL report the failure and SHALL NOT report a successful outcome.
