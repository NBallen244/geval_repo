## Context

The current web calculator app uses standard algebraic notation (infix) with operator precedence (PEMDAS). The backend parses expressions using Python's native `ast` module, evaluates them recursively, and performs operations with exact decimal precision using the `decimal` module. The React frontend maintains the expression as a single string and evaluates it either dynamically in the background or upon clicking the `=` key.

To support the Stage 4 breaking refactoring to Reverse Polish Notation (RPN), we must design a stack-based evaluator, a tokenizer, and an infix-to-postfix (Shunting Yard) converter, while adapting the frontend state and layout to display the stack levels in real-time.

See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**
- Implement a unified stack-based math evaluator engine in the Python backend.
- Implement the Shunting Yard Algorithm to parse standard algebraic expressions into RPN tokens to ensure backward compatibility for Standard Mode.
- Support direct RPN evaluation in the backend.
- Modify the React UI to support a dual mode: Standard Mode and RPN Mode.
- Add a real-time stack visualizer in the React UI displaying levels (X, Y, Z, T) when in RPN Mode.
- Adapt memory operations (MC, MR, M+, M-) to interact with the top of the stack (level X) in RPN Mode.
- Maintain $\ge 80\%$ test coverage in both backend and frontend.

**Non-Goals:**
- Supporting arbitrary multi-line programmability or user-defined variables (other than the single local memory register).
- Redesigning the Docker architecture or removing existing deployment setups (CORS, Nginx, etc.).

## Decisions

### Decision 1: Unified Stack-Based Evaluation
- **Approach**: In both Standard and RPN modes, the core engine will execute calculations via a stack evaluator.
  - In **Standard Mode**, standard infix expressions are converted to postfix (RPN) tokens using the Shunting Yard Algorithm, and then run through the stack evaluator.
  - In **RPN Mode**, postfix/RPN tokens or step-by-step operations are evaluated directly on the stack.
- **Rationale**: This consolidates all math calculation logic into a single, highly-testable stack engine rather than maintaining two entirely separate math evaluation systems.
- **Alternatives**: Maintaining the `ast`-based evaluator for standard mode and a separate stack engine for RPN mode. This was rejected due to increased complexity, code duplication, and maintenance overhead.

### Decision 2: Stack Element Ordering for Binary Operators
- **Approach**: Define clear stack semantics for binary operations ($a \text{ op } b$). If $b$ is pushed onto the stack after $a$, $b$ will occupy level $X$ (top of stack) and $a$ will occupy level $Y$. Executing the binary operator pops $X$ ($b$) and $Y$ ($a$), performs the calculation as $a \text{ op } b$ (or $Y \text{ op } X$), and pushes the result.
  - **Example**: Pressing `2`, `Enter`, `4`, `Enter`, `**` computes $2^4 = 16$.
- **Rationale**: This is the standard, intuitive RPN stack behavior established by classic HP calculators.
- **Alternatives**: Evaluating operators in reverse ($X \text{ op } Y$). This is highly unintuitive for users (e.g. division `10 / 2` would become `2 / 10`).

### Decision 3: Frontend Stack State and Virtual ENTER Key
- **Approach**: The React app will maintain the current active stack in state as an array of numbers/strings.
  - In **Standard Mode**, it continues to act as an infix input calculator.
  - In **RPN Mode**, the `=` key is replaced by an `ENTER` key. Clicking `ENTER` pushes the current numeric buffer onto the active stack. Clicking an operator key (like `+`, `*`, `sin`, etc.) immediately executes that operation on the stack via the backend, updating the stack state.
  - A real-time stack visualizer will display stack levels (T, Z, Y, X) stacked vertically.
- **Rationale**: Keeps the user experience tactile, visual, and compliant with physical RPN calculators.

### Decision 4: API Endpoint Interface Extension
- **Approach**: Modify the POST `/api/v1/evaluate` endpoint or introduce a clean payload contract to support either Standard or RPN mode operations.
  - Payloads can specify `"mode": "standard"` or `"mode": "rpn"`.
  - For standard mode, the payload is an infix string expression.
  - For RPN mode, the payload can either be a full RPN string (space-separated tokens) or a serialized stack with a pending operator to evaluate. Sending the full stack state or space-separated tokens ensures stateless REST compliance. We will support a space-separated RPN expression format (e.g., `"2 4 **"`) or direct evaluation of a full RPN token stream.
- **Rationale**: Keeps the API clean and stateless.

## Risks / Trade-offs

- **[Risk] Stack Underflow Error**: If a user executes a binary operator when there are fewer than 2 items on the stack, or a unary operator when the stack is empty.
  - *Mitigation*: The backend stack evaluator will raise a specific `CalculatorError("Insufficient operands on stack")` which maps to an HTTP 400 Bad Request error. The frontend will display this error and prevent crash.
- **[Risk] Decimal Precision during intermediate stack states**: RPN users can do multiple step-by-step intermediate evaluations, which might introduce floating-point errors if stored as standard JavaScript floats.
  - *Mitigation*: The frontend will maintain stack levels as exact strings, and the backend will parse and evaluate them using `decimal.Decimal` to ensure exact decimal precision is preserved at every intermediate step.
- **[Risk] Maintaining live preview**: Live-preview makes sense for standard infix mode as the user types, but in RPN mode, evaluation is immediate and step-by-step.
  - *Mitigation*: Disable live-preview debouncing when the user is in RPN Mode.
