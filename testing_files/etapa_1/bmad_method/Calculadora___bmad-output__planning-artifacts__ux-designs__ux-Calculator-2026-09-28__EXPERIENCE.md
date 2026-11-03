---
title: Basic Web Calculator Experience Spec
status: draft
sources:
  - {planning_artifacts}/prds/prd-Calculator-2026-09-28/prd.md
created: 2026-09-28
updated: 2026-09-28
---

# EXPERIENCE.md: Basic Web Calculator Experience Spec

This document details the behavioral patterns, state models, interaction mechanics, accessibility criteria, and core user flows for the Basic Web Calculator. It defines *how the application works* and references visual tokens established in `DESIGN.md` (via `{colors.light.*}` / `{colors.dark.*}` etc. syntax).

---

## 1. Foundation

The Basic Web Calculator is a single-page, single-surface responsive web application designed for desktop, tablet, and mobile browsers.
- **UI System:** Vanilla CSS / HTML5 with React and TypeScript.
- **Visual Baseline:** Standard physical-inspired calculator layout defined in `DESIGN.md`.
- **Theme Support:** Standard system preference media queries (`@media (prefers-color-scheme: dark)`) are honored to transition between `{colors.light}` and `{colors.dark}` styles automatically without layout shifts.

---

## 2. Information Architecture

The application is unified on a single high-signal layout surface, avoiding multi-level navigation drawers, settings tabs, or pop-over menus in v1.

```
+───────────────────────────────────────────────────+
│                                                   │
│   Calculator Display Region                       │
│   +───────────────────────────────────────────+   │
│   │  [Faded History Display Slot]             │   │
│   │  [Primary Display - Active Input]         │   │
│   │  [Result Display - Live/Final Output]     │   │
│   +───────────────────────────────────────────+   │
│                                                   │
│   Numpad Button Grid (CSS Grid)                   │
│   +───────────+───────────+───────────+───────+   │
│   │     (     │     )     │ Backspace │  AC   │   │
│   +───────────+───────────+───────────+───────+   │
│   │     7     │     8     │     9     │   /   │   │
│   +───────────+───────────+───────────+───────+   │
│   │     4     │     5     │     6     │   *   │   │
│   +───────────+───────────+───────────+───────+   │
│   │     1     │     2     │     3     │   -   │   │
│   +───────────+───────────+───────────+───────+   │
│   │     0     │     .     │     =     │   +   │   │
│   +───────────+───────────+───────────+───────+   │
│                                                   │
+───────────────────────────────────────────────────+
```

### Display Content Slots
1. **Faded History Display Slot:** Shows the preceding expression and its completed result (e.g., `12.5 + 3 = 15.5`) in small `{typography.size-history}` muted text.
2. **Primary Display (Active Input):** Shows the current active expression string being constructed by the user, left-aligned or right-aligned (standard physical desktop alignment is right-aligned). Characters adapt gracefully as tokens are appended.
3. **Result Display (Output):** Shows live, low-contrast preview calculations or finalized, high-contrast results.

---

## 3. Voice and Tone

Microcopy for system prompts, error alerts, and interactive attributes is direct, professional, and completely free of conversational fluff, emojis, or exclamation points.

| Scenario | Preferred Microcopy (Do) | Discouraged Microcopy (Don't) |
| :--- | :--- | :--- |
| Division by zero | `Error: Division by zero` | `Oops! You can't divide by zero!` |
| Unbalanced brackets | `Error: Unbalanced parentheses` | `Check your brackets!` |
| Syntax/Operator error | `Error: Invalid operator sequence` | `Whoops, syntax error there.` |
| Loading live preview | (Keep empty or render subtle skeleton) | `Evaluating...` |
| Screen Reader reset | `Calculator cleared.` | `Reset completed.` |

---

## 4. Component Patterns

All interactive elements have specific behavioral expectations:

| Component | UI Context | Behavioral Rules |
| :--- | :--- | :--- |
| **Grid Button** | Button Grid | • Active hover gains subtle lift and shadow shift (see `DESIGN.md.Elevation`).<br>• Clicking triggers physical depress scale scaling to `0.97` with `0.1s` transition.<br>• Touch screen press triggers immediate tactile focus outline ring matching `{colors.*.btn-focus-ring}`. |
| **AC Button** | Grid Button | • Single click clears the current input and result (resets to default display state).<br>• If error state is active, clicking `AC` clears the error immediately. |
| **Backspace** | Grid Button | • Tapping deletes the trailing single character of the active expression.<br>• Long-pressing has no complex custom macro triggers (standard deletion of characters continues one-by-one). |
| **Display Recess**| Screen Display | • Acts as the visual target. Never accepts direct mouse typing/focus clicks (focus must remain bound to the core calculator container). |

---

## 5. State Patterns

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

### 5.1 Idle State
* **Displays:** Primary Display shows `0`. Result Display is empty. History Slot is empty.
* **Keyboard Focus:** Primary calculator container is ready to intercept keystrokes.

### 5.2 Active Input State
* **Displays:** Primary Display shows the constructed expression string character-by-character.
* **Behaviors:** Each keypress (operand or operator) appends a token. The caret cursor is hidden to match physical LCD screens.

### 5.3 Live Preview State
* **Triggers:** Entered string is mathematically complete but has not been finalized with `=` or `Enter`.
* **Displays:** Result Display dynamically shows the temporary calculated value using muted `{colors.*.text-result-preview}` color.
* **Engine Connection:** Live calculations are processed by querying the backend REST API via a debounced (`300ms`) request to prevent network spam.

### 5.4 Evaluated State
* **Triggers:** User clicks `=` or presses `Enter`.
* **Displays:** 
  - The evaluated expression is pushed to the History Slot.
  - The Result Display shows the exact evaluation result in bold `{colors.*.text-result-final}` color.
* **Operand Chaining:** Subsequent operator keypresses (e.g. `+`, `*`) automatically carry over this evaluated result as the starting operand of the next active expression.

### 5.5 Error State
* **Triggers:** The backend AST parser encounters a syntactic or mathematical error (e.g., division by zero).
* **Displays:**
  - Result Display turns `{colors.*.text-error}` color, showing the precise error message (e.g. `Error: Division by zero`).
  - Active expression remains in the Primary Display to allow editing.
* **Behaviors:** The `=` button is disabled. Clicking any number key clears the active input and restarts typing. Clicking `Backspace` or `AC` clears the error and restores the prior input state.

---

## 6. Interaction Primitives

* **Focus Trapping:** When the web page loads, keyboard focus is bound to the calculator container. Clicking outside does not release focus; clicking anywhere on the page returns focus to the calculator, allowing keyboard entry immediately.
* **Numpad Interception:** Global window event listeners intercept numeric keypad inputs and block default browser shortcuts that conflict with calculator controls:
  - `Escape` is intercepted and mapped to `AC`.
  - `Backspace` is intercepted and deletes the trailing character.
  - `Enter` is intercepted and triggers evaluation.
  - `/` is intercepted and blocks standard browser quick-find triggers in browsers like Firefox.

---

## 7. Accessibility Floor

The Basic Web Calculator must maintain standard AA rating accessibility compliance, supporting screen reader layouts and keyboard-only operation out of the box.

* **Contrast Ratios:** Text on button bases and displays must maintain a minimum contrast ratio of 4.5:1 against their backgrounds (complies with WCAG 2.1 AA).
* **Button Labeling:** Every interactive grid element has an explicit, non-visual `aria-label`:
  - Number keys: `aria-label="Number 5"`, `aria-label="Decimal point"`.
  - Operator keys: `aria-label="Add"`, `aria-label="Subtract"`, `aria-label="Multiply"`, `aria-label="Divide"`.
  - Utility keys: `aria-label="Open parenthesis"`, `aria-label="Close parenthesis"`, `aria-label="Delete last character"`, `aria-label="Clear all"`.
  - Equals key: `aria-label="Calculate result"`.
* **Live Regions:** The screen display container is marked with `aria-live="polite"` and `role="region"`. When an evaluation is triggered, the screen reader announces: `"Result: {evaluated_result}"`. If an error occurs, it announces: `"Error: {error_detail}"`.
* **Focus Traversal:** Tab index traversal of the buttons is disabled (`tabIndex="-1"`) to prevent users from tab-navigating through the grid. The entire keyboard navigation is bound to direct global keystrokes.

---

## 8. Key Flows

### Flow 1 — Daily Grocery Splitting (Elena, mobile screen)
1. Elena opens her mobile browser to the calculator URL.
2. The page loads and centers the calculator container. Focus is immediately bound.
3. Elena taps the on-screen brackets, digits, and operator buttons: `(`, `4`, `5`, `.`, `5`, `0`, `+`, `1`, `2`, `.`, `8`, `0`, `+`, `1`, `1`, `5`, `)`, `/`, `3`.
4. As she types, the display updates, and a grayed-out live preview (`57.7666666667`) is displayed in the Result Display.
5. Elena taps `=`.
6. The calculator sends a payload to `/api/v1/evaluate`, which returns the exact evaluation.
7. **Climax:** The Result Display animates to bold blue `{colors.light.text-result-final}`, and the screen reader announces `"Result: 57.7666666667"`.

### Flow 2 — High-Speed Invoice Reconciliation (Marcus, desktop numpad)
1. Marcus launches the calculator tab on his desktop computer.
2. He uses his desktop numeric keyboard exclusively to type `150.75 + 325.20 * 1.15` and presses `Enter`.
3. The on-screen keys hover and trigger click depress scales rapidly, mirroring his physical entries.
4. **Climax:** The calculator performs the exact calculation (evaluating multiplication first, then addition, maintaining exact high-precision decimal representation).
5. The result `524.73` is displayed in bold blue `{colors.light.text-result-final}` instantly.
6. Marcus presses `Escape` to clear, then types the next invoice expression.
