---
name: Calculator Frontend Client
description: React-TypeScript scientific responsive daily-use calculator UI with Tailwind CSS, memory register, history drawer, and full keyboard support
targets:
  - ../frontend/src/App.tsx
  - ../frontend/src/components/Calculator.tsx
  - ../frontend/Dockerfile
  - ../docker-compose.yml
---

# Calculator Frontend Client

## User Interface & Responsive Scientific Design

- The UI must render a daily-use, desktop-style scientific calculator mimicking a physical device.
- The layout must use Tailwind CSS and be fully responsive (mobile, tablet, and desktop viewports) with no horizontal scroll or clipped buttons.
- On smaller screens, the scientific buttons must fit perfectly (e.g. through a responsive layout grid or collapsible scientific section) without overcrowding the display.
- Display requirements:
  - An expression view area showing the full sequence of inputs.
  - A result view area displaying the current or final calculated result (or "Evaluating..." during API calls, or clear user-friendly errors).
  - A **visual badge or indicator** (such as an "M" marker) displayed whenever the memory register is non-zero.
  - An **angle unit toggle** ("Rad" and "Deg") to let the user switch between Radians and Degrees mode.
- Button keypads:
  - **Standard buttons:** Numbers `0-9`, `.`, operator buttons (`+`, `-`, `*`, `/`), parenthesis (`(`, `)`), clear (`C`), backspace (`⌫`), and evaluation (`=`).
  - **Scientific buttons:** `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `ln`, `log`, `sqrt`, `^` (exponentiation), `x²` (appends `^2`), `10^x` (appends `10^`), constants `pi` and `e`.
  - **Memory buttons:** `M+`, `M-`, `MR`, `MC`.

`[@test] ../frontend/src/App.test.tsx`

---

## Memory Register System & Angle Units

- The client must maintain a local **Memory Register** state (initialized to 0).
  - `M+`: Adds the current result (or standard input number if evaluated) to the memory value.
  - `M-`: Subtracts the current result from the memory value.
  - `MR`: Recalls the memory value and appends it to the active expression.
  - `MC`: Clears the memory register (sets it to 0).
- An angle unit state ("Radians" or "Degrees") must be maintained on the client. Toggling this state updates the UI indicator and gets transmitted as `angle_unit` in the API payload during evaluation.

`[@test] ../frontend/src/App.test.tsx`

---

## Session Calculation History Drawer

- The UI must implement an interactive, collapsible side drawer or collapsible section displaying the history of successfully evaluated expressions in the current session.
- **Persistent State:** The history must persist throughout the active user session in state.
- **Reloading / Reuse:**
  - Clicking a historical item's expression must reload that expression back into the active expression area.
  - Clicking a historical item's result must append or reload that result into the active expression area.
- A **Clear History** button must be provided to empty the current session's calculation history list.

`[@test] ../frontend/src/App.test.tsx`

---

## Keyboard Integration & Accessibility

- Keypress events must map to calculator actions:
  - Number keys `0`-`9` input digits.
  - Operators `+`, `-`, `*`, `/`, `^`, and parentheses `(`, `)` input operators/operations.
  - Dot `.` inputs a decimal point.
  - Enter or `=` evaluates the current expression.
  - Backspace deletes the last character.
  - Escape resets the calculator.
  - Key `p` or similar custom mapping inputs the constant `pi`.
- The UI must employ clear `aria-label` attributes on all interactive buttons.
- The display areas must use `aria-live` or appropriate role attributes for screen reader accessibility.

`[@test] ../frontend/src/App.test.tsx`

---

## API Integration & State Management

- Inputting digits, operators, constants, and scientific function names updates the expression state locally.
- Clicking `=` or pressing `Enter` triggers a `POST /api/v1/evaluate` request to the backend with:
  ```json
  {
    "operation": "expression_string",
    "angle_unit": "radians_or_degrees"
  }
  ```
- The UI must display a loading or evaluating state during API requests.
- Successful responses:
  - Display the exact numeric result returned by the backend.
  - Append the evaluation pair (`expression = result`) to the Session History list.
- Erroneous responses (e.g. math domain errors, syntax errors, division by zero) must display a clear, user-friendly error message on the display instead of breaking the app.
- For async memory actions (`M+`/`M-` triggering background evaluations), network or validation errors must be caught gracefully and display clear, user-friendly error messages rather than breaking the application state.

`[@test] ../frontend/src/App.test.tsx`

---

## Non-Functional & Containerized Deployment Specifications (Stage 3)

### 1. Unified Test Quality Thresholds
- Automated test suites must achieve and verify **$\ge 80\%$ Statement and Branch coverage** on the React client layer.
  `[@test] ../frontend/src/App.test.tsx`

### 2. Multi-Stage Production Frontend Dockerfile
- The frontend codebase must compile and bundle assets into a high-performance web server container.
- **Core Constraints:**
  - **Stage 1 (Build):** Leverage minimal node base image (`node:20-alpine`) to install dependencies and run static compilers (`npm run build`).
  - **Stage 3 (Runtime):** Copy built statics into Nginx runtime (`nginx:1.25-alpine`).
  - **Nginx Gzip Rules:** Enable gzip compression for standard text/CSS/JS file formats to reduce page loading latencies.
  - **Single Page Application Routing:** Configure Nginx's location settings so all client-side URL paths fallback to `index.html`.
  - **Port Exposure:** Expose port `80`.
  `[@test] ../frontend/Dockerfile`
  `[@test] ../frontend/nginx.conf`

### 3. Unified Orchestration Configuration
- Provide a `docker-compose.yml` file at the root repository directory to wire together frontend and backend modules under a single command.
- **Service Configuration:**
  - `backend`: Binds local port `8000` to container `8000`.
  - `frontend`: Binds local port `80` to container `80`, declaring dependency on `backend`.
  `[@test] ../docker-compose.yml`
