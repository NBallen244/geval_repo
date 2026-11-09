# Addendum: Scientific Web Calculator Technical Details

This document captures high-level technical decisions, architectural considerations, and design choices made during the expansion of the Scientific Web Calculator project (Stage 2 and Stage 3).

---

## 1. Math Parsing Alternatives Matrix

To select the most robust method for expression parsing and PEMDAS-compliant evaluation, three technical approaches were considered:

| Alternative | Pros | Cons | Decision/Recommendation |
| :--- | :--- | :--- | :--- |
| **1. Python `eval()` (Raw)** | Zero dependencies; trivial implementation. | **Severe security risk** (remote code execution vulnerability). Does not handle custom decimal precision natively out-of-the-box. | **REJECTED** due to security and standard requirements. |
| **2. Python `ast` parsing with custom Node Visitor + `decimal` module** | Highly secure; no external dependencies; exact decimal mapping at node evaluation level; full control over AST node resolution. | Requires writing a custom safe node-evaluation class traversing the standard Python AST. | **ACCEPTED**. Sourced as the most secure, maintainable, and high-precision approach. Extended to support whitelisted function calls and operators securely. |
| **3. External Parsing Library (e.g., `sympy`, `pyparsing`)** | Handles advanced parsing, fractions, and symbols cleanly out-of-the-box. | Heavy dependency; complex custom configuration needed to force exact high-precision decimal division globally. | **REJECTED** to avoid external library footprint. |

---

## 2. API Design Drafts

### 2.1 Endpoint: Evaluate Expression
* **Method:** `POST`
* **Path:** `/api/v1/evaluate`
* **Content-Type:** `application/json`

#### Request Payload
```json
{
  "expression": "sin(90) + 2 ** 3",
  "angle_unit": "degrees"
}
```

#### Successful Response (HTTP 200 OK)
```json
{
  "status": "success",
  "expression": "sin(90) + 2 ** 3",
  "result": "9"
}
```

#### Error Response (HTTP 422 Unprocessable Content)
```json
{
  "status": "error",
  "error_type": "division_by_zero",
  "message": "Error: Division by zero"
}
```

---

## 3. UI/UX Focus Details: Scientific & Memory Layout

For ergonomics and touchscreen size targets, keypress behaviors and state managers correspond exactly to physical instrument expectations:

```
  Memory Synchronization Loop:
  [UI Component Action (M+ / M-)]
                │
                ▼
  Dispatches API Request: POST /api/v1/evaluate
  { "expression": "memory +/- (cleanedValue)" }
                │
                ▼
  [FastAPI Backend returns exact high-precision result]
                │
                ▼
  [Frontend stores result in local 'memory' state]
  (Shows "M" Badge inside bezel)
```

| Physical Key | UI Component Action | Description |
| :--- | :--- | :--- |
| `0` - `9` | Appends digit | Appends character to active expression string. |
| `.` | Appends decimal | Appends decimal separator; only one allowed per active token operand. |
| `+`, `-`, `*`, `/` | Appends Operator | Appends standard mathematical operators. |
| `(`, `)` | Appends Bracket | Appends opening or closing parentheses. |
| `Enter`, `=` | Triggers evaluation | Serializes and posts expression to backend service. |
| `Backspace` | Deletes last character | Deletes trailing character in the input display; performs smart deletion of full words like `sin(` or `log10(`. |
| `Escape` | Resets calculator state | Clears active expressions and restores default zero displays (AC). |
| `MC` | Clears memory | Resets the memory state back to `0`. |
| `MR` | Recalls memory | Appends the memory value to the active expression. |
