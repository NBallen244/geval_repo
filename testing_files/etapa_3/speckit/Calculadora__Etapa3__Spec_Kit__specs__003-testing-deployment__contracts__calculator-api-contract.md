# Calculator Service API Interface Contract

This contract defines the public interface exposed by the calculator backend API, reverse-proxied by Nginx inside our containerized environment.

---

## 1. Expression Evaluation Endpoint

Evaluates a mathematical expression with exact decimal precision and strict PEMDAS parsing rules.

- **URL Path**: `/api/v1/evaluate`
- **HTTP Method**: `POST`
- **Headers**:
  - `Content-Type`: `application/json`

### 1.1 Request Payload Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "expression": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1000,
      "description": "The mathematical arithmetic expression to evaluate."
    },
    "angle_unit": {
      "type": "string",
      "enum": ["radians", "degrees"],
      "default": "radians",
      "description": "The unit to use for trigonometric operations."
    }
  },
  "required": ["expression"]
}
```

### 1.2 Response Payload Schema (HTTP 200 - Success)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "expression": {
      "type": "string",
      "description": "The original evaluated mathematical expression."
    },
    "result": {
      "type": "string",
      "description": "The highly precise calculated decimal result."
    }
  },
  "required": ["expression", "result"]
}
```

### 1.3 Error Response Schema (HTTP 400 - Client Error / Calculation Failure)

Returned when evaluating invalid expressions, division by zero, undefined trigonometric domains, etc.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "error": {
      "type": "string",
      "description": "Unique uppercase machine-readable error code."
    },
    "details": {
      "type": "string",
      "description": "User-friendly mathematical explanation of the error."
    }
  },
  "required": ["error", "details"]
}
```

---

## 2. Sample Payloads

### 2.1 Standard Calculation
**Request**:
```json
{
  "expression": "0.1 + 0.2"
}
```
**Response (HTTP 200)**:
```json
{
  "expression": "0.1 + 0.2",
  "result": "0.3"
}
```

### 2.2 Error: Division by Zero
**Request**:
```json
{
  "expression": "5 / 0"
}
```
**Response (HTTP 400)**:
```json
{
  "error": "DIVISION_BY_ZERO",
  "details": "Division by zero is mathematically undefined."
}
```

### 2.3 Error: Out of Trigonometric Domain
**Request**:
```json
{
  "expression": "arcsin(2.5)"
}
```
**Response (HTTP 400)**:
```json
{
  "error": "OUT_OF_DOMAIN",
  "details": "The input for arcsin(x) must satisfy |x| <= 1."
}
```
