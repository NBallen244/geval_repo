---
title: Basic Web Calculator Visual Identity
status: draft
created: 2026-09-28
updated: 2026-09-28
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
spacing:
  padding-outer: "24px"
  padding-inner: "16px"
  display-to-grid: "20px"
  grid-gap: "12px"
---

# DESIGN.md: Basic Web Calculator Visual Identity

This document defines the visual design system, aesthetic identity, design tokens, and components for the Basic Web Calculator. It guarantees high accessibility, modern physical desktop calculator realism, and smooth transitions.

---

## 1. Brand & Style

The Basic Web Calculator balances professional precision with contemporary minimalism. Rather than feeling flat and generic, it draws inspiration from classic, tactile, high-end hardware desktop calculators (such as standard physical desktop instruments and Braun designs). It achieves this through discrete visual depths, tactile button travel physical plunge cues, a recessing screen bezel inset, and stable, high-contrast, non-drifting monospace displays.

The aesthetic philosophy centers around **"Absolute Clarity and Ergonomics."**
- **Contrast First:** Colors are optimized to exceed WCAG 2.1 AA standards at all scale steps.
- **Physical Clues:** Subtle, high-performance styling (active button depress states and screen recession shadows) creates tactile realism without using heavy or outdated skeletal skeumorphisms.
- **State Transparency:** Color shifts (e.g., active input vs. final results vs. error warnings) give clear, prompt visual feedback on the state of the system without text-heavy messaging.

---

## 2. Colors

The color palette features dedicated functional scales for Light and Dark modes. Light mode leverages deep, charcoal-like text on crisp white/gray fields, accented with Google Blue; Dark mode leverages high-contrast light-gray operands on slate foundations, accented with pastel blue highlights.

### 2.1 Color Tokens Reference

#### Light Mode Tokens
- **Canvas Base (`bg-app`):** `#F8F9FA` - Soft off-white to prevent glare.
- **Calculator Frame Base (`bg-frame`):** `#F1F3F4` - Smooth structural gray housing the interface.
- **Display Screen Bezel Inset (`bg-display`):** `#E8EAED` - Faded gray mimicking physical LCD screen backing.
- **Active Operand Text (`text-primary`):** `#202124` - Slate black for maximum readability.
- **Result Preview Text (`text-result-preview`):** `#5F6368` - Dimmed slate text indicating live calculations.
- **Final Result Highlight (`text-result-final`):** `#1A73E8` - Saturated blue signaling a finalized mathematical evaluation.
- **Error Banner Text (`text-error`):** `#EA4335` - Saturated red highlighting invalid actions.

#### Dark Mode Tokens
- **Canvas Base (`bg-app`):** `#202124` - Dark charcoal surface.
- **Calculator Frame Base (`bg-frame`):** `#303134` - Elevated charcoal foundation.
- **Display Screen Bezel Inset (`bg-display`):** `#202124` - Flat dark panel housing digital readouts.
- **Active Operand Text (`text-primary`):** `#E8EAED` - Crisp white for sharp legibility.
- **Result Preview Text (`text-result-preview`):** `#9AA0A6` - Muted gray indicating live calculations.
- **Final Result Highlight (`text-result-final`):** `#8AB4F8` - Neon pastel blue signaling a finalized mathematical evaluation.
- **Error Banner Text (`text-error`):** `#F28B82` - Warm pastel red highlighting invalid actions.

### 2.2 Button Color Mapping
To make visual navigation immediate, buttons are categorized into four visual hierarchies:
1. **Operand Buttons (`0-9`, `.`):** Light card fills with high-contrast text. Simple and approachable.
2. **Operator Buttons (`+`, `-`, `*`, `/`):** Medium gray/tinted fills with accented operator symbols.
3. **Command Buttons (`C`/`AC`, `Backspace`, `(`, `)`):** Darker structural fills denoting utility and state-clearing options.
4. **Equals Button (`=`):** Saturated accent color base (`text-result-final`) with inverted high-contrast text. Establishes the visual terminal climax of the interface.

---

## 3. Typography

Display numbers must remain stable under typing to prevent horizontal jitter or layout shifts during calculation. 

- **Display Text Font:** `Courier New`, `Menlo`, `SF Mono`, `Consolas`, or generic `monospace`.
  - Used for history expressions, active inputs, and evaluated results.
  - Guarantees exact character width sizing so that columns and decimals align predictably.
- **UI Interface Font:** `Inter`, `-apple-system`, `system-ui`, or generic `sans-serif`.
  - Used for button labels, clear text, error alerts, and helper text.
  - Ensures clean visual readability for small control strings.

### 3.1 Sizing and Visual Hierarchy
- **Historical Expression Slot:** `14px` (`size-history`), normal weight.
- **Active Expression Input Display:** `28px` (`size-display-input`), medium weight.
- **Evaluation Result Display:** `40px` (`size-display-result`), bold weight.

---

## 4. Layout & Spacing

The Basic Web Calculator centers itself in the user's viewport on desktop environments, scaling fluidly on smaller, touch-screen devices.

- **Calculator Frame Aspect Ratio:** Maintain a stable 4:5 vertical-to-horizontal grid distribution.
- **Inner Frame Padding:** `24px` (`padding-outer`) separates the bezel and button grid from the calculator border.
- **Bezel Screen Padding:** `16px` (`padding-inner`) internally pads the digital readouts from the display border.
- **Layout Margins:** Screen display insets are padded from the buttons by a robust `20px` (`display-to-grid`) boundary.
- **Grid Gap:** `12px` (`grid-gap`) of physical separation between individual buttons ensures that tap targets do not overlap, reducing input mistakes on mobile touchscreens.

---

## 5. Elevation & Depth

To achieve the physical-inspired aesthetic, the design applies subtle CSS depth properties:

- **The Screen display Inset:** Inside the calculator frame, apply an internal box shadow `inset 0px 2px 4px rgba(0, 0, 0, 0.1)` on the display container. This mimics a recessed glass screen, giving depth without distracting the eyes.
- **Interactive Button Elevation:** Buttons sit flat with a hairline border in light mode. On hover, they gain a minimal outer shadow `0px 1px 3px rgba(0, 0, 0, 0.1)`. On active depress/click, the shadow is cleared, and the element scales to `0.97` size to simulate physical plunge travel.

---

## 6. Shapes

The shapes use clean, slightly softened corner radii to mimic a modern desktop device:

- **Calculator Frame Corners:** `16px` (`rounded-frame`)
- **Display Screen Corners:** `12px` (`rounded-display`)
- **Button Corners:** `8px` (`rounded-button`)

Fully-rounded buttons (capsules/circles) are strictly avoided to preserve the classic layout feel of a physical desktop instrument.

---

## 7. Components

### 7.1 Screen Display Panel
- A single unified, recessed container with dark `bg-display` backing.
- Top slot contains the Faded History expression.
- Middle slot contains the active input expression.
- Bottom slot contains the Result Display.

### 7.2 Numpad Buttons
- Grid elements structured via CSS Grid.
- Button height to width ratio is 1:1 (perfect squares) on desktop, slightly fluid vertical rectangles on mobile views to maximize tap ergonomics.
- Integrated CSS `transition: transform 0.1s ease-in-out, background-color 0.15s ease-in-out`.

---

## 8. Do's and Don'ts

| Do | Don't |
| :--- | :--- |
| Use monospace fonts for Display regions. | Use variable-width fonts in displays (leads to layout shifting). |
| Maintain a generous `12px` gap between buttons. | Compress buttons together to fit more buttons in v1. |
| Use CSS scale transformations on active press states. | Render static buttons that lack visual click confirmation. |
| Contrast colors according to WCAG 2.1 AA specifications. | Use saturated accents as button background behind light text. |
| Recess the display region using an inner inset shadow. | Apply complex outer gradients or skeletons to emulate 3D. |
