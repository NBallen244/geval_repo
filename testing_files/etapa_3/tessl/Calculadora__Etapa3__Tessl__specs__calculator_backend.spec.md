---
name: Calculator Backend Engine
description: Parsing, PEMDAS evaluation, scientific functions, and high-precision REST API for arithmetic expressions
targets:
  - ../backend/app/main.py
  - ../backend/app/calculator.py
  - ../backend/Dockerfile
---

# Calculator Backend Engine

## Arithmetic & Scientific Evaluation API

The calculator service exposes a single API endpoint to evaluate expressions, supporting standard and scientific operations.

```http
POST /api/v1/evaluate
Content-Type: application/json

{
  "operation": "sin(pi / 2) + 2^3",
  "angle_unit": "radians"
}

Response (200 OK):
{
  "result": 9.0
}
```
`[@test] ../backend/tests/test_api.py`

### Request Specification
- `operation`: String. The arithmetic or scientific expression to evaluate. Required.
- `angle_unit`: String, either `"radians"` or `"degrees"`. Optional, defaults to `"radians"`. Determines the unit for trigonometric calculations (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`).

---

## Core Evaluation Engine & Scientific Functions

### 1. Precedence & Parsing Rules (PEMDAS)
- Parentheses `()` have the highest precedence.
- Exponentiation `^` has the second highest precedence (above Multiplication/Division, below Parentheses).
  `[@test] ../backend/tests/test_calculator.py`
- Multiplication `*` and Division `/` have the third highest precedence.
- Addition `+` and Subtraction `-` have the lowest precedence.

### 2. Scientific Functions & Constants
- **Trigonometric Functions:** `sin(x)`, `cos(x)`, `tan(x)`, and their inverses `asin(x)`, `acos(x)`, `atan(x)`.
  - Angle evaluation must respect the provided `angle_unit` (degrees or radians).
  `[@test] ../backend/tests/test_calculator.py`
- **Powers & Roots:**
  - Binary exponentiation `x^y` (e.g. `2^3` evaluates to `8`).
  - Square root `sqrt(x)` (e.g. `sqrt(9)` evaluates to `3`).
  - Natural logarithm `ln(x)` and base-10 logarithm `log(x)`.
  `[@test] ../backend/tests/test_calculator.py`
- **Constants:**
  - `pi` (evaluates to high-precision Pi value $\approx 3.141592653589793$).
  - `e` (evaluates to high-precision Euler's number $\approx 2.718281828459045$).
  `[@test] ../backend/tests/test_calculator.py`

### 3. High Precision Representation
- Calculations must avoid standard float precision errors by utilizing Python's built-in `decimal` module where possible. Constants and functions are computed using higher-precision decimal methods or standard high-precision math modules converted to Decimal.
  `[@test] ../backend/tests/test_calculator.py`

---

## Error Handling & HTTP Status Codes

- **Division by zero** catches standard division by zero and returns HTTP 400 with descriptive error.
  `[@test] ../backend/tests/test_api.py`
- **Mathematical Domain Errors:**
  - Square root of a negative number (e.g., `sqrt(-1)`) must return HTTP 400 indicating a math domain error.
  - Logarithm of a zero or negative number (e.g., `ln(-5)` or `log(0)`) must return HTTP 400.
  - Inverse trig functions outside valid domain $[-1, 1]$ (e.g., `asin(2)`) must return HTTP 400.
  - Undefined trigonometric tangent operations (e.g. `tan(90)` degrees or `tan(pi/2)` radians) must return HTTP 400 indicating a division by zero / undefined tangent error.
  - Giant integer exponentiation triggering calculation overflows (such as `10^100000000000000000000` throwing a `decimal.Overflow`) must return HTTP 400.
  `[@test] ../backend/tests/test_api.py`
  `[@test] ../backend/tests/test_calculator.py`
- **Syntax or Parsing Errors:**
  - Invalid character sequences, unclosed parentheses, or unmatched operators must return HTTP 400.
  `[@test] ../backend/tests/test_api.py`

---

## Non-Functional & Containerized Deployment Specifications (Stage 3)

### 1. High-Precision Test Coverage
- Unit and integration test suites must enforce a strict **$\ge 80\%$ statement coverage** requirement for the backend codebase (`calculator.py` and `main.py`).
  `[@test] ../backend/tests/test_calculator.py`
  `[@test] ../backend/tests/test_api.py`

### 2. Multi-Stage Production Docker Configuration
- The backend application must package into a secure, multi-stage, minimized container image.
- **Core Constraints:**
  - **Base Image:** Utilize high-performance, minimal base images (`python:3.13-slim`).
  - **Security Mandate:** Run all processes under a non-root system user (`appuser` with uid/gid `10001`) to protect host processes.
  - **Health Monitoring:** Embed an automated HEALTHCHECK command verifying server socket responsiveness every 30s.
  - **Port Exposure:** Expose and listen on port `8000` for REST requests.
  `[@test] ../backend/Dockerfile`
