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

- [x] 44. Backward-compatibility and coverage-gate checkpoint
  - Run the full combined suite — backend pytest with coverage (Stage 1 Requirement 15 tests + Stage 2 Requirement 25 tests + properties P1–P24 + the new Stage 3 edge-case tests) and frontend Vitest with coverage (Stage 1/2 component/reducer tests + the new Stage 3 tests) — and confirm zero failures and zero errors on both suites and ≥80% statement and branch coverage on both layers
  - Perform the negative check once: run a deliberately under-covered subset to confirm the coverage gate actually fails below threshold and reports the unmet metric, then restore the full run
  - Reject or correct any Stage 3 change that reports a failure or error against a Requirement 1–25 criterion, preserving the Stage 1 and Stage 2 baseline until resolved
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 27.1, 27.2, 27.3, 27.4, 26.6, 30.3, 30.4, 30.5, 30.6_

- [x] 45. Create the backend container image artifacts
  - Create `backend/Dockerfile` as a multi-stage build: a builder stage installs only runtime dependencies into `/opt/venv`, and a final stage based on `python:3.11-slim` copies the venv and `app/`, creates a non-root `appuser` with a uid that is not 0, sets `USER appuser`, sets `ENV PORT=8000`, `EXPOSE 8000`, and execs `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}` so a startup failure exits with a non-zero status and an unset `PORT` falls back to the default port
  - Create `backend/.dockerignore` excluding `.venv`, `tests/`, `.pytest_cache`, `.hypothesis`, and `__pycache__`
  - _Requirements: 31.1, 31.2, 31.3, 31.4, 31.5, 31.6, 31.7_

- [x] 46. Create the frontend container image artifacts
  - Create `frontend/Dockerfile` as a multi-stage build: a `node:20-alpine` build stage runs `npm ci && npm run build` producing `dist/`, and a final `nginx:alpine` stage copies only `dist/` into `/usr/share/nginx/html` and copies `nginx.conf`
  - Create `frontend/nginx.conf` with an SPA fallback `location / { try_files $uri $uri/ /index.html; }` (unknown routes return `index.html` with a success status; existing assets return the asset with a success status) and `location /api/ { proxy_pass http://backend:8000; }` to reverse-proxy the Evaluate_Endpoint to the backend service by name
  - Create `frontend/.dockerignore` excluding `node_modules`, `dist`, and `coverage`
  - _Requirements: 32.1, 32.2, 32.3, 32.4, 32.5, 32.6, 33.3_

- [x] 47. Create the multi-container orchestration compose file
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

- [x] 49. Final Stage 3 checkpoint
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

---

## Stage 4 Tasks (RPN Engine Migration)

Stage 4 performs a drastic **internal** architectural migration of the Evaluation_Engine from infix AST-walking to Reverse Polish Notation (RPN / postfix) evaluation, while preserving every externally observable behavior: the arithmetic results, the error conditions, the `POST /api/v1/evaluate` contract (Requirements 5, 24), and the frontend no-local-arithmetic rule (Requirements 14, 24). All Stage 1 tasks (1–15), Stage 2 tasks (16–38), and Stage 3 tasks (39–49) remain in force and unchanged. Per the design and the SEED-4 agent instructions, work proceeds **backend-first**: the persisted Migration_Audit_Log is produced **first** (before any other Stage 4 change), then the engine migration (errors → RPN model/linearizer → stack evaluator → rewire), then the backend tests and coverage/regression gate, then the frontend dual-mode surface, then the frontend tests, then container verification, with the final backward-compatibility checkpoint last. The chosen approach **keeps the recursive-descent parser and adds a pure AST→RPN linearization** (`to_rpn`) plus a `stack_evaluate` stack machine, so Requirement 2 precedence/associativity is inherited rather than re-implemented, and the single public entry point `evaluate_expression()` keeps its exact signature. Stage 4 adds new correctness properties **P25–P35** and reuses P1–P24 as the backward-compatibility regression proof. Per the steering note, long-running servers (uvicorn `--reload`, `npm run dev`, `docker compose up`) are run manually in a terminal, never as blocking automation.

- [x] 50. Produce the persisted Migration_Audit_Log (before any other Stage 4 change)
  - Create `docs/stage4-audit-log.md` persisted before the first Stage 4 edit so its creation provably precedes all other Stage 4 work (this is wave 0); the inspection covers every Stage 1, Stage 2, and Stage 3 source component (the full `backend/app/engine/*`, `backend/app/api/*`, `backend/app/main.py`, the `backend/tests/` suite incl. `tests/properties/strategies.py`, the frontend `src/api/*`, `src/state/*`, `src/hooks/*`, `src/components/*`, and the container artifacts)
  - Record the four inspection categories — **functional bug**, **architectural flaw**, **Decimal_Precision issue**, and **test coverage gap** — each with either ≥1 documented defect entry or an explicit "No defect found" record so no category is left unaddressed (the audit found no behavior-changing defect; record the known *forward* coverage gap for the not-yet-existing RPN modules — `rpn.py`, `rpn_evaluator.py`, the four RPN error classes, and the frontend RPN surface — as a planned gap closed by task 55/59, not a defect in shipped code)
  - Use the per-defect record schema for any entry: a unique `M-NN` id, exactly one of the four categories, the affected component, the reproduction input/ordered steps, and **distinct** Expected vs. Actual values
  - Document the remediation-gating ledger structure: no fix without a prior logged defect id; on any applied remediation re-verify every applicable Requirement 1–33 criterion recording a pass/fail outcome; accept only if all pass; reject on any regression and preserve the pre-remediation baseline until resolved; note that because no defect was found, no code remediation is required to begin the migration
  - _Requirements: 34.1, 34.2, 34.3, 34.4, 34.5, 34.6, 34.7_

- [x] 51. Extend the backend error taxonomy for RPN evaluation failures
  - Add four new subclasses to `app/engine/errors.py`, each deriving from the existing `EvaluationError` base (carrying `kind` + descriptive `message`) so the single existing `EvaluationError` handler in `main.py` maps them to 4xx `ErrorResponse` with **no handler change**: `StackUnderflowError` (`kind = "stack_underflow"`, message names the operator that could not be satisfied), `SurplusOperandsError` (`kind = "surplus_operands"`, message names the count of values remaining), `EmptyStackError` (`kind = "empty_stack"`), and `UnprocessableTokenError` (`kind = "unprocessable_token"`, message names the offending token)
  - Preserve the mutually exclusive success/Error_Response contract (an `error` field, no `result` field) defined in Requirements 5 and 24
  - _Requirements: 36.8, 36.9, 37.7, 38.1, 38.2, 38.3, 38.4, 38.5_

- [x] 52. Implement the RPN token model and Shunting Yard linearization
  - Create `app/engine/rpn.py` with the typed, frozen `RpnToken` dataclasses `Operand(value: Decimal)`, `Constant(name: str)`, `BinaryOp(symbol: str)`, `UnaryFunc(name: str)` (trig/inverse-trig, `ln`, `log10`, `sqrt`, and unary `neg`), and `RootOp` (n-th root), plus the `RpnTokenSequence = list[RpnToken]` alias — carrying `Decimal` operands, never `float`, and containing **no parenthesis tokens**
  - Implement `to_rpn(ast) -> RpnTokenSequence` as a pure, deterministic post-order traversal of the parsed AST: `NumberNode → [Operand]`, `ConstantNode → [Constant]`, `UnaryOpNode(-, x) → to_rpn(x) ++ [UnaryFunc("neg")]`, `BinaryOpNode(op,l,r) → to_rpn(l) ++ to_rpn(r) ++ [BinaryOp(op)]`, `FunctionNode(f,x) → to_rpn(x) ++ [UnaryFunc(f)]`, `RootNode(rad,deg) → to_rpn(rad) ++ to_rpn(deg) ++ [RootOp]`; precedence/associativity, right-assoc `^`, the unary-minus-after-`^` rule, and function/constant placement are inherited from the already-correct AST, so the sequence is parenthesis-free (35.5), carries function/constant tokens in postfix order (35.6), and is identical across repeated submissions (35.7)
  - Rely on `parse()` raising `InvalidSyntaxError`/`UnbalancedParenthesesError`/`InvalidCharacterError`/`EmptyExpressionError` **before** `to_rpn`, so a grammar violation never produces a partial RPN_Token_Sequence (35.8); `to_rpn` runs only on a fully valid AST
  - _Requirements: 35.1, 35.2, 35.3, 35.4, 35.5, 35.6, 35.7, 35.8_

- [x] 53. Implement the stack-based Stack_Evaluator
  - Create `app/engine/rpn_evaluator.py` with `stack_evaluate(seq, angle_mode="radians") -> Decimal` over a Decimal-only Evaluation_Stack (never `float` — 36.6): push each `Operand`/`Constant` as a `Decimal` in sequence order (a `Constant` pushes its high-precision `Decimal` from the unchanged `constants.py`, ≥10 sig digits — 36.1, 37.4); for a `BinaryOp` pop two operands treating **first popped = right, second popped = left**, apply with `Decimal` arithmetic, push the result (36.2); for a `UnaryFunc` pop one operand and apply the **unchanged** `scientific.py` kernel under the active `angle_mode` (unary `neg` negates), push the result (36.3, 37.1, 37.2); for `RootOp` pop two treating **first popped = degree, second popped = radicand**, apply the same n-th-root computation as the current `RootNode` path (37.3); recalled Memory_Register values arrive as ordinary numeric operands and are pushed like any other `Operand` with their full decimal value (37.5)
  - On completion, return the single remaining value through the **shared `_finalize`** path (≥10-sig-digit, round-half-even normalization — 36.4, 36.7); defensively raise the four new RPN errors — `StackUnderflowError` when an operator needs more operands than the stack holds (36.8, 37.7, 38.1), `SurplusOperandsError` when >1 value remains after consumption (36.9, 38.2), `EmptyStackError` when 0 values remain (38.3), `UnprocessableTokenError` for a token that is neither a valid operand nor a supported operator/function (38.4); propagate the unchanged `DomainError` from the kernels on any out-of-domain/non-finite operand (37.6)
  - Preserve pre-migration result parity: any expression that produced a valid result under the infix engine returns an equal result to ≥10 sig digits (36.5)
  - _Requirements: 36.1, 36.2, 36.3, 36.4, 36.5, 36.6, 36.7, 36.8, 36.9, 37.1, 37.2, 37.3, 37.4, 37.5, 37.6, 37.7_

- [x] 54. Rewire the single engine entry point to the RPN pipeline
  - Update `app/engine/__init__.py` so `evaluate_expression(expression: str, angle_mode: str = "radians") -> Decimal` keeps its **exact signature and docstring contract** but internally does `ast = parse(expression); rpn = to_rpn(ast); return stack_evaluate(rpn, angle_mode)`, continuing to propagate every `EvaluationError` subclass (including the four new RPN errors); add `to_rpn`, `stack_evaluate`, the `RpnToken`/`RpnTokenSequence` symbols, and the new error classes to the re-export list / `__all__`
  - Retain the legacy AST-walking `evaluate()` as a **test-only reference oracle** for the parity property (no longer on the request path); leave `app/api/routes.py`, `app/api/schemas.py`, and `app/main.py` **unchanged**
  - _Requirements: 35.1, 36.5, 43.3_

- [x] 55. Backend RPN engine checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 56. Refactor and extend the backend RPN test suite
  - [x] 56.1 Extend Hypothesis strategies and the independent reference oracle
    - Extend `tests/properties/strategies.py` with an independent reference arithmetic oracle distinct from the RPN engine (either the retained legacy AST-walking `evaluate()` or a standalone `Decimal` reference) and any generators needed for P25–P30, spanning ≥3 precedence levels, parentheses, scientific functions, constants, and both angle modes, plus out-of-domain/grammar-violation generators for the error-parity property
    - _Requirements: 41.4, 43.3, 43.4_
  - [ ]* 56.2 Write RPN conversion unit tests
    - Add `tests/test_rpn_conversion.py` asserting exact RPN_Token_Sequence equality for hand-picked expressions combining ≥3 precedence levels, parentheses, right-assoc `^`, and the unary-minus rule (e.g. `3+4*2`, `(1+2)*3`, `2^2^3`, `-3^2`, `sin(pi/2)+root(27,3)`); reference backstops P26, P27
    - _Requirements: 41.1_
  - [ ]* 56.3 Write Stack_Evaluator unit tests
    - Add `tests/test_rpn_evaluator.py` asserting push/pop + operator evaluation with results equal to the expected value to ≥10 significant digits, pinning non-commutative operand order (`8 3 -` = 5, `2 3 ^` = 8, `root(27,3)` = 3); reference backstops P25, P28
    - _Requirements: 41.2_
  - [ ]* 56.4 Write RPN error unit tests
    - Add `tests/test_rpn_errors.py` asserting each RPN evaluation error — Stack_Underflow, Surplus_Operands, empty Evaluation_Stack, and unprocessable token — returns a 4xx Error_Response with no `result` and a descriptive message (operator / remaining count / token named); reference backstop P29
    - _Requirements: 41.3_
  - [ ]* 56.5 Write property test P25 (RPN engine matches the reference oracle)
    - **Property 25: RPN engine matches an independent reference oracle (result parity)**
    - **Validates: Requirements 35.2, 35.3, 35.4, 35.6, 36.2, 36.3, 36.5, 37.1, 37.2, 37.3, 37.4, 37.5, 43.3**
    - Hypothesis ≥100 examples, cross-checking `parse → to_rpn → stack_evaluate` against the oracle to ≥10 sig digits; tag `# Feature: web-calculator, Property 25: ...` in `tests/properties/test_rpn_parity.py`
  - [ ]* 56.6 Write property tests P26 and P27 (deterministic conversion, parenthesis-free)
    - **Property 26: Shunting Yard conversion is deterministic** — **Validates: Requirements 35.7**
    - **Property 27: The RPN_Token_Sequence is parenthesis-free** — **Validates: Requirements 35.5**
    - Tag each `# Feature: web-calculator, Property N: ...` in `tests/properties/test_rpn_conversion_property.py`
  - [ ]* 56.7 Write property test P28 (well-formed RPN yields exactly one value)
    - **Property 28: Well-formed RPN evaluation yields exactly one value**
    - **Validates: Requirements 36.1, 36.4**
    - Tag `# Feature: web-calculator, Property 28: ...` in `tests/properties/test_rpn_parity.py`
  - [ ]* 56.8 Write property test P29 (malformed RPN always errors, never a result)
    - **Property 29: Malformed RPN sequences always signal an error and never return a result**
    - **Validates: Requirements 36.8, 36.9, 37.7, 38.1, 38.2, 38.3, 38.4**
    - Tag `# Feature: web-calculator, Property 29: ...` in `tests/properties/test_rpn_errors_property.py`
  - [ ]* 56.9 Write property test P30 (error-condition parity with the pre-migration engine)
    - **Property 30: Error-condition parity with the pre-migration engine**
    - **Validates: Requirements 35.8, 37.6, 43.4**
    - Tag `# Feature: web-calculator, Property 30: ...` in `tests/properties/test_rpn_parity.py`

- [x] 57. Backend coverage and backward-compatibility gate
  - Run the full backend suite under coverage — Stage 1 Requirement 15 tests + Stage 2 Requirement 25 tests + the P1–P24 regression properties + the new Stage 4 RPN conversion/evaluator/error/parity tests — and confirm zero failures, zero errors, and zero collection errors (41.10, 43.1)
  - Reuse the Requirement 30 Coverage_Threshold (`pytest --cov=app --cov-branch --cov-fail-under=80` plus the `[tool.coverage.report] fail_under = 80` branch gate) so the run fails and reports the unmet metric if statement **or** branch coverage of `app/` (including the new `rpn.py`, `rpn_evaluator.py`, and the four new error classes) falls below 80% (41.8, 41.9)
  - Confirm result parity (≥10 sig digits, 43.3) and error-condition parity (43.4) hold via P25/P30; reject or correct any Stage 4 change that reports a failure against a Requirement 1–33 criterion, preserving the Stage 1–3 baseline until resolved (43.6, 43.7)
  - _Requirements: 41.8, 41.9, 41.10, 43.1, 43.3, 43.4, 43.6, 43.7_

- [x] 58. Implement the pure RPN reducer
  - Create `src/state/rpnReducer.ts` as a pure, side-effect-free reducer with an exhaustive `assertNever` guard holding `RpnState { mode: "standard" | "rpn" (default "standard"); operandEntry: string; stack: { x?; y?; z?; t? } of Decimal strings; error: string | null }` and actions `TOGGLE_MODE`, `APPEND_OPERAND_CHAR`, `PUSH`, `SET_STACK`, `SET_RPN_ERROR`, `RESET`
  - `TOGGLE_MODE` switches `mode` and clears `operandEntry`, `stack`, and the result/error so no value carries across the switch (39.2); `PUSH` (Enter_Control) with a non-empty `operandEntry` places the operand at `X`, shifts `X→Y→Z→T` (dropping `T` when full), and clears `operandEntry` (39.4, 40.2), and with an empty `operandEntry` is a no-op that sets an error indication "no operand to push" (39.6); `SET_STACK` applies a confirmed backend success (40.3, 40.7 on the retain path); `SET_RPN_ERROR` leaves the `stack` unchanged and shows no computed result (39.7, 40.7); result and error are mutually exclusive; the reducer computes **no arithmetic locally** (39.9)
  - _Requirements: 39.1, 39.2, 39.4, 39.6, 39.9, 40.2, 40.7_

- [x] 59. Implement the dual-mode RPN UI components
  - [x] 59.1 Implement ModeToggle and StackDisplay
    - Create `src/components/ModeToggle.tsx` selecting between Standard_Mode and RPN_Mode, displaying the active mode and defaulting to Standard_Mode (39.1), reusing the Stage 1 `CalcButton` accessibility pattern (visible label + matching `aria-label` + focus/pressed state), and `src/components/StackDisplay.tsx` (+ `StackDisplay.css`) rendering the X/Y/Z/T Stack_Levels with an identifying text label per level and an empty-state indication when no value is held (40.1, 40.4, 40.6), wrapped in an `aria-live="polite"` region so stack changes are announced (40.5)
    - _Requirements: 39.1, 40.1, 40.4, 40.5, 40.6_
  - [x] 59.2 Extend useKeyboard for RPN parity
    - Extend `src/hooks/useKeyboard.ts` so in RPN_Mode the `Enter` key drives the same `PUSH` reducer action as the on-screen Enter_Control and operator keys drive the same operator flow as their keypad buttons (identical state changes — 39.8), while preserving every Stage 1/2 mapping for Standard_Mode (39.3); keep the "callbacks via ref" pattern for stable listeners
    - _Requirements: 39.3, 39.8_
  - [x] 59.3 Integrate the RPN surface into Calculator.tsx
    - Extend `src/components/Calculator.tsx` to compose `rpnReducer` alongside the Stage 1/2 reducers and mount `ModeToggle`; when `mode === "standard"` render and wire the **entire unchanged** Stage 1/2 infix surface (39.3); when `mode === "rpn"` render `StackDisplay`, route Enter to `PUSH`, and map a binary operator control (with ≥2 stack values) to "build an infix expression from the top stack values (e.g. `` `${y} ${op} ${x}` ``, `` `${fn}(${x})` `` for a unary op) → submit via the unchanged `useEvaluator`/`evaluateExpression` with the active `angleMode` → dispatch `SET_STACK` replacing the consumed operands with the single backend result at `X`" (39.5, 40.3); with fewer than the required values the operator is a no-op with an "insufficient values" error indication and **no backend call** (39.7); every calculated result comes exclusively from the backend (39.9, 43.5), and a backend Error_Response or transport failure retains the pre-operation Stack_Display and shows no local result (40.7, 43.5) — no orphaned code
    - _Requirements: 39.3, 39.5, 39.7, 39.9, 40.3, 40.7, 43.5_

- [x] 60. Add responsive, accessible RPN styling
  - Add/extend `src/components/StackDisplay.css` and the `src/styles/theme.css`/`src/styles/global.css` tokens so the mode toggle and Stack_Display re-flow responsively with no horizontal overflow or clipping, provide ≥44×44 px touch targets for the RPN controls at mobile widths, and meet WCAG contrast (body/label ≥4.5:1, large text ≥3:1, component boundaries and focus indicators ≥3:1), reusing the Stage 1/2 responsive/accessibility tokens (Stage 4 adds no new responsive requirement numbers)
  - _Requirements: 40.6_

- [x] 61. Frontend RPN checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 62. Add frontend RPN component and reducer tests (Vitest + RTL + MSW)
  - [ ]* 62.1 Write RPN reducer property tests (P31, P33)
    - **Property 31: RPN push places the operand at X and shifts prior levels** — **Validates: Requirements 39.4, 39.6, 40.2**
    - **Property 33: Switching mode resets all transient state** — **Validates: Requirements 39.2**
    - Generator/table-driven cases; tag each `# Feature: web-calculator, Property N: ...` in `src/tests/rpnReducer.test.ts`
  - [ ]* 62.2 Write RPN result-update and keypad/keyboard parity property tests (P32, P34)
    - **Property 32: A backend result replaces the consumed operands with a single value** — **Validates: Requirements 39.5, 40.3**
    - **Property 34: Keypad and keyboard produce identical RPN state changes** — **Validates: Requirements 39.8**
    - Tag each `# Feature: web-calculator, Property N: ...` in `src/tests/rpnReducer.test.ts`
  - [ ]* 62.3 Write RPN input + Enter-push + StackDisplay component tests
    - Add `src/tests/rpn.test.tsx` asserting that entering an operand and activating the Enter_Control pushes it to the X level and the `StackDisplay` renders the active X/Y/Z/T levels, with all backend calls MSW-mocked and no live network request (41.5); reference backstop P31
    - _Requirements: 41.5_
  - [ ]* 62.4 Write mode-switch reset component test
    - Add `src/tests/rpnMode.test.tsx` asserting that toggling between RPN_Mode and Standard_Mode resets the Stack_Display and the in-progress operand entry to empty with no residual Stack_Levels (41.6); reference backstop P33
    - _Requirements: 41.6_
  - [ ]* 62.5 Write backend-error-retains-stack component test (P35)
    - **Property 35: RPN results come only from the backend and errors retain the stack**
    - **Validates: Requirements 39.5, 39.9, 40.7, 43.5**
    - Add `src/tests/rpnError.test.tsx` with MSW configured to return an Error_Response during an RPN operation, asserting an error indication renders, no calculated result is displayed, and the pre-operation Stack_Display values are retained (41.7); tag `# Feature: web-calculator, Property 35: ...`
    - _Requirements: 41.7_

- [x] 63. Frontend coverage and backward-compatibility gate
  - Run the full frontend suite in a single non-interactive `vitest run --coverage` — Stage 1/2/3 component/reducer tests + the new Stage 4 RPN tests — and confirm zero failures, zero errors, and zero collection errors (41.10, 43.2), with MSW `onUnhandledRequest: 'error'` so no test issues a live network request (41.5)
  - Reuse the Requirement 30 Coverage_Threshold (v8 provider, `thresholds.statements = 80`, `thresholds.branches = 80` over `src/**`, including `rpnReducer.ts`, `ModeToggle.tsx`, and `StackDisplay.tsx`) so an unmet statement or branch threshold fails the run and reports it (41.8, 41.9); confirm the no-local-arithmetic guarantee holds via P35 (43.5)
  - _Requirements: 41.8, 41.9, 41.10, 43.2, 43.5_

- [ ] 64. Verify the container stack under the RPN engine (run manually, not blocking automation)
  - [ ]* 64.1 Rebuild and verify the backend image
    - Rebuild the Backend_Image from the **unchanged** multi-stage, non-root `python:3.11-slim` `backend/Dockerfile` (42.1, 42.5) and confirm it starts the Backend_Service as a non-root uid listening on `${PORT:-8000}` serving the Evaluate_Endpoint backed by the RPN engine (42.3), that a forwarded `POST /api/v1/evaluate` returns an RPN-computed result in the Stage 1/2 success shape with Decimal_Precision (42.6), and that a forced build failure exits non-zero with no tagged image (42.7)
    - _Requirements: 42.1, 42.3, 42.5, 42.6, 42.7_
  - [ ]* 64.2 Rebuild and verify the frontend image
    - Rebuild the Frontend_Image from the **unchanged** multi-stage `node:20-alpine` → `nginx:alpine` `frontend/Dockerfile` serving the compiled `dist/` including the new RPN-mode UI assets (42.2), confirming an unknown SPA route returns `index.html` with a success status and an existing static asset returns that asset
    - _Requirements: 42.2_
  - [ ]* 64.3 Verify compose orchestration end-to-end under the RPN engine
    - Bring up `docker-compose.yml` (topology unchanged — 42.5) and confirm both services start on the shared network with service-name DNS (42.4), a request through the frontend `/api` proxy returns an RPN-computed result in the Decimal_Precision success shape (42.6), and with the backend stopped the `/api` path yields a service-unavailable error with no computed result
    - _Requirements: 42.4, 42.5, 42.6_

- [x] 65. Final Stage 4 checkpoint
  - Confirm the full combined suite passes with zero failures/errors on both layers — backend pytest (Stage 1/2/3 tests + properties P1–P24 + the new Stage 4 RPN conversion/evaluator/error/parity tests) and frontend Vitest (Stage 1/2/3 tests + the new RPN tests) — with the ≥80% statement + branch coverage gate holding on both layers (41.10, 43.1, 43.2), result parity (≥10 sig digits) and error-condition parity with the pre-migration engine confirmed via P25/P30 (43.3, 43.4), the frontend computing no arithmetic locally (43.5), and the container stack (backend image, frontend image, compose orchestration) verified under the RPN engine
  - Reject or correct the migration before it is considered complete if any Requirement 1–33 criterion reports a failure, preserving the Stage 1–3 baseline until resolved (43.6, 43.7)
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 41.10, 42.1, 42.4, 42.6, 43.1, 43.2, 43.3, 43.4, 43.5, 43.6, 43.7_

## Stage 4 Notes

- Core implementation artifacts are required (non-optional): the Migration_Audit_Log (task 50), the four RPN error classes (task 51), the RPN model/linearizer (task 52), the Stack_Evaluator (task 53), the entry-point rewire (task 54), the extended Hypothesis strategies/oracle (task 56.1), the RPN reducer (task 58), the RPN UI components and `Calculator` integration (task 59), and the RPN styling (task 60).
- The Migration_Audit_Log (task 50) is produced **first**, in wave 0, before any other Stage 4 change, so its creation provably precedes the migration (Requirement 34.1, 34.7). Work then proceeds backend-first (errors → RPN model → evaluator → rewire → backend tests/gate → frontend reducer/components → frontend integration → frontend tests → docker → final checkpoint).
- Stage 4 adds correctness properties **P25–P35**; P1–P24 are **reused** as the backward-compatibility regression proof (Requirements 43.1, 43.2) — P1 now exercises `parse → to_rpn → stack_evaluate` unchanged, P2 is reused because the Stack_Evaluator routes its result through the same `_finalize` path, P4/P5/P17 back the RPN domain/error paths, P6 covers the mutually-exclusive RPN error contract, P12 extends to the Stack_Display level labels, and P13/Requirement 14.4 back the RPN transport-failure handling reused in P35.
- With the already-correct recursive-descent parser, Stack_Underflow, Surplus_Operands, empty-stack, and unprocessable-token are **defensive internal invariants** (a valid AST always linearizes to a sequence evaluating to exactly one value), but they are still raised, mapped to 4xx, and tested per Requirements 38 and 41.3.
- The frontend performs **no local arithmetic** in either mode: RPN operator actions build an infix expression from the top stack values and submit it to the existing `/api/v1/evaluate` endpoint, so there is no new endpoint and no contract change; the stack is mutated only on a confirmed backend success, and retained on any error/transport failure.
- Tasks marked with `*` are optional test or manual-verification sub-tasks and can be skipped for a faster MVP; top-level tasks and core implementation sub-tasks are never optional.
- Long-running servers (uvicorn `--reload`, `npm run dev`, `docker compose up`) are run manually in a terminal, not as blocking automation; full WCAG conformance still requires manual assistive-technology testing beyond the automated contrast/label checks.

## Stage 4 Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["50"] },
    { "id": 1, "tasks": ["51"] },
    { "id": 2, "tasks": ["52"] },
    { "id": 3, "tasks": ["53"] },
    { "id": 4, "tasks": ["54"] },
    { "id": 5, "tasks": ["56.1"] },
    { "id": 6, "tasks": ["56.2", "56.3", "56.4", "56.5", "56.6", "56.7", "56.8", "56.9"] },
    { "id": 7, "tasks": ["57"] },
    { "id": 8, "tasks": ["58"] },
    { "id": 9, "tasks": ["59.1", "59.2"] },
    { "id": 10, "tasks": ["59.3", "60"] },
    { "id": 11, "tasks": ["62.1", "62.2", "62.3", "62.4", "62.5"] },
    { "id": 12, "tasks": ["63"] },
    { "id": 13, "tasks": ["64.1", "64.2", "64.3"] }
  ]
}
```
