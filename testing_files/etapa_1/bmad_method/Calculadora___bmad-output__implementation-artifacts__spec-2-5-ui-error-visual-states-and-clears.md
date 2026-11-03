---
title: UI Error Visual States & Clears
type: feature
created: 2026-09-28
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Standard calculators crash or display dry, unhelpful raw runtime messages when encountering mathematical exceptions (e.g., division by zero), and do not provide clear visual cues of system failure states.

**Approach:** Develop an explicit, high-contrast visual error state. When a mathematical or parsing exception is returned by the backend REST API, the Result Display must immediately turn high-contrast red, the on-screen `=` button must be disabled, and any numeric entry must clear the error and restart typing fresh.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Connected custom exception details returned by `/api/v1/evaluate` to state managers inside our UI. Rendered a specific `.error` red/orange text visual state when an error occurs, and disabled the `=` equals button. Pressing `AC`, `Backspace`, or typing any number automatically clears the error state and restores active typing safely.
- **Files Touched/Created:**
  - `frontend/src/hooks/useEvaluate.ts` - Math evaluation error catch handles and clear controllers.
  - `frontend/src/components/DisplayPanel.tsx` - Transitions typography to red/orange alert color styles.
  - `frontend/src/components/ButtonGrid.tsx` - Disables the `=` equals button.
  - `frontend/src/styles/index.css` - Custom color definitions for `--text-error`.
