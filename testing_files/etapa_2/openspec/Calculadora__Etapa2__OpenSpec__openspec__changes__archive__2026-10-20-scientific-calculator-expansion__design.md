## Context

See `proposal.md` for the motivation. The current system uses a stateless FastAPI backend to evaluate standard arithmetic expressions using Python's `ast` parser and custom manual AST traversal to maintain absolute decimal precision. The frontend is a single-page React app that performs live preview evaluation as the user types and sends final requests on Enter/Equal. We need to expand this design to support advanced scientific operations, angle modes, local memory, and calculation history.

## Goals / Non-Goals

**Goals:**
- Maintain complete statelessness of the FastAPI backend while enabling advanced scientific function evaluations and angle modes.
- Achieve exact decimal precision for all standard operators, powers, roots, and logarithms natively, and clean decimal representations for trigonometric results.
- Implement responsive, interactive, and accessible UI additions (scientific keyboard toggle, interactive history drawer, memory badge) conforming to the look-and-feel of Stage 1.
- Avoid introducing any heavy external libraries or databases to maintain a minimal surface area.

**Non-Goals:**
- Server-side persistence of calculation history or memory register across browser reloads or distinct users (local state or optional LocalStorage is sufficient).
- Dynamic plotting of graphs or supporting arbitrary variables outside standard constants (`pi`, `e`).

## Decisions

### 1. Stateless API Extension with Request-Scoped Context
- **Decision**: Update `POST /api/v1/evaluate` request body model (`EvaluateRequest`) to include an optional field `angle_unit: str = "radians"` (with accepted values: `"radians"` and `"degrees"`).
- **Rationale**: Keeps the backend completely stateless, avoiding any race conditions or session management complexity that would arise from maintaining active angle modes on the server.
- **Alternatives Considered**: Dedicated stateful session endpoint for angle mode, but this would break backend statelessness and require session tracking.

### 2. AST Evaluator Upgrades for Constants, Functions, and Powers
- **Decision**: Upgrade `evaluate_ast_node(node)` in `backend/app/calculator.py` to handle:
  - `ast.Name`: Resolve `"pi"` to `decimal.Decimal("3.141592653589793238462643383")` and `"e"` to `decimal.Decimal("2.718281828459045235360287471")`.
  - `ast.Call`: Resolve functions `sin`, `cos`, `tan`, `asin`, `acos`, `atan` (converted through standard Python `math` module floats and cast back to `Decimal` string representation), `ln` (mapped to `Decimal.ln()`), `log10` (mapped to `Decimal.log10()`), `sqrt` (mapped to `Decimal.sqrt()`), and `root(x, y)` (evaluated as $x^{1/y}$ using `**`).
  - `ast.BinOp` with `ast.Pow`: Map to `decimal.Decimal.__pow__` or standard power operations with domain validation.
  - Expand `allowed_chars` set on the input validator to permit alphanumeric character components used in allowed function/constant names (e.g. `[a-z0-9]`), while strictly restricting parsing to the approved whitelist at the AST level to prevent any arbitrary code execution.
- **Rationale**: Guarantees secure, robust math compilation while keeping standard evaluation behaviors intact.

### 3. Frontend-Managed Memory Register & Session History
- **Decision**: Manage the memory register (`memory` state initialized to `0`) and session history (`history` list state of `{ expression, result }` objects) entirely inside the React frontend.
- **Rationale**: Keeps memory operations and previous calculation listings instantaneous, light on server resources, and perfectly matched to local user interactions. Memory "M" badge and sidebar elements will be implemented with complete semantic and ARIA markers.
- **Alternatives Considered**: Server-managed memory/history endpoints, but this introduces unnecessary network latency and database persistence requirements.

### 4. Collapsible Advanced/Scientific Keypad for Responsive Devices
- **Decision**: Structure the frontend UI grid to house a toggle button ("Scientific" or "Advanced") which expands or collapses the scientific keypad rows on mobile/tablet screens. On desktop screens, both basic and scientific keys are shown side-by-side.
- **Rationale**: Preserves the clean layout and prevents the UI grid from being cramped or clipped on smaller viewports.

## Risks / Trade-offs

- **[Risk] Trigonometric precision conversion** → Floating point values from `math.sin` can introduce rounding anomalies when converted to Decimal.
  - *Mitigation*: Round trigonometric results to a reasonable precision (e.g., 15 decimal places) during Decimal casting, so that values like `sin(pi)` return exactly `0` rather than `1e-16`.
- **[Risk] Arbitrary variable injection** → Permitting letters in the expression validation set could lead to security risks if someone tries to inject malicious python code.
  - *Mitigation*: Strictly validate AST nodes. Only allow `ast.Expression`, `ast.Constant`, `ast.BinOp`, `ast.UnaryOp`, `ast.Call` (with whitelisted function names), and `ast.Name` (with whitelisted constant names). Any other AST node type must immediately raise a `CalculatorError`. This ensures sandbox integrity regardless of character allowance.
