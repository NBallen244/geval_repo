# Quickstart Validation Guide: Shift Bank Stage 1 (Revised)

This guide outlines the end-to-end runnable scenarios to validate the functional requirements, transactional atomicity, and on-demand MFA lifecycles of Shift Bank Stage 1 after implementation.

---

## 1. Setup & Installation

To run this application locally, ensure you have **Python 3.13** and **Node.js (v18+)** installed.

### 1.1 Development-Time Local Communication
Vite (React) and FastAPI run locally on separate ports during development:
- **FastAPI Backend**: `http://127.0.0.1:8000`
- **Vite Frontend**: `http://localhost:5173`

To allow zero-infrastructure local communication, the development-time setup uses **FastAPI's built-in CORS middleware** explicitly configured to allow requests from the Vite source:

```python
# Minimal backend/src/main.py development setup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 1.2 Backend Boot
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize the SQLite database and seed initial schemas/data:
   ```bash
   python -c "import database; database.init_db()"
   ```
4. Start the FastAPI local server:
   ```bash
   uvicorn src.main:app --host 127.0.0.1 --port 8000
   ```

### 1.3 Frontend Boot
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Boot Vite development server:
   ```bash
   npm run dev
   ```
4. Open the displayed local browser URL (`http://localhost:5173`).

---

## 2. Runnable Validation Scenarios

### Scenario 1: Initial Dashboard View
- **Action**: Open the web application in a browser.
- **Expected Outcome**:
  - The UI displays Checking and Savings with balances Checking `COP 5,000,000` and Savings `COP 15,000,000`. No database primary keys or internal IDs are visible.

### Scenario 2: Historical Movement Audit
- **Action**: Select the transaction history view.
- **Expected Outcome**:
  - Exactly two pre-seeded historical transfers are displayed: Savings $\rightarrow$ Checking (`COP 500,000`) and Checking $\rightarrow$ Savings (`COP 100,000`).
  - No "resulting balance" is shown in history.

### Scenario 3: Standard Transfer execution (< COP 1,000,000)
- **Action**: Transfer `COP 300,000` from Checking to Savings.
- **Expected Outcome**:
  - Executes immediately, balances update (Checking: `COP 4,700,000`, Savings: `COP 15,300,000`). Database writes are atomic.

### Scenario 4: Strict Scope & Validation Boundary Check
- **Action**: Submit Checking $\rightarrow$ Checking for `COP 50,000` or a negative amount.
- **Expected Outcome**:
  - Rejected immediately with an error before any states are recorded.

### Scenario 5: Modal Cancellation & Retention of PENDING_MFA
- **Action**: Initiate a transfer of `COP 2,000,000` from Savings to Checking. When the MFA modal appears, click "Close" or click outside to cancel the modal.
- **Expected Outcome**:
  - The modal closes. The transfer **remains in the database** with status `PENDING_MFA`.
  - Balances are NOT changed. No `CANCELED` state is recorded.
  - Re-open the transfer or re-trigger verification: the transfer can still be successfully completed by entering the code `123456` (provided it is within 5 minutes of initial creation).

### Scenario 6: On-Demand MFA Expiration
- **Action**: Initiate a sensitive transfer of `COP 1,500,000` to trigger the MFA overlay, but do not complete it. Wait 5 minutes, then enter the code `123456`.
- **Expected Outcome**:
  - The backend detects that the 5-minute deadline has passed during the POST request, updates the transfer status in the database to `EXPIRED`, rejects the execution, and leaves balances unchanged. No background scheduler or daemon is used.

### Scenario 7: Database-Level Atomicity & Decimal Precision Verification
- **Action**: Trigger a sensitive transfer, open the MFA modal, and confirm with `123456`.
- **Expected Outcome**:
  - The entire state transition is executed within a database-level transaction. All monetary calculations are performed strictly in Python using `decimal.Decimal`, with final values stored as string updates (`UPDATE accounts SET balance = ? WHERE id = ?`). No floating-point casts, SQLite `REAL`, or SQL-level math occurs. 
  - If balance re-validation fails due to insufficient funds, no account balances are modified, but the transfer status transitions to `FAILED` and is committed successfully. `ROLLBACK` is strictly reserved for unexpected system, query, or technical exceptions.
