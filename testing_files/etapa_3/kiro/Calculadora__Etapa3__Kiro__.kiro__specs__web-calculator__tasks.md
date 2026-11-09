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

  - [x]* 2.3 Write unit tests for the Tokenizer
    - Test recognition of numbers, all operators, parentheses, and whitespace skipping; test that disallowed characters raise `InvalidCharacterError`
    - _Requirements: 4.4_

  - [x] 2.4 Implement the recursive-descent Parser and render() inverse
    - Create `app/engine/parser.py` with AST node types (`NumberNode`, `UnaryOpNode`, `BinaryOpNode`) and a `parse()` implementing the design grammar: `+ -` (left-assoc) < `* /` (left-assoc) < `^` (right-assoc) < unary `-` < parentheses, so `2^2^3 == 256` and `-3^2 == -9`
    - Raise `EmptyExpressionError` on empty/whitespace input, `InvalidSyntaxError` on invalid operator sequences, and `UnbalancedParenthesesError` on unclosed/unmatched parentheses, each with a descriptive, position-aware message
    - Implement `render(node) -> str` as the inverse used by the round-trip property
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 2.6, 4.2, 4.3, 4.5, 6.1, 6.2, 6.3_

  - [x]* 2.5 Write unit tests for the Parser
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

- [x] 5. Backend example-based tests
  - [x]* 5.1 Write PEMDAS, associativity, and decimal-exactness unit tests
    - Verify PEMDAS across ≥3 precedence levels (e.g. `2 + 3 * 4 ^ 2 == 50`, `12.5 + 3 * (4 - 1.5) / 2 == 16.25`), associativity (`2^2^3 == 256`, `8/4/2 == 1`, `8-4-2 == 2`, `-3^2 == -9`), and `0.1 + 0.2 == Decimal("0.3")`, asserting exact expected values (`tests/test_pemdas.py`)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 15.1_

  - [x]* 5.2 Write Requirement 4 error-case and boundary-length tests
    - Verify each error case (division by zero, invalid operator sequence `3 + * 4`, unclosed parentheses `(1 + 2`, invalid characters `2 & 3`, empty/whitespace) returns an Error_Response with a 4xx status; verify lengths 1 and 256 accepted and 257 rejected (`tests/test_errors.py`)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.2, 5.6, 15.2_

- [x] 6. Backend property-based tests (Hypothesis)
  - [x] 6.1 Implement Hypothesis strategies and reference oracle
    - Create `tests/properties/strategies.py` with a recursive strategy generating valid ASTs (Decimal-from-string numbers, unary minus, binary `+ - * / ^`, nested parens, bounded depth), a `render(ast)` serializer, invalid-input strategies (disallowed characters, zero divisors, over-length strings), and an independent Decimal AST reference evaluator; configure `@settings(max_examples=100)` (or higher)
    - _Requirements: 6.1, 6.3, 15.3_

  - [x]* 6.2 Write property test P1 (engine matches PEMDAS/Decimal reference)
    - **Property 1: Engine matches PEMDAS/Decimal reference evaluation**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.2, 3.3, 6.1**
    - Tag `# Feature: web-calculator, Property 1: ...` in `tests/properties/test_engine_property.py`

  - [x]* 6.3 Write property test P2 (non-terminating division rounding)
    - **Property 2: Non-terminating division is rounded to ≥10 significant digits (round-half-even)**
    - **Validates: Requirements 3.4**
    - Tag `# Feature: web-calculator, Property 2: ...` in `tests/properties/test_engine_property.py`

  - [x]* 6.4 Write property test P3 (parser round-trip preserves value)
    - **Property 3: Parser round-trip preserves value** — `evaluate(parse(render(ast))) == evaluate(ast)` to ≥10 significant digits
    - **Validates: Requirements 6.3, 6.4**
    - Tag `# Feature: web-calculator, Property 3: ...` in `tests/properties/test_roundtrip.py`; satisfies the mandated round-trip test (Requirement 15.3)

  - [x]* 6.5 Write property tests P4 and P5 (division-by-zero and invalid character)
    - **Property 4: Division by zero always signals an error** — **Validates: Requirements 4.1**
    - **Property 5: Invalid characters always signal an error** — **Validates: Requirements 4.4**
    - Tag each `# Feature: web-calculator, Property N: ...` in `tests/properties/test_error_properties.py`

  - [x]* 6.6 Write property tests P6 and P7 (response discriminated union and length limit)
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

---

## Stage 2 Tasks (Scientific Calculator Extension)

Stage 2 extends the same web-calculator spec into a scientific calculator. All Stage 1 tasks above remain in force and unchanged. Per the SEED-2 "Instructions for AI Agents", work proceeds backend-first: Step 1 Stage 1 inspection remediation (Requirement 16), Step 2 the backend Evaluation_Engine extension (tokenizer/parser/evaluator/scientific/constants/errors) and API, Step 3 the frontend local state (angle mode, memory register, calculation history) and hooks, Step 4 the UI surfaces (scientific keypad, history panel, memory indicator, angle toggle) with responsive, accessible styling. Each task builds on prior tasks and ends wired into `Calculator.tsx`, leaving no orphaned code. New tokens, grammar productions, AST nodes, and evaluator operations are purely additive and must not weaken Requirements 1–15 (Requirement 16.3).

- [ ] 16. Remediate Stage 1 inspection findings and lock them with tests
  - Apply the optional cosmetic remediations recorded in the design's "Stage 1 Codebase Inspection Report": correct the Stage 1 design precedence prose to `+ -` < `* /` < unary `-` < `^` < parentheses (documentation-only, no code change), and optionally improve the malformed-number message in `tokenizer.py`/`parser.py` (e.g. detect adjacent NUMBER tokens or a lexeme with two dots and raise `InvalidSyntaxError` "Malformed number near position N") WITHOUT changing which inputs are accepted or rejected (preserve Requirement 4.2 behavior)
  - Preserve every Stage 1 acceptance criterion (Requirements 1–15); if any remediation regresses a Stage 1 criterion, revert or correct it before continuing
  - [ ]* 16.1 Write regression-safe pytest for the remediated engine-affecting behavior
    - Add `backend/tests/test_inspection_fixes.py` asserting the corrected malformed-number behavior still returns a 4xx Error_Response with no result (Requirement 4.2 unchanged) and that the full Stage 1 suite continues to pass with zero failures/errors
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6_

- [x] 17. Extend the backend error taxonomy for scientific failures
  - Add `DomainError` (`kind = "domain_error"`) and `InvalidFunctionError` (`kind = "invalid_function"`) subclasses to `app/engine/errors.py`, each carrying a descriptive, position/domain-naming message; both inherit from the existing `EvaluationError` base so the single `main.py` handler maps them to 4xx with no handler change
  - _Requirements: 17.7, 17.8, 18.7, 18.8, 18.9, 18.10, 18.11, 24.8_

- [x] 18. Extend the Tokenizer for identifiers, constants, and commas
  - [x] 18.1 Add identifier/function/constant lexing and the COMMA token
    - Extend `app/engine/tokenizer.py` with new `TokenType` members (function/constant identifiers and `COMMA`); on an ASCII letter read a maximal `[a-zA-Z]` run and match it against the known-name table — functions `sin, cos, tan, asin, acos, atan, ln, log10, sqrt, root` and constants `pi, e`; special-case `log10` (after the `log` letter-run, if the next two chars are `10`, consume them as part of the `log10` keyword); expand the allowed character set to include ASCII letters and `,`; preserve whitespace handling, number scanning, and single-character operators from Stage 1
    - Raise the new `InvalidFunctionError` naming the unknown identifier and position for any unrecognized letter-run; keep raising the Stage 1 `InvalidCharacterError` for characters still outside the expanded set (Requirement 4.4 preserved)
    - _Requirements: 17.1, 17.2, 18.4, 18.5, 19.1, 19.2, 24.8_
  - [ ]* 18.2 Write unit tests for the extended tokenizer
    - Test recognition of each function name, `pi`/`e`, `root`, `log10`, and `,`; that `sin2` lexes as `sin` then `2`; that unknown identifiers raise `InvalidFunctionError`; and that disallowed characters still raise `InvalidCharacterError`
    - _Requirements: 4.4, 24.8_

- [x] 19. Add the high-precision Decimal constants module
  - Create `app/engine/constants.py` storing `pi` and `e` as `Decimal` string literals with ≥50 significant digits (well beyond the ≥10-digit contract); expose them as exact `Decimal` operands and as the sole basis for degree↔radian conversion
  - _Requirements: 19.1, 19.2, 17.5_

- [x] 20. Extend the Parser with scientific nodes and grammar
  - [x] 20.1 Add ConstantNode/FunctionNode/RootNode and the extended primary productions
    - Extend `app/engine/parser.py` with frozen `ConstantNode(name)`, `FunctionNode(name, operand)`, and `RootNode(radicand, degree)` and widen the `Node` union; add the `primary` productions `constant | function | unaryfunc "(" expression ")" | "root" "(" expression "," expression ")"` so operator precedence/associativity from Stage 1 is untouched (functions/constants bind at `primary` level)
    - Extend `render()` so a `ConstantNode` renders `pi`/`e`, a `FunctionNode` renders `name(render(operand))`, and a `RootNode` renders `root(render(radicand), render(degree))` (self-parenthesizing, re-parses to a structurally equivalent tree — Requirement 6.3 carried forward); raise the Stage 1 `InvalidSyntaxError` with position for a function name not followed by `(`, a missing comma in `root`, or a missing argument (Requirement 4.2 preserved)
    - _Requirements: 6.1, 6.3, 18.3, 19.1, 19.2_
  - [ ]* 20.2 Write unit tests for the extended parser
    - Test the new node structures, `root(x, n)` parsing, function-call nesting, extended `render()` output, and that malformed function/constant/root forms raise `InvalidSyntaxError`
    - _Requirements: 6.1, 6.3, 4.2_

- [x] 21. Implement the Decimal-native scientific operations module
  - Create `app/engine/scientific.py` running under the Stage 1 `decimal.Context(prec=50, ROUND_HALF_EVEN)` with a few guard digits, using NO raw `float` in any calculation path: degree↔radian conversion via `Decimal` `pi` (`radians = degrees * pi / 180`, `degrees = radians * 180 / pi`); `sin`/`cos` via range reduction (modulo `2*pi`, into `[-pi/4, pi/4]` with quadrant identities) plus a Maclaurin series to working precision, `tan = sin/cos`; `atan` via Taylor series with `atan(x)=pi/2-atan(1/x)` for `|x|>1`, `asin(x)=atan(x/sqrt(1-x^2))`, `acos(x)=pi/2-asin(x)`; powers/roots/logs helpers via `Decimal.ln`/`log10`/`sqrt`/`exp`/power
  - Implement the domain checks that raise `DomainError`: `asin`/`acos` require `-1 ≤ x ≤ 1`; `tan` undefined at odd multiples of 90°/`pi/2` (precision-aware tolerance in `Decimal`); `sqrt` and even-integer-degree `root` require `x ≥ 0`; `root` degree ≠ 0; `ln`/`log10` require `x > 0`; negative base to non-integer exponent rejected; non-finite result rejected
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.8, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9, 18.10, 18.11_

- [x] 22. Extend the Evaluator to dispatch scientific nodes and thread angle mode
  - Extend `app/engine/evaluator.py` to accept an `angle_mode` parameter (default `"radians"`) threaded through the walk and consulted only by trig/inverse-trig nodes; dispatch `ConstantNode` to `constants.py`, `FunctionNode`/`RootNode` to `scientific.py`, applying the domain checks and returning `DomainError` on violation; reuse the Stage 1 `_finalize`/rounding so non-terminating scientific results round to ≥10 significant digits (Requirements 17.6, 18.6); extend the existing `_power()` guards so a negative base with a non-integer exponent raises `DomainError` (Requirement 18.9) rather than `InvalidSyntaxError`; leave all non-trig Stage 1 behavior identical regardless of mode
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.6, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.9, 19.1, 19.2_

- [x] 23. Wire the scientific engine entry point
  - Update `app/engine/__init__.py` so `evaluate_expression(expression: str, angle_mode: str = "radians") -> Decimal` threads `angle_mode` into `evaluate(ast, angle_mode=...)` and continues to propagate `EvaluationError` subclasses (including the new `DomainError`/`InvalidFunctionError`)
  - _Requirements: 24.3_

- [x] 24. Backend scientific engine checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 25. Extend the backend API for angle mode
  - Update `app/api/schemas.py` so `EvaluateRequest` gains `angle_mode: Literal["radians", "degrees"] = "radians"` (missing field defaults to radians; any other value fails Pydantic literal validation → 4xx); update `app/api/routes.py` to call `evaluate_expression(request.expression, angle_mode=request.angle_mode)` as a thin adapter, keeping the string result and the mutually exclusive success/error contract; broaden the validation-error message in `app/main.py` to also name an invalid angle mode and add a docstring note for the new `DomainError`/`InvalidFunctionError` kinds (handler already covers the `EvaluationError` base class)
  - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 17.9, 17.10_

- [ ] 26. Backend example-based scientific tests
  - [ ]* 26.1 Write Requirement 25 function, conversion, power/root/log, constant, and boundary tests
    - Add `tests/test_scientific.py` (25.1: each trig/inverse-trig in both radians and degrees, e.g. `sin(30°)=0.5`, `cos(0)=1`, `atan(1)=45°`, to ≥10 sig digits), `tests/test_conversions.py` (25.2: deg↔rad), `tests/test_powers_roots_logs.py` (25.3: `sqrt(2)`, `root(27,3)=3`, `ln(e)=1`, `log10(1000)=3`), `tests/test_constants.py` (25.5: pi/e to ≥10 sig digits), and `tests/test_boundaries.py` (25.6: `asin(-1)`, `asin(1)`, `acos(-1)`, `acos(1)`, `sqrt(0)`, `ln`/`log10` just above 0)
    - _Requirements: 25.1, 25.2, 25.3, 25.5, 25.6_
  - [ ]* 26.2 Write domain-error and angle-mode default/invalid API tests
    - Add `tests/test_domain_errors.py` (25.4: `asin(2)`, `tan(90°)`, `sqrt(-1)`, `root(-8,2)`, `ln(0)`, `log10(-5)`, `root(5,0)`, `(-8)^0.5` each → 4xx Error_Response, no result) and `tests/test_api_angle_mode.py` (omitted mode behaves as radians; `angle_mode="grads"` → 4xx with descriptive message)
    - _Requirements: 25.4, 17.7, 17.8, 18.7, 18.8, 18.9, 18.10, 18.11, 24.8, 17.9, 17.10, 24.3, 24.4_

- [x] 27. Backend scientific property-based tests (Hypothesis)
  - [x] 27.1 Extend Hypothesis strategies and the reference oracle
    - Extend `tests/properties/strategies.py` so the recursive AST strategy generates `ConstantNode`, `FunctionNode` (with per-function in-domain operand strategies), and `RootNode`, plus separate out-of-domain generators per domain-error category; extend `render(ast)` to serialize the new nodes; add an independent high-precision `Decimal` reference oracle (trig via a documented series, powers/roots/logs via `Decimal` built-ins) for P14/P16/P18
    - _Requirements: 6.3, 17.1, 18.1, 19.1_
  - [ ]* 27.2 Write property test P14 (trig/inverse-trig vs reference, both modes)
    - **Property 14: Trigonometric and inverse-trig results match a high-precision reference in both angle modes**
    - **Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.6, 24.5**
    - Tag `# Feature: web-calculator, Property 14: ...` in `tests/properties/test_scientific_property.py`
  - [ ]* 27.3 Write property test P15 (deg↔rad conversion round-trip)
    - **Property 15: Degree/radian conversion round-trips via Decimal pi**
    - **Validates: Requirements 17.5**
    - Tag `# Feature: web-calculator, Property 15: ...` in `tests/properties/test_conversion_property.py`
  - [ ]* 27.4 Write property test P16 (powers/roots/logs vs reference)
    - **Property 16: Powers, roots, and logarithms match a Decimal reference**
    - **Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 24.5**
    - Tag `# Feature: web-calculator, Property 16: ...` in `tests/properties/test_scientific_property.py`
  - [ ]* 27.5 Write property test P17 (domain errors → 4xx, no result)
    - **Property 17: Domain errors always signal a 4xx and never return a result**
    - **Validates: Requirements 17.7, 17.8, 18.7, 18.8, 18.9, 18.10, 18.11, 24.8**
    - Tag `# Feature: web-calculator, Property 17: ...` in `tests/properties/test_domain_property.py`
  - [ ]* 27.6 Write property test P18 (pi/e substitution to ≥10 sig digits)
    - **Property 18: Mathematical constants are substituted to at least 10 significant digits**
    - **Validates: Requirements 19.1, 19.2**
    - Tag `# Feature: web-calculator, Property 18: ...` in `tests/properties/test_scientific_property.py`
  - [ ]* 27.7 Write property test P19 (extended render/parse round-trip)
    - **Property 19: Round-trip render/parse preserves value over functions, constants, and roots**
    - **Validates: Requirements 6.3, 6.4**
    - Tag `# Feature: web-calculator, Property 19: ...` in `tests/properties/test_roundtrip.py` (extends the Stage 1 round-trip test)
  - [ ]* 27.8 Write property test P22 (angle-mode default and invalid rejection)
    - **Property 22: Angle mode defaults to radians and rejects invalid values**
    - **Validates: Requirements 17.9, 17.10, 24.3, 24.4**
    - Tag `# Feature: web-calculator, Property 22: ...` in `tests/properties/test_angle_mode_property.py`
  - [ ]* 27.9 Enforce the scientific coverage and zero-failure gates
    - Configure `pytest --cov` with `--cov-fail-under=90` across the scientific engine modules (`scientific.py`, `constants.py`, and the scientific branches of `evaluator.py`/`parser.py`/`tokenizer.py`) so the suite reports failure if coverage is below 90% or any test fails (Stage 1 Requirement 15 tests + Stage 2 tests + remediation tests run with zero failures/errors)
    - _Requirements: 25.7, 25.8, 16.6_

- [x] 28. Backend scientific completion checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 29. Extend the frontend typed API contract
  - Extend `src/api/types.ts` with `AngleMode = "radians" | "degrees"` (restricted literal union), add `angleMode: AngleMode` to `EvaluateRequest`, and add `MemoryState { value: string }`, `HistoryEntry { expression: string; result: string }`, and `CalculationHistory = readonly HistoryEntry[]` (newest-first, ≤100), all typed without `any`; keep the `isSuccess`/`isError` guards unchanged
  - _Requirements: 24.6_

- [x] 30. Send angle mode from the typed API client
  - Update `src/api/client.ts` so `evaluateExpression` maps the typed `angleMode` to the backend's snake_case `angle_mode` in the JSON body, using the exact same call path for scientific requests, still returning the normalized `{ ok: true; result } | { ok: false; error }` shape, and still surfacing a service-unavailable error (never a local result) on transport failure
  - _Requirements: 24.1, 24.7_

- [x] 31. Implement the pure memory reducer
  - Create `src/state/memoryReducer.ts` holding a single `Decimal`-string register initialized `"0"`, with actions `MEM_ADD(result)`, `MEM_SUB(result)`, `MEM_RECALL`, `MEM_CLEAR`; `MEM_ADD`/`MEM_SUB` require a current numeric result (guarded — no change + error indication when absent) and aggregate via an arbitrary-precision decimal-string helper, NEVER JavaScript `number`/`float`, preserving full decimal value; `MEM_CLEAR` zeroes the register; the Memory_Indicator is derived state (shown iff register ≠ 0); `MR` inserts the register value into the expression guarded so it never exceeds 256 characters (no change + error indication otherwise)
  - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8, 20.9_

- [x] 32. Implement the pure history reducer
  - Create `src/state/historyReducer.ts` holding `CalculationHistory` newest-first; `HISTORY_APPEND(entry)` prepends on a successful evaluation only and caps at 100 by dropping the oldest, and is NOT dispatched on an error response; `HISTORY_CLEAR` empties it; selecting an entry's expression or result replaces the entire current expression; expose empty-state so the panel can render an empty indication
  - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7, 21.8_

- [x] 33. Extend the input hooks for scientific keyboard and evaluation
  - Extend `src/hooks/useKeyboard.ts` preserving every Stage 1 mapping (Requirement 23.5): `^` appends the exponentiation operator; `p` appends `pi` and `e` appends `e`; add a key-sequence recognizer with a 1000 ms inter-key timeout that buffers keystrokes forming a valid function-name prefix and appends the function token (e.g. `sin(`) on a full match, discarding the buffer on timeout or a non-continuing key and leaving the expression/display unchanged; a single unmapped key that is neither a constant binding nor a valid sequence prefix is a no-op (preserving Requirement 10.8). Extend `src/hooks/useEvaluator.ts` to pass the current `angleMode` into `evaluateExpression` and, on success only, trigger the history append (still the only path to a result)
  - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 24.7_

- [ ] 34. Frontend reducer, keyboard, and constant-render property tests
  - [ ]* 34.1 Write memory reducer property tests (P20)
    - **Property 20: Memory register algebra and indicator invariant**
    - **Validates: Requirements 20.2, 20.3, 20.5, 20.6, 20.7**
    - Also cover guards 20.8 (`M+`/`M-` with no numeric result leave the register unchanged + error indication) and 20.9 (`MR` exceeding 256 chars leaves state unchanged + error indication), using the decimal-string helper (never `number`); tag `# Feature: web-calculator, Property 20: ...` in `src/tests/memory.test.ts`
  - [ ]* 34.2 Write history reducer property tests (P21)
    - **Property 21: Calculation history invariants**
    - **Validates: Requirements 21.1, 21.2, 21.5, 21.6, 21.7**
    - Also cover empty-state (21.8) and selection replacing the whole expression (21.3, 21.4); tag `# Feature: web-calculator, Property 21: ...` in `src/tests/history.test.ts`
  - [ ]* 34.3 Write keyboard sequence property tests (P23)
    - **Property 23: Scientific keys append their token and unmapped keys are no-ops**
    - **Validates: Requirements 23.1, 23.2, 23.4, 23.5**
    - Also cover sequence completion within the 1000 ms window (23.3) and discard on timeout/invalid continuation (23.6) using fake timers; tag `# Feature: web-calculator, Property 23: ...` in `src/tests/keyboard.test.ts`
  - [ ]* 34.4 Write constant-render determinism property tests (P24)
    - **Property 24: Constant tokens render deterministically**
    - **Validates: Requirements 19.5**
    - Also verify pi/e controls insert the token at the cursor (19.3, 19.4); tag `# Feature: web-calculator, Property 24: ...` in `src/tests/keyboard.test.ts` (or a dedicated constants test)

- [x] 35. Implement scientific UI components and integrate into the Calculator
  - [x] 35.1 Implement MemoryIndicator and AngleModeToggle
    - Create `src/components/MemoryIndicator.tsx` (a badge shown iff the register is non-zero, derived from memory state, contrast-compliant) and `src/components/AngleModeToggle.tsx` (displays the active mode `radians`/`degrees` and flips it on activation, updating within 100 ms), reusing the Stage 1 `CalcButton` accessibility pattern
    - _Requirements: 20.6, 20.7, 22.6, 22.7, 11.3_
  - [x] 35.2 Implement ScientificKeypad and HistoryPanel
    - Create `src/components/ScientificKeypad.tsx` rendering the trig, inverse-trig, `ln`/`log10`, `sqrt`, `root`, `^`, `pi`/`e`, memory controls, and hosting the angle toggle (collapsible on mobile, reporting collapsed/expanded state), and `src/components/HistoryPanel.tsx` listing entries newest-first with independently selectable expression and result (loading into the expression), a Clear History control, and an empty-state indication; both reuse `CalcButton` so visible labels + matching `aria-label`s and focus/pressed states are inherited
    - _Requirements: 19.3, 19.4, 19.5, 22.1, 22.8, 21.2, 21.3, 21.4, 21.6, 21.8, 11.6, 12.1, 12.2_
  - [x] 35.3 Integrate the scientific surfaces into Calculator.tsx
    - Extend `src/components/Calculator.tsx` to compose the `memoryReducer` and `historyReducer` alongside the Stage 1 `calculatorReducer`, mount `ScientificKeypad`, `HistoryPanel`, `MemoryIndicator`, and `AngleModeToggle`, pass `angleMode` into `useEvaluator`, wire memory/history dispatches (append on success, memory add/subtract of the displayed result), and route keyboard events through the extended `useKeyboard` — no orphaned code
    - _Requirements: 22.1, 20.6, 20.7, 21.1, 21.2, 24.7_

- [x] 36. Implement responsive, accessible scientific styling
  - Add `src/components/ScientificKeypad.css` and `src/components/HistoryPanel.css` and extend `src/styles/theme.css`/`src/styles/global.css` with a responsive scientific grid (collapsible on mobile) that re-flows across 320–767 / 768–1023 / 1024–2560 px with no horizontal overflow or clipping, ≥44×44 px touch targets for every scientific and memory control at mobile widths, and WCAG-contrast theme tokens for the angle toggle and memory indicator (body/label ≥4.5:1, large text ≥3:1, component boundaries and focus indicators ≥3:1)
  - _Requirements: 22.2, 22.3, 22.4, 22.5, 22.9, 11.1, 11.2, 11.3, 11.4_

- [ ] 37. Frontend scientific component and accessibility tests
  - [ ]* 37.1 Write component and a11y tests for the scientific surfaces
    - Add `src/tests/scientificKeypad.test.tsx` (all required controls present with matching `aria-label`s), `src/tests/historyPanel.test.tsx` (newest-first list, selectable expression/result, clear, empty state), `src/tests/angleModeToggle.test.tsx` (displays and flips the mode, updates within 100 ms using fake timers), and memory-indicator show/hide tests; extend `src/tests/client.test.ts` to assert `angle_mode` is sent, scientific success renders the result, and a domain 4xx renders the error (P13 preserved)
    - _Requirements: 22.6, 22.7, 24.1, 24.7, 11.3, 11.6, 12.1, 12.3, 12.4_

- [x] 38. Final Stage 2 checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Stage 2 Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["16", "17"] },
    { "id": 1, "tasks": ["16.1", "18.1", "19"] },
    { "id": 2, "tasks": ["18.2", "20.1"] },
    { "id": 3, "tasks": ["20.2", "21"] },
    { "id": 4, "tasks": ["22"] },
    { "id": 5, "tasks": ["23"] },
    { "id": 6, "tasks": ["25", "26.1", "26.2", "27.1"] },
    { "id": 7, "tasks": ["27.2", "27.3", "27.4", "27.5", "27.6", "27.7", "27.8"] },
    { "id": 8, "tasks": ["27.9"] },
    { "id": 9, "tasks": ["29"] },
    { "id": 10, "tasks": ["30", "31", "32"] },
    { "id": 11, "tasks": ["33"] },
    { "id": 12, "tasks": ["34.1", "34.2", "34.3", "34.4", "35.1"] },
    { "id": 13, "tasks": ["35.2"] },
    { "id": 14, "tasks": ["35.3", "36"] },
    { "id": 15, "tasks": ["37.1"] }
  ]
}
```
---

## Stage 3 Tasks (Testing Quality, Coverage & Containerization)

Stage 3 adds **no new runtime behavior**: it adds a persisted audit, exhaustive edge-case tests, measured coverage gates on both layers, and container/orchestration artifacts around the unchanged Stage 1 + Stage 2 code. All Stage 1 tasks (1–15) and Stage 2 tasks (16–38) remain in force and unchanged. Per the design, the audit document is produced **first** (before any other Stage 3 change), then coverage tooling and tests, then the backward-compatibility/coverage gate, then the container images and compose orchestration, with verification and checkpoints last. Stage 3 introduces **no new PBT properties** (numbering stops at P24); the Requirement 1–25 regression guarantee is provided by re-running the existing P1–P24 suite and the Stage 1/2 example tests, and new edge-case tests reference existing property backstops by their existing numbers. Per the steering note, long-running servers (uvicorn `--reload`, `npm run dev`, `docker compose up`) are run manually in a terminal, never as blocking automation.

- [x] 39. Produce the persisted Stage 1 + Stage 2 Audit_Log (before any other Stage 3 change)
  - Create `docs/stage3-audit-log.md` persisted before the first Stage 3 edit so its creation provably precedes all other Stage 3 work (this is wave 0)
  - Record the four inspection categories — functional bug, mathematical inaccuracy, state leakage, and unhandled edge case — each with an explicit "No defect found" record (the audit found no behavior-changing defects), using the per-defect schema (unique `D-NN` id, category, affected component, reproduction input/steps, distinct Expected vs. Actual) for any future entry
  - Record the feature inventory enumerating every Stage 1 and Stage 2 operation, state surface, and endpoint, marking each present or absent — explicitly note the modulo/`%` operator is ABSENT from the grammar
  - Document the remediation-gating ledger structure: no fix without a prior logged defect id, re-verify Requirements 1–25 recording pass/fail per criterion, reject on any regression; note that because no defect was found, no code remediation is required for Stage 3
  - _Requirements: 26.1, 26.2, 26.3, 26.4, 26.5, 26.6, 26.7_

- [x] 40. Add backend coverage tooling and gate (pytest-cov)
  - Edit `backend/pyproject.toml` to add `pytest-cov` to the `[test]` optional dependencies
  - Add pytest `addopts` `--cov=app --cov-branch --cov-report=term-missing --cov-fail-under=80` and a `[tool.coverage.report] fail_under = 80` branch gate so the run fails and reports the unmet metric when statement or branch coverage is below 80%
  - Use `--cov=app` so `tests/` are excluded from the coverage denominator; keep the existing Stage 2 Requirement 25.7 ≥90% scientific-module gate as an additional stricter check (reconcile, do not replace)
  - _Requirements: 30.1, 30.3, 30.5, 30.7_

- [ ] 41. Add comprehensive backend edge-case tests (through the FastAPI TestClient)
  - [ ]* 41.1 Add division-by-zero and syntactic error tests
    - Add `backend/tests/test_errors.py` asserting that a division-by-zero Expression (`1/0`) returns an Error_Response with a 4xx status and no result (28.1), and one test each for an invalid operator sequence (`1++2`), an unclosed parenthesis (`(1+2`), an invalid character (`1+a`), and an empty Expression (`""`), each returning 4xx with no result (28.6)
    - Document inline that modulo-by-zero (28.2) is N/A — the `%` operator is absent from the grammar so the WHERE guard is false and no test is written; reference property backstops P4 (division by zero) and P5 (invalid character) without creating new properties
    - _Requirements: 28.1, 28.2, 28.6_
  - [ ]* 41.2 Add inverse-trig and logarithm/square-root domain-error tests
    - Add `backend/tests/test_domain_errors.py` asserting `asin(2)` and `acos(2)` (|x|>1) each return 4xx with no result (28.3), and that `ln(0)`, `log10(-5)`, and `sqrt(-1)` each return 4xx with no result (28.5); reference property backstop P17 without creating new properties
    - _Requirements: 28.3, 28.5_
  - [ ]* 41.3 Add boundary-success and non-finite overflow tests
    - Add `backend/tests/test_boundaries.py` asserting `asin(±1)` and `acos(±1)` (|x|==1) each return 200 with a calculated result and no error (28.4), and that an arithmetic operation producing a non-finite result through overflow (e.g. a huge `^`) returns 4xx with no result (28.7); reference property backstop P17's non-finite clause without creating new properties
    - Confirm the backend edge-case suite completes with zero failures and zero errors (28.8)
    - _Requirements: 28.4, 28.7, 28.8_

- [x] 42. Add frontend coverage tooling and gate (@vitest/coverage-v8)
  - Edit `frontend/package.json` to add `@vitest/coverage-v8` as a devDependency and a `"coverage": "vitest run --coverage"` script
  - Edit `frontend/vite.config.ts` `test.coverage` to use provider `'v8'`, `include: ['src/**']`, exclude test and setup files from the denominator, and set `thresholds.statements = 80` and `thresholds.branches = 80` so an unmet statement or branch threshold fails the run and reports it (30.2, 30.4, 30.6, 30.7)
  - Edit `src/tests/setup.ts` to configure the MSW server with `onUnhandledRequest: 'error'` so any un-mocked network request fails the run
  - _Requirements: 30.2, 30.4, 30.6, 30.7, 29.5_

- [ ] 43. Add comprehensive frontend component and state tests (Vitest + RTL + MSW)
  - [ ]* 43.1 Add expression input-handling tests
    - Add `src/tests/input.test.tsx` asserting the `Expression_Display` text content equals the expected sequence exactly after appending a digit (0-9), an operator (`+ - * /`), a decimal point, and both opening and closing parentheses, and after backspace on a non-empty Expression (last character removed) and on an empty Expression (Expression stays `""`), with all backend calls MSW-mocked; reuse property backstops P8/P9 without creating new properties
    - _Requirements: 29.1, 29.5_
  - [ ]* 43.2 Add memory register and indicator tests
    - Add `src/tests/memory.test.ts` asserting the register initialized to `0` and that M+, M-, MR, and MC each produce the expected register value and `Expression_Display` content, and `src/tests/memoryIndicator.test.tsx` asserting the Memory_Indicator renders iff the register value is non-zero; reuse property backstop P20 without creating new properties
    - _Requirements: 29.2, 29.5_
  - [ ]* 43.3 Add keyboard event-handling tests
    - Add `src/tests/keyboard.test.ts` asserting handling of a digit key, an operator key, each evaluate key (`Enter` and `=`), backspace on a non-empty Expression (last char removed) and an empty Expression (stays `""`), `Escape` (Expression and result cleared), and an unmapped key (Expression, result, and error all unchanged); reuse property backstops P8/P10/P11 without creating new properties
    - _Requirements: 29.3, 29.5_
  - [ ]* 43.4 Add calculation-history panel tests
    - Add `src/tests/historyPanel.test.tsx` asserting all stored entries render newest-first (most recent first), that selecting the expression portion and selecting the result portion of a History_Entry each populate the `Expression_Display` with the selected text, that clearing leaves zero entries, and that the empty-state indication renders at zero entries; reuse property backstop P21 without creating new properties
    - Confirm the frontend component/state suite completes in a single non-interactive `vitest run` with zero failures and zero errors (29.6)
    - _Requirements: 29.4, 29.5, 29.6_

- [~] 44. Backward-compatibility and coverage-gate checkpoint
  - Run the full combined suite — backend pytest with coverage (Stage 1 Requirement 15 tests + Stage 2 Requirement 25 tests + properties P1–P24 + the new Stage 3 edge-case tests) and frontend Vitest with coverage (Stage 1/2 component/reducer tests + the new Stage 3 tests) — and confirm zero failures and zero errors on both suites and ≥80% statement and branch coverage on both layers
  - Perform the negative check once: run a deliberately under-covered subset to confirm the coverage gate actually fails below threshold and reports the unmet metric, then restore the full run
  - Reject or correct any Stage 3 change that reports a failure or error against a Requirement 1–25 criterion, preserving the Stage 1 and Stage 2 baseline until resolved
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 27.1, 27.2, 27.3, 27.4, 26.6, 30.3, 30.4, 30.5, 30.6_

- [~] 45. Create the backend container image artifacts
  - Create `backend/Dockerfile` as a multi-stage build: a builder stage installs only runtime dependencies into `/opt/venv`, and a final stage based on `python:3.11-slim` copies the venv and `app/`, creates a non-root `appuser` with a uid that is not 0, sets `USER appuser`, sets `ENV PORT=8000`, `EXPOSE 8000`, and execs `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}` so a startup failure exits with a non-zero status and an unset `PORT` falls back to the default port
  - Create `backend/.dockerignore` excluding `.venv`, `tests/`, `.pytest_cache`, `.hypothesis`, and `__pycache__`
  - _Requirements: 31.1, 31.2, 31.3, 31.4, 31.5, 31.6, 31.7_

- [~] 46. Create the frontend container image artifacts
  - Create `frontend/Dockerfile` as a multi-stage build: a `node:20-alpine` build stage runs `npm ci && npm run build` producing `dist/`, and a final `nginx:alpine` stage copies only `dist/` into `/usr/share/nginx/html` and copies `nginx.conf`
  - Create `frontend/nginx.conf` with an SPA fallback `location / { try_files $uri $uri/ /index.html; }` (unknown routes return `index.html` with a success status; existing assets return the asset with a success status) and `location /api/ { proxy_pass http://backend:8000; }` to reverse-proxy the Evaluate_Endpoint to the backend service by name
  - Create `frontend/.dockerignore` excluding `node_modules`, `dist`, and `coverage`
  - _Requirements: 32.1, 32.2, 32.3, 32.4, 32.5, 32.6, 33.3_

- [~] 47. Create the multi-container orchestration compose file
  - Create `docker-compose.yml` at the repository root defining a backend service built from `./backend` and a frontend service built from `./frontend` on the shared default network so each service resolves the other by its service name
  - Map exactly one host port to the frontend container's listening port (e.g. `8080:80`), do NOT host-publish the backend service, and set `restart: unless-stopped` on both services so an unexpected non-zero exit auto-restarts unless an operator stopped the container
  - _Requirements: 33.1, 33.2, 33.5, 33.6_

- [ ] 48. Verify the container stack (run manually, not blocking automation)
  - [ ]* 48.1 Verify the backend image
    - Build the Backend_Image and confirm it runs the Backend_Service process as a non-zero uid, that `POST /api/v1/evaluate` returns 200 for a valid expression, that an unset `PORT` falls back to the default port, and that a forced startup failure exits with a non-zero status
    - _Requirements: 31.3, 31.4, 31.6, 31.7_
  - [ ]* 48.2 Verify the frontend image
    - Build the Frontend_Image and confirm an unknown SPA route returns `index.html` with a success status, and an existing static asset returns that asset with a success status
    - _Requirements: 32.3, 32.4, 32.5_
  - [ ]* 48.3 Verify compose orchestration end-to-end
    - Bring the stack up and confirm both services start, the frontend reaches the backend by service name, a request through the frontend `/api` path returns a computed result, and with the backend stopped the `/api` path yields a service-unavailable error with no computed result
    - _Requirements: 33.2, 33.3, 33.4_

- [~] 49. Final Stage 3 checkpoint
  - Confirm the full combined test suite passes with zero failures/errors and the ≥80% statement + branch coverage gate holds on both layers, and that the container stack (backend image, frontend image, compose orchestration) is verified
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 27.3, 30.3, 30.4, 31.1, 32.1, 33.1_

## Stage 3 Notes

- Core implementation artifacts — the Audit_Log (task 39), coverage configuration (tasks 40, 42), Dockerfiles and nginx.conf (tasks 45, 46), and the compose file (task 47) — are required (non-optional).
- Test-writing sub-tasks (41.x, 43.x) and the manual container verification sub-tasks (48.x) are marked optional with `*` per the existing convention.
- Stage 3 adds no new PBT properties (numbering stops at P24); edge-case tests reference the existing property backstops (P4, P5, P8, P9, P10, P11, P17, P20, P21) by their existing numbers.
- Modulo-by-zero (Requirement 28.2) is N/A because the `%` operator is absent from the grammar (recorded in the feature inventory); the WHERE guard is false, so no test is written.
- Long-running servers (uvicorn `--reload`, `npm run dev`, `docker compose up`) are run manually in a terminal, not as blocking automation.

## Stage 3 Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["39"] },
    { "id": 1, "tasks": ["40", "42"] },
    { "id": 2, "tasks": ["41.1", "41.2", "41.3", "43.1", "43.2", "43.3", "43.4"] },
    { "id": 3, "tasks": ["44"] },
    { "id": 4, "tasks": ["45", "46"] },
    { "id": 5, "tasks": ["47"] },
    { "id": 6, "tasks": ["48.1", "48.2", "48.3"] }
  ]
}
```
