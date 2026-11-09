# Data Model: Scientific Web Calculator & Extended State Management

This document defines the data models and schemas used in Stage 2 of the Web Calculator application.

## 1. API Models (TypeScript & Python/Pydantic)

To maintain absolute type-safety between the backend FastAPI service and frontend React client, the following models define the structural contract of all REST communication.

### CalculationRequest
Used when submitting an expression for calculation.
* **Fields**:
  - `expression` (`string`): The mathematical formula to parse and evaluate. Must have length between 1 and 1000 characters.
  - `angle_unit` (`string`, optional): The unit to use for trigonometric operations. Valid values: `"radians"`, `"degrees"`. Defaults to `"radians"`.

* **Pydantic Schema (Python)**:
  ```python
  from pydantic import BaseModel, Field
  from typing import Optional

  class CalculationRequest(BaseModel):
      expression: str = Field(
          ...,
          min_length=1,
          max_length=1000,
          description="The mathematical expression to evaluate.",
          example="sin(pi / 2) + 3 ^ 2"
      )
      angle_unit: Optional[str] = Field(
          "radians",
          description="Angle unit for trig operations. Must be 'radians' or 'degrees'."
      )
  ```

* **TypeScript Interface**:
  ```typescript
  export interface CalculationRequest {
    expression: string;
    angle_unit?: 'radians' | 'degrees';
  }
  ```

---

### CalculationResponse
Returned by the backend upon successful mathematical evaluation.
* **Fields**:
  - `expression` (`string`): The original evaluated expression.
  - `result` (`string`): The computed precise mathematical outcome represented as a string.

* **Pydantic Schema (Python)**:
  ```python
  class CalculationResponse(BaseModel):
      expression: str = Field(..., description="The original evaluated expression")
      result: str = Field(..., description="The highly precise computed decimal result as a string")
  ```

* **TypeScript Interface**:
  ```typescript
  export interface CalculationResponse {
    expression: string;
    result: string;
  }
  ```

---

### ErrorResponse
Returned by the backend upon any syntactic or mathematical validation failure.
* **Fields**:
  - `error` (`string`): A machine-readable error code (e.g., `"DIVISION_BY_ZERO"`, `"SYNTAX_ERROR"`, `"DOMAIN_ERROR"`).
  - `details` (`string`): A human-readable description of the issue to display to the user.

* **Pydantic Schema (Python)**:
  ```python
  class ErrorResponse(BaseModel):
      error: str = Field(..., description="Unique error identifier code")
      details: str = Field(..., description="User-friendly error explanation")
  ```

* **TypeScript Interface**:
  ```typescript
  export interface ErrorResponse {
    error: string;
    details: string;
  }
  ```

---

## 2. In-Memory Client State Entities (TypeScript Only)

These entities represent client-side persistent structures that do not exist on the stateless server.

### CalculationSession
Represents the current calculator application session context.
* **Fields**:
  - `history` (`HistoryItem[]`): Array of calculations successfully processed during the current page lifespan.
  - `memory_register` (`string`): The active numeric value stored in memory. Represented as a string to guarantee exact precision during storage and display.
  - `angle_unit` (`'radians' | 'degrees'`): The active angle evaluation mode.
  - `expression` (`string`): The current mathematical expression in the active input display.

* **TypeScript Interface**:
  ```typescript
  export interface CalculationSession {
    history: HistoryItem[];
    memory_register: string;
    angle_unit: 'radians' | 'degrees';
    expression: string;
  }
  ```

---

### HistoryItem
Represents an individual entry in the session calculation history log.
* **Fields**:
  - `id` (`string`): Unique identifier (UUID or sequential) for the UI list indexing.
  - `expression` (`string`): The mathematical formula that was evaluated.
  - `result` (`string`): The precise result returned by the API.

* **TypeScript Interface**:
  ```typescript
  export interface HistoryItem {
    id: string;
    expression: string;
    result: string;
  }
  ```
