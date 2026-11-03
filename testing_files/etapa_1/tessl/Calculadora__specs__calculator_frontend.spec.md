---
name: Calculator Frontend Client
description: React-TypeScript daily-use responsive desktop-style calculator UI with Tailwind CSS and full keyboard support
targets:
  - ../frontend/src/App.tsx
  - ../frontend/src/components/Calculator.tsx
---

# Calculator Frontend Client

## User Interface & Responsive Design

- The UI must render a daily-use, desktop-style calculator mimicking a physical device.
- It must feature a high-contrast display with:
  - An expression view area showing the full sequence of inputs.
  - A result view area displaying the current or final calculated result.
- The layout must use Tailwind CSS and be fully responsive (mobile, tablet, and desktop viewports) with no horizontal scroll or clipped buttons.
- A virtual button pad must contain numbers `0-9`, standard operator buttons (`+`, `-`, `*`, `/`), parenthesis buttons (`(`, `)`), a decimal point button (`.`), a backspace button (`⌫`), a reset button (`C`), and an evaluation button (`=`).

`[@test] ../frontend/src/App.test.tsx`

## Keyboard Integration & Accessibility

- Keypress events must map to calculator actions:
  - Number keys `0`-`9` input digits.
  - Operators `+`, `-`, `*`, `/` and parenthesis `(`, `)` input operators.
  - Dot `.` inputs a decimal point.
  - Enter or `=` evaluates the current expression.
  - Backspace deletes the last character.
  - Escape resets the calculator.
- The UI must employ clear `aria-label` attributes on interactive buttons.
- The display areas must use `aria-live` or appropriate role attributes for screen reader accessibility.

`[@test] ../frontend/src/App.test.tsx`

## API Integration & State Management

- Inputting digits and operators updates the expression state locally.
- Clicking `=` or pressing `Enter` must trigger a `POST /api/v1/evaluate` request to the backend.
- The UI must display a loading or evaluating state during API requests.
- Successful responses must display the exact numeric result returned by the backend.
- Erroneous responses (e.g. invalid syntax, division by zero) must display a clear, user-friendly error message on the display instead of breaking the app.

`[@test] ../frontend/src/App.test.tsx`
