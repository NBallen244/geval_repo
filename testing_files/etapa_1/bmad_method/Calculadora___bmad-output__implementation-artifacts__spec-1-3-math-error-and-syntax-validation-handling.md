---
title: Math Error & Syntax Validation Handling
type: feature
created: 2026-09-28
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Raw mathematical errors (such as division by zero) and invalid syntaxes (like unbalanced parentheses or invalid consecutive operators) bubble up raw Python exceptions (e.g., `ZeroDivisionError`, `SyntaxError`, `decimal.DivisionByZero`), leaking internal stack traces and presenting unformatted messages to the client.

**Approach:** Harmonize all mathematical, syntactical, and whitelisting node visitor exceptions into a single unified exception mapping system. Any syntax compiled by `ast.parse` or evaluated by `SafeMathEvaluator` that fails must be caught and raised as a clean, user-friendly domain error starting exactly with `"Error: "` (e.g. `"Error: Division by zero"`, `"Error: Unbalanced parentheses"`, `"Error: Invalid expression structure"`).

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Created a dedicated `MathEvaluationError` (ValueError subclass) representing the unified domain exception for all mathematical and parsing anomalies. Structured all catches to return messages prefixed exactly with `"Error: "`.
- **Files Touched/Created:**
  - `backend/app/engine/parser.py` - Standardized exception harmonizer and custom error class.
  - `backend/app/engine/evaluator.py` - Prefixed whitelisting errors.
  - `backend/tests/test_engine.py` - Expanded test suite to cover non-string types, division by zero, unbalanced parentheses, empty inputs, and syntax errors.
- **Surprises:** Added rigorous input type checking (`isinstance(expression, str)`) to catch non-string types early and prevent raw runtime `AttributeError` exceptions.

## Review Triage Log

| Finding | Verdict | Evidence |
| :--- | :--- | :--- |
| **Precision Loss in Floating-Point Literals** | `low` | Standard floats are fully sufficient for a daily calculator MVP. |
| **Missing Input Type Validation** | `high` | **Patched!** Added type check enforcing string inputs early and raising a clean `MathEvaluationError` validation exception. |
| **Implicit Dependency on Inherited Decimal Context Traps** | `low` | Standard division by zero exception traps are sufficient. |
| **Missing Handling of Other Decimal-Specific Exceptions** | `low` | General Exception block covers any unexpected anomalies gracefully. |
| **Brittle SyntaxError Message Parsing for Parentheses Checking** | `medium` | **Patched!** Added `"unclosed"` to the match list to ensure reliable unclosed bracket detection. |
| **No Maximum Input Length (DoS)** | `low` | Inputs are user-typed, making standard stack limits sufficient for MVP. |
| **Redundant f-string Formatting** | `low` | **Patched!** Cleaned up unused template placeholders. |
| **Lack of Whitespace, Multiline, and Comment Validation** | `low` | Standard Python parser successfully handles Whitespace, making additional manual triggers redundant. |

