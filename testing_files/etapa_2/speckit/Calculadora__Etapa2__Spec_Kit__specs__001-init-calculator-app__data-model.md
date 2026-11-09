# Data Model: Web Calculator

This document outlines the high-level data models and validation constraints for the Web Calculator application, ensuring robust types across the FastAPI and React application borders.

## 1. Entities & Validation Rules

### CalculationRequest
Represents the expression payload submitted by the frontend UI to the backend math engine for evaluation.

| Field | Type | Required | Validation Rules | Description |
|-------|------|----------|------------------|-------------|
| `expression` | string | Yes | - Min length: 1<br>- Max length: 1000<br>- MUST only contain numbers, operators (`+`, `-`, `*`, `/`, `^`), decimal points (`.`), parentheses, and whitespaces. | The complete raw mathematical string to evaluate. |

### CalculationResponse
Represents the successful outcome of a valid math expression calculation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `expression` | string | Yes | The original math expression string that was evaluated. |
| `result` | string | Yes | The exact decimal representation of the final evaluated math result (free of floating-point artifacts). |

### ErrorResponse
Represents a structured error payload returned when input validation fails or a runtime calculation error occurs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error` | string | Yes | A short, unique error category identifier (e.g., `DIVISION_BY_ZERO`, `SYNTAX_ERROR`, `VALIDATION_ERROR`). |
| `details` | string | Yes | A localized, user-friendly description of the error explaining what went wrong and how the user can resolve it. |

---

## 2. State & Transitions
The web calculator represents a stateless execution flow. No calculations or historic items are persisted in database systems. 

```text
       [ User Enters Text / Clicks Button ]
                       │
                       ▼
            [ Frontend Display State ]
                       │
             (Press Enter / Equal)
                       │
                       ▼
          [ POST /api/v1/evaluate ]
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       [ Success ]            [ Error ]
      (Status: 200)        (Status: 400)
             │                   │
             ▼                   ▼
     Render 'result'      Render error 'details'
```
