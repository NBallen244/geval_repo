# Stage 1 Codebase Inspection & Pre-Existing Error Detection Report

As mandated by **SEED-2.md (Section 2.2)**, we have analyzed the Stage 1 implementation codebase of the Web Calculator before applying any Stage 2 modifications. Below is a detailed summary of discovered bugs, architectural flaws, precision issues, and missing edge-case handlers.

---

## 1. Discovered Bugs & Decimal Precision Issues

### 1.1 Precision Loss during Decimal-to-Float Serialization
* **Location:** `backend/app/main.py` (Line 42)
* **Code:** `return EvaluateResponse(result=float(decimal_result))`
* **Issue:** Although the calculator engine (`backend/app/calculator.py`) leverages the Python `decimal.Decimal` module to perform high-precision arithmetic, the FastAPI endpoint serializes the result by casting it to a standard Python `float`. This causes a loss of decimal precision for highly precise decimal fractions (e.g., `0.0000000000000001` or very long numbers).
* **Fix Strategy:** Keep `Decimal` type directly in the response model or serialize it using formatted decimal strings where exact visual precision is needed on the frontend. Since we need to keep full precision, we should ensure the frontend displays the precise string representation or has sufficient precision safeguards.

---

## 2. Parsing & Parsing Edge Cases

### 2.1 Double-Decimal Point Validation (e.g. `1.2.3`)
* **Location:** `backend/app/calculator.py`
* **Issue:** The regex pattern `re.compile(r'(\d*\.?\d+)|([+\-*/()])|(\s+)')` matches `1.2` first and then matches `.3` as separate tokens. When parsing `1.2.3`, the parser treats them as two separate number tokens (`["1.2", ".3"]`). When evaluated, the parsing function fails with an "Unexpected token '.3'" error.
* **Refactoring:** This is handled gracefully by the syntax checker (it fails during the parser's validation stage and returns 400), but a cleaner regex or tokenization rule would reject double-decimal points at the tokenization phase.

### 2.2 Unary Operator Nesting
* **Location:** `backend/app/calculator.py`
* **Observation:** The factor rule correctly parses nested unary operators (e.g., `3 * -5` or `-(3 + 5)`), but doesn't explicitly restrict adjacent operators without parenthesization. Since the baseline parser behaves as expected and passes PEMDAS tests, we should preserve its recursive descent structure while extending it for scientific operators.

---

## 3. Architectural Flaws & Missing Handlers

### 3.1 Hardcoded Localhost CORS Origins
* **Location:** `backend/app/main.py`
* **Issue:** CORS middleware allows `allow_origins=["*"]`. While acceptable for local greenfield development, it should be configurable or restricted in production. We will maintain this for local communication but note it as a legacy setting.

---

## 4. Stage 2 Impact Analysis

To accommodate Stage 2 requirements (Trigonometric functions, power/roots, constants, and memory), the parsing engine must undergo a major expansion:
1. **Tokenizer Extension:** We must support letters to tokenize function names (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `ln`, `log`, `sqrt`), and constants (`pi`, `e`).
2. **Degrees vs. Radians Integration:** The backend endpoint must accept an optional `angle_unit` parameter (defaulting to `radians`) inside `EvaluateRequest` to direct trig calculations correctly.
3. **Memory & History State Management:** These will be managed on the frontend, with local session state tracking, synchronization, and interactive click-to-load reloading.
