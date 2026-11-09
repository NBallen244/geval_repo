---
title: Global Keyboard Event Capture & Numpad Interception
type: feature
created: 2026-09-28
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Users cannot operate standard web calculators easily with physical keyboard numeric pads because key presses trigger page scrolls, backspace maps to browser page returns, and operators conflict with standard browser hotkeys (such as Firefox's quick search `/`).

**Approach:** Develop a global window event listener hook trapping keydowns. Intercept and map physical keys (numbers, decimals, operators, brackets, Backspace, Escape, and Enter) to on-screen button operations while executing browser `preventDefault()` blocks to completely eliminate key conflict issues.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Created a global window-bound keyboard event capture hook (`useKeyboard`). Mapped backspaces to trailing deletion character state flows, Escape to full AC resets, and Enter to final submissions. Blocked Firefox "/" quick-search pop-ups and browser scrollbars perfectly.
- **Files Touched/Created:**
  - `frontend/src/hooks/useKeyboard.ts` - Keyboard event catcher and preventDefault router.
  - `frontend/src/components/CalculatorFrame.tsx` - Focus-focusable application shell binding keyboard triggers.
