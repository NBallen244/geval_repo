# Data Model: Reverse Polish Notation (RPN) Engine and UI Migration

This document defines the data models, payload structures, schemas, and client/server states for the RPN calculator application.

---

## 1. Backend REST API Schema Entities

### Entity 1: `CalculationRequest` (Pydantic Model)
Represents the input payload sent from the React client to the FastAPI backend.

| Field Name | Type | Validation Rules | Description |
|:---|:---|:---|:---|
| `expression` | `string` | Min: 1 character, Max: 1000 characters | The mathematical formula or space-separated postfix string to evaluate. |
| `angle_unit` | `string` | Value MUST be `"radians"` or `"degrees"`. Defaults to `"radians"`. | The angular units used for trigonometric calculations. |
| `mode` | `string` | Value MUST be `"standard"` or `"rpn"`. Defaults to `"standard"`. | The mode of evaluation. `"standard"` triggers Shunting Yard. `"rpn"` evaluates directly. |

---

### Entity 2: `CalculationResponse` (Pydantic Model)
Represents the computed outcome payload returned from the backend.

| Field Name | Type | Validation Rules | Description |
|:---|:---|:---|:---|
| `expression` | `string` | Matches the request expression. | The original evaluated mathematical expression. |
| `result` | `string` | Valid high-precision decimal representation. | The final computed result (top of stack). |
| `stack` | `list[string]` | Optional. Required in RPN mode. | The complete list of remaining stack levels after execution (level X is the last item). |

---

## 2. Frontend Client Application State

The React client manages UI-side state within the interactive layout:

### State 1: `CalculatorState` (TypeScript Interface)

- **`activeMode`**: `"standard" | "rpn"`
  - Determines which input layout, button bindings, and keyboard listeners are active.
- **`currentInput`**: `string`
  - The current value typed into the active display buffer (cleared upon pressing `ENTER` in RPN mode).
- **`stack`**: `string[]`
  - Active RPN calculation stack array. Level X corresponds to `stack[stack.length - 1]`, level Y is `stack[stack.length - 2]`, and so on.
- **`result`**: `string`
  - Holds the latest computed evaluation result.
- **`error`**: `string`
  - Holds active API/validation errors (e.g. `"STACK_UNDERFLOW"`, `"DIVISION_BY_ZERO"`).
- **`angleUnit`**: `"radians" | "degrees"`
  - Active angle setting.
- **`memoryRegister`**: `string`
  - Holds the numerical decimal value stored in memory via memory keys (`M+`, `M-`, `MR`, `MC`).

---

## 3. Backend Evaluator Core State

### Entity 3: `EvaluationStack` (LIFO Stack)
The primary execution structure within `evaluator.py`.

- **Internal Data**: `list[Decimal]`
- **Invariants & Validations**:
  - Binary Operations: Stack size MUST be $\ge 2$ before execution.
  - Unary Operations: Stack size MUST be $\ge 1$ before execution.
  - Constants & Numerical Inputs: Push triggers conversion to `Decimal(token_string)` to maintain high-precision integrity.
  - Limits: No arbitrary stack depth limit, but UI displays up to 4 levels (`X`, `Y`, `Z`, `T`) clearly.
