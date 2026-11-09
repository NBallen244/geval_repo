# Stage 3 Code Inspection & Audit Report

## 1. Executive Summary
As part of the **Stage 3** requirements for the Scientific Web Calculator, a comprehensive audit was performed on the existing codebase (built during Stages 1 and 2). This inspection focused on identifying pre-existing bugs, state leakage, mathematical edge cases, and test integration challenges before implementing containerization and expanding test suites.

---

## 2. Discovered Bugs & Architectural Omissions

### 2.1 Memory Register State Priority Bug (UI State Machine)
* **Finding:** In `frontend/src/hooks/useEvaluate.ts` (Line 183), the memory accumulation helper `handleMemoryOperation` calculates the value to store using the following logic:
  ```typescript
  const valueToOperate = state === 'error' ? '0' : (result && state !== 'idle' ? result : (expression || '0'));
  ```
  If a user has typed an expression (e.g. `10`) but has not yet triggered a final evaluation, the calculator state is `'active'`. Because `result` is initialized to `'0'` (which is truthy as a string) and `state !== 'idle'` is true, `valueToOperate` resolves to the stale `result` (`'0'`) rather than the active user-typed `expression` (`'10'`).
* **Impact:** Active typing values are ignored during memory accumulation operations (`M+`, `M-`), resulting in mathematical inaccuracy where `0` is stored instead of the visible expression.
* **Resolution:** Refactor `useEvaluate.ts` to prioritize `result` only when the expression has been evaluated or is a stable preview:
  ```typescript
  const valueToOperate = state === 'error' ? '0' : (((state === 'evaluated' || state === 'preview') && result) ? result : (expression || '0'));
  ```

### 2.2 Broken Local Pytest Environment Launchers
* **Finding:** The backend `.venv` was configured with absolute path bindings pointing to a different folder structure. Standard terminal test runs via `pytest` crashed with a launcher process creation error.
* **Resolution:** Re-created the virtual environment natively inside the local workspace and installed the dependencies including `pytest-cov`.
* **Verification:** Tests now run and verify with 91% code coverage on the FastAPI backend.

---

## 3. Deployment & Containerization Strategy

### 3.1 Multi-Stage Dockerfile for FastAPI Backend
* Minimal secure base image (`python:3.13-slim`).
* Multi-stage build to minimize image size and eliminate build tool overhead.
* Secure non-root user execution (`chmod` and `chown` setup).
* Proper environment variables (`PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`).

### 3.2 Nginx Static Serving Dockerfile for React Frontend
* Multi-stage build: Stage 1 compiles TypeScript and builds assets using Node.js, Stage 2 uses `nginx:alpine` to serve static assets.
* Custom lightweight Nginx configuration supporting client-side routing.

### 3.3 Orchestrated docker-compose.yml
* Combined backend and frontend running under unified networking.
* Exposed ports aligned with requirements (FastAPI backend at `http://localhost:8000`, Frontend served at `http://localhost:3000`).

---

## 4. Test Expansion Strategy (Targeting >= 80% Coverage)

### 4.1 Backend
* The FastAPI backend already has 91% coverage.
* We will verify coverage using `pytest-cov`.

### 4.2 Frontend
* No frontend test suites existed previously.
* Set up a complete Vitest, jsdom, and React Testing Library environment.
* Implement unit tests in `src/tests/useEvaluate.test.ts` to test state transitions, debounces, and memory logic.
* Implement integration tests in `src/tests/CalculatorFrame.test.tsx` to test keyboard capture, accessibility features, toggles, and the calculation history panel.
