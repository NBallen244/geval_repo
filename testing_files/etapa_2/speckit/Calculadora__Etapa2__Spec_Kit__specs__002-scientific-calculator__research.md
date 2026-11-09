# Technical Research: Scientific Web Calculator & Extended State Management

This document details the research, technical decisions, and rationales for implementing Stage 2 of the Web Calculator application.

## 1. Mathematical Evaluation & Precision

### Exact Decimal Precision with Transcendental Functions
* **Decision**: Basic arithmetic operations continue to use Python's built-in `decimal.Decimal` module. Transcendental operations (trigonometric, logarithms, powers, roots) will be evaluated using Python's standard `math` module via intermediate conversion to `float`, then converted back to `decimal.Decimal` with standard context precision (at least 28 decimal digits) and normalized to eliminate trailing zeros.
* **Rationale**: Python's `decimal` module does not natively support advanced transcendental functions like trigonometric or logarithmic operations out of the box without complex custom Taylor series or external packages. Since transcendental functions often result in irrational numbers, standard floating-point representation cannot be avoided entirely. Intermediate conversion to standard float, evaluation in `math`, and conversion back to `Decimal` rounded to 28 decimal places is the industry standard for lightweight calculators. It avoids adding external dependencies while preserving 28-digit precision for the remainder of the chained calculation.
* **Alternatives Considered**: 
  - Using an external package like `mpmath` or `sympy` for arbitrary-precision math. *Rejected* because it adds heavy third-party dependencies, complex license checking, and increases bundle/deployment sizes, which is unjustified for standard high-school or scientific calculator layouts.
  - Implementing custom Taylor series expansions using pure `Decimal`. *Rejected* as overly complex, prone to performance issues, and hard to verify mathematically for all edge cases.

### Safe AST Parsing and Whitelisting
* **Decision**: We will extend the existing AST evaluator (`backend/src/core/evaluator.py`) to support:
  - Whitelisting of functions: `{"sin", "cos", "tan", "asin", "acos", "atan", "sqrt", "ln", "log10", "root"}`.
  - Whitelisting of constants: `{"pi", "e"}`.
  - Mapping function calls (`ast.Call`) and variables (`ast.Name`) to their corresponding mathematical evaluations in our evaluator function.
  - Translating the visual caret `^` into Python's exponentiation operator `**` in the expression string before parsing, so it natively compiles to `ast.Pow`.
* **Rationale**: Restricting parsing to a strict whitelist of AST nodes (`ast.Expression`, `ast.Constant`, `ast.BinOp`, `ast.UnaryOp`, `ast.Call`, `ast.Name`) prevents any arbitrary execution of code, injection of system calls, or variable assignments. It guarantees a highly secure sandboxed mathematical execution.

---

## 2. Stateless Angle Toggle Support

* **Decision**: To support Degrees and Radians, the `POST /api/v1/evaluate` payload will be extended to accept an optional `angle_unit` field:
  ```json
  {
    "expression": "sin(90)",
    "angle_unit": "degrees"
  }
  ```
  - When `angle_unit="degrees"`, the backend converts arguments of `sin`, `cos`, and `tan` from degrees to radians using `math.radians()` before evaluation.
  - For `asin`, `acos`, and `atan`, the backend evaluates the result in radians and converts it to degrees using `math.degrees()` before returning.
  - If `angle_unit="radians"` (or is absent), the system operates directly in radians.
* **Rationale**: This design respects the stateless RESTful architecture of the backend. It keeps the calculation engine simple and robust, avoiding the need for the backend to maintain a session or track the user's active UI state.
* **Alternatives Considered**: 
  - Storing the selected angle unit in a backend database or user session. *Rejected* because it violates the statelessness of the REST API and increases infrastructure overhead.

---

## 3. Frontend-Managed Memory and History Registers

### Memory Register System
* **Decision**: The memory register value is managed in React state as a single precise state variable (`memoryValue: string`).
  - `M+` / `M-`: Computes the updated memory by evaluating the current display result plus/minus the existing memory value on the frontend, or sending a request to the backend to perform the high-precision sum.
  - `MR`: Injects the current memory value as a literal string directly into the expression input.
  - `MC`: Resets the frontend state variable to `0`.
  - Display Badge: A simple conditional rendering displays the "M" badge when `parseFloat(memoryValue) !== 0`.
* **Rationale**: Managing memory on the frontend keeps the backend stateless, simplifies components, and ensures immediate, responsive UI updates.

### Session History Drawer
* **Decision**: Session history is stored as an array of objects in React state (`history: Array<{id: string, expression: string, result: string}>`).
  - When a calculation returns successfully, the expression and result are added to the list.
  - Clicking on the expression or result inserts it directly into the input cursor position.
  - A "Clear History" button sets the history array back to `[]`.
* **Rationale**: Client-side state is perfect for session-only history. It is highly performant and requires zero backend resources.
