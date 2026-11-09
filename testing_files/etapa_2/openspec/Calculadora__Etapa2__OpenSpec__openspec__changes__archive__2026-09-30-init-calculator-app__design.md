## Context

We are starting from scratch in the `OpenSpec` workspace directory. This design establishes a clean, decoupled architecture:
1. A FastAPI-based Python backend located at `backend/` to handle safe and exact mathematical evaluation.
2. A React-based TypeScript frontend located at `frontend/` to manage UI components, visual states, standard keyboard interactions, and accessibility.

See `proposal.md` for overall motivation.

## Goals / Non-Goals

**Goals:**
- Provide a robust mathematical parsing engine with standard PEMDAS rules and strict decimal precision.
- Build a visually-polished, highly responsive physical-desktop-calculator mimic layout with a dual-line display (expression + result).
- Implement thorough accessibility (keyboard capture, ARIA labels, focus states) without clipping or styling breakage.
- Ensure the backend has robust test coverage using `pytest`.

**Non-Goals:**
- Support for complex math/scientific functions (e.g., trigonometric, algebraic variables, calculus) beyond standard arithmetic operators (+, -, *, /, parentheses).
- Multi-user authentication, history persistence in databases, or server-side session tracking.

## Decisions

### 1. Mathematical Evaluation Strategy
- **Choice**: Hand-written recursive descent parser or a safe AST (Abstract Syntax Tree) walker leveraging Python's `ast` module, where all math operations are executed using `decimal.Decimal` objects.
- **Rationale**: Avoids the security vulnerabilities of `eval()` while allowing us to capture and format floating-point values perfectly to avoid binary IEEE-754 errors (e.g., `0.1 + 0.2` becomes exactly `0.3`).
- **Alternatives Considered**: 
  - *SymPy / External Math Libraries*: High dependencies overhead, not needed for basic arithmetic.
  - *Raw Python `eval()`*: Unsafe, security hazard, uses float math by default.

### 2. Frontend Framework & Styling
- **Choice**: React with TypeScript (bootstrapped with Vite) and Vanilla CSS.
- **Rationale**: TS provides complete compiler-level safety for API responses and payload contracts. Vite is extremely fast to build and run. Vanilla CSS is highly flexible, lightweight, and avoids heavy runtime styling dependencies or complex tailwind configurations.
- **Alternatives Considered**: Tailwind CSS (complex configuration, sometimes prone to clipping/layout bugs on smaller viewports if not carefully managed).

### 3. API Contract and Payload Structure
- **Choice**: JSON REST API with clear payload structure and meaningful status codes.
- **Payload Structure**:
  - Request: `POST /api/v1/evaluate`
    ```json
    { "expression": "12.5 + 3 * (4 - 1.5) / 2" }
    ```
  - Success Response (200 OK):
    ```json
    { "expression": "12.5 + 3 * (4 - 1.5) / 2", "result": "16.25" }
    ```
  - Error Response (400 Bad Request):
    ```json
    { "error": "Division by zero" }
    ```
- **Rationale**: Clean separation of concerns. The frontend manages local cursor and button pushes; the backend acts as a stateless validation and math oracle.

## Risks / Trade-offs

- **[Risk] Float arithmetic anomalies** → *Mitigation*: Ensure the backend parser never casts input strings to floats. Numbers must be parsed directly into Python's `decimal.Decimal` type from string tokens.
- **[Risk] Focus-stealing / Keyboard hook collision** → *Mitigation*: Register the physical keyboard event listener on the global `window` object in React, but ensure we check `event.target` to prevent hijacking input text fields if forms are added later. Ensure active visual focus indicators are visible at all times.
