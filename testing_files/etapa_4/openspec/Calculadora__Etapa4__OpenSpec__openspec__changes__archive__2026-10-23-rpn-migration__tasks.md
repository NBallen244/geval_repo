## 1. Audit & Preparation

- [x] 1.1 Perform the Stage 1–3 Legacy Code Audit, documenting any issues, gaps, or findings in an audit report, and verify all pre-existing tests pass before migration.

## 2. Backend: Core RPN & Infix Parser Engine

- [x] 2.1 Implement a Shunting Yard Algorithm tokenizer and converter in `backend/app/calculator.py` to parse standard mathematical expressions into Postfix (RPN) tokens, verifying via unit tests.
- [x] 2.2 Implement a robust stack-based mathematical execution engine in `backend/app/calculator.py` to evaluate Postfix (RPN) tokens with exact `decimal.Decimal` precision, and verify stack operations under basic and scientific operators.
- [x] 2.3 Refactor the FastAPI endpoint in `backend/app/main.py` to handle both `"standard"` and `"rpn"` modes in payload requests, returning evaluated results and active stack states, and verify via TestClient endpoint tests.

## 3. Frontend: Dual-Mode & Real-Time Stack Visualizer

- [x] 3.1 Update the React state in `frontend/src/App.tsx` to handle standard and RPN modes, including the evaluation stack level array and input buffers, verifying Standard Mode is unaffected.
- [x] 3.2 Implement a real-time vertical stack visualizer in `frontend/src/App.tsx` displaying levels X, Y, Z, T when in RPN Mode, and verify that layout adapts responsively to desktop and mobile sizes without horizontal overflow or clipping.
- [x] 3.3 Map keyboard event listeners and virtual keypad buttons for RPN Mode, ensuring physical/virtual `Enter` pushes to the stack, and arithmetic/scientific keys execute immediately, verifying stack updates correctly.
- [x] 3.4 Adapt Memory operations (M+, M-, MR, MC) and History actions to interact with the top stack level (X) when in RPN Mode, and verify correct memory/history values.

## 4. Non-Functional & Verification

- [x] 4.1 Refactor backend unit tests in `backend/tests/test_calculator.py` to cover Shunting Yard tokenization, direct RPN stack evaluation, stack underflows, and other error scenarios, verifying via `pytest`.
- [x] 4.2 Refactor frontend test suite in `frontend/src/App.test.tsx` to validate standard/RPN dual-mode toggling, stack visualizer levels, and `Enter` key handlers, verifying via `vitest`.
- [x] 4.3 Run code coverage tools for both backend (`pytest-cov`) and frontend (`vitest --coverage`) to verify statement and branch coverage is strictly $\ge 80\%$.
- [x] 4.4 Run Docker Compose up to build and execute both backend and frontend containers, verifying they build cleanly and integrate successfully.
