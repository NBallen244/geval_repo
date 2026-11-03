---
name: Calculator Backend Engine
description: Parsing, PEMDAS evaluation, and high-precision REST API for arithmetic expressions
targets:
  - ../backend/app/main.py
  - ../backend/app/calculator.py
---

# Calculator Backend Engine

## Arithmetic Evaluation API

The calculator service must expose a single API endpoint to evaluate expressions.

```http
POST /api/v1/evaluate
Content-Type: application/json

{
  "operation": "12.5 + 3 * (4 - 1.5) / 2"
}

Response (200 OK):
{
  "result": 16.25
}
```
`[@test] ../backend/tests/test_api.py`

## Core Evaluation Engine

- Expression parsing must respect PEMDAS rules: Parentheses, Multiplication/Division, Addition/Subtraction.
  `[@test] ../backend/tests/test_calculator.py`
- All calculations must avoid standard float precision errors by utilizing Python's built-in `decimal` module. For example, `0.1 + 0.2` must strictly evaluate to `0.3`.
  `[@test] ../backend/tests/test_calculator.py`
- White spaces in the input string must be ignored or handled gracefully.
  `[@test] ../backend/tests/test_calculator.py`

## Error Handling & HTTP Status Codes

- Division by zero must be caught and return a standard HTTP 400 Bad Request error indicating a division by zero.
  `[@test] ../backend/tests/test_api.py`
- Invalid operator sequences (e.g., `12 + * 3` or unclosed parentheses) must be caught and return a standard HTTP 400 Bad Request error indicating syntax or parse errors.
  `[@test] ../backend/tests/test_api.py`
- Empty input strings or malformed payloads must return a standard HTTP 400 Bad Request.
  `[@test] ../backend/tests/test_api.py`
