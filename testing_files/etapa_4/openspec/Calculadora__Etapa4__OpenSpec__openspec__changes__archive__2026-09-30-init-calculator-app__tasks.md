## 1. Backend Setup and Core Math Engine

- [x] 1.1 Scaffold the `backend/` directory, initialize a Python virtual environment, install FastAPI, pytest, uvicorn, and create a `requirements.txt` file. Verify setup by checking that all dependencies install successfully and uvicorn starts.
- [x] 1.2 Implement the exact decimal expression evaluation parser utilizing Python's `ast` module or custom tokenization. Ensure expressions are evaluated with `decimal.Decimal` precision and strictly follow PEMDAS. Verify by running simple Python test evaluations for addition, subtraction, multiplication, division, and parentheses.
- [x] 1.3 Implement the FastAPI web server exposing `POST /api/v1/evaluate` accepting `{ "expression": string }` and returning `{ "expression": string, "result": string }` or a `400` status with `{ "error": string }`. Verify by querying the endpoint using a dummy client or curl, and checking response codes and JSON content.
- [x] 1.4 Write backend unit tests in `backend/tests/test_calculator.py` with `pytest` covering simple math, PEMDAS precedence, exact decimal calculation (`0.1 + 0.2` strictly evaluating to `0.3`), division by zero, and unclosed/invalid parentheses. Verify by running `pytest` in the backend and confirming all tests pass.

## 2. Frontend Setup and UI Layout

- [x] 2.1 Scaffold the `frontend/` directory with Vite, React, and TypeScript. Set up standard `package.json`, `tsconfig.json`, and dependencies. Verify by running `npm run build` or similar to ensure a clean TypeScript compilation.
- [x] 2.2 Create the basic web calculator component layout mimicking a physical desktop calculator using Vanilla CSS. Design a dual-display section showing the current expression on the top line and the result on the bottom line. Verify by visually inspecting the layout in a responsive web browser at desktop, tablet, and mobile breakpoints (e.g. 375px wide) to ensure no layout clipping or overflow occurs.
- [x] 2.3 Implement standard calculator button clicks (digits, decimal, operators, clear, delete, evaluate). Integrate state management to handle input construction. Verify by clicking through basic calculations via the interactive buttons and verifying the expression display updates accordingly.

## 3. Keyboard Integration and Accessibility

- [x] 3.1 Bind keyboard event listeners to the global window object in React to support digits, standard operators (+, -, *, /), parentheses, Enter/= for evaluation, Backspace for delete, and Escape for clearing. Verify by focusing the application, pressing various keys, and confirming that the expression display and results mirror the keyboard input.
- [x] 3.2 Add comprehensive accessibility attributes (including `aria-label` for screen readability, explicit `role="button"`, and `aria-live="polite"` live regions for screen reader announcements). Verify by auditing HTML markup or inspecting elements using accessibility developer tools.

## 4. End-to-End Integration and Final Verification

- [x] 4.1 Integrate the React frontend API service layer to call the FastAPI `POST /api/v1/evaluate` endpoint. Wire the live or final result field of the display with the API response. Verify by completing a complex chained operation (e.g., `0.1 + 0.2` or `12.5 + 3 * (4 - 1.5) / 2`) and confirming the correct result is displayed without decimal inaccuracies.
- [x] 4.2 Verify client-side visual handling of math and parsing errors (e.g. "Division by zero" or "Mismatched parentheses") returned by the backend by entering malformed inputs and ensuring a clear visual error message is shown in the result area.
