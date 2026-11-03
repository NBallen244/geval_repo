# Glossary: Basic Web Calculator Specification

Downstream workflows and readers must use these terms exactly. Introducing any synonyms anywhere else in the code, tests, or documentation is a visual and behavioral violation of this contract.

---

*   **Expression** — A mathematical string representing arithmetic operations to be evaluated (e.g., `12.5 + 3 * (4 - 1.5) / 2`).
*   **Token** — The smallest individual unit of an Expression, representing either an Operand, an Operator, or a Parenthesis.
*   **Operand** — A numeric value in an Expression, which can be an integer or an arbitrary-precision decimal number.
*   **Operator** — A symbol representing an arithmetic operation (specifically `+`, `-`, `*`, `/`).
*   **PEMDAS** — The standard order of operations: Parentheses, Exponents (not supported in v1), Multiplication, Division, Addition, Subtraction.
*   **AST** — Abstract Syntax Tree, a tree representation of the syntactic structure of an Expression, used by the Backend Service for safe parsing and validation.
*   **Primary Display** — The upper, larger display area of the calculator screen that shows the full, active Expression constructed by the user.
*   **Result Display** — The lower, dedicated display area of the calculator screen showing either the live, debounced calculation preview or the final exact Evaluation Result.
*   **Evaluation Result** — The exact calculated decimal value of an Expression, produced by the Backend Service using the `decimal` module.
