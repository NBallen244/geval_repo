---
title: Interactive Dual Screen Displays & State Controllers
type: feature
created: 2026-09-28
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Standard calculators perform heavy, laggy, or visually shifting layout refreshes during typing, and lack live feedback on mathematically valid sub-expressions as the user types.

**Approach:** Develop a dual-line screen display panel housing three visual segments: small history slots, large active input strings, and live preview calculated outputs. Manage state transitions character-by-character, and invoke a debounced (`300ms`) live REST API calculator evaluation call only when parentheses counts are mathematically balanced.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Created a dedicated `useEvaluate` hook managing expression input state transitions (Idle, Active, Preview, Evaluated, Error). Implemented a `300ms` debounce timer and a parentheses bracket-balance matcher, completely avoiding invalid network query spam. Set a stable monospace font family across displays to guarantee character alignment and prevent layout drifting.
- **Files Touched/Created:**
  - `frontend/src/types/api.ts` - REST payload TypeScript schemas.
  - `frontend/src/hooks/useEvaluate.ts` - Debounced live preview API coordinator.
  - `frontend/src/components/DisplayPanel.tsx` - Inset bezel screen display housing three distinct content lines.
