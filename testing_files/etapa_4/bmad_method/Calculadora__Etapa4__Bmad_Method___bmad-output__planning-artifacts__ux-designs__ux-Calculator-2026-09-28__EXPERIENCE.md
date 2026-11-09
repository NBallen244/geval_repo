---
title: Scientific Web Calculator Experience Spec
status: active
sources:
  - {planning_artifacts}/prds/prd-Calculator-2026-09-28/prd.md
created: 2026-09-28
updated: 2026-10-27
---

# EXPERIENCE.md: Scientific Web Calculator Experience Spec

This document details the behavioral patterns, state models, interaction mechanics, accessibility criteria, and core user flows for the Scientific Web Calculator. It defines *how the application works* and references visual tokens established in `DESIGN.md`.

---

## 1. Foundation
The Scientific Web Calculator is a single-page responsive web application designed for mobile, tablet, and desktop browsers.
* **Theme Support:** Standard system preferences media queries are honored to transition between `{colors.light}` and `{colors.dark}` styles automatically without layout shifts.

---

## 2. Information Architecture

The application is laid out on a unified surface containing:
* **Interactive Toggles Header:** Header row toggling standard vs. scientific keypad display, layout modes (Standard vs RPN), and the Session calculation history drawer.
* **Bezel Display Screen:** Multi-line inset display showing memory indicator, angle unit mode indicator, active badges ("RPN"), faded previous calculations (or RPN registers T, Z, Y, X), active inputs, and calculated output lines.
* **Double-Keypad Grid:** Standard numeric keypad paired with an expandable scientific controls grid. In RPN Mode, brackets are disabled and the `=` key transforms into a dedicated `ENTER` key.
* **Calculation History Sidebar Panel:** Sliding drawer containing calculation history (which displays space-separated postfix tokens for RPN calculations) and action buttons to restore stack configurations.

---

## 3. State Patterns (Standard Mode)

```
                 [ IDLE STATE ]
                        │
                        │ User inputs Character / Numpad click
                        ▼
             [ ACTIVE INPUT STATE ]
                        │
                        ├───► (Input forms valid sub-expression)
                        │           │
                        │           ▼
                        │    [ LIVE PREVIEW STATE ]
                        │           │
                        ├───► User presses Enter / Click "="
                        │           │
                        │           ▼
                        │    [ EVALUATED STATE ]
                        │
                        └─► (AST engine throws Syntax / Math Exception)
                                    │
                                    ▼
                             [ ERROR STATE ]
```

### 3.1 Idle State
- Primary display shows `0`. Result Display is empty. History Slot is empty.

### 3.2 Active Input State
- Primary display shows active string. Characters are appended one-by-one.

### 3.3 Live Preview State
- Debounced (`300ms`) live REST API calculations are requested to preview sub-totals in result line using muted `{colors.*.text-result-preview}` color. Preview requests are strictly blocked if parentheses are unbalanced or end with a mathematical operator.

### 3.4 Evaluated State
- Triggered by clicking `=` or physical `Enter`. Evaluated result replaces active input in Primary Display, Result display turns bold `{colors.*.text-result-final}`, and calculations push to history caches. 
- **Typing Resumption Guard:** Resuming typing with numbers/functions starts fresh; starting with arithmetic operators (+, -, *, /) automatically carries over the evaluated result to chain the calculation.
- **State Lock Guard:** Once evaluated, the debounced preview `useEffect` is bypassed when `expression === result` to prevent overriding the finalized visual state.

### 3.5 Error State
- Triggers when math parser throws exceptions (e.g. division by zero, unbalanced parentheses). Result Display turns red/orange `{colors.*.text-error}`, showing standard messages prefixed with `Error: `. The `=` equals key is disabled. Backspace, AC, or typing any number clears the error instantly.

---

## 4. State Patterns (RPN Mode)

In **RPN Mode**, the state is governed by a multi-level operand stack and an active input buffer (`expression`).

### 4.1 Operand Typing & Buffering
- Typing digits or decimal points appends characters directly to the active input buffer (`expression`).

### 4.2 Stack Push (ENTER Action)
- Pressing `ENTER` (or keyboard `Enter`) pushes the active input onto the operand stack (register X), shifting previous registers up ($X \rightarrow Y \rightarrow Z \rightarrow T$).
- If the active input is empty and the stack has elements, pressing `ENTER` duplicates the top stack element ($X \rightarrow Y$, pushing others up).

### 4.3 Operator & Scientific Function Execution
- Pressing an operator key (`+`, `-`, `*`, `/`) or scientific key (`sin`, `sqrt`, etc.) immediately executes the operation:
  1. If there is an active input in the buffer, it is pushed onto the stack first.
  2. The stack and the operator token are sent to the backend endpoint `/api/v1/evaluate` with formatting system `"postfix"`.
  3. The backend pops the necessary operand(s), calculates, and returns the updated stack.
  4. The frontend stores the updated stack, updates the display result, and resets the input buffer.

### 4.4 Backspacing and Stack Dropping
- If the active input buffer is non-empty, backspacing deletes characters one by one.
- If the active input buffer is empty, backspacing drops the top of the stack (register X), pulling lower registers down.

---

## 5. Interaction Primitives

* **Focus Trapping:** Clicks anywhere on the workspace focus back onto the calculator body. Keyboard navigation is active on load.
* **Physical Numpad Interception:** Global window keystroke captures capture standard digits, decimals, operators, Escape (as AC), Enter (as equals/push), and block Firefox "/" quick-search pop-ups.
* **Smart Backspacing:** Backspace deletes single characters; if trailing characters match scientific keywords (such as `sin(`, `acos(`, `log10(`), backspace deletes the full keyword cleanly in one shot.

---

## 6. Accessibility (a11y) Floor

* **Contrast Ratios:** Exceeds 4.5:1 standard contrast ratio thresholds.
* **Descriptive Labels:** Grid buttons utilize non-visual `aria-label` attributes.
* **No Tab Grid Leaks:** Keypad buttons strictly feature `tabIndex="-1"`, trapping focus to the main container.
* **Polite Announcements:** The display screen features `role="region"` and `aria-live="polite"` live announcements speaking changes aloud dynamically:
  - Speaking mode units changes (Radian/Degrees), active memory registers, and active modes (Standard vs RPN).
  - In RPN mode, screen readers announce the full stack registers $T, Z, Y, X$, current buffer inputs, and errors.
  - In Standard mode, screen readers speak standard expressions and results.
