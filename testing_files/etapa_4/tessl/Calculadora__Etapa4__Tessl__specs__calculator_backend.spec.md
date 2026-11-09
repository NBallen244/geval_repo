---
name: Calculator Backend Engine
description: Parsing, PEMDAS evaluation, RPN / Shunting Yard engine, scientific functions, and high-precision REST API
targets:
  - ../backend/app/main.py
  - ../backend/app/calculator.py
  - ../backend/Dockerfile
---

# Calculator Backend Engine

## Arithmetic & Scientific Evaluation API

The calculator service exposes a single API endpoint to evaluate expressions, supporting standard (infix) and postfix (RPN) operations.

```http
POST /api/v1/evaluate
Content-Type: application/json

{
  "operation": "sin(pi / 2) + 2^3",
  "angle_unit": "radians",
  "mode": "infix"
}

Response (200 OK):
{
  "result": 9.0
}
```
`[@test] ../backend/tests/test_api.py`

### Request Specification
- `operation`: String. The arithmetic or scientific expression (or space-separated postfix expression) to evaluate. Required.
- `angle_unit`: String, either `"radians"` or `"degrees"`. Optional, defaults to `"radians"`. Determines the unit for trigonometric calculations.
- `mode`: String, either `"infix"` or `"postfix"`. Optional, defaults to `"infix"`.
  - `"infix"`: Evaluates standard mathematical notation by converting it to postfix via the Shunting Yard Algorithm, then running the stack-based evaluator.
  - `"postfix"`: Evaluates a space-separated string of RPN tokens using the stack-based evaluator.

---

## Core RPN Evaluation Engine & Scientific Functions

To ensure robustness, all expressions are evaluated using a high-precision, stack-based RPN evaluation engine.

### 1. Shunting Yard Algorithm (Infix to Postfix Conversion)
- Standard infix expressions are parsed and converted to Reverse Polish Notation (Postfix) using the Shunting Yard Algorithm.
- Supports operator precedence:
  - Unary `+` and `-` have the highest precedence (represented as internal tokens `u+` and `u-`).
  - Parentheses `()` override all precedence.
  - Exponentiation `^` has second highest precedence (right-associative).
  - Multiplication `*` and Division `/` have third highest precedence.
  - Addition `+` and Subtraction `-` have lowest precedence.
- Supports functions as high-precedence prefix operators: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `ln`, `log`, `sqrt`.
  `[@test] ../backend/tests/test_calculator.py`

### 2. Stack Evaluator Engine
- Evaluates postfix tokens by pushing numbers onto a stack and popping them when operators or functions are encountered.
- **Precise Decimal Math:** Maintains Python's `Decimal` precision for all stack elements, constants, and computations.
- Supports all operations:
  - **Binary operators:** `+`, `-`, `*`, `/`, `^`.
  - **Unary operators:** `u-` (negation), `u+` (identity).
  - **Scientific functions:** `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `ln`, `log`, `sqrt`.
  - **Constants:** `pi`, `e`.
  `[@test] ../backend/tests/test_calculator.py`

---

## Error Handling & HTTP Status Codes

- **Stack Underflow:** Enforcing sufficient operands for all operators/functions. For example, executing `+` when the stack has only one element returns HTTP 400 with a descriptive error.
  `[@test] ../backend/tests/test_calculator.py`
  `[@test] ../backend/tests/test_api.py`
- **Division by zero** returns HTTP 400 with a descriptive error.
  `[@test] ../backend/tests/test_api.py`
- **Mathematical Domain Errors:**
  - Square root of a negative number (e.g., `sqrt(-1)`) returns HTTP 400.
  - Logarithm of a zero or negative number (e.g., `ln(0)`) returns HTTP 400.
  - Inverse trig functions outside valid domain $[-1, 1]$ returns HTTP 400.
  - Undefined trigonometric tangent operations returns HTTP 400.
  - Exponentiation overflows or fractional powers on negative numbers return HTTP 400.
  `[@test] ../backend/tests/test_api.py`
  `[@test] ../backend/tests/test_calculator.py`
- **Syntax or Parsing Errors:**
  - Invalid character sequences, unclosed parentheses, or unmatched operators return HTTP 400.
  `[@test] ../backend/tests/test_api.py`

---

## Non-Functional & Containerized Deployment Specifications (Stage 3)

### 1. High-Precision Test Coverage
- Unit and integration test suites must enforce a strict **$\ge 80\%$ statement coverage** requirement for the backend codebase (`calculator.py` and `main.py`).
  `[@test] ../backend/tests/test_calculator.py`
  `[@test] ../backend/tests/test_api.py`

### 2. Multi-Stage Production Docker Configuration
- Base Image: `python:3.13-slim`.
- Secure system user: `appuser` (uid/gid `10001`).
- Embed an automated HEALTHCHECK.
- Expose and listen on port `8000`.
  `[@test] ../backend/Dockerfile`
