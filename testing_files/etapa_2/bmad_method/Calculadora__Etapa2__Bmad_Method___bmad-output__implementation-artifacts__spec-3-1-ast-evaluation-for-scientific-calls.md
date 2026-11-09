---
title: AST Evaluation for Scientific Function Calls
type: feature
created: 2026-10-20
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Standard arithmetic limits are insufficient for engineering and scientific use. Supporting advanced math functions (like `sin`, `cos`, `tan`, `sqrt`, `ln`) in AST is difficult to do without exposing security risks or raw code evaluation vulnerabilities.

**Approach:** Securely whitelist `ast.Call` nodes inside the `SafeMathEvaluator` AST visitor. Ensure that `node.func` is strictly a simple `ast.Name` node and that the called function ID is whitelisted. Enforce that functions accept exactly one argument and evaluate them safely with Decimal operations where possible.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Whitelisted `ast.Call` nodes in `backend/app/engine/evaluator.py`. Supported function names are whitelisted in `WHITELISTED_FUNCS` (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sqrt`, `ln`, `log`, `log10`). Added explicit validations to ensure calls only have exactly one parameter and do not contain attribute accesses (e.g. `foo.bar()`), eliminating code execution injection surfaces.
- **Files Touched/Created:**
  - `backend/app/engine/evaluator.py` - AST call node visitors whitelists.
  - `backend/tests/test_engine.py` - Unit test assertions verifying secure function evaluations.

## Review Triage Log

| Finding | Verdict | Evidence |
| :--- | :--- | :--- |
| **Attribute Calls Injection** | `false` | Blocked explicitly in `visit_Call`: `not isinstance(node.func, ast.Name)` throws ValueError. |
| **Infinite Argument Overloading** | `false` | Enforced strict single parameter limit: `len(node.args) != 1` throws ValueError. |
| **Float Conversion Precision Leak** | `low` | Trigonometric operations use double-precision floats wrapper since `decimal` doesn't support them natively; results are converted back to Decimal cleanly with high accuracy. |
