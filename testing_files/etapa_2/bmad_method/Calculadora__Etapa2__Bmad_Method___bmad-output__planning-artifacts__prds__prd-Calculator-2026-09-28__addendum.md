# Addendum: Basic Web Calculator Technical Details

This document captures high-level technical decisions, architectural considerations, and design choices made during the initiation of the Basic Web Calculator project. It serves as a bridge between the business requirements outlined in the PRD and the downstream engineering implementation (Architecture and Codebase).

---

## 1. Math Parsing Alternatives Matrix

To select the most robust method for expression parsing and PEMDAS-compliant evaluation, three technical approaches were considered:

| Alternative | Pros | Cons | Decision/Recommendation |
| :--- | :--- | :--- | :--- |
| **1. Python `eval()` (Raw)** | Zero dependencies; trivial implementation. | **Severe security risk** (remote code execution vulnerability). Does not handle custom decimal precision natively out-of-the-box. | **REJECTED** due to security and standard requirements. |
| **2. Python `ast` parsing with custom Node Visitor + `decimal` module** | Highly secure; no external dependencies; exact decimal mapping at node evaluation level; full control over AST node resolution. | Requires writing a custom safe node-evaluation class traversing the standard Python AST. | **ACCEPTED (Recommended)**. Sourced as the most secure, maintainable, and high-precision approach. |
| **3. External Parsing Library (e.g., `sympy`, `pyparsing`)** | Handles advanced parsing, fractions, and symbols cleanly out-of-the-box. | Heavy dependency; complex custom configuration needed to force exact high-precision decimal division globally. | **REJECTED** for MVP to avoid external library footprint and keep the backend lightweight. |

---

## 2. API Design Drafts

### 2.1 Endpoint: Evaluate Expression
* **Method:** `POST`
* **Path:** `/api/v1/evaluate`
* **Content-Type:** `application/json`

#### Request Payload
```json
{
  "expression": "12.5 + 3 * (4 - 1.5) / 2"
}
```

#### Successful Response (HTTP 200 OK)
```json
{
  "status": "success",
  "expression": "12.5 + 3 * (4 - 1.5) / 2",
  "result": "16.25",
  "precision_digits": 12
}
```

#### Error Response (HTTP 422 Unprocessable Entity / HTTP 400 Bad Request)
```json
{
  "status": "error",
  "error_type": "division_by_zero",
  "message": "Error: Division by zero",
  "detail": "Attempted to divide expression operand (10) by zero."
}
```

---

## 3. UI/UX Focus Details: Desktop Numpad Key bindings
To ensure optimal ergonomics for accountants and high-speed operators, the frontend keyboard event handlers should map keys as follows:

| Physical Key | UI Component Action | Description |
| :--- | :--- | :--- |
| `0` - `9` | Appends digit | Appends character to active expression string. |
| `.` | Appends decimal | Appends decimal separator; only one allowed per active token operand. |
| `+`, `-`, `*`, `/` | Appends Operator | Appends standard mathematical operators. |
| `(`, `)` | Appends Bracket | Appends opening or closing parentheses. |
| `Enter`, `=` | Triggers evaluation | Serializes and posts expression to backend service. |
| `Backspace` | Deletes last character | Deletes trailing character in the input display. |
| `Escape` | Resets calculator state | Clears active expressions and restores default zero displays. |
