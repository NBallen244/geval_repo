---
title: Exponentiation, Roots, and Mathematical Constants
type: feature
created: 2026-10-20
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Standard basic calculators lack exponents ($x^y$), roots ($\sqrt{x}$), and common constants ($\pi$, $e$), which are essential for conducting compound interest modeling and physics formulas securely with absolute decimal precision.

**Approach:** Whitelist `ast.Pow` binary nodes and resolve name variables representing `pi` and `e`. Integrate standard mathematical boundary validators (e.g. non-positive logarithms, negative square roots, or complex numbers from fractional powers of negative bases) to prevent math engine crashes and provide user-friendly alerts.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Added `ast.Pow` to `BIN_OPS` mapping to lambda `a, b: a ** b`. Whitelisted `ast.Name` nodes inside `visit_Name` mapping `'pi'` to `3.141592653589793238462643383` and `'e'` to `2.718281828459045235360287471`.
- **Custom Bounds Checks:**
  - Exponents: Blocked fractional powers of negative bases (raising ValueError) to prevent complex number outputs. Blocked division by zero for negative exponents (e.g. `0 ** -1`).
  - Roots: Blocked `sqrt` of negative numbers.
  - Logarithms: Blocked logs of numbers $\le 0$.
- **Files Touched/Created:**
  - `backend/app/engine/evaluator.py` - Custom validations, constants, and operators.
  - `backend/tests/test_engine.py` - Unit test cases verifying power, roots, logarithms, and domain limits.

## Review Triage Log

| Finding | Verdict | Evidence |
| :--- | :--- | :--- |
| **Logarithm of Negatives Crash** | `false` | **Patched!** Log domain checks explicitly raise ValueError. |
| **Float Precision Jittering in e/pi** | `false` | Evaluated using 28-digit high precision `Decimal` constants, matching exact hardware calculators. |
