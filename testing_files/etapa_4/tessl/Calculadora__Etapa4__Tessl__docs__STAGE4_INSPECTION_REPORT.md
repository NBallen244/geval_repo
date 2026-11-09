# Stage 4 Legacy Code Audit & Inspection Report

As mandated by **SEED-4.md (Section 2.2, Section 5)**, we have performed a comprehensive audit and inspection of the pre-existing codebase from Stages 1–3 before implementing any Stage 4 modifications (Reverse Polish Notation engine and UI).

---

## 1. Executive Status of the Existing Codebase

The pre-existing calculator application is highly robust, fully functional, and compliant with all Stage 1–3 specifications:
- **Backend:** Achieves **93% Statement Coverage** with 29 passing tests in `pytest`. Leverages FastAPI and Python's native `decimal` module for high-precision arithmetic and scientific calculations.
- **Frontend:** Achieves **93.22% Statement Coverage** and **84.9% Branch Coverage** with 13 passing test suites in `vitest`. Includes a responsive physical-style layout with keypads, keyboard shortcut integrations, memory register markers, and a session history panel.
- **Containerization & Deployment:** Secure multi-stage Dockerfiles for both frontend and backend are fully integrated, with non-root user enforcement (`appuser` with UID `10001` in Python) and health check sockets configured.

---

## 2. Identified Risks, Gaps, and Edge Cases for the RPN Refactor

To successfully transition the engine to RPN while preserving backward compatibility and high precision, we have audited the existing code and identified the following architectural details:

### 2.1 Backend Tokenization of Sign/Unary Operators
- **Current Tokenizer:** `backend/app/calculator.py` uses a regex-based tokenizer:
  `pattern = re.compile(r'(\d*\.?\d+)|([a-zA-Z_][a-zA-Z0-9_]*)|([+\-*/()^])|(\s+)')`
- **RPN Considerations:**
  - In infix expressions, a minus sign `-` can be binary (`3 - 2`) or unary (`-5`). The recursive descent parser determines the meaning based on grammar rules.
  - When converting infix to postfix using the **Shunting Yard Algorithm**, unary minus and unary plus must be distinguished from binary subtraction and addition. Otherwise, `3 * -5` might convert incorrectly or cause stack underflow.
  - **Audit Insight:** We must introduce separate tokens for unary operators during Shunting Yard conversion (e.g., mapping unary `-` to `u-`) or ensure that our RPN evaluator natively understands unary operators.

### 2.2 Real-time Stack Boundaries and Operand Sufficiency
- **Current Parser:** The recursive descent parser automatically catches syntax errors by enforcing token presence (e.g., expecting `)` or a number).
- **RPN Stack Evaluator:** A pure stack evaluator pop operations on an empty stack (e.g., inputting `+` when the stack has only 1 element) will throw an error.
- **Audit Insight:** We must catch stack underflow errors gracefully, returning clear, user-friendly HTTP 400 errors (e.g., `"Insufficient operands on the stack for operator '+'"`), rather than allowing a raw Python `IndexError` or crash.

### 2.3 Floating-point vs Decimal Domain Validation
- **Current Evaluation:** Trigonometric, logarithmic, and power functions in `calculator.py` are mapped to high-precision Decimal implementations or carefully converted from floating-point limits.
- **RPN Engine:** When executing scientific RPN commands (like pushing operands and evaluating unary functions like `sin`), we must keep the exact same domain limits (`asin` input in $[-1, 1]$, `log` input $>0$, undefined tangents, etc.) and decimal precision.

### 2.4 Frontend Stack Management and Synchronization
- **Standard vs RPN Modes:** The frontend needs to support both standard infix inputs and RPN stack workflows.
- **Audit Insight:** To provide a seamless dual-mode experience, we will implement:
  - An **Infix to RPN Dynamic Preview:** When in Standard Mode, a live badge or display line can show the Postfix token representation of the current expression.
  - An **Interactive RPN Stack Display:** When in RPN Mode, we will display active stack levels ($T, Z, Y, X$), change the `=` button to a dedicated `ENTER` key, and apply operators immediately to the stack.
  - To maintain maximum consistency, the frontend can send postfix strings (e.g., `2 3 +`) to the backend `/api/v1/evaluate` with an optional `mode: "postfix"` parameter, so all precision math and mathematical error checking remain centralized in the backend.

---

## 3. Step-by-Step Execution Plan

1. **Step 1:** Formulate the RPN Engine design and document it in a Spec-Driven Development format.
2. **Step 2:** Implement the **Shunting Yard Algorithm** and **Stack Evaluator Engine** in `backend/app/calculator.py` to support both Infix conversion and direct Postfix evaluation.
3. **Step 3:** Extend `backend/app/main.py` to accept the updated input options.
4. **Step 4:** Refactor and expand backend tests in `backend/tests/` to cover RPN stack underflows, Shunting Yard conversions, and direct postfix calculations.
5. **Step 5:** Modify the frontend UI (`frontend/src/components/Calculator.tsx`) to support Standard/RPN dual modes, stack level rendering, keyboard event mappings (including Enter as Push), and live postfix conversion.
6. **Step 6:** Refactor and expand frontend unit tests in `frontend/src/App.test.tsx` to verify RPN interactions, stack visuals, and edge cases.
7. **Step 7:** Run full verification inside the Docker environment.
