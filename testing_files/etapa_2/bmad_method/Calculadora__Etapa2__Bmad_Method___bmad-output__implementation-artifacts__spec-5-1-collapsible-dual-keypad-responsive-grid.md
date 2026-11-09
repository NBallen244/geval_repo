---
title: Collapsible Dual-Keypad Responsive Grid
type: feature
created: 2026-10-20
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Adding scientific keys doubles the button count. Simply expanding the grid to include everything can overcrowd mobile viewports, clip labels, or violate the WCAG interactive tap target clearance minimum ($48\text{px}$).

**Approach:** Transition the button keypad to a dual-mode layout. Keep standard arithmetic keys in a default Basic grid and render scientific keys in an expandable/collapsible keypad drawer. On wider viewports, display panels can expand side-by-side gracefully using CSS flex-wrap and responsive grid columns.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Managed `showScientific` toggle inside `CalculatorFrame.tsx`. If active, the layout expands to render the `scientific-grid` above the `basic-grid`. Mapped scientific classes cleanly in CSS.
- **Responsive Sizing:** Enabled CSS flex-wrap on `.calculator-layout-wrapper`. On wide desktop screens, the history drawer sits side-by-side beside the calculator. On mobile viewports, the layout collapses vertically and buttons preserve their $48\text{px}$ aspect ratio target boundaries.
- **Files Touched/Created:**
  - `frontend/src/components/CalculatorFrame.tsx` - Toggle buttons and header wrappers.
  - `frontend/src/components/ButtonGrid.tsx` - Conditional rendering of standard vs scientific grids.
  - `frontend/src/styles/index.css` - Grid, flex, toggles, badges, and viewport media styling.

## Review Triage Log

| Finding | Verdict | Evidence |
| :--- | :--- | :--- |
| **Mobile Layout Overcrowding** | `false` | Collapsible panels ensure that buttons remain large ($48\text{px}$ aspect target) on smaller viewports and do not overflow. |
| **Layout Shift Jittering** | `low` | Fixed width grid columns prevent horizontal shifts during toggles or inputs. |
