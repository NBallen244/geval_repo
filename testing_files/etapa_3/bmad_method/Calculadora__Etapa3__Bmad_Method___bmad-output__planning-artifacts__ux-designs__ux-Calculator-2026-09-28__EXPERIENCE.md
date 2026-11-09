---
title: Scientific Web Calculator Experience Spec
status: active
sources:
  - {planning_artifacts}/prds/prd-Calculator-2026-09-28/prd.md
created: 2026-09-28
updated: 2026-10-23
---

# EXPERIENCE.md: Scientific Web Calculator Experience Spec

This document details the behavioral patterns, state models, interaction mechanics, accessibility criteria, and core user flows for the Scientific Web Calculator. It defines *how the application works* and references visual tokens established in `DESIGN.md`.

---

## 1. Foundation
The Scientific Web Calculator is a single-page responsive web application designed for mobile, tablet, and desktop browsers.
* **Theme Support:** Standard system preferences media queries (`@media (prefers-color-scheme: dark)`) are honored to transition between `{colors.light}` and `{colors.dark}` styles automatically without layout shifts.

---

## 2. Information Architecture

The application is laid out on a unified surface containing:
* **Interactive Toggles Header:** Header row toggling standard vs. scientific keypad display and the Session calculation history drawer.
* **Bezel Display Screen:** Multi-line inset display showing memory indicator, angle unit mode indicator, faded previous calculations, active inputs, and calculated output lines.
* **Double-Keypad Grid:** Standard numeric keypad paired with an expandable scientific controls grid.
* **Calculation History Sidebar Panel:** Sliding drawer appearing from the side (desktop) or overlaying the main frame (mobile) containing calculation history and action buttons.

```
+───────────────────────────────────────────────────+
│                                                   │
│   [Scientific Toggle]         [History Toggle]    │
│                                                   │
│   Calculator Display Region                       │
│   +───────────────────────────────────────────+   │
│   │ [M] [RAD]                                 │   │
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

---

## 3. State Patterns

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
- Primary display shows active string. CARE CUT is hidden. Characters are appended one-by-one.

### 3.3 Live Preview State
- debounced (`300ms`) live REST API calculations are requested to preview sub-totals in result line using muted `{colors.*.text-result-preview}` color. Preview requests are strictly blocked if parentheses are unbalanced or end with a mathematical operator.

### 3.4 Evaluated State
- Triggered by clicking `=` or physical `Enter`. Evaluated result replaces active input in Primary Display, Result display turns bold `{colors.*.text-result-final}`, and calculations push to history caches. 
- **Typing Resumption Guard:** Resuming typing with numbers/functions starts fresh; starting with arithmetic operators (+, -, *, /) automatically carries over the evaluated result to chain the calculation.
- **State Lock Guard:** Once evaluated, the debounced preview `useEffect` is bypassed when `expression === result` to prevent overriding the finalized visual state.

### 3.5 Error State
- Triggers when math parser throws exceptions (e.g. division by zero, modulo zero, negative roots). Result Display turns red/orange `{colors.*.text-error}`, showing standard messages prefixed with `Error: `. The `=` equals key is disabled. Backspace, AC, or typing any number clears the error instantly.

---

## 4. Interaction Primitives

* **Focus Trapping:** Clicks anywhere on the workspace focus back onto the calculator body. Keyboard navigation is active on load.
* **Physical Numpad Interception:** Global window keystroke captures capture standard digits, decimals, operators, Escape (as AC), Enter (as equals), and block Firefox "/" quick-search pop-ups.
* **Smart Backspacing:** Backspace deletes single characters; if trailing characters match scientific keywords (such as `sin(`, `acos(`, `log10(`), backspace deletes the full keyword cleanly in one shot.

---

## 5. Accessibility (a11y) Floor

* **Contrast Ratios:** Exceeds 4.5:1 standard contrast ratio thresholds.
* **Descriptive Labels:** Grid buttons utilize non-visual `aria-label` attributes.
* **No Tab Grid Leaks:** Keypad buttons strictly feature `tabIndex="-1"`, trapping focus to the main container.
* **Polite Announcements:** The display screen features `role="region"` and `aria-live="polite"` live announcements speaking changes aloud dynamically:
  - Speaking mode units changes (Radian/Degrees) and active memory registers.
  - Speaking evaluated result states (e.g., `"Result: 15"`) or alert messages (e.g., `"Error: Division by zero"`).
