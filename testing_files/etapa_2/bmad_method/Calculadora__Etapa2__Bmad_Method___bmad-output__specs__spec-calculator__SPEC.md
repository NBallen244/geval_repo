---
id: SPEC-calculator
companions:
  - glossary.md
  - ../../planning-artifacts/prds/prd-Calculator-2026-09-28/prd.md
  - ../../planning-artifacts/prds/prd-Calculator-2026-09-28/addendum.md
  - ../../planning-artifacts/ux-designs/ux-Calculator-2026-09-28/DESIGN.md
  - ../../planning-artifacts/ux-designs/ux-Calculator-2026-09-28/EXPERIENCE.md
  - ../../planning-artifacts/architecture/architecture-Calculator-2026-09-28/ARCHITECTURE-SPINE.md
  - ../../planning-artifacts/epics.md
sources: []
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Basic Web Calculator

## Why

Standard digital calculators suffer from frustrating binary floating-point representation errors (e.g. `0.1 + 0.2` evaluating to `0.30000000000000004`) and poor physical keyboard-only integration, which slows down high-speed administrative and financial operators. The Basic Web Calculator solves this by combining an arbitrary-precision, secure AST mathematical parser backend (Python/FastAPI) with a responsive, physical-inspired, accessible (WCAG 2.1 AA) React frontend. This setup provides absolute decimal accuracy and mouse-free ergonomics for daily administrative tasks, ensuring stable column alignments and immediate tactile feedback.

## Capabilities

- **CAP-1: Secured AST Arithmetic Evaluation**
  - **intent:** System safely parses nested mathematical expressions and executes operations according to standard PEMDAS precedence rules without using dangerous execution functions.
  - **success:** The backend AST parsing engine validates expressions up to 10 nested parenthesis levels deep, rejecting any dangerous Python injections or raw string evals.

- **CAP-2: Exact Decimal Arithmetic Precision**
  - **intent:** System performs calculations using arbitrary-precision representation to produce mathematically exact decimal results.
  - **success:** Evaluating standard float-error prone inputs like `0.1 + 0.2` or `1.0 - 0.9` returns mathematically exact string results (`"0.3"` and `"0.1"`), matching expected physical calculator decimals.

- **CAP-3: Tactile Grid Interface**
  - **intent:** User can operate the calculator via a physical-inspired 4x5 button grid and a recess display screen showing active inputs, results, and live previews.
  - **success:** CSS Grid adapts responsively down to 320px width without layout shifting, and buttons transition visually on hover, focus, and active clicks (with scale depress transform `scale(0.97)` travel).

- **CAP-4: Global Keyboard Numpad Interception**
  - **intent:** User can operate all calculator keys using standard numeric pads and physical keyboard hotkeys without a mouse.
  - **success:** physical keystrokes (`0-9`, `.`, operators, brackets, Backspace, Escape as AC, Enter as evaluate) intercept globally and trigger actions while blocking default browser hotkeys (such as Firefox Quick Find).

- **CAP-5: Full Screen Reader Accessibility**
  - **intent:** Vision-impaired users can navigate and hear active displays, results, and error readouts announced dynamically by screen readers.
  - **success:** Buttons feature non-visual descriptive `aria-label` tags, grid buttons disable tab focus (`tabIndex="-1"`), and display outputs trigger immediate `polite` screen reader live announcements.

- **CAP-6: Structured Error Serialization**
  - **intent:** System validates inputs and serializes exceptions (e.g., division by zero) into standard, clean error strings that trigger visual red warning states.
  - **success:** Evaluating an invalid operation like `10 / 0` triggers a visual error state (red typography, disabled `=` key) and displays a prominent `"Error: Division by zero"` message on the screen.

- **CAP-7: Advanced Scientific & Constant Operations**
  - **intent:** System evaluates trigonometric, logarithmic, root, and exponential functions, along with standard constants (pi, e), while adhering to standard math domains.
  - **success:** Backend whitelists `ast.Call`, `ast.Name`, and `ast.Pow`. Evaluating functions (e.g. `sin(pi/2)` in Radian mode or `sin(90)` in Degree mode) returns exactly `"1"`. Attempting invalid domain math (e.g. `sqrt(-4)` or `ln(0)`) triggers user-friendly `"Error: <detail>"` responses.

- **CAP-8: Exact Precision Memory Register System**
  - **intent:** User can perform standard calculator memory functions (M+, M-, MR, MC) backed by high-precision decimal operations and track its state with a visual screen indicator.
  - **success:** Clicking `M+` / `M-` dispatches a REST query to compute addition/subtraction, updating local memory state with absolute precision. A visual "M" indicator appears on screen when the memory value is non-zero.

- **CAP-9: Interactive Session History Drawer**
  - **intent:** Users can view, clear, and reload past calculations (either the expression or the result) from the current session.
  - **success:** An interactive, accessible side drawer caches successfully evaluated expressions. Tapping an item opens a submenu to load either the expression or the result into the display, or clear history completely.

## Constraints

- **Arbitrary-Precision Math:** All calculations must execute via Python's standard `decimal` module; raw floating-point calculations are banned. Trigonometric functions utilize standard float wrappers converted from/to `Decimal` safely.
- **Secure AST Execution Only:** Parsing must traverse AST node expressions via a custom `NodeVisitor` subclass; raw `eval()` execution is forbidden. Whitelisted nodes are extended to support `ast.Call`, `ast.Name`, and `ast.Pow`.
- **Stateless REST API Endpoint:** The calculation service endpoint `POST /api/v1/evaluate` must be completely stateless and accept an optional `angle_unit` parameter.
- **Stable Monospace Readouts:** Monospace font families must be utilized inside display panels to prevent horizontal character jittering.
- **Ergonomic Mobile Tap Targets:** Buttons must occupy at least `48px` x `48px` on mobile layouts.
- **No Grid Tab Traversal:** Buttons must have `tabIndex="-1"` to keep keyboard navigation bound strictly to global window intercepts.

## Non-goals

- **No Multi-currency/Unit Conversions:** No multi-currency or weight/unit conversion.
- **No Standalone Offline Operation:** The application requires active REST API backend connectivity; offline local evaluations are out of scope.

## Success signal

- All backend mathematical precedence, decimal precision, and error validation unit tests run and pass under `pytest` with 100% correctness. All responsive layouts, active transitions, contrast hierarchies, keyboard event interceptions, and screen reader announcements conform to WCAG 2.1 AA specifications under audits with zero visual drift.
