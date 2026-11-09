# Quickstart & Verification Guide: Web Calculator App

This guide outlines runnable verification scenarios that prove the Web Calculator app features function
correctly end-to-end.

## 1. Prerequisites
- **Python**: Version 3.11+ with `pip`.
- **Node.js**: Version 18+ with `npm`.

## 2. Setup Commands

### Backend Setup
```bash
# Navigate to backend and install dependencies
cd backend
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Frontend Setup
```bash
# Navigate to frontend and install dependencies
cd frontend
npm install
```

---

## 3. Running Scenarios

### Scenario 1: Backend Calculation Accuracy Validation
Verify the backend's PEMDAS sequence evaluation and arbitrary-precision decimal operations.

- **Command**:
  ```bash
  # Execute pytest suite covering precision and precedence
  cd backend
  pytest tests/unit/test_evaluator.py
  ```
- **Manual API Test**:
  ```bash
  # Send a REST POST request to verify evaluation accuracy
  curl -X POST http://localhost:8000/api/v1/evaluate \
       -H "Content-Type: application/json" \
       -d '{"expression": "0.1 + 0.2"}'
  ```
- **Expected Outcome**:
  - `pytest` passes with 100% success rate.
  - API response yields exactly:
    ```json
    {
      "expression": "0.1 + 0.2",
      "result": "0.3"
    }
    ```

### Scenario 2: Error and Boundary Parsing
Verify validation of malformed inputs and divisions.

- **Manual API Test**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/evaluate \
       -H "Content-Type: application/json" \
       -d '{"expression": "10 / 0"}'
  ```
- **Expected Outcome**:
  - HTTP Status: `400 Bad Request`
  - JSON Body:
    ```json
    {
      "error": "DIVISION_BY_ZERO",
      "details": "Cannot divide a decimal number by exactly zero."
    }
    ```

### Scenario 3: End-to-End Application Launch
Validate integration between React frontend client and FastAPI backend evaluation endpoint.

1. **Launch Backend**:
   ```bash
   cd backend
   uvicorn src.main:app --reload --port 8000
   ```
2. **Launch Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
3. **User Flow Validation**:
   - Open browser at local vite port (e.g. `http://localhost:5173`).
   - Press keys `1`, `2`, `.`, `5`, `+`, `3`, `*`, `(`, `4`, `-`, `1`, `.`, `5`, `)`, `/`, `2`, `Enter`.
   - Verify that the expression display shows: `12.5+3*(4-1.5)/2`.
   - Verify that the live preview and final result displays show exactly: `16.25`.
