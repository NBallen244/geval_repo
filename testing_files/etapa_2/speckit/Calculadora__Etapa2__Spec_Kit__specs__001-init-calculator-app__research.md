# Research Report: Web Calculator Implementation

This document consolidates findings, technical decisions, and library selection for the Web Calculator
application, ensuring alignment with `SEED.md` and the project `constitution.md`.

## 1. Decimal Precision & Precedence Evaluation (Backend)

### Decision
Use Python's built-in `decimal` module for high-precision math and the built-in `ast` (Abstract Syntax Tree) module to parse mathematical expressions safely.

### Rationale
- **Decimal Module**: Standard floating-point evaluation in Python (and JS) suffers from binary representation limits (e.g. `0.1 + 0.2` becomes `0.30000000000000004`). Python's `decimal.Decimal` handles arbitrary-precision decimal arithmetic, yielding `0.3` exactly.
- **AST Parsing**: Evaluating expressions using `eval()` is a critical security vulnerability. Using Python's `ast.parse` and traversing the tree with a customized recursive node evaluator allows us to:
  1. Enforce strict mathematical precedence (PEMDAS) inherently through AST node structures.
  2. Whitelist only safe operations (addition, subtraction, multiplication, division, parentheses, exponents) and reject any functions, code-execution primitives, or variables.
  3. Seamlessly map float literals to `Decimal` types during evaluation.

### Alternatives Considered
- **Third-Party Parsers (e.g., `sympy`, `numexpr`)**: Rejected to keep the API lightweight and avoid unnecessary external dependencies.
- **Simple Regex/Stack Evaluator (e.g., Shunting-Yard Algorithm)**: While viable, `ast` is built-in, highly robust, automatically constructs precedence syntax trees, and reduces manual parsing bugs.

---

## 2. API Design & Type Safety (FastAPI & React Integration)

### Decision
Expose a single REST endpoint: `POST /api/v1/evaluate` accepting a JSON payload with `expression` and returning `expression` and `result` with status `200 OK`. Error states (such as division by zero or syntax errors) will return status `400 Bad Request` with structured error messages.

### Rationale
- **FastAPI**: Provides automatic OpenAPI schema generation, rapid speed, and built-in type validation using `pydantic`.
- **TypeScript Integration**: By defining matching TypeScript interfaces (`CalculationRequest`, `CalculationResponse`, `ErrorResponse`) on the frontend, we guarantee structural type-safety and catch contract drift early.

### Alternatives Considered
- **GET Endpoint with Query Params**: Rejected. Complex expressions can include special characters (like `+` or `/`) which need URL-encoding and can cause routing/security filter issues. `POST` with a JSON body is much cleaner and more secure.

---

## 3. Keyboard Integration & Focus Accessibility (Frontend)

### Decision
Implement global keydown listeners using React `useEffect` hooks, mapping keys to standard button actions. Standard ARIA attributes (`aria-live="polite"` for calculation results, `aria-label` for symbol buttons) will be applied directly.

### Rationale
- ** Tactile Accessibility**: Listening to document-level keydowns makes the interface functional for speed-oriented physical-keyboard users.
- **Screen Reader Support**: Accessibility tags are required by the constitution to ensure that visually impaired users can navigate the button matrix and hear calculation outputs immediately.

### Alternatives Considered
- **Local Input-Focused Listeners**: Rejected. This requires the user to manually click an input box first. A global document listener ensures a tactile "ready out-of-the-box" experience matching physical desktop devices.
