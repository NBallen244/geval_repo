---
title: Keyboard Binding Expansion and a11y ARIA Announcements
type: feature
created: 2026-10-20
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Vision-impaired users and keyboard-only power users need to navigate the expanded scientific functions, toggle modes, and memory registers seamlessly and audibly, without experiencing focus-trapping issues or missing indicator updates.

**Approach:** Map physical numpads and keys (like `^` for power, `e` for e, `p` for pi) globally. Add comprehensive `aria-label` tags to all newly added scientific and memory buttons. Update the hidden screen reader live regions (`aria-live="polite"`) to read out memory register additions, subtractions, and active angle unit mode changes.

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Expanded `useKeyboard.ts` global captures. Added descriptive spoken string construction inside `DisplayPanel.tsx`'s live polite announcer:
  - Spoke active memory values whenever `memory !== '0'`.
  - Spoke active angle mode unit system (Radian vs Degrees).
- **Tab Focus Avoidance:** Enforced strict `tabIndex={-1}` on newly created scientific and memory keypad buttons to block browser-native Tab focus leakage, ensuring focus remains bound to global intercepts.
- **Files Touched/Created:**
  - `frontend/src/hooks/useKeyboard.ts` - Expanded key intercepts.
  - `frontend/src/components/DisplayPanel.tsx` - Extended spoken live text constructor.
  - `frontend/src/components/ButtonGrid.tsx` - Added explicit descriptive `aria-label`s to all new keys.

## Review Triage Log

| Finding | Verdict | Evidence |
| :--- | :--- | :--- |
| **Silent Memory Indicator** | `false` | **Patched!** Screen readers automatically speak the memory value (e.g., "Memory stored: 45.") during display update cycles. |
| **Rogue Tab Traversal** | `false` | Checked all scientific buttons; they strictly feature `tabIndex={-1}` to maintain focus trapping. |
