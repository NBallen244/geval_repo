---
stepsCompleted:
  - 1
  - 2
  - 3
  - 4
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-Calculator-2026-09-28/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-Calculator-2026-09-28/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/ux-designs/ux-Calculator-2026-09-28/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-Calculator-2026-09-28/EXPERIENCE.md
---

# Calculator - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Calculator, decomposing the requirements from the PRD, UX Design, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR-1: Expression Evaluation API Endpoint - Expose a RESTful HTTP endpoint `POST /api/v1/evaluate` accepting a JSON payload containing the mathematical Expression string.
FR-2: AST Parsing & PEMDAS Precedence - The evaluation engine must parse the Expression string into an Abstract Syntax Tree (AST) to validate and execute precedence rules strictly according to standard PEMDAS mathematical order.
FR-3: Exact Decimal Precision - All arithmetic operations within the Backend Service must be performed using arbitrary-precision decimals (e.g., Python's built-in `decimal` module) rather than standard IEEE-754 floating-point operations.
FR-4: Safe Error and Edge Case Handling - The math engine must validate inputs and gracefully handle common mathematical errors, throwing descriptive messages rather than crashing (e.g., division by zero, unbalanced parentheses).
FR-5: Physical-Inspired Grid Layout - The layout must feature a clean, physical-inspired visual grid representing a desktop calculator, with buttons for numbers (`0-9`), operators (`+`, `-`, `*`, `/`), brackets (`(`, `)`), decimals (`.`), clear (`C`/`AC`), delete (`Backspace`), and evaluate (`=`).
FR-6: Dual Display Outputs - The interface must feature two distinct display areas: the Primary Display (showing the active typed Expression) and the Result Display (showing the calculated Evaluation Result or live calculation preview).
FR-7: Standard Keyboard Accessibility - The Frontend Client must listen to global keyboard events and bind corresponding actions to the physical keyboard keys, allowing keyboard-only users to operate the application without a mouse.
FR-8: Screen Reader Integration (a11y) - The Frontend Client must include explicit accessibility attributes to support assistive technologies such as screen readers (e.g., `aria-label`, `aria-live`).

### NonFunctional Requirements

NFR-1: Mathematical Exactness - 100% of arithmetic calculations must be executed with exact decimal precision (0 floating-point rounding issues).
NFR-2: Performance Latency - Backend API response latency for `POST /api/v1/evaluate` must be under 50ms for the 95th percentile under normal network conditions.
NFR-3: Multi-Device Fluidity - Full responsive web layout supporting viewports as small as 320px and as large as 3840px without clipped elements or horizontal scrollbars.
NFR-4: Interactive Numpad Capture - Direct global keyboard event interception mapping to calculator keys (0-9, standard operators, parentheses, Backspace, Escape, Enter/equals) preventing default browser shortcuts.
NFR-5: WCAG 2.1 AA Compliance - Strict contrast ratio of at least 4.5:1 for displays and button text against backgrounds, and full support for screen reader ARIA tags and `aria-live` announcements.

### Additional Requirements

- **Secure AST evaluation:** Math engine must use Python's built-in `ast` module to safely parse expression strings, completely avoiding unsafe `eval()`.
- **Stateless REST API:** The `/api/v1/evaluate` endpoint must be stateless, receiving an expression string in request JSON payloads, and returning evaluation strings in responses.
- **Automated Verification:** Standard testing suite using `pytest` covering 100% of mathematical PEMDAS rules and decimal accuracy on the backend service.
- **Debounced Calculations:** Frontend must debounce requests to `/api/v1/evaluate` by `300ms` for live previews, only sending requests when the active expression has balanced parentheses.

### UX Design Requirements

UX-DR1: Light & Dark Theme Support - Support both standard Light and Dark modes matching system preferences via media queries (`@media (prefers-color-scheme: dark)`), implementing `{colors.light.*}` and `{colors.dark.*}` design tokens.
UX-DR2: Monospace Display Typography - Display regions (History, Active Display, and Result Display) must use monospace typography (`Courier New`, `Menlo`, `SF Mono`, `Consolas`, or `monospace`) to guarantee character-width stability and prevent visual horizontal shifting.
UX-DR3: Unified Recessed Display Box - Construct a unified screen bezel display box utilizing an inset box shadow (`inset 0px 2px 4px rgba(0,0,0,0.1)`) containing three distinct content lines: small historical expression, large active input expression, and bold evaluation results.
UX-DR4: Interactive Key Press Tactile Feedback - Buttons must transition visual styles on hover, focus, and active depress clicks. Active press must scale down to `0.97` to mimic physical plunge travel.
UX-DR5: Screen Reader Announcements & ARIA - Every button must feature a non-visual `aria-label` attribute (e.g., `aria-label="Number 9"`). Display results and errors must be wrapped in `aria-live="polite"` regions so announcements are read aloud automatically.
UX-DR6: Global Focus Trapping & Numpad Capture - Intercept physical key presses globally, trap focus within the calculator container, and disable browser `Tab` navigation on the grid buttons (`tabIndex="-1"`) so users can operate the app with a physical keyboard.
UX-DR7: Standard Error Visual Styling - If a syntactic or mathematical exception is thrown (e.g. division by zero), the Result Display must turn red/orange (`{colors.*.text-error}`) and the `=` button must be disabled, letting the user clear the error via `AC` or `Backspace`.

### FR Coverage Map

FR-1: Epic 1 - Expression Evaluation API Endpoint
FR-2: Epic 1 - AST Parsing & PEMDAS Precedence
FR-3: Epic 1 - Exact Decimal Precision
FR-4: Epic 1 - Safe Error and Edge Case Handling
FR-5: Epic 2 - Physical-Inspired Grid Layout
FR-6: Epic 2 - Dual Display Outputs
FR-7: Epic 2 - Standard Keyboard Accessibility
FR-8: Epic 2 - Screen Reader Integration (a11y)

## Epic List

### Epic 1: High-Precision Evaluation Engine (Backend & Math Core)
Develop a stateless, secure Python FastAPI backend service and custom AST-based calculation engine that parses arithmetic expressions and evaluates them with absolute arbitrary-precision decimal accuracy (solving standard floating-point issues), backed by a 100% verified test suite.
**FRs covered:** FR-1, FR-2, FR-3, FR-4

### Epic 2: Responsive, Accessible Tactile Interface (Frontend & Keyboard Client)
Implement a responsive, physical-inspired React TypeScript frontend web client featuring a 4x5 tactile button grid, dual-line display panels, monospace typography, debounced live preview queries, global physical numpad interception, and comprehensive WCAG-compliant screen reader accessibility.
**FRs covered:** FR-5, FR-6, FR-7, FR-8

---

## Epic 1: High-Precision Evaluation Engine (Backend & Math Core)

Develop a stateless, secure Python FastAPI backend service and custom AST-based calculation engine that parses arithmetic expressions and evaluates them with absolute arbitrary-precision decimal accuracy (solving standard floating-point issues), backed by a 100% verified test suite.

### Story 1.1: Math Parsing and Safe AST Evaluation

As a Math Parser,
I want to parse arithmetic expressions safely into an AST tree and resolve binary operator nodes,
So that I can evaluate chained calculations without raw Python eval() security vulnerabilities.

**Acceptance Criteria:**

**Given** a math expression string containing numbers and standard arithmetic operators (`+`, `-`, `*`, `/`, `(`, `)`)
**When** the parsing engine compiles the string into an Abstract Syntax Tree (AST) using Python's native `ast` package
**Then** it must successfully parse nested sub-expressions and strictly traverse nodes utilizing a custom `NodeVisitor` subclass
**And** any dangerous code injections or calls to Python's built-in `eval()` function must be completely blocked and rejected.

---

### Story 1.2: Arbitrary-Precision Math with the Decimal Module

As an Accountant,
I want all evaluations to execute using arbitrary-precision decimals,
So that I can trust calculations are 100% exact and free from binary float representation errors.

**Acceptance Criteria:**

**Given** an arithmetic expression requiring exact decimal logic (e.g. `0.1 + 0.2` or `1.0 - 0.9`)
**When** the AST custom node evaluator processes addition, subtraction, multiplication, and division operations
**Then** it must convert all operands to Python's standard `decimal.Decimal` objects before execution
**And** it must return exact decimal values represented as strings (e.g. `"0.3"` and `"0.1"`), matching standard physical calculator outputs.

---

### Story 1.3: Math Error & Syntax Validation Handling

As a Mathematics Engine,
I want to catch mathematical and structural anomalies during parsing,
So that I can validate expressions and generate standardized user-facing error outputs.

**Acceptance Criteria:**

**Given** an invalid or mathematically impossible expression (such as division by zero `10 / 0`, unbalanced brackets `(5 + 3`, or consecutive operators `12 ++ 3`)
**When** the custom parser compiles and validates the expression
**Then** it must catch the mathematical or syntactical error gracefully
**And** it must raise a custom exception that outputs a structured, user-friendly error message prefixed exactly with `"Error: "` (e.g. `"Error: Division by zero"`).

---

### Story 1.4: Stateless FastAPI HTTP Endpoint Setup

As a Frontend Client Developer,
I want a stateless FastAPI REST API endpoint `/api/v1/evaluate`,
So that I can post mathematical expressions and receive exact evaluation results.

**Acceptance Criteria:**

**Given** a running FastAPI backend service
**When** a client sends a `POST` request to `/api/v1/evaluate` with a JSON payload containing `{"expression": "12.5 + 3 * (4 - 1.5) / 2"}`
**Then** the server must process the expression using the safe decimal engine and return HTTP 200 with a success JSON containing `"status": "success"` and `"result": "16.25"`
**And** if an invalid expression is posted, the server must return HTTP 422 with an error JSON containing `"status": "error"`, `"error_type"` (e.g., `division_by_zero`), and `"message": "Error: <detail>"`.

---

## Epic 2: Responsive, Accessible Tactile Interface (Frontend & Keyboard Client)

Implement a responsive, physical-inspired React TypeScript frontend web client featuring a 4x5 tactile button grid, dual-line display panels, monospace typography, debounced live preview queries, global physical numpad interception, and comprehensive WCAG-compliant screen reader accessibility.

### Story 2.1: Physical-Style Responsive Calculator Layout & Grid

As a Mobile and Desktop Web User,
I want a responsive 4x5 button grid layout mimicking a physical desktop calculator that shifts color themes based on my system settings,
So that I can operate a beautiful and ergonomic calculator interface on any viewport size.

**Acceptance Criteria:**

**Given** any viewport size from as small as 320px (mobile phones) to as large as 3840px (4K desktop monitors)
**When** the React application renders the visual layout
**Then** it must render a centered, physical-inspired 4x5 grid of buttons representing digits, operators, brackets, backspace, AC, and equals without layout breaking or clipped labels
**And** it must automatically load visual design tokens (colors, frame sizes, spacings) matching Light Mode or Dark Mode based strictly on browser preferences (`@media (prefers-color-scheme: dark)`).

---

### Story 2.2: Interactive Dual Screen Displays & State Controllers

As Elena calculating grocery splits,
I want to see my active input character-by-character along with a debounced live calculation preview,
So that I can confirm my sub-expressions are correct as I write them.

**Acceptance Criteria:**

**Given** an empty calculator display area showing `0` (Idle State)
**When** Elena types characters using on-screen buttons
**Then** the Primary Display must update character-by-character to show the active expression (e.g., `(45.50 + 12.80 + 115) / 3`) utilizing a stable, non-drifting monospace font
**And** if the typed expression is mathematically valid, the Result Display must dynamically query `/api/v1/evaluate` (debounced by `300ms` when brackets match) and preview the temporary evaluated result (e.g., `57.7666666667`) in muted, low-contrast text.

---

### Story 2.3: Global Keyboard Event Capture & Numpad Interception

As Marcus typing invoices on a physical keyboard,
I want to use my desktop numeric pad keys to trigger calculator buttons directly,
So that I can process calculations at high speeds without touching my mouse.

**Acceptance Criteria:**

**Given** the web calculator focused in a desktop browser
**When** Marcus physical keypresses are entered (`0-9`, `.`, `+`, `-`, `*`, `/`, `(`, `)`, `Backspace`, `Escape` as AC, `Enter` or `=` as evaluate)
**Then** the application must capture these global window keydown events and execute the correct calculator state transitions instantly (with active buttons scaling down to `0.97` to mimic tactile plunge travel)
**And** it must block browser quick-search hotkeys (such as `/` in Firefox) using `event.preventDefault()`.

---

### Story 2.4: Accessibility (a11y) Screen Reader ARIA & Contrasts

As a Screen Reader User,
I want descriptive labels on every button and automatic polite live reading of calculation results,
So that I can use the calculator with complete independence.

**Acceptance Criteria:**

**Given** a browser operating with screen reader technologies (VoiceOver or TalkBack)
**When** a user tab-traverses or reads the calculator elements
**Then** every interactive grid button must contain an explicit, descriptive `aria-label` (e.g., `aria-label="Number 9"`, `aria-label="Divide"`) and have `tabIndex="-1"` to prevent browser tab focus leaks
**And** the display container must contain `role="region"` and `aria-live="polite"` so that finalized evaluated results (e.g., `"Result: 524.73"`) are spoken aloud instantly.

---

### Story 2.5: UI Error Visual States & Clears

As a Calculator User,
I want invalid expressions to trigger a visual red error state that is easily cleared,
So that I can quickly recover and fix mistakes.

**Acceptance Criteria:**

**Given** the active expression triggers a mathematical error response from the backend REST API
**When** the client processes the HTTP error code
**Then** the Result Display must render the descriptive message (e.g. `Error: Division by zero`) in high-contrast red/orange visual warning color
**And** the on-screen `=` button must be disabled, forcing the user to tap `AC` or `Backspace` to clear the error state and restore active typing.
