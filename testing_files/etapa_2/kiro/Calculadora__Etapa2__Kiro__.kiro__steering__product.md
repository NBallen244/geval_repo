# Product

## What this is

A modern, daily-use, responsive **web calculator**. Users type or click a chained
arithmetic expression (e.g. `12.5 + 3 * (4 - 1.5) / 2`) and get an exact result.

## Core promises

- **PEMDAS order of operations** — parentheses, exponents, multiplication/division,
  addition/subtraction, evaluated in standard precedence.
- **Exact decimal precision** — no binary floating-point error. `0.1 + 0.2`
  evaluates to exactly `0.3`. Non-terminating results (e.g. `1/3`) are rounded to
  at least 10 significant digits (round-half-even).
- **Descriptive errors** — division by zero, invalid operator sequences, unclosed
  parentheses, invalid characters, and empty input each return a clear message.
- **Accessible and responsive** — full keyboard control, screen-reader support
  (ARIA labels + live regions), WCAG-checked contrast, and a layout that adapts
  from mobile to desktop without overflow or clipping.

## Shape of the system

Two independently testable halves joined by a single typed REST contract:

- A **backend** that owns all arithmetic (a stateless math oracle).
- A **frontend** that owns all UI and input state and performs **no** arithmetic
  locally — every result comes from the backend.

## Non-negotiable rules

- Never compute arithmetic on the frontend. The backend is the single source of
  computed truth.
- Never use raw `float` in calculation paths. Use exact decimal arithmetic.
- Keep the success/error API contract mutually exclusive: a response carries a
  result or an error, never both.

The full product intent lives in `docs/SEED.md`. The formal requirements, design,
and task history live under `.kiro/specs/web-calculator/`.
