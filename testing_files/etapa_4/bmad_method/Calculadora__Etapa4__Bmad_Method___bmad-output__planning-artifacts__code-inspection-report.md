# Code Inspection & Stage 1 Audit Report

## 1. Overview
As part of the **Stage 2** expansion of the **Basic Web Calculator** into a **Scientific Web Calculator**, a rigorous audit of the Stage 1 codebase (backend and frontend) was performed. The goal is to identify any pre-existing bugs, architectural flaws, precision issues, or refactoring requirements that must be resolved as part of the Stage 2 execution.

---

## 2. Environment & Tooling Audit
### 2.1 Broken Virtual Environment Paths
* **Finding:** The pre-configured backend virtual environment (`backend/.venv`) contained absolute system path bindings pointing to `C:\Users\nicol\OneDrive\Documents\Caso 1-Calculadora\Etapa 1\Bmad Method\backend\.venv`. Because of this, launching `pytest` directly via standard terminal script launchers failed on the local workspace environment.
* **Resolution:** Recreated the virtual environment locally via `python -m venv .venv` and successfully installed all packages listed in `requirements.txt`.
* **Recommendation:** Ensure all local shell/test invocations are run using `.\backend\.venv\Scripts\python -m pytest` with the appropriate `PYTHONPATH` set to the project directory to prevent absolute path dependency issues.

---

## 3. Backend Engine Audit (Python & FastAPI)
### 3.1 Pydantic V2 Deprecation Warnings
* **Finding:** In `backend/app/routers/evaluate.py` (Line 10), the schema uses deprecated Pydantic syntax:
  ```python
  expression: str = Field(..., description="The mathematical expression to evaluate", example="12.5 + 3 * (4 - 1.5) / 2")
  ```
  Pydantic V2 deprecates passing arbitrary keyword arguments (like `example`) directly to `Field`. It recommends using `json_schema_extra` instead.
* **Refactoring Plan:** Refactor to use `json_schema_extra={"examples": ["12.5 + 3 * (4 - 1.5) / 2"]}` to eliminate warnings and ensure future-proofing.

### 3.2 Starlette Deprecation Warnings
* **Finding:** Starlette deprecation warnings appear in tests and exception handling:
  * `Using httpx with starlette.testclient is deprecated; install httpx2 instead.`
  * `HTTP_422_UNPROCESSABLE_ENTITY` is deprecated in Starlette's newer versions in favor of `HTTP_422_UNPROCESSABLE_CONTENT`.
* **Refactoring Plan:** While these do not prevent tests from passing, keeping Starlette constants and test clients up-to-date is recommended.

### 3.3 Strict AST Node Whitelisting
* **Finding:** The backend `SafeMathEvaluator` only whitelists:
  * `ast.Add`, `ast.Sub`, `ast.Mult`, `ast.Div`
  * `ast.UAdd`, `ast.USub`
  * `ast.Constant`
* **Limitation for Stage 2:** The current AST visitor completely blocks any other syntax nodes. Scientific operations such as `sin`, `cos`, `tan`, `log`, etc. are typically represented as **function calls** (`ast.Call`) in Python AST. To support these, we must expand the whitelist to allow `ast.Call` and evaluate valid scientific functions securely, while continuing to block any malicious code injection or unauthorised function execution.

---

## 4. Frontend Client Audit (React & TypeScript)
### 4.1 Parentheses Balancing & Preview Logic
* **Finding:** In `frontend/src/hooks/useEvaluate.ts`, the `isParenthesesBalanced` helper performs basic character-by-character validation:
  ```typescript
  const isParenthesesBalanced = (expr: string): boolean => {
    let count = 0;
    for (const char of expr) {
      if (char === '(') count++;
      if (char === ')') count--;
      if (count < 0) return false;
    }
    return count === 0;
  };
  ```
  * **Limitation for Stage 2:** In Stage 2, scientific expressions will contain functions like `sin(0.5)`. This basic check remains correct for balance but does not validate syntax.
  * **Chained/Preview Execution:** Currently, live previews are disabled if there is a trailing operator. With functions, a user typing `sin(` will have unbalanced parentheses, which correctly suppresses preview until the closing parenthesis is typed (`sin(0.5)`). This is elegant and prevents unnecessary bad requests.

### 4.2 Hardcoded API Server Endpoint
* **Finding:** The `useEvaluate.ts` hook hardcodes `API_BASE_URL` to `http://localhost:8000`.
* **Refactoring Plan:** Keep as is for local development/prototype simplicity, but document it as a known static configuration.

### 4.3 App Layout & Responsive Buttons
* **Finding:** The button keypad currently utilizes a strict 4x5 CSS Grid (`grid-template-columns: repeat(4, 1fr)`).
* **Limitation for Stage 2:** Adding trigonometric functions (`sin`, `cos`, `tan`), inverses, exponents (`x^y`, `x^2`, `10^x`), logarithms (`ln`, `log`), mathematical constants (`pi`, `e`), angle units toggle (`Rad/Deg`), and memory controls (`M+`, `M-`, `MR`, `MC`) will double the button count.
* **Layout Plan:** Transition to an elegant responsive design featuring a dual-mode layout (e.g., standard keypad with an expandable/collapsible scientific keypad panel or a side history panel/drawer) to fit mobile displays seamlessly.

---

## 5. Audit Verdict & Readiness
The Stage 1 implementation is highly robust, clean, and runs with 100% test success under Python 3.13. No major breaking bugs were found in baseline operations. 

We are fully prepared to proceed with **Stage 2 Requirements and Architecture updates**.
