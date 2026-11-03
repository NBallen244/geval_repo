# Implementation Plan: Web Calculator

## Overview

This plan builds the web calculator in two ordered halves connected by the typed REST contract. Per SEED.md, the backend math engine is implemented and verified first (Python 3.11+ / FastAPI with exact `decimal.Decimal` arithmetic), then the frontend (React + TypeScript / Vite). Each task builds incrementally on prior tasks, ending with wiring that leaves no orphaned code. Property-based tests (Hypothesis on the backend, table/generator-driven on the frontend) validate the correctness properties defined in the design, and example-based tests cover documented behaviors and edge cases.

## Tasks

- [x] 1. Scaffold backend project structure and dependencies
  - Create the `backend/` directory tree per the design's module structure (`app/`, `app/api/`, `app/engine/`, `tests/`, `tests/properties/`) with the required `__init__.py` files
  - Add dependency/config files declaring `fastapi`, `uvicorn`, `pydantic`, `pytest`, and `hypothesis` (e.g., `pyproject.toml` or `requirements.txt`), targeting Python 3.11+
  - Configure pytest (test discovery paths, options) so the suite can run
  - _Requirements: 14.2, 15.4_

- [x] 2. Implement the backend Evaluation_Engine core
  - [x] 2.1 Define the EvaluationError hierarchy
    - Create `app/engine/errors.py` with an `EvaluationError` base carrying a `kind` and human-readable `message`, plus subclasses `EmptyExpressionError`, `InvalidCharacterError`, `InvalidSyntaxError`, `UnbalancedParenthesesError`, and `DivisionByZeroError`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 2.2 Implement the Token model and Tokenizer
    - Create the `Token`/`TokenType` model and `app/engine/tokenizer.py` that converts a raw string into a token stream: numbers (single decimal point), operators `+ - * / ^`, parentheses `( )`, and `EOF`; skip insignificant whitespace; preserve source position for error messages
    - Raise `InvalidCharacterError` with a descriptive message identifying the offending character/position for any character outside the allowed set
    - _Requirements: 4.4, 6.1_

  - [ ]* 2.3 Write unit tests for the Tokenizer
    - Test recognition of numbers, all operators, parentheses, and whitespace skipping; test that disallowed characters raise `InvalidCharacterError`
    - _Requirements: 4.4_

  - [x] 2.4 Implement the recursive-descent Parser and render() inverse
    - Create `app/engine/parser.py` with AST node types (`NumberNode`, `UnaryOpNode`, `BinaryOpNode`) and a `parse()` implementing the design grammar: `+ -` (left-assoc) < `* /` (left-assoc) < `^` (right-assoc) < unary `-` < parentheses, so `2^2^3 == 256` and `-3^2 == -9`
    - Raise `EmptyExpressionError` on empty/whitespace input, `InvalidSyntaxError` on invalid operator sequences, and `UnbalancedParenthesesError` on unclosed/unmatched parentheses, each with a descriptive, position-aware message
    - Implement `render(node) -> str` as the inverse used by the round-trip property
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 2.6, 4.2, 4.3, 4.5, 6.1, 6.2, 6.3_

  - [ ]* 2.5 Write unit tests for the Parser
    - Test precedence/associativity structure, unary minus, parenthesization, and that grammar violations raise the correct error types
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 2.6, 4.2, 4.3, 4.5_

  - [x] 2.6 Implement the Decimal Evaluator
    - Create `app/engine/evaluator.py` that walks the AST computing a `decimal.Decimal` under a module-level `decimal.Context` (e.g., `prec = 50`); construct operands via `Decimal(str)` from lexemes, never via `float`
    - Raise `DivisionByZeroError` when a divisor subexpression evaluates to zero; round non-terminating results to at least 10 significant digits using `ROUND_HALF_EVEN`; normalize terminating results so `0.1 + 0.2` yields `0.3`; apply exponentiation before unary minus
    - _Requirements: 1.2, 1.3, 2.3, 2.6, 3.1, 3.2, 3.3, 3.4, 4.1_

  - [x] 2.7 Implement the evaluate_expression entry point
    - Create `app/engine/__init__.py` exposing `evaluate_expression(expression: str) -> Decimal` that wires tokenizer → parser → evaluator and propagates `EvaluationError` subclasses
    - _Requirements: 1.1, 14.2_

- [x] 3. Backend engine checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement the backend API layer
  - [x] 4.1 Define Pydantic request/response schemas
    - Create `app/api/schemas.py` with `EvaluateRequest` (`expression: str`, `min_length=1`, `max_length=256`), `EvaluateSuccess` (`result: str`), and `ErrorResponse` (`error: str`)
    - _Requirements: 1.5, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 4.2 Implement the evaluate route
    - Create `app/api/routes.py` with the FastAPI router and `POST /api/v1/evaluate` handler that calls `evaluate_expression`, returns `200` with `{ "result": "<string>" }` (`Content-Type: application/json`) on success, and never returns both `result` and `error`
    - Return the exact decimal result as a **string** to avoid JSON float coercion
    - _Requirements: 5.1, 5.2, 5.3, 5.5_

  - [x] 4.3 Implement application assembly, exception handlers, and CORS
    - Create `app/main.py` that instantiates the FastAPI app, mounts the router, configures CORS for the Vite dev server, and registers exception handlers that map `EvaluationError` subclasses and Pydantic validation failures (malformed JSON, missing field, >256 chars) to `ErrorResponse` bodies with 4xx status codes
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.4, 5.6, 14.3_

- [ ] 5. Backend example-based tests
  - [ ]* 5.1 Write PEMDAS, associativity, and decimal-exactness unit tests
    - Verify PEMDAS across ≥3 precedence levels (e.g. `2 + 3 * 4 ^ 2 == 50`, `12.5 + 3 * (4 - 1.5) / 2 == 16.25`), associativity (`2^2^3 == 256`, `8/4/2 == 1`, `8-4-2 == 2`, `-3^2 == -9`), and `0.1 + 0.2 == Decimal("0.3")`, asserting exact expected values (`tests/test_pemdas.py`)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 15.1_

  - [ ]* 5.2 Write Requirement 4 error-case and boundary-length tests
    - Verify each error case (division by zero, invalid operator sequence `3 + * 4`, unclosed parentheses `(1 + 2`, invalid characters `2 & 3`, empty/whitespace) returns an Error_Response with a 4xx status; verify lengths 1 and 256 accepted and 257 rejected (`tests/test_errors.py`)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.2, 5.6, 15.2_

- [x] 6. Backend property-based tests (Hypothesis)
  - [x] 6.1 Implement Hypothesis strategies and reference oracle
    - Create `tests/properties/strategies.py` with a recursive strategy generating valid ASTs (Decimal-from-string numbers, unary minus, binary `+ - * / ^`, nested parens, bounded depth), a `render(ast)` serializer, invalid-input strategies (disallowed characters, zero divisors, over-length strings), and an independent Decimal AST reference evaluator; configure `@settings(max_examples=100)` (or higher)
    - _Requirements: 6.1, 6.3, 15.3_

  - [ ]* 6.2 Write property test P1 (engine matches PEMDAS/Decimal reference)
    - **Property 1: Engine matches PEMDAS/Decimal reference evaluation**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.2, 3.3, 6.1**
    - Tag `# Feature: web-calculator, Property 1: ...` in `tests/properties/test_engine_property.py`

  - [ ]* 6.3 Write property test P2 (non-terminating division rounding)
    - **Property 2: Non-terminating division is rounded to ≥10 significant digits (round-half-even)**
    - **Validates: Requirements 3.4**
    - Tag `# Feature: web-calculator, Property 2: ...` in `tests/properties/test_engine_property.py`

  - [ ]* 6.4 Write property test P3 (parser round-trip preserves value)
    - **Property 3: Parser round-trip preserves value** — `evaluate(parse(render(ast))) == evaluate(ast)` to ≥10 significant digits
    - **Validates: Requirements 6.3, 6.4**
    - Tag `# Feature: web-calculator, Property 3: ...` in `tests/properties/test_roundtrip.py`; satisfies the mandated round-trip test (Requirement 15.3)

  - [ ]* 6.5 Write property tests P4 and P5 (division-by-zero and invalid character)
    - **Property 4: Division by zero always signals an error** — **Validates: Requirements 4.1**
    - **Property 5: Invalid characters always signal an error** — **Validates: Requirements 4.4**
    - Tag each `# Feature: web-calculator, Property N: ...` in `tests/properties/test_error_properties.py`

  - [ ]* 6.6 Write property tests P6 and P7 (response discriminated union and length limit)
    - **Property 6: Response shape is an unambiguous success-XOR-error discriminated union** — **Validates: Requirements 4.6, 5.3, 5.4, 5.5**
    - **Property 7: Expressions exceeding the length limit are rejected** — **Validates: Requirements 1.5, 5.6**
    - Use FastAPI's test client; tag each `# Feature: web-calculator, Property N: ...` in `tests/test_api.py`

- [x] 7. Backend completion checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Scaffold frontend project structure and dependencies
  - Initialize a Vite React + TypeScript project under `frontend/` with strict `tsconfig`, and add dev dependencies `vitest`, React Testing Library, and MSW; add an ESLint `no-explicit-any` rule over client code
  - Create the `src/` directory tree per the design (`api/`, `state/`, `hooks/`, `components/`, `styles/`, `tests/`)
  - _Requirements: 13.4, 14.1_

- [x] 9. Implement the typed API contract and client
  - [x] 9.1 Define API types and narrowing guards
    - Create `src/api/types.ts` with `EvaluateRequest`, `EvaluateSuccess`, `ErrorResponse`, the `EvaluateResponse` union, and `isSuccess`/`isError` type guards, with no use of `any`
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [x] 9.2 Implement the typed API client
    - Create `src/api/client.ts` with `evaluateExpression(expression)` that builds a typed `EvaluateRequest`, POSTs to `/api/v1/evaluate`, and returns a narrowed success or error; treat responses matching neither guard and network failures as errors
    - _Requirements: 13.4, 13.5, 14.3, 14.4_

  - [ ]* 9.3 Write client tests (P13, success/error/network)
    - **Property 13: Non-conforming responses are treated as errors** — **Validates: Requirements 13.5**
    - Also test typed request construction, success renders result, 4xx renders error, and network failure surfaces "service unavailable" with no local result (`src/tests/client.test.ts`)
    - _Requirements: 13.4, 14.3, 14.4_

- [x] 10. Implement the pure calculator reducer
  - Create `src/state/calculatorReducer.ts` handling expression/result/error state transitions: append character, backspace, escape/reset, set result (clearing error), set error (clearing result); compute no arithmetic locally
  - _Requirements: 7.1, 7.2, 7.3, 7.6, 10.1, 10.2, 10.3, 10.5, 10.7, 14.1_

- [x] 11. Implement input hooks
  - [x] 11.1 Implement the useKeyboard hook
    - Create `src/hooks/useKeyboard.ts` with a global `keydown` listener mapping digits `0-9`, operators `+ - * /`, `.`, `( )` to append; `Enter`/`=` to submit; `Backspace` to delete last char (no-op when empty); `Escape` to reset; unmapped keys are no-ops
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

  - [x] 11.2 Implement the useEvaluator hook
    - Create `src/hooks/useEvaluator.ts` that calls the typed API client, manages loading/error state, ensures results come only from the backend, and surfaces the service-unavailable error on transport failure
    - _Requirements: 14.3, 14.4_

  - [ ]* 11.3 Write reducer property-style tests (P8–P11)
    - **Property 8: Mapped character keys append their character** — **Validates: Requirements 10.1, 10.2, 10.3**
    - **Property 9: Backspace removes exactly the last character** — **Validates: Requirements 10.5**
    - **Property 10: Escape resets to the empty state** — **Validates: Requirements 10.7**
    - **Property 11: Unmapped keys are no-ops** — **Validates: Requirements 10.8**
    - Use generator/table-driven cases over the key set in `src/tests/reducer.test.ts`

- [x] 12. Implement UI components
  - [x] 12.1 Implement CalcButton
    - Create `src/components/CalcButton.tsx` as a native `<button>` with a visible label and an `aria-label` matching its function, plus a visible pressed/active-state indication
    - _Requirements: 11.5, 11.6, 12.1, 12.2_

  - [x] 12.2 Implement Keypad
    - Create `src/components/Keypad.tsx` rendering all controls (digits 0–9, `.`, `+ - * /`, parentheses, evaluate, reset) in a CSS Grid arranged 7-8-9 / 4-5-6 / 1-2-3 with 0 below, operators grouped in a dedicated region
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 12.3 Implement ExpressionDisplay and ResultDisplay
    - Create `src/components/ExpressionDisplay.tsx` (renders current expression, empty initially, `aria-live="polite"`) and `src/components/ResultDisplay.tsx` (renders result or error, empty initially, result region `aria-live="polite"`, error region `aria-live="assertive"`, mutually exclusive)
    - _Requirements: 7.1, 7.2, 7.4, 7.5, 7.6, 12.3, 12.4, 12.5_

  - [x] 12.4 Implement Calculator container
    - Create `src/components/Calculator.tsx` owning all state via the reducer, wiring the keypad, displays, `useKeyboard`, and `useEvaluator`; on button/keyboard input it updates expression state and on submit renders backend results/errors
    - _Requirements: 7.3, 8.4, 14.1, 14.3_

  - [x] 12.5 Implement App shell
    - Create `src/App.tsx` as the root layout container mounting `Calculator`
    - _Requirements: 8.4_

- [x] 13. Implement responsive, accessible styling
  - Create `src/styles/` with a responsive CSS Grid layout ensuring no horizontal overflow and no clipping at mobile (320–767), tablet (768–1023), and desktop (1024–2560) widths, ≥44×44px touch targets on mobile, and a contrast-compliant theme (body/label ≥4.5:1, large text ≥3:1, component boundaries and focus indicators ≥3:1)
  - _Requirements: 8.4, 9.1, 9.2, 9.3, 9.4, 11.1, 11.2, 11.3, 11.4_

- [ ] 14. Frontend component and accessibility tests
  - [ ]* 14.1 Write component/example tests for displays and layout
    - Test empty initial displays, expression updates on input, result/error rendering and mutual exclusivity, presence of all required controls, and the 7-8-9 / 4-5-6 / 1-2-3 keypad arrangement with 0 below and grouped operators (`src/tests/components.test.tsx`)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 8.1, 8.2, 8.3_

  - [ ]* 14.2 Write accessibility tests (P12) and responsiveness checks
    - **Property 12: Every control exposes a matching accessible label** — **Validates: Requirements 12.1**
    - Also verify `aria-live` regions configured `polite`/`assertive`, active-state indication on press, visible labels, and no-overflow/≥44px touch targets at representative viewport widths (`src/tests/components.test.tsx`)
    - _Requirements: 8.4, 9.1, 9.2, 9.3, 9.4, 11.5, 11.6, 12.3, 12.4, 12.5_

- [x] 15. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP; core implementation tasks are never optional.
- Each task references specific requirement clauses for traceability, and each property test task references its property number from the design.
- Checkpoints ensure incremental validation; the backend is fully implemented and verified before frontend work begins (per SEED.md).
- Property-based tests use Hypothesis (backend, ≥100 iterations, tagged) and generator/table-driven cases (frontend reducer); example-based tests cover documented behaviors and edge cases.
- Full WCAG conformance requires manual testing with assistive technologies and expert review, which the automated checks supplement but do not replace.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2"] },
    { "id": 3, "tasks": ["2.3", "2.4"] },
    { "id": 4, "tasks": ["2.5", "2.6"] },
    { "id": 5, "tasks": ["2.7"] },
    { "id": 6, "tasks": ["4.1", "5.1", "6.1"] },
    { "id": 7, "tasks": ["4.2", "6.2", "6.3", "6.4", "6.5"] },
    { "id": 8, "tasks": ["4.3", "5.2"] },
    { "id": 9, "tasks": ["6.6"] },
    { "id": 10, "tasks": ["8"] },
    { "id": 11, "tasks": ["9.1", "10"] },
    { "id": 12, "tasks": ["9.2", "11.1", "11.3"] },
    { "id": 13, "tasks": ["9.3", "11.2", "12.1", "12.3"] },
    { "id": 14, "tasks": ["12.2", "13"] },
    { "id": 15, "tasks": ["12.4"] },
    { "id": 16, "tasks": ["12.5"] },
    { "id": 17, "tasks": ["14.1", "14.2"] }
  ]
}
```
