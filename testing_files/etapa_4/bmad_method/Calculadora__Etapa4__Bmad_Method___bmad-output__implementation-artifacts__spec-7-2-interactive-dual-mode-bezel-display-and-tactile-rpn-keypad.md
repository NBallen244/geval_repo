---
title: Interactive Dual-Mode Bezel Display and Tactile RPN Keypad
type: feature
created: 2026-10-27
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Vision-impaired and power users operating in RPN mode need visual, tactile, and spoken representation of multi-level stack register changes ($T, Z, Y, X$) and keyboard shortcuts, without encountering focus-trapping defects or state synchronization crashes.

**Approach:** Develop an interactive Dual-Mode layout on the React client. When toggled to RPN Mode, render visual multi-register displays ($T, Z, Y, X$), transform the `=` key into a dedicated `ENTER` key mapping, disable brackets, and configure polite ARIA screen readers to speak stack levels, current inputs, and active modes dynamically.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:**
  - Introduced `calcMode` state ('standard' | 'rpn') and a `stack` array inside `useEvaluate.ts`.
  - Configured RPN-mode typing: digit entries buffer characters in `expression`, `ENTER` pushes values (or duplicates the top stack value), and backspace drops elements from the stack when the typing buffer is empty.
  - Programmed operators and scientific controls to trigger instant, stateless backend postfix REST executions when clicked, clearing buffers and pushing outcomes to registers.
  - Refactored `DisplayPanel.tsx` to render levels T, Z, Y, and X using stable CSS grids and custom monospace font readouts to prevent character jittering.
  - Programmed a hidden polite screen reader live region spoken text constructor that speaks memory states, active angle modes, RPN stack layers, current inputs, and errors dynamically (WCAG 2.1 AA).
- **Files Touched/Created:**
  - `frontend/src/hooks/useEvaluate.ts` - Dual-mode controller hook.
  - `frontend/src/components/DisplayPanel.tsx` - Bezel visual registers stack and polite ARIA speakers.
  - `frontend/src/components/ButtonGrid.tsx` - Keyboard ENTER toggle and disabled brackets.
  - `frontend/src/components/CalculatorFrame.tsx` - RPN layout mode header toggle buttons.
  - `frontend/src/styles/index.css` - Custom styles for RPN badges and stack alignments.

## Review Triage Log

| Finding | Verdict | Evidence |
| :--- | :--- | :--- |
| **Stack Clearing on Backspace** | `high` | **Patched!** Refactored backspace hook handler to prevent clearing the entire stack in RPN mode if the display state is `'evaluated'`. |
| **Silent RPN State Changes** | `false` | Screen readers speak all active registers $T, Z, Y, X$ during display update cycles. |
| **Focus-Trapping Keyboards** | `false` | Standardised keyboard navigation via global captures, maintaining zero tabIndex grid leaks. |
