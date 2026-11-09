# Research Report: Shunting Yard Algorithm and Stack-Based RPN Engine

This report details the architectural investigation, algorithm choices, and system-wide design patterns for migrating the web calculator app from traditional infix parsing to a robust stack-based Reverse Polish Notation (RPN) engine.

---

## 1. Core Mathematical Evaluation Architecture

### Decision
Implement the **Shunting Yard Algorithm** to parse and convert infix mathematical strings into a stream of postfix/RPN tokens, which are then processed by a dedicated **Stack-Based Evaluation Engine**. 
The backend REST API `/api/v1/evaluate` will be extended to support standard infix and explicit postfix (RPN) payloads through a `mode` parameter.

### Rationale
- **Single Source of Truth**: By sharing the same underlying Stack-Based Evaluator for both Infix (after conversion) and direct RPN inputs, we guarantee 100% behavioral consistency and eliminate mathematical discrepancies.
- **Precision Preservation**: Using Python's native `Decimal` library directly within the stack push/pop and evaluation cycles eliminates floating-point representation anomalies (e.g., standard floats returning `0.30000000000000004` instead of `0.3`).
- **PEMDAS Enforcement**: The Shunting Yard algorithm mathematically guarantees correct operator precedence and associativity, resolving the AST reliance of the legacy codebase and facilitating cleaner error reporting.

### Alternatives Considered
- **Direct AST Evaluation (Legacy)**: In the legacy codebase, standard expressions were parsed into a Python AST. While functional, it is incompatible with direct RPN stack inputs and makes real-time stack state synchronization very complex.
- **Frontend-only RPN Evaluation**: Evaluating RPN calculations on the client side in JavaScript. This was rejected because it violates **Constitution Principle IV (RESTful Clean Architecture)**, which mandates that all arithmetic operations and mathematical validations occur strictly on the backend.

---

## 2. Shunting Yard Algorithm Details with Scientific Functions

### Decision
The Shunting Yard converter will handle standard operators, functions (unary and binary), and constants by assigning precise precedence and associativity properties:

| Token / Type | Precedence | Associativity | Description / Usage |
|:---|:---:|:---:|:---|
| `+`, `-` (Binary) | 1 | Left | Addition, Subtraction |
| `*`, `/` | 2 | Left | Multiplication, Division |
| `^` (or `**`) | 3 | Right | Exponentiation / Power |
| `+`, `-` (Unary) | 4 | Right | Positived/Negated Sign (e.g., `-5`) |
| Scientific Functions | 5 | Right | `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sqrt`, `ln`, `log10`, `root` |
| `(`, `)` | - | - | Grouping Parentheses |
| Constants / Numbers | - | - | `pi`, `e`, numerical literals |

#### Handling Multi-Argument Functions (`root(x, y)`)
When Shunting Yard parses infix expressions, multiple-argument functions are handled by adding support for a argument separator `,` (comma):
1. When a comma `,` is encountered, tokens from the operator stack are popped to the output queue until a left parenthesis `(` is at the top of the stack.
2. This ensures that the left operand (e.g., `x`) is fully resolved and outputted to the queue.
3. The comma itself is discarded.
4. When the matching right parenthesis `)` is closed, the function `root` is popped to the output queue.
5. Infix `root(8, 3)` converts to postfix `8 3 root`.

---

## 3. Stack Evaluation and RPN Engine Specification

### Decision
The stack-based execution engine operates on a list of tokens processed from left to right. It maintains an evaluation stack (a LIFO list of high-precision `Decimal` objects):

1. **Numeric / Constant Token**: Push the corresponding `Decimal` value onto the stack. For constants (`pi`, `e`), push their precise constant values (e.g., `Decimal("3.141592653589793238462643383")`).
2. **Binary Operator / Function**: Pop the top two elements from the stack.
   - For an operator like `/`, pop `right_operand` first, then `left_operand`. Evaluate `left_operand / right_operand` and push the result back onto the stack.
   - For the binary function `root`, pop `y` (degree) first, then `x` (radicand). Evaluate $x^{1/y}$ and push.
3. **Unary Operator / Function**: Pop the top element from the stack (e.g., `x`). Apply the function (e.g., `sin(x)` or negated `-x`) and push the result.
4. **Final Result**: Once all tokens are processed, the top of the stack is returned as the primary calculation result.

---

## 4. API & State Synchronization Design

### Decision
Extend the FastAPI request/response schema to allow stateful RPN interaction.

**Request Payload (`CalculationRequest`)**:
```json
{
  "expression": "10 20 30 +",
  "angle_unit": "radians",
  "mode": "rpn"
}
```

**Response Payload (`CalculationResponse`)**:
```json
{
  "expression": "10 20 30 +",
  "result": "50",
  "stack": ["10", "50"]
}
```

#### State Synchronization Flow in RPN Mode:
1. The frontend maintains an array state `stack: string[]` representing the stack.
2. When the user types a number and presses `ENTER`, the frontend appends that number to the `stack` array.
3. When the user clicks an operator (e.g. `+`):
   - The frontend serializes the entire stack as a space-separated string (e.g., `"10 50 +"`).
   - It calls `/api/v1/evaluate` with `mode: "rpn"`.
   - The backend processes the RPN string, performs the calculation, and returns the new stack state `["60"]`.
   - The frontend overwrites its local `stack` state with the returned `stack` payload, updating the X, Y, Z, T visualizer instantly.
4. This ensures that the backend remains the sole authority for mathematical operations, conforming perfectly to our RESTful Clean Architecture guidelines.
