# Quickstart Validation Guide: Reverse Polish Notation (RPN) Migration

This guide outlines the steps to run and validate the RPN evaluation capabilities across the frontend and backend applications.

---

## 1. Prerequisites & Environment Setup

Before performing any validation checks, ensure the repository environment is correctly configured:

1. **Backend Environment**:
   - Python 3.11+ installed.
   - Active virtual environment (`.venv`).
   - Project dependencies installed via `pip install -r backend/requirements.txt`.
2. **Frontend Environment**:
   - Node.js (v18+) and npm installed.
   - Frontend dependencies installed via `npm install` inside the `frontend/` directory.

---

## 2. Running the Services

### Start the Backend Service
From the repository root, run the FastAPI backend using `uvicorn`:
```bash
cd backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend API is now running at `http://127.0.0.1:8000`.

### Start the Frontend Application
In a separate terminal, start the Vite development server:
```bash
cd frontend
npm run dev
```
The client is now accessible at the URL printed in your terminal (typically `http://localhost:5173`).

---

## 3. Automated Verification & Testing

### Running Backend Unit Tests
Execute the comprehensive Pytest suite to verify the Shunting Yard Algorithm parsing, stack operations, exact decimal mathematical execution, and trigonometric precision:
```bash
cd backend
pytest tests/unit/
```
Verify that all unit tests pass with green statuses and report **$\ge 80\%$ statement and branch coverage**.

### Running Frontend Tests
Run Vitest/Jest component tests to confirm state binding, dual-mode switches, visual stack rendering, and keyboard listeners:
```bash
cd frontend
npm run test
```

---

## 4. Manual End-to-End Validation Scenarios

### Scenario A: Standard Infix Calculation (PEMDAS Verification)
1. Launch the frontend application in your browser.
2. Ensure "Standard Mode" is active on the mode toggle.
3. Type: `12.5 + 3 * (4 - 1.5) / 2` and click `=` (or press physical `Enter` / `=` key).
4. **Expected Outcome**: 
   - The result field displays exactly `16.25`.
   - No floating-point noise is present (e.g. not `16.2500000000001`).

### Scenario B: RPN Mode Direct Stack Execution (Basic Operators)
1. Click the mode toggle to switch to **RPN Mode**.
2. Notice the **Stack Visualizer Panel** appears, showing empty rows for `T`, `Z`, `Y`, and `X`.
3. Input `12.5` and click **`ENTER`** (or press keyboard `Enter`).
   - *Result*: Input display is cleared, and `12.5` appears next to `X:`.
4. Input `3` and click **`ENTER`**.
   - *Result*: `3` appears next to `X:`, and `12.5` shifts up next to `Y:`.
5. Click the multiplication key `*` (or press keyboard `*`).
   - *Result*: The stack level `X` updates to `37.5`, and level `Y` becomes empty.

### Scenario C: RPN Mode Scientific Function Execution
1. In RPN Mode, with `37.5` in stack level `X`, click the memory add key **`M+`**.
   - *Result*: The badge indicator `M` turns on, and memory stores `37.5`.
2. Clear the current stack using the clear/reset keys.
3. Input `pi` (or press keyboard `p`) and click **`ENTER`**.
   - *Result*: `3.141592653589793...` is pushed to level `X`.
4. Input `2` and click **`ENTER`**.
   - *Result*: `2` is in level `X`, `pi` is in level `Y`.
5. Click division `/`.
   - *Result*: Level `X` becomes `1.570796326794896...` ($pi / 2$).
6. Click the scientific button **`sin`**.
   - *Result*: Level `X` evaluates to precisely `1` ($sin(pi/2)$).

---

## 5. API Schema Reference
For detailed payload specifications (including request and response JSON structures for both `standard` and `rpn` evaluation modes), see [evaluation-api.json](./contracts/evaluation-api.json) in the `contracts` directory.
