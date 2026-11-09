---
name: Calculator Frontend Client
description: React-TypeScript responsive dual-mode Standard/RPN scientific calculator UI with Tailwind CSS, stack display, memory register, history, and full keyboard support
targets:
  - ../frontend/src/App.tsx
  - ../frontend/src/components/Calculator.tsx
  - ../frontend/Dockerfile
  - ../docker-compose.yml
---

# Calculator Frontend Client

## Dual Mode: Standard Infix & RPN Workflows

The frontend UI supports two operational modes: **Standard Infix Mode** and **RPN Mode**, with a toggle to switch between them.

### 1. Mode Selector Toggle
- A visual toggle allows the user to switch between `"Standard"` and `"RPN"` modes.
  `[@test] ../frontend/src/App.test.tsx`

### 2. Standard Infix Mode Behavior
- Behaves as a traditional calculator. Digits and operators build an expression. Clicking `=` or pressing `Enter` calls `POST /api/v1/evaluate` with `{ "operation": expression, "angle_unit": unit, "mode": "infix" }`.
- **Dynamic Postfix Preview:** Standard mode displays a small visual preview converting the active infix expression to its corresponding RPN postfix representation (e.g. `2 3 4 * +` for `2 + 3 * 4`).
  `[@test] ../frontend/src/App.test.tsx`

### 3. RPN Stack Mode Behavior
- **Visual Stack Display:** Displays active stack levels $T$ (top), $Z$, $Y$, $X$ (bottom / active input). Unused levels are displayed as `0` or empty.
- **Dedicated ENTER button:**
  - Standard `=` key is replaced by `ENTER` (or `PUSH` action).
  - Pressing `ENTER` or clicking `ENTER` pushes the current input value in $X$ onto the stack.
- **Immediate Operator Evaluation:**
  - Pressing an operator (like `+`, `-`, `*`, `/`, `^`) or function (like `sin`, `sqrt`, `ln`) immediately executes that operation on the active stack values.
  - Evaluation is routed to `POST /api/v1/evaluate` with `mode: "postfix"` to ensure high-precision Decimal evaluation.
  - The stack is updated in real-time with the returned result.
- **Error Handling:** If an operation causes stack underflow (insufficient operands) or a math domain error, the error is displayed on the screen and the stack state is preserved.
  `[@test] ../frontend/src/App.test.tsx`

---

## User Interface & Responsive Scientific Design

- The layout must use Tailwind CSS and be fully responsive (mobile, tablet, and desktop viewports) with no horizontal scroll.
- Display requirements:
  - Display showing standard expression, postfix preview, or the RPN stack registers.
  - A **visual badge or indicator** (such as an "M" marker) displayed whenever the memory register is non-zero.
  - An **angle unit toggle** ("Rad" and "Deg") to switch between Radians and Degrees.
- Button keypads:
  - **Standard buttons:** Numbers `0-9`, `.`, operator buttons (`+`, `-`, `*`, `/`), parenthesis (disabled in RPN mode), clear (`C`), backspace (`⌫`), and evaluation (`=` in standard, `ENTER` in RPN).
  - **Scientific buttons:** `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `ln`, `log`, `sqrt`, `^`, `x²` (appends `^2` in standard, or evaluates squaring in RPN), `10^x` (appends `10^` in standard, or evaluates in RPN), constants `pi` and `e`.
  - **Memory buttons:** `M+`, `M-`, `MR`, `MC`.

`[@test] ../frontend/src/App.test.tsx`

---

## Memory Register System & Angle Units

- The client maintains a local **Memory Register** (initialized to 0).
  - `M+`/`M-`: Performs memory addition/subtraction.
  - `MR`: Recalls the memory value and inserts/appends it.
  - `MC`: Clears the memory register (sets to 0).
- Supports switching between Radians and Degrees mode, transmitting `angle_unit` in all API evaluation payloads.

`[@test] ../frontend/src/App.test.tsx`

---

## Session Calculation History Drawer

- Session calculations are recorded and displayed in a collapsible drawer.
- In Standard Mode: Clicking a historical item's expression or result reloads or appends it.
- In RPN Mode: Clicking a historical item's result pushes that value onto the RPN stack.
- A **Clear History** button is provided.

`[@test] ../frontend/src/App.test.tsx`

---

## Keyboard Integration & Accessibility

- Keypress events map to calculator actions:
  - Number keys `0`-`9` and `.` input digits.
  - Operators `+`, `-`, `*`, `/`, `^` input operators or execute stack reduction immediately in RPN mode.
  - Enter or `=` evaluates the expression (standard) or acts as `PUSH` / `ENTER` (RPN mode).
  - Backspace deletes the last character.
  - Escape resets the calculator.
  - Key `p` inputs the constant `pi`.
- Clear `aria-label` attributes on all buttons.

`[@test] ../frontend/src/App.test.tsx`

---

## Non-Functional & Containerized Deployment Specifications (Stage 3)

### 1. Unified Test Quality Thresholds
- Automated test suites must achieve and verify **$\ge 80\%$ Statement and Branch coverage** on the React client layer.
  `[@test] ../frontend/src/App.test.tsx`

### 2. Multi-Stage Production Frontend Dockerfile
- Compiled with static compilers and served with Nginx.
  `[@test] ../frontend/Dockerfile`
  `[@test] ../frontend/nginx.conf`
