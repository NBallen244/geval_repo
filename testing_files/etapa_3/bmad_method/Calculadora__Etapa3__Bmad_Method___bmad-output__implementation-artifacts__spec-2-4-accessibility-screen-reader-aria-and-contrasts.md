---
title: Accessibility Screen Reader ARIA & Contrasts
type: feature
created: 2026-09-28
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Standard web calculators are completely inaccessible for blind, motor-impaired, or keyboard-only users. On-screen button grid clicks lack descriptive voice readers, tab traversal leaks out to browser addresses, and display updates are not spoken.

**Approach:** Implement strict WCAG 2.1 AA accessibility standards on all custom elements. Embed descriptive `aria-label` fields on every grid button, disable standard browser tab traversal on the buttons (`tabIndex="-1"`) to prevent focus leaks, and include polite `aria-live` announcement readers on display states.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Incorporated explicit non-visual accessible labels on all number, operator, and command keys. Blocked button tab-indexing perfectly to lock focus inside window intercepts. Constructed an invisible `sr-only` live screen reader announcer on the display panel utilizing `aria-live="polite"` to dynamically speak final evaluated values (e.g. `"Result: 524.73"`) or active errors.
- **Files Touched/Created:**
  - `frontend/src/components/CalculatorButton.tsx` - Disables tabIndex and embeds descriptive aria labels.
  - `frontend/src/components/DisplayPanel.tsx` - Embeds a polite live screen reader region.
  - `frontend/src/components/ButtonGrid.tsx` - Standardizes aria labels across the 4x5 layout.
