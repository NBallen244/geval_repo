# Stage 4 Code Inspection & Audit Report

## 1. Executive Summary
Before executing the drastic migration to Reverse Polish Notation (RPN) required by **Stage 4**, a comprehensive audit was performed on the existing web calculator repository (built during Stages 1–3). This inspection documents pre-existing bugs, edge case behaviors, and test coverage gaps to establish a baseline of the application prior to the RPN refactor.

---

## 2. Pre-Existing Code Conditions & Edge Case Audit

### 2.1 Trigonometric Precision vs. Floating-Point Escape
* **Finding:** While the core mathematical engine evaluates basic arithmetic (`+`, `-`, `*`, `/`) with absolute precision using Python's `decimal.Decimal` module, trigonometric and inverse trigonometric functions (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`) convert decimal values to Python `float` types underneath. After float execution, the float results are parsed back into decimals:
  ```python
  val_float = float(x_rad)
  res = math.sin(val_float)
  return Decimal(f"{res:.15g}")
  ```
* **Impact:** Although this approach isolates float-induced IEEE-754 noise to 15 decimal places via `.15g` formatting, it represents an inherent precision bottleneck compared to pure arbitrary-precision expansion. This is documented and accepted in `SPEC.md` as an expected technical constraint.

### 2.2 Uncovered Lines & Test Coverage Gaps
An analysis of the current test coverage reports (`pytest-cov` and `vitest` coverage) reveals minor coverage gaps:
1. **Frontend keyboard event dispatching (`useKeyboard.ts`):** 45.46% of statements in keyboard hotkey capture are uncovered. The test suite does not fully simulate all keystrokes (`+`, `-`, `*`, `/`, `^`, `(`, `)`, `p`, `e`, `Escape`).
2. **Display visual fallback states (`DisplayPanel.tsx`):** Uncovered lines exist in custom screen reader announcements (`getScreenReaderSpokenText`), such as when memory is non-zero, or when presenting raw active expressions vs. stable results.
3. **Network error fallbacks (`useEvaluate.ts`):** Uncovered branches exist for network failure catch blocks (e.g. falling back to Javascript's native float calculation during `M+` or `M-` if the backend FastAPI service is unreachable).

### 2.3 Syntax Parsing Assumptions
* **Finding:** The AST parsing engine relies on compiling standard infix strings into python's native Abstract Syntax Trees.
* **Impact:** Transitioning to RPN requires a paradigm shift: we must convert infix expressions to postfix tokens (via the Shunting Yard Algorithm) or evaluate RPN sequences directly on a stack. Under the hood, RPN operates via sequential stack operations, rendering deep AST expression nesting obsolete for evaluation, though the conversion engine from infix to postfix may still require robust tokenization.

---

## 3. RPN Refactoring Risk Assessment & Strategy

### 3.1 Migration Risks
* **State Machine Incompatibility:** The standard mode's live preview (debounced typing calculations) expects a standard mathematical infix expression. RPN, on the other hand, evaluates when an operator is encountered on a stack. We must ensure the UI and backend handle both:
  * **RPN Mode:** Evaluates dynamically on stack push/operator execution.
  * **Standard Mode (RPN-backed):** Tokenizes standard infix strings, converts them to postfix RPN under-the-hood using Shunting Yard, and evaluates them on the RPN stack.
* **Test Suite Disruption:** Frontend and backend tests currently assert infix-style evaluations. Refactoring the engine to support RPN must preserve standard-mode evaluation logic while adding specific test cases for pure RPN stack interactions.

### 3.2 Mitigation Plan
1. **Unified Endpoint:** The FastAPI endpoint `/api/v1/evaluate` will support both standard infix-to-RPN evaluation and direct RPN list-of-tokens evaluation.
2. **Dual-Mode UI:** The UI will provide a toggle between Standard Mode (which translates standard typing to RPN) and RPN Mode (which features an `ENTER` key and a visual stack display).
3. **Expanding the Test Suite:** Preserve 100% of standard-mode test cases by backing them with Shunting-Yard translation to RPN, and write additional unit tests to assert pure RPN behaviors (stack push/pop, stack underflow, postfix evaluation).
