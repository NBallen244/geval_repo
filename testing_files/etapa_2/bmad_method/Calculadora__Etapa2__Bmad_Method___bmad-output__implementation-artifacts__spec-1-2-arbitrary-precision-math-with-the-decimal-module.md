---
title: Arbitrary-Precision Math with the Decimal Module
type: feature
created: 2026-09-28
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Standard IEEE-754 binary floating-point representation errors make operations like `0.1 + 0.2` yield inaccurate approximations (`0.30000000000000004`) on the screen, which violates the exact decimal precision required for standard desktop and financial calculators.

**Approach:** Upgrade the custom AST evaluator (`SafeMathEvaluator` in `evaluator.py`) to convert all parsed numeric constant values to Python `decimal.Decimal` objects, resolving all whitelisted arithmetic operations (+, -, *, /) strictly via the `decimal` module to prevent rounding errors, and returning exact decimal strings.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Refactored the math evaluator nodes to evaluate strictly via Python's standard `decimal` module, returning arbitrary-precision values. Wrapped AST evaluations inside a local context (`decimal.localcontext()`) to completely prevent thread/process-wide pollution of default precision parameters.
- **Files Touched/Created:**
  - `backend/app/engine/evaluator.py` - Updated visitor resolving constants to Decimals.
  - `backend/tests/test_engine.py` - Appended decimal precision checks and boolean rejection tests.
- **Surprises:** Boolean `True` and `False` values inherit from `int` in Python. We explicitly added boolean type guards inside the whitelisting Constant block to prevent raw Decimal exceptions and bubble up correct TypeErrors instead.

## Review Triage Log

| Finding | Verdict | Evidence |
| :--- | :--- | :--- |
| **Global side-effect of modifying thread/process Decimal context** | `high` | **Patched!** Shifted evaluation logic to run within a self-contained local context (`localcontext`), maintaining system-wide context isolation. |
| **Boolean values are treated as numbers raising raw internal error** | `high` | **Patched!** Blocked boolean types explicitly in `visit_Constant` to ensure TypeErrors are generated. |
| **Unhandled division by zero** | `false` | This is scheduled for implementation in `Story 1.3: Math Error & Syntax Validation Handling`. |
| **Missing mathematical operators (modulo, pow)** | `false` | Out of scope; requirements and `SEED.md` mandate only standard arithmetic operations. |
| **Missing imports in tests** | `false` | Imports are complete and tests pass perfectly. |
| **Fragile float-to-string conversion** | `low` | Standard stable Python conversion method used for exact string representations. |
| **Custom lambdas instead of operator modules** | `low` | Lambdas are completely clear and keep the mapping self-contained. |
| **Incomplete type annotations / docstring formats** | `low` | Trivial formatting layout concern. |

