# Project Structure & Conventions

## Layout

```
.
├── docs/SEED.md                  # product source of truth
├── .kiro/
│   ├── specs/web-calculator/     # requirements.md, design.md, tasks.md
│   └── steering/                 # these files
├── backend/                      # FastAPI math oracle
│   ├── app/
│   │   ├── main.py               # app assembly: router, CORS, exception handlers
│   │   ├── api/
│   │   │   ├── routes.py         # POST /api/v1/evaluate
│   │   │   └── schemas.py        # Pydantic EvaluateRequest/Success/ErrorResponse
│   │   └── engine/               # pure, HTTP-agnostic computation core
│   │       ├── __init__.py       # evaluate_expression() public entry point
│   │       ├── tokenizer.py      # string -> tokens
│   │       ├── parser.py         # tokens -> AST + render() inverse
│   │       ├── evaluator.py      # AST -> Decimal
│   │       └── errors.py         # EvaluationError hierarchy
│   ├── tests/                    # pytest + tests/properties/ (Hypothesis)
│   └── pyproject.toml
└── frontend/                     # React + TypeScript UI
    └── src/
        ├── api/                  # types.ts (contract + guards), client.ts
        ├── state/                # calculatorReducer.ts (pure state)
        ├── hooks/                # useKeyboard.ts, useEvaluator.ts
        ├── components/           # Calculator, Keypad, CalcButton, *Display (+ .css)
        ├── styles/               # theme.css (tokens), global.css (layout)
        ├── tests/                # Vitest specs + setup.ts
        └── App.tsx, main.tsx
```

## Backend conventions

- **Layered pipeline:** transport (`api/routes.py`) → validation (Pydantic) →
  `engine`. Each layer depends only on the one below. The `engine` package is pure
  and never imports HTTP/FastAPI concerns, so it stays independently unit-testable.
- **Single engine entry point:** callers use `app.engine.evaluate_expression()`.
  Do not reach into the tokenizer/parser/evaluator from the API layer directly.
- **Errors:** raise a subclass of `EvaluationError` (carrying `kind` + `message`)
  in the engine; the exception handlers in `main.py` map them to `4xx`
  `ErrorResponse` bodies. Do not build HTTP responses inside the engine.
- **Decimal only:** construct operands as `Decimal(lexeme_string)`, never from
  `float`. All arithmetic runs under the configured `decimal.Context`.
- **Precision policy:** exact/terminating results are returned exactly (trailing
  zeros normalized); non-terminating results round to ≥10 significant digits with
  `ROUND_HALF_EVEN`.
- **Precedence note:** exponentiation is right-associative and binds tighter than
  unary minus, so `-3^2 == -9` and `2^2^3 == 256`. This is intentional and matches
  standard math convention (documented in `parser.py`).
- **Style:** module docstrings that reference the requirement numbers they satisfy,
  `from __future__ import annotations`, `__all__` export lists, frozen dataclasses
  for AST/token models.

## Frontend conventions

- **No client-side arithmetic.** Results and errors only ever come from the backend
  via `api/client.ts`. The reducer and components hold display state only.
- **Strict typing, no `any`.** ESLint enforces `no-explicit-any` over `src/**`.
  Validate untyped API payloads at runtime with the `isSuccess`/`isError` guards in
  `api/types.ts`; treat non-conforming responses as errors.
- **Normalized client result:** `evaluateExpression` returns
  `{ ok: true; result } | { ok: false; error }`. Transport failure yields a
  service-unavailable error, never a local result.
- **Pure reducer:** `calculatorReducer` handles `APPEND_CHAR`, `BACKSPACE`, `RESET`,
  `SUBMIT`, `SET_RESULT`, `SET_ERROR`. Result and error are mutually exclusive
  (setting one clears the other). Keep it side-effect free with an exhaustive
  `assertNever` guard.
- **Hooks take callbacks, not dispatch.** `useKeyboard` and `useEvaluator` accept
  caller callbacks and use a ref to hold the latest callbacks (stable listeners,
  no stale closures). The `Calculator` container wires them to reducer dispatches.
- **Input parity:** the on-screen keypad and physical keyboard drive the same
  reducer actions.
- **Accessibility is part of "done":** every control has a function-describing
  `aria-label` matching its visible label; displays use `aria-live` (`polite` for
  expression/result, `assertive` for errors); focus and pressed states stay
  visible; contrast ratios are met (colors defined as tokens in `theme.css` with
  ratios noted in comments).
- **CSS structure:** grid/layout structure per component (e.g. `Keypad.css`),
  color tokens in `styles/theme.css`, page layout + responsive breakpoints in
  `styles/global.css` (imported once in `main.tsx`). Keypad order is
  7-8-9 / 4-5-6 / 1-2-3 with 0 below; operators in a dedicated region.

## API contract

`POST /api/v1/evaluate`

- Request: `{ "expression": string }` (1–256 chars)
- Success: `200` `{ "result": string }` — result is a **string** to preserve exact
  decimal precision through JSON (avoid number coercion).
- Error: `4xx` `{ "error": string }` — descriptive message.
- The two shapes are mutually exclusive; keep the TypeScript interfaces in
  `api/types.ts` in sync with the Pydantic schemas in `api/schemas.py`.

## Testing conventions

- Backend property tests use Hypothesis (≥100 examples), tagged
  `# Feature: web-calculator, Property N: ...`, cross-checked against an
  independent reference oracle in `tests/properties/strategies.py`.
- Frontend tests use Vitest + React Testing Library with network mocked.
- Full WCAG conformance requires manual assistive-technology testing beyond the
  automated contrast checks.
