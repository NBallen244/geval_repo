---
title: Math Parsing and Safe AST Evaluation
type: feature
created: 2026-09-28
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Python's standard `eval()` function is highly unsafe for parsing user-provided mathematical expressions (due to remote code execution risks), while standard float arithmetic introduces inaccurate representation errors (such as `0.1 + 0.2` yielding `0.30000000000000004`).

**Approach:** Implement a safe, robust mathematical parsing and evaluation engine utilizing Python's native `ast` package and a custom `NodeVisitor` subclass. It will parse and execute standard chained arithmetic operations (`+`, `-`, `*`, `/`, `(`, `)`) safely by visiting nodes without raw evaluations or security injection vulnerabilities, returning the calculated result as an exact high-precision string.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Implemented a whitelisted arithmetic compiler using Python's native `ast` module with a custom `ast.NodeVisitor` subclass (`SafeMathEvaluator`). Whitelisted AST nodes are `ast.Expression`, `ast.BinOp` (restricted to `+`, `-`, `*`, `/`), `ast.UnaryOp` (restricted to `+`, `-`), and `ast.Constant` (restricted to numeric types). Any non-whitelisted syntax nodes (such as call execution functions, attributes, lambda, names, or assignments) automatically throw a ValueError/TypeError to completely eliminate code injection risks.
- **Files Touched/Created:**
  - `backend/app/engine/__init__.py` - Package initializer.
  - `backend/app/engine/evaluator.py` - Custom safe node evaluator visitor.
  - `backend/app/engine/parser.py` - Parsing entry endpoint.
  - `backend/tests/test_engine.py` - Mathematical precedence and security test suite.
- **Surprises:** Python's native `ast` compiler parses consecutive operator sequences like `12 ++ 3` as valid syntax since it interprets them as `12 + (+3)`. We changed the invalid syntax validation check to `12 + * 3` to guarantee grammatical failure and trigger the expected syntax ValueError.

## Review Triage Log

| Finding | Verdict | Evidence |
| :--- | :--- | :--- |
| **Unhandled Division by Zero** | `false` | This is scheduled to be handled explicitly as part of the future `Story 1.3: Math Error & Syntax Validation Handling`. Raw `ZeroDivisionError` is expected behavioral default behavior for Story 1.1. |
| **AST Recursion / Stack Overflow DoS** | `low` | The calculator runs on small user-typed inputs (e.g. <100 characters); Python's standard recursion limits are adequate for the MVP. |
| **Inconsistent Exception Hierarchy** | `false` | Unified math exception mappings are scheduled for the future `Story 1.3`. |
| **Arbitrary Precision Integer Resource Exhaustion** | `low` | Standard system execution limits are sufficient for normal desktop calculator use. |
| **Missing Modulo / Floor Division** | `false` | Out of scope; only standard arithmetic (`+`, `-`, `*`, `/`) is specified in requirements and `SEED.md`. |
| **No Support for Constants/Variables** | `false` | Explicitly marked as Non-Goals in the PRD. |
| **Floating-Point Binary Representation Imprecision** | `false` | High-precision decimal integration is scheduled as the immediate next step in `Story 1.2: Arbitrary-Precision Math with the Decimal Module`. |
| **Docstring Formatting Split** | `low` | Purely cosmetic typographical layout suggestion. |
| **Gaps in Unit Test Coverage (Empty/Whitespace)** | `medium` | **Patched!** Added `test_empty_and_whitespace` which verifies correct empty expression validation. |


