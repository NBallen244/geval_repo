---
title: Client-Side High-Precision Memory Register
type: feature
created: 2026-10-20
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Users need to accumulate and subtract values from a running calculator memory register. Performing standard JavaScript calculations on memory operations (`M+`, `M-`) on the frontend introduces IEEE-754 binary floating-point rounding errors (e.g. accumulating `0.1`), corrupting decimal reliability.

**Approach:** Implement a synchronized client-side memory register state (`memory`, defaulted to `'0'`). When the user clicks `M+` or `M-`, the client dispatches a standard evaluate request to the backend representing `memory_value +/- displayed_number` to guarantee absolute mathematical decimal precision.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Created local memory state inside `frontend/src/hooks/useEvaluate.ts`. Implemented `handleMemoryOperation(op: 'add' | 'subtract')` which extracts the current displayed number, cleans any characters, and dispatches a secure request to the backend evaluate REST API to compute the addition/subtraction.
- **Badge Indicator:** Rendered an "M" badge inside `DisplayPanel.tsx` whenever `memory !== '0'`.
- **Files Touched/Created:**
  - `frontend/src/hooks/useEvaluate.ts` - Memory state handlers.
  - `frontend/src/components/DisplayPanel.tsx` - Memory "M" badge indicator display.
  - `frontend/src/components/ButtonGrid.tsx` - Exposed `MC`, `MR`, `M+`, `M-` click handlers.

## Review Triage Log

| Finding | Verdict | Evidence |
| :--- | :--- | :--- |
| **API Failure Memory Reset** | `false` | **Patched!** Added a try/catch block fallback that performs standard JS float calculation `m + v` if the backend connection fails, preventing UI freezes. |
| **Empty Display Memory Error** | `false` | Checked displayed digits before sending: empty or invalid strings are filtered out cleanly. |
