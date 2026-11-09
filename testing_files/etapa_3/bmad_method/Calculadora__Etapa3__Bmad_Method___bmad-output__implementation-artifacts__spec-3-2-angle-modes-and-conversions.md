---
title: Degrees & Radians Angle Modes and Conversions
type: feature
created: 2026-10-20
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Standard scientific operations evaluate trigonometric functions using radians as standard unit, requiring physics and maths students to perform manual, error-prone unit conversions when working in degrees mode.

**Approach:** Accept an optional `angle_unit` parameter in the evaluation REST payload (`"radians"` or `"degrees"`). Implement secure conversion routines prior to running trigonometric functions and post-processing inverse trigonometric function results using high-precision Decimal constants.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Extended `SafeMathEvaluator` constructor to accept and enforce `angle_unit`. Added conversion multipliers using high-precision decimal representation of $\pi$ (`3.141592653589793238462643383`):
  - Degrees to Radians: $\text{radians} = \text{degrees} \times \frac{\pi}{180}$
  - Radians to Degrees (for inverse trig): $\text{degrees} = \text{radians} \times \frac{180}{\pi}$
- **Files Touched/Created:**
  - `backend/app/engine/evaluator.py` - Custom conversions and validations.
  - `backend/app/engine/parser.py` - Signature expanded to forward `angle_unit`.
  - `backend/app/routers/evaluate.py` - Extended API routers.
  - `backend/tests/test_engine.py` & `test_api.py` - Extended unit and integration test assertions.

## Review Triage Log

| Finding | Verdict | Evidence |
| :--- | :--- | :--- |
| **Invalid Angle Unit Values** | `false` | Enforced strict Litval matching on schema: `angle_unit: Literal["radians", "degrees"] = Field("radians")`. Invalid values throw standard validation 422 errors. |
| **Tangent Asymptote Zero Div** | `false` | **Patched!** Explicitly check cos values before calculating tangent: `if abs(cos_val) < 1e-15` raises standard ValueError. |
