---
title: Shunting Yard Translation and Decimal RPN Engine
type: feature
created: 2026-10-27
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Standard AST-based evaluators require fully-balanced standard mathematical expression strings, meaning they cannot process sequential stack-based calculations (RPN) statelessly or allow high-speed numeric entries without nested parentheses.

**Approach:** Rewrite the backend evaluation engine to utilize a classic, secure Shunting Yard Algorithm that parses infix tokens into postfix (RPN) sequences, and a custom stack-based Decimal evaluator. All push, pop, and operators must evaluate with absolute Decimal precision, and the REST endpoint `/api/v1/evaluate` must accept stack states and direct postfix commands to enable stateless RPN workflows.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:**
  - Implemented `tokenize(expr)` splitting numeric constants, characters, operators, and functions safely using regex.
  - Implemented `infix_to_postfix(tokens)` converting standard infix streams using the Shunting Yard Algorithm, properly classifying unary operators (`u-`, `u+`) and validating unclosed parentheses.
  - Implemented `evaluate_postfix(postfix_tokens, initial_stack, angle_unit)` executing operations with arbitrary `Decimal` precision within local thread-isolated environments (`decimal.localcontext`).
  - Extended `/api/v1/evaluate` to accept an optional `stack` list and format settings (`expr_format: Literal["infix", "postfix"]`), resolving operations statelessly on top of incoming arrays.
- **Files Touched/Created:**
  - `backend/app/engine/evaluator.py` - Custom Shunting Yard and Decimal postfix evaluator.
  - `backend/app/engine/parser.py` - Integrated with the new evaluator, wrapping postfix syntax underflow errors as standard structural anomalies in infix mode.
  - `backend/app/routers/evaluate.py` - Router extended with Pydantic stack input schemas.

## Review Triage Log

| Finding | Verdict | Evidence |
| :--- | :--- | :--- |
| **Infix Syntax Underflow Leak** | `high` | **Patched!** Standardized Shunting-Yard induced stack underflows during standard infix parsing as standard `"Error: Invalid syntax structure"` responses. |
| **Decimal Import Missing** | `high` | **Patched!** Added explicit `import decimal` inside evaluate router to prevent NameError inside Exception wrappers. |
| **Exponent Power Domain Boundary** | `false` | Retained custom checks (such as negative fractional exponents or division by zero power operations) from previous stages. |
