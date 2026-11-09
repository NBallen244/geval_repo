---
id: SPEC-calculator
companions:
  - glossary.md
  - code-inspection-report-stage-3.md
  - code-inspection-report-stage-4.md
  - ../../planning-artifacts/prds/prd-Calculator-2026-09-28/prd.md
  - ../../planning-artifacts/prds/prd-Calculator-2026-09-28/addendum.md
  - ../../planning-artifacts/ux-designs/ux-Calculator-2026-09-28/DESIGN.md
  - ../../planning-artifacts/ux-designs/ux-Calculator-2026-09-28/EXPERIENCE.md
  - ../../planning-artifacts/architecture/architecture-Calculator-2026-09-28/ARCHITECTURE-SPINE.md
  - ../../planning-artifacts/epics.md
sources: []
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Scientific Web Calculator

## Why

Standard digital calculators suffer from frustrating binary floating-point representation errors (e.g. `0.1 + 0.2` evaluating to `0.30000000000000004`) and poor physical keyboard-only integration, which slows down high-speed administrative and financial operators. The Scientific Web Calculator solves this by combining an arbitrary-precision, secure RPN evaluation engine backend (Python/FastAPI) with a responsive, physical-inspired, accessible (WCAG 2.1 AA) React frontend. This setup provides absolute decimal accuracy, mouse-free ergonomics, and high-speed stack-based operations (Reverse Polish Notation) for daily administrative and mathematical tasks, ensuring stable column alignments, immediate tactile feedback, and interactive stack visualization.

## Capabilities

- **CAP-1: Secured Postfix (RPN) Evaluation & Shunting Yard Parser**
  - **intent:** System converts standard mathematical expressions to Postfix (RPN) notation using the Shunting Yard Algorithm, and securely evaluates them on a dedicated stack-based engine without using dangerous execution functions.
  - **success:** The backend tokenizes standard infix mathematical expressions and converts them to postfix RPN safely. Evaluating standard float-error prone inputs like `0.1 + 0.2` or complex expressions up to 10 nested parentheses deep converts correctly to postfix and computes the exact same high-precision decimal results.

- **CAP-2: Exact Decimal Arithmetic Precision**
  - **intent:** System performs calculations using arbitrary-precision representation to produce mathematically exact decimal results across both Standard and RPN modes.
  - **success:** Evaluating standard float-error prone inputs like `0.1 + 0.2` or `1.0 - 0.9` returns mathematically exact string results (`"0.3"` and `"0.1"`), matching expected physical calculator decimals.

- **CAP-3: Tactile Grid Interface**
  - **intent:** User can operate the calculator via a physical-inspired button grid and a recess display screen showing active inputs, results, live previews, and the current RPN stack level.
  - **success:** CSS Grid adapts responsively down to 320px width without layout shifting, and buttons transition visually on hover, focus, and active clicks (with scale depress transform `scale(0.97)` travel).

- **CAP-4: Global Keyboard Numpad Interception**
  - **intent:** User can operate all calculator keys (including digits, operators, backspace, and the new RPN `ENTER` key) using standard numeric pads and physical keyboard hotkeys without a mouse.
  - **success:** physical keystrokes (`0-9`, `.`, operators, brackets, Backspace, Escape as AC, Enter as evaluate/push) intercept globally and trigger actions while blocking default browser hotkeys.

- **CAP-5: Full Screen Reader Accessibility**
  - **intent:** Vision-impaired users can navigate and hear active displays, results, error readouts, and active stack levels announced dynamically by screen readers.
  - **success:** Buttons feature non-visual descriptive `aria-label` tags, grid buttons disable tab focus (`tabIndex="-1"`), and display outputs trigger immediate `polite` screen reader live announcements.

- **CAP-6: Structured Error Serialization**
  - **intent:** System validates inputs and serializes exceptions (e.g., division by zero, stack underflow, invalid syntax) into standard, clean error strings that trigger visual red warning states.
  - **success:** Evaluating an invalid operation like `10 0 /` in RPN mode or an unbalanced parenthesis in Standard mode triggers a visual error state (red typography) and displays a prominent `"Error: Division by zero"` or `"Error: Stack underflow"` message.

- **CAP-7: Advanced Scientific & Constant Operations**
  - **intent:** System evaluates trigonometric, logarithmic, root, and exponential functions, along with standard constants (pi, e), in both Standard (via infix-to-postfix conversion) and pure RPN stack execution.
  - **success:** Functions applied to the stack pop the required operand(s), compute the operation, and push the high-precision result back onto the stack (e.g., evaluating `90 sin` in Degree mode returns exactly `"1"`).

- **CAP-8: Exact Precision Memory Register System**
  - **intent:** User can perform standard calculator memory functions (M+, M-, MR, MC) backed by high-precision decimal operations and track its state with a visual screen indicator.
  - **success:** Clicking `M+` / `M-` updates local memory state with absolute precision. A visual "M" indicator appears on screen when the memory value is non-zero.

- **CAP-9: Interactive Session History Drawer**
  - **intent:** Users can view, clear, and reload past calculations (either the expression or the result) from the current session.
  - **success:** An interactive, accessible side drawer caches successfully evaluated expressions or stack calculations, allowing users to reload them into the display.

- **CAP-10: High-Coverage Testing & Edge Case Verification**
  - **intent:** Both frontend and backend logic are fully verified with exhaustive test coverage, ensuring 100% computational correctness under critical mathematical and stack boundaries.
  - **success:** Statement and branch code coverage strictly meets or exceeds **80%** across both the backend (`pytest` suite) and frontend (`vitest` suite) codebases under RPN and Standard modes.

- **CAP-11: Secure Containerization & Orchestration**
  - **intent:** Calculator services are isolated into secure runtime containers to enable standard continuous integration pipelines and simple, portable local development orchestrations.
  - **success:** Multi-stage production `Dockerfile`s for the Python FastAPI server and the React web assets compiler build and coordinate seamlessly under `docker-compose.yml`.

- **CAP-12: Real-time RPN Stack Visualizer and Interactive Input**
  - **intent:** User can operate the calculator in a direct stack-based Reverse Polish Notation (RPN) mode, utilizing an `ENTER` key to push values onto a multi-level stack ($X, Y, Z, T$) with an interactive real-time visual stack display.
  - **success:** Switching to RPN Mode displays the active levels of the evaluation stack ($X, Y, Z, T$) which update instantly when operands are pushed or operators are applied.

## Constraints

- **Arbitrary-Precision Math:** All calculations must execute via Python's standard `decimal` module; raw floating-point calculations are banned. Trigonometric functions utilize standard float wrappers converted from/to `Decimal` safely.
- **Secure Stack & Postfix Execution Only:** Infix expressions are parsed and converted to postfix (RPN) tokens using a secure Shunting Yard Algorithm before execution on a stack-based engine; raw `eval()` execution is strictly forbidden.
- **Stateless REST API Endpoint:** The calculation service endpoint `POST /api/v1/evaluate` must be completely stateless, support angle mode, and accommodate both Standard (infix) expressions and pure RPN stack execution payloads.
- **Stable Monospace Readouts:** Monospace font families must be utilized inside display panels and stack levels to prevent horizontal character jittering.
- **Ergonomic Mobile Tap Targets:** Buttons must occupy at least `48px` x `48px` on mobile layouts.
- **No Grid Tab Traversal:** Buttons must have `tabIndex="-1"` to keep keyboard navigation bound strictly to global window intercepts.
- **Quality Gates Threshold:** Statement and branch code coverage must strictly exceed the 80% boundary across both software layers prior to production container deployment runs.
- **Minimal Secure Runtimes:** Production containers must operate under non-privileged system accounts (UID `10001` for backend) and serve static assets via lightweight alpine web servers.

## Non-goals

- **No Multi-currency/Unit Conversions:** No multi-currency or weight/unit conversion.
- **No Standalone Offline Operation:** The application requires active REST API backend connectivity; offline local evaluations are out of scope.

## Success signal

- All backend mathematical precedence, decimal precision, RPN stack operations, and error validation unit tests run and pass under `pytest` with 100% correctness. All responsive layouts, RPN stack visualizers, active transitions, contrast hierarchies, keyboard event interceptions, and screen reader announcements conform to WCAG 2.1 AA specifications. Code statement and branch coverage exceeds the 80% threshold, and container deployments run stably under Docker Compose orchestration.
