# Pre-Existing Codebase Audit Log (Stages 1 & 2)

This audit documents findings, limitations, and edge-case behaviors identified during the inspection of the Stage 1 & 2 Web Calculator codebase.

---

## 1. Frontend Architectural Audit

### Finding 1.1: Live-Preview Asynchronous Race Conditions (State Leakage)
* **Severity**: High
* **Description**: In `frontend/src/App.tsx`, the debounced `useEffect` Hook for background live-evaluation dispatches asynchronous API `fetch` requests without tracking if the request is still relevant.
* **Mechanism**:
  ```typescript
  const debounceTimer = setTimeout(async () => {
    const outcome = await evaluateExpressionOnBackend(trimmed, angleUnit);
    if (outcome.success && outcome.result !== undefined) {
      setResult(outcome.result);
      setError("");
    } else {
      setResult("");
    }
  }, 200);
  ```
  If a user types rapidly (e.g., `1`, `+`, `2`), multiple backend requests are scheduled. While the debounce timer is cleared, any request that has already been dispatched is NOT canceled. If the API request for `1` is slow but the request for `1+` is fast, the response for `1` can resolve *after* `1+` and overwrite the display with outdated information.
* **Remedy**: Integrate a debounce-linked native browser `AbortController` into the `useEffect` hook to explicitly cancel stale requests upon subsequent dependency changes.

### Finding 1.2: Hardcoded Backend API Host
* **Severity**: Low (Refactoring candidate)
* **Description**: The API base URL is hardcoded as `"http://localhost:8000/api/v1/evaluate"`.
* **Mechanism**:
  This functions perfectly for local development, but in containerized environments (such as Docker Compose or production servers), hardcoded URLs limit portability.
* **Remedy**: Keep this default but document environment variable mapping configurations for multi-container networking.

### Finding 1.3: Missing Frontend Unit and Component Testing
* **Severity**: High (Compliance Gap)
* **Description**: There are no testing dependencies (`vitest`, `jsdom`, `@testing-library/react`) or files under `frontend/` to verify layout responsiveness, memory state, keyboard mappings, and history panels.
* **Remedy**: Set up a comprehensive test runner and write unit/integration specs.

---

## 2. Backend Mathematical Engine Audit

### Finding 2.1: Binary Floating-Point Fallback for Trigonometry
* **Severity**: Medium
* **Description**: While the parser uses standard high-precision `decimal.Decimal` for basic arithmetic (+, -, *, /) and basic functions (`sqrt`, `ln`, `log10`), trigonometric operations convert decimals back to standard Python float (`float(args[0])`) before evaluating them in the standard library's `math` functions.
* **Mechanism**:
  ```python
  f_val = float(args[0])
  r = math.radians(f_val) if angle_unit == "degrees" else f_val
  # ... math.sin(r), etc.
  rounded_res = round(res, 15)
  return decimal.Decimal(str(rounded_res))
  ```
  This causes minor truncation and potential rounding differences when evaluating extreme trigonometry values. However, rounding back to 15 decimal places successfully mitigates common floating-point errors (e.g., `sin(pi)` resulting in `0.0`).
* **Verdict**: Retained as designed to support inverse/direct trigonometric functions reliably without complex Taylor expansion libraries, but must be thoroughly covered by edge case testing.

### Finding 2.2: Permitted Characters Check Constraint
* **Severity**: Low
* **Description**: The input validation checks allowed characters strictly using:
  ```python
  allowed_chars = set("0123456789.+-*/(), abcdefghijklmnopqrstuvwxyz")
  ```
  This successfully blocks potential code injection vectors while allowing alphabetic function names (`sin`, `cos`, `root`, etc.). No additional operators should be supported at this stage unless requested, guaranteeing backward compatibility.
