# Validation Guide: Scientific Web Calculator & Extended State Management

This document provides a runnable validation guide to verify the correct end-to-end operation of the expanded Stage 2 Scientific Web Calculator.

## Prerequisites & Setup

Ensure the virtual environment is active and all backend dependencies are installed.

1. **Backend Service Setup**:
   ```bash
   cd backend
   # Active virtual environment
   .venv\Scripts\activate
   # Install dependencies (if not completed)
   pip install -r requirements.txt
   # Start the development server
   uvicorn src.main:app --reload --port 8000
   ```

2. **Frontend Client Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 1. Automated Test Suites (Fastest Verification)

Validate the backend core implementation and contract bindings using the project-configured test runners:

* **Evaluate Unit Tests**:
  ```bash
  cd backend
  pytest tests/unit -v
  ```
* **Contract Integration Tests**:
  ```bash
  cd backend
  pytest tests/contract -v
  ```

---

## 2. End-to-End Manual Verification Scenarios

Run the following manual tests directly through the browser UI (by default at `http://localhost:5173`) or via HTTP client queries.

### Scenario A: Scientific Trigonometry & Angle Units
1. Open the Web Calculator application.
2. Observe the expanded Scientific panel (or toggle it open using the "Scientific" button on mobile viewports).
3. Confirm the default unit label shows **"Rad"** (Radians).
4. Click or type: `sin(pi / 2)` and click `=`.
   * **Expected display result**: `1`
5. Toggle the angle button to **"Deg"** (Degrees).
6. Click or type: `sin(90)` and click `=`.
   * **Expected display result**: `1`

### Scenario B: Exponents, Roots, and Constants
1. Click the `C` key to clear the current expression.
2. Select **"Rad"** mode.
3. Click or type: `3 ^ 2` and click `=`.
   * **Expected display result**: `9`
4. Click or type: `sqrt(16)` and click `=`.
   * **Expected display result**: `4`
5. Click or type: `ln(e)` and click `=`.
   * **Expected display result**: `1`

### Scenario C: Memory Management
1. Clear the screen.
2. Click or type: `50` and click `=`.
3. Click the `M+` button on the keyboard layout.
   * **Expected UI change**: A distinct visual **"M" badge** appears on the display.
4. Clear the screen.
5. Click or type: `100` and click `=`.
6. Click the `MR` button.
   * **Expected behavior**: The display appends the stored value `50` to become `100 + 50` or just inserts it as `50` depending on the current input buffer state.
7. Click `=` and confirm result: `150`.
8. Click the `MC` button.
   * **Expected UI change**: The visual **"M" badge** disappears completely.

### Scenario D: Session History Drawer
1. Execute three calculations:
   - `2 + 3 = 5`
   - `10 * 10 = 100`
   - `sin(pi / 2) = 1`
2. Open the collapsible History Drawer (if hidden, toggle via the history icon).
3. Confirm three items are listed in the history list:
   - `2 + 3 = 5`
   - `10 * 10 = 100`
   - `sin(pi / 2) = 1`
4. Clear the active calculator input display.
5. Click the formula `10 * 10` inside the second history entry.
   * **Expected display result**: The active input expression is loaded with `10 * 10`.
6. Clear the display.
7. Click the outcome `1` inside the third history entry.
   * **Expected display result**: The active display value is loaded with `1`.
8. Click **"Clear History"** inside the history panel.
   * **Expected behavior**: History drawer is instantly cleared and reports "No history yet".
