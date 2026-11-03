---
title: Physical-Style Responsive Calculator Layout & Grid
type: feature
created: 2026-09-28
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Standard web calculators have flat, uninspiring user interfaces and do not scale properly across high-resolution screens or mobile devices, resulting in poor usability and a lack of visual polish.

**Approach:** Develop a responsive, physical-inspired desktop calculator card layout using HTML5/React/Vite. Set up modular grids utilizing clean CSS spacing scales, softened radii matching our DESIGN.md specifications, and support automatic Light/Dark mode transitions via browser system theme preferences (`@media (prefers-color-scheme: dark)`).

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Configured a beautiful 4x5 button layout using a centered grid of custom tactile elements. Adopted exact hex tokens from `DESIGN.md` mapping custom hover, active, and focus styles, including a smooth `scale(0.97)` active press transform representing physical plunger key travel.
- **Files Touched/Created:**
  - `frontend/package.json` - Node dependencies and scripts.
  - `frontend/tsconfig.json` & `frontend/vite.config.ts` - TypeScript compiler and bundler flags.
  - `frontend/index.html` - Base HTML container shell.
  - `frontend/src/main.tsx` - App runtime mounting.
  - `frontend/src/App.tsx` - Centers the calculator card.
  - `frontend/src/styles/index.css` - Responsive layout frames, physical shadow recess depths, and active plunger transition timings.
