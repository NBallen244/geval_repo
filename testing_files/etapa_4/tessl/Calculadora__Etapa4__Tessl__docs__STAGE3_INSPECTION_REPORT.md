# Stage 3 Codebase Inspection & Pre-Existing Error Detection Report

As mandated by **SEED-3.md (Section 2.2 & Section 4)**, we have analyzed the Stage 2 implementation codebase of the Web Calculator before applying any Stage 3 modifications. Below is a detailed summary of discovered bugs, architectural flaws, precision issues, and missing edge-case handlers.

---

## 1. Discovered Bugs & Edge-Case Omissions

### 1.1 Uncovered API Fetch in Memory Operations (`Calculator.tsx`)
* **Location:** `frontend/src/components/Calculator.tsx` (Lines 137–172)
* **Issue:** The `handleMemoryAdd` and `handleMemorySubtract` handlers include a fallback block that performs an asynchronous API `fetch` to evaluate the active expression if a user clicks `M+` or `M-` while an unevaluated complex expression is on the display. This entire code path has 0% test coverage.
* **Impact:** Any network error or schema mismatch during this specific flow would result in unhandled component state or silent failure. We need to add tests for this specific user interaction.

### 1.2 Underflow/Overflow Behavior in Power Operations (`calculator.py`)
* **Location:** `backend/app/calculator.py`
* **Issue:** While division by zero and basic domain limits (like negative square roots and logs) are explicitly raised and caught, extreme power operations like `10^100000` could cause an overflow in python's `float` exponentiation before converting back to `Decimal`, or trigger slow execution. Adding tests and verifying precise limits on exponent sizes will safeguard backend availability.

---

## 2. Refactoring & Testing Improvement Plan

### 2.1 Standardizing Test Coverage ($\ge 80\%$)
* **Backend:** Current backend coverage is already at **88%**, but can be pushed higher by testing:
  - Error branches for empty expression in FastAPI main app.
  - Invalid character errors in tokenization.
  - Trigonometric edge cases (e.g. undefined tangent values like `tan(90)` vs `tan(pi/2)`).
  - Power operation overflows and negative numbers with fractional powers.
* **Frontend:** Current frontend coverage has **82.5% Statement** and **77.9% Branch** coverage. To strictly meet and exceed 80% across both statements and branches:
  - We must write tests specifically simulating a user clicking `M+` or `M-` with an unevaluated complex expression (triggers the async fetch inside memory handlers).
  - Test keyboard shortcuts for 'p' (which inputs 'pi'), 'Backspace', and 'Escape'.
  - Verify display states during loading / evaluation (`Evaluating...`).
  - Add tests for server error payloads to ensure user-friendly error messages are rendered properly.

### 2.2 Docker & Compose Orchestration
* Provide highly secure, production-ready multi-stage container files:
  - `backend/Dockerfile`: Minimal python base image, non-root user execution.
  - `frontend/Dockerfile`: Multi-stage build with Vite packaging, using Nginx for high-performance static file delivery.
  - `docker-compose.yml`: Binds frontend and backend, sets environment variables, and enables single-command local orchestration.
