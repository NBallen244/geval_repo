---
title: Scientific Web Calculator Visual Identity
status: active
created: 2026-09-28
updated: 2026-10-23
colors:
  light:
    bg-app: "#F8F9FA"
    bg-frame: "#F1F3F4"
    bg-display: "#E8EAED"
    text-primary: "#202124"
    text-result-preview: "#5F6368"
    text-result-final: "#1A73E8"
    text-error: "#EA4335"
    btn-operand-bg: "#FFFFFF"
    btn-operand-text: "#3C4043"
    btn-operator-bg: "#F1F3F4"
    btn-operator-text: "#1A73E8"
    btn-command-bg: "#DADCE0"
    btn-command-text: "#3C4043"
    btn-equals-bg: "#1A73E8"
    btn-equals-text: "#FFFFFF"
    btn-focus-ring: "#1A73E8"
    badge-memory-bg: "#FFF2CC"
    badge-memory-text: "#B45F06"
    badge-angle-bg: "#E2F0D9"
    badge-angle-text: "#385723"
  dark:
    bg-app: "#202124"
    bg-frame: "#303134"
    bg-display: "#202124"
    text-primary: "#E8EAED"
    text-result-preview: "#9AA0A6"
    text-result-final: "#8AB4F8"
    text-error: "#F28B82"
    btn-operand-bg: "#3C4043"
    btn-operand-text: "#E8EAED"
    btn-operator-bg: "#303134"
    btn-operator-text: "#8AB4F8"
    btn-command-bg: "#4A4D51"
    btn-command-text: "#E8EAED"
    btn-equals-bg: "#8AB4F8"
    btn-equals-text: "#202124"
    btn-focus-ring: "#8AB4F8"
    badge-memory-bg: "#4A3B1B"
    badge-memory-text: "#F1C232"
    badge-angle-bg: "#2A3A1B"
    badge-angle-text: "#93C47D"
typography:
  font-family-display: "Courier New, Menlo, SF Mono, Consolas, monospace"
  font-family-ui: "Inter, system-ui, -apple-system, sans-serif"
  size-history: "14px"
  size-display-input: "28px"
  size-display-result: "40px"
rounded:
  frame: "16px"
  display: "12px"
  button: "8px"
  badge: "4px"
spacing:
  padding-outer: "24px"
  padding-inner: "16px"
  display-to-grid: "20px"
  grid-gap: "12px"
---

# DESIGN.md: Scientific Web Calculator Visual Identity

This document defines the visual design system, aesthetic identity, design tokens, and components for the Scientific Web Calculator. It guarantees high accessibility, modern physical desktop calculator realism, and responsive layouts.

---

## 1. Brand & Style

The Scientific Web Calculator balances professional precision with contemporary minimalism. Rather than feeling flat and generic, it draws inspiration from classic, tactile, high-end hardware instruments (Braun designs and physical scientific instruments) featuring:
- **Tactile Realism:** Buttons animate dynamically on hover, focus, and active clicks, scaling down to `0.97` to emulate physical plunge travel.
- **Visual Depth:** Recessed screen bevels use inset box shadows to separate the digital readouts cleanly.
- **Indicator Badges:** Smooth indicator badges provide high-contrast tracking of system states (Radian vs. Degrees modes and Memory Register states).
- **Collapsible Drawer Architecture:** A responsive sliding history side panel enables review of calculations.

---

## 2. Colors & Typography

### 2.1 Display Indicators Badges
- **Memory Active Badge ("M"):**
  * Light Mode: Yellow fill (`#FFF2CC`) / Amber text (`#B45F06`).
  * Dark Mode: Amber fill (`#4A3B1B`) / Yellow text (`#F1C232`).
- **Angle Unit Badge ("RAD" / "DEG"):**
  * Light Mode: Soft green fill (`#E2F0D9`) / Deep green text (`#385723`).
  * Dark Mode: Forest green fill (`#2A3A1B`) / Light green text (`#93C47D`).

### 2.2 Typographic Hierarchy
* **Faded History Display Line:** `14px` (`size-history`), normal weight.
* **Active Expression Input:** `28px` (`size-display-input`), medium weight.
* **Evaluation Output:** `40px` (`size-display-result`), bold weight.
* Display slots use strict monospace families to completely prevent character-width jittering.

---

## 3. Responsive Layout & Spacing

To preserve the minimum touch target clearance of **$48\text{px}$** (WCAG 2.1 AA) and prevent mobile screen overcrowding, the button grid employs a dual-keypad collapsible grid system:

1. **Standard Arithmetic Grid:** Renders default operators, digits, decimals, Backspace, AC, and equals keys.
2. **Scientific Grid Expansion:** Conditional keypad slide-out containing:
   - Angle Units Toggles (`RAD/DEG`).
   - Memory Register Controls (`MC`, `MR`, `M+`, `M-`).
   - Trigonometric & Logarithmic functions (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sqrt`, `ln`, `log`).
   - Exponential operations (`xʸ`, `x²`, `10ˣ`, `^`) and Constants (`π`, `e`).
3. **Viewport Adaptability:**
   - On wide viewports ($>768\text{px}$): Calculator frame expands and slides beside the History sidebar panel gracefully.
   - On mobile viewports ($<480\text{px}$): Scientific panel stacks vertically; spacing shrinks to `8px` grid gaps to prevent overflow while keeping the targets $\ge 48\text{px}$.

---

## 4. Elevation & Depth

*   **Bezel Screen:** `inset 0px 2px 4px rgba(0,0,0,0.1)` gives a tactile recessed depth.
*   **Tactile Keycaps:** Flat boundaries with minimal hover lift shadows (`0px 1px 3px rgba(0,0,0,0.1)`). Scales to `0.97` when active.
*   **History Sidebar:** `box-shadow: -2px 0px 8px rgba(0,0,0,0.05)` indicates sliding overlap layering.
