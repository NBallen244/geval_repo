## Why

The current Web Calculator is limited to basic arithmetic operations (addition, subtraction, multiplication, and division). Expanding the application with scientific calculation functions, memory registers, and an interactive session calculation history is required to support advanced mathematical needs and improve user productivity.

## What Changes

- **Backend API Expansion**: Extend the math evaluation engine to parse and evaluate scientific functions (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `ln`, `log10`, `sqrt`), power operations, and constants (`pi`, `e`), while adhering to exact decimal precision constraints.
- **Radians/Degrees Angle Unit Toggles**: Implement a toggle to switch between Radians and Degrees for all trigonometric computations.
- **Memory Register System**: Add MC (Clear), MR (Recall), M+ (Add), M- (Subtract) operations, along with a visual "M" badge on the calculator screen when a non-zero value is in memory.
- **Session Calculation History**: Build an interactive sidebar/drawer displaying previously evaluated expressions, with the ability to click any history entry to reload its expression or result into the current active input area.
- **Enhanced Responsive UI Layout**: Upgrade the grid layout to support scientific buttons and memory controls smoothly on all device form factors (desktop, tablet, mobile), without cluttering or clipping content.
- **Keyboard Shortcuts Extension**: Expand physical keyboard mapping to support scientific operations where appropriate.

## Capabilities

### New Capabilities
- `scientific-calculator`: Covers advanced scientific mathematical operations, constants, angle unit toggles, persistent memory registers, and an interactive session calculation history.

### Modified Capabilities
<!-- None, as the core basic-calculator requirements remain backward-compatible and unchanged. -->

## Impact

- **Backend API**: The AST parser and evaluator in `backend/app/calculator.py` and `backend/app/main.py` will be upgraded to support function parsing (`ast.Call`), variable resolution (`ast.Name`), and additional operator parsing (e.g. `ast.Pow`).
- **Frontend App**: `frontend/src/App.tsx` and its accompanying styling in `frontend/src/index.css` will be expanded to support the scientific keypad layout, memory state, interactive history panel/drawer, and new keyboard mappings.
- **No New Dependencies**: Built-in Python `math` library and standard React hooks will be used, keeping the project's dependency surface lightweight and clean.
