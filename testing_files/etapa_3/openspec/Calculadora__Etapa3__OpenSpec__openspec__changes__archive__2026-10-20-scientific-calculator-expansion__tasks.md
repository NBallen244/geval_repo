## 1. Backend Engine Expansion

- [x] 1.1 Update `EvaluateRequest` in `backend/app/main.py` to accept `angle_unit: str = "radians"`. Verify this by running a test request payload with/without this field and checking it succeeds.
- [x] 1.2 Implement trigonometric and inverse trigonometric AST evaluation logic (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`) in `evaluate_ast_node()` inside `backend/app/calculator.py`, converting degrees to radians as necessary. Verify by running `pytest backend/tests/` with new tests checking angle modes.
- [x] 1.3 Support logarithmic (`ln`, `log10`), power (`**`, square, base-10 exponentiation), and root (`sqrt`, custom n-th root `root`) functions and operators in `evaluate_ast_node()`. Verify by running `pytest` with validation tests for power and logarithm inputs.
- [x] 1.4 Add `pi` and `e` mathematical constant resolution to `evaluate_ast_node()` inside `backend/app/calculator.py`. Verify by running unit tests evaluating `pi` and `e` expressions in the engine.
- [x] 1.5 Update expression character whitelist in `backend/app/calculator.py` to allow letters and comma characters, and add strict AST node type validation to reject unapproved nodes. Verify by running `pytest` to confirm the entire test suite passes without any regression.

## 2. Frontend State & Operations

- [x] 2.1 Add React state hooks for `memory` (MC/MR/M+/M-), `history` (list of evaluated calculation objects), and `angleUnit` ("radians"/"degrees") in `frontend/src/App.tsx`. Verify state changes via UI inspection.
- [x] 2.2 Implement MC, MR, M+, and M- click handlers and display integration, including a conditional on-screen "M" badge when `memory` is non-zero. Verify memory operation behaviors via UI clicking simulation.
- [x] 2.3 Integrate successfully evaluated expressions into the interactive `history` panel state. Provide a collapsible sidebar/drawer that renders history items with options to load either the expression or the result into the display, and a "Clear History" button. Verify history rendering and clear mechanism manually.

## 3. UI Keypad & Accessibility Integration

- [x] 3.1 Redesign the button grid to support scientific keys, memory keys, and angle toggles. Implement a collapsible panel or expansion toggle for smaller mobile viewports. Verify layout responsively via mobile browser devtools.
- [x] 3.2 Update physical keyboard listeners in `frontend/src/App.tsx` to handle keys like `^` (power) or custom mapping for constants. Verify keyboard shortcut functionality.
- [x] 3.3 Ensure ARIA roles, labels, and focus indicators exist on the new scientific buttons and history drawers. Verify screen reader announcements in `aria-live` for trigonometric outputs and memory actions.

## 4. End-to-End Verification

- [x] 4.1 Execute full pytest backend tests (`pytest backend/tests/`) to verify scientific operations and angle conversions work completely.
- [x] 4.2 Run frontend production build inside the `frontend/` directory to ensure no TypeScript or CSS compile errors are introduced.
