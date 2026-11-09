## Purpose

Enables scientific mathematical operations, constants, and memory register management on the Web Calculator with local session state persistence.

## ADDED Requirements

### Requirement: Advanced Scientific Math Evaluation
The backend and evaluation engine SHALL support evaluating trigonometric functions (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`), logarithms (`ln`, `log10`), powers (`**`, square, base-10 power), and roots (square root, $n$-th root) with high precision.

#### Scenario: Exponentiation evaluation
- **WHEN** user requests evaluation of expression `2 ** 4`
- **THEN** system evaluates expression and returns exactly `16`

#### Scenario: Square root evaluation
- **WHEN** user requests evaluation of expression `sqrt(9)`
- **THEN** system evaluates expression and returns exactly `3`

#### Scenario: Natural logarithm evaluation
- **WHEN** user requests evaluation of expression `ln(e)`
- **THEN** system evaluates expression and returns exactly `1`

#### Scenario: Domain error handling
- **WHEN** user requests evaluation of expression `sqrt(-1)` or `ln(0)`
- **THEN** system returns an HTTP 400 Bad Request error stating "Math domain error"

### Requirement: Trigonometric Units (Radians and Degrees Toggle)
The calculator SHALL support toggling between Radians and Degrees modes, applying the selected mode to all trigonometric and inverse trigonometric computations.

#### Scenario: Sine evaluation in Radians
- **WHEN** user toggles angle unit to Radians and evaluates `sin(pi / 2)`
- **THEN** system returns exactly `1`

#### Scenario: Sine evaluation in Degrees
- **WHEN** user toggles angle unit to Degrees and evaluates `sin(90)`
- **THEN** system returns exactly `1`

### Requirement: Scientific Mathematical Constants
The calculator SHALL support quick input and evaluation of standard mathematical constants `pi` and `e`.

#### Scenario: Expression containing pi constant
- **WHEN** user evaluates `pi * 2`
- **THEN** system replaces `pi` with its high-precision value and returns the product

### Requirement: Local Memory Register System
The calculator SHALL provide a memory register supporting standard memory operations: M+ (add current display to memory), M- (subtract current display from memory), MR (recall memory), and MC (clear memory), displaying a visual "M" badge on screen whenever the stored value is non-zero.

#### Scenario: Memory add and recall operations
- **WHEN** user adds `5` to memory using `M+`, clears display, and presses `MR`
- **THEN** display displays `5` and active visual indicator shows "M" badge

### Requirement: Interactive Session Calculation History
The frontend SHALL provide an interactive history panel displaying previously evaluated expressions in the current active session. Users can click any historical entry to reload either the historical expression or its final result into the input display.

#### Scenario: Reloading historical expression
- **WHEN** user clicks on a historical calculation `10 + 20` in the history panel and selects expression reuse
- **THEN** the active input display is loaded with `10 + 20`

### Requirement: Enhanced Responsive Layout and Keyboard Mapping
The calculator interface SHALL adapt responsively to display the scientific keypad layout alongside memory operations and history controls without clipping content, and support corresponding keyboard mappings.

#### Scenario: Mobile responsive scientific keyboard layout
- **WHEN** user views the calculator on a mobile screen width of 375px
- **THEN** the scientific function keys are fully accessible without breaking the layout or causing horizontal overflow
