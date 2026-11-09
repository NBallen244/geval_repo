---
stepsCompleted:
  - 1
  - 2
  - 3
  - 4
  - 5
  - 6
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-Calculator-2026-09-28/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-Calculator-2026-09-28/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/ux-designs/ux-Calculator-2026-09-28/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-Calculator-2026-09-28/EXPERIENCE.md
---

# Calculator - Epic Breakdown

## Overview
This document provides the complete epic and story breakdown for the Scientific Web Calculator, decomposing the requirements from the PRD, UX Design, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements
* **FR-1:** Expression Evaluation API Endpoint
* **FR-2:** AST Parsing & PEMDAS Precedence
* **FR-3:** Exact Decimal Precision
* **FR-4:** Safe Error and Edge Case Handling
* **FR-5:** Physical-Inspired Grid Layout
* **FR-6:** Dual Display Outputs
* **FR-7:** Standard Keyboard Accessibility
* **FR-8:** Screen Reader Integration (a11y)
* **FR-9:** Advanced Scientific Functionality
* **FR-10:** High-Precision Client-Side Memory Accumulator
* **FR-11:** Slide-Out Session Calculation History Drawer
* **FR-12:** Multi-Container Secure Packaging & Orchestration

---

## Epic List

### Epic 1: High-Precision Evaluation Engine (Backend & Math Core)
Develop a stateless, secure Python FastAPI backend service and custom AST-based calculation engine.
**FRs covered:** FR-1, FR-2, FR-3, FR-4

### Epic 2: Responsive, Accessible Tactile Interface (Frontend & Keyboard Client)
Implement a responsive, physical-inspired React TypeScript frontend web client featuring a 4x5 tactile button grid and dual-line displays.
**FRs covered:** FR-5, FR-6, FR-7, FR-8

### Epic 3: Advanced Scientific Mathematics (Backend & API Core)
Develop backend parser logic to securely process scientific operations, angle modes, and constants.
**FRs covered:** FR-9

### Epic 4: Integrated State Sync, Memory, and History Panel (Frontend & Client)
Extend frontend state management to store local memory registers and session history.
**FRs covered:** FR-10, FR-11

### Epic 5: Responsive Scientific Keypad Layout & Accessibility (Frontend Layout)
Re-design the main keypad layout to cleanly support scientific functions and memory keys.
**FRs covered:** FR-5, FR-8

### Epic 6: Security, Testing Quality & Containerization
Enforce rigorous, automated testing gates and multi-container Docker deployments.
**FRs covered:** FR-4, FR-12

---

## Epic List Details

### Epic 1: High-Precision Evaluation Engine (Backend & Math Core)

#### Story 1.1: Math Parsing and Safe AST Evaluation
- **intent:** Parse arithmetic expressions safely into an AST tree and resolve binary operator nodes.
- **Acceptance Criteria:** Given a math expression containing arithmetic operators, compile into an AST and traverse using `NodeVisitor`, rejecting unsafe code or raw string evals.

#### Story 1.2: Arbitrary-Precision Math with the Decimal Module
- **intent:** Perform all calculations with absolute arbitrary-precision decimal accuracy.
- **Acceptance Criteria:** Operands must convert to standard `decimal.Decimal` objects, returning exact decimal values as strings.

#### Story 1.3: Math Error & Syntax Validation Handling
- **intent:** Catch and validate mathematical or syntactical anomalies during parsing.
- **Acceptance Criteria:** Catch common errors gracefully (e.g. division by zero, unbalanced parentheses), throwing user-friendly messages prefixed with `"Error: "`.

#### Story 1.4: Stateless FastAPI HTTP Endpoint Setup
- **intent:** Expose a stateless REST API endpoint `/api/v1/evaluate` to process queries.
- **Acceptance Criteria:** `POST /api/v1/evaluate` accepts standard payloads and returns success result or structured errors.

---

### Epic 2: Responsive, Accessible Tactile Interface (Frontend & Keyboard Client)

#### Story 2.1: Physical-Style Responsive Calculator Layout & Grid
- **Acceptance Criteria:** Adaptive grid representing a tactile 4x5 standard keypad that conforms to Light/Dark modes.

#### Story 2.2: Interactive Dual Screen Displays & State Controllers
- **Acceptance Criteria:** Primary Display shows characters, Result Display previews calculation dynamically when balanced.

#### Story 2.3: Global Keyboard Event Capture & Numpad Interception
- **Acceptance Criteria:** Capture keydown events and execute state transitions, blocking default browser actions.

#### Story 2.4: Accessibility (a11y) Screen Reader ARIA & Contrasts
- **Acceptance Criteria:** Non-visual `aria-label` on buttons, `tabIndex="-1"`, and display regions marked with `aria-live="polite"`.

#### Story 2.5: UI Error Visual States & Clears
- **Acceptance Criteria:** Visual red error state on display, equals button disabled, typing any number clears the error.

---

### Epic 3: Advanced Scientific Mathematics (Backend & API Core)

#### Story 3.1: AST Evaluation for Whitelisted Scientific Function Calls
- **Acceptance Criteria:** Whitelist `ast.Call` nodes. Trigonometric, root, and log functions evaluate accurately.

#### Story 3.2: Degrees & Radians Angle Modes and Conversions
- **Acceptance Criteria:** Convert degree angle inputs to radians prior to trig execution, and convert radians to degrees for inverse trig results.

#### Story 3.3: Exponentiation, Roots, and Mathematical Constants
- **Acceptance Criteria:** Whitelist `ast.Pow` and resolve names `pi` and `e` with high decimal precision, validating domains.

---

### Epic 4: Integrated State Sync, Memory, and History Panel (Frontend & Client)

#### Story 4.1: Client-Side High-Precision Memory Register (M+, M-, MR, MC)
- **Acceptance Criteria:** Sync memory operations by dispatching precision-preserving API evaluations, displaying the "M" badge on screen when active.

#### Story 4.2: Interactive Side Drawer Session Calculation History
- **Acceptance Criteria:** Sliding sidebar list panel allowing users to inspect or reload past session expressions/results.

---

### Epic 5: Responsive Scientific Keypad Layout & Accessibility (Frontend Layout)

#### Story 5.1: Collapsible Dual-Keypad Responsive Grid and Memory Badges
- **Acceptance Criteria:** Keypad collapses on mobile screen viewports preserving a minimum touch clearance target of $48\text{px}$.

#### Story 5.2: Keyboard Binding Expansion and a11y ARIA Announcements
- **Acceptance Criteria:** Shortcut mappings globally trap scientific keys; changes to mode or memory trigger immediate polite live announcements.

---

### Epic 6: Security, Testing Quality & Containerization

#### Story 6.1: Code Inspection & Pre-Existing Bug Audit
- **intent:** Audit pre-existing code to document state leakage, precision errors, and state machine bugs.
- **Acceptance Criteria:** Inspect frontend/backend code, reporting any anomalies (such as the memory state priority bug) in a Stage 3 audit log before applying fixes.

#### Story 6.2: High-Coverage Automated Unit and Integration Test Suites
- **intent:** Maintain quality control by keeping code coverage above 80% on both frontend and backend.
- **Acceptance Criteria:** Create thorough automated test files in both backend (`pytest`) and frontend (`vitest`), confirming statement/branch coverage exceeds the 80% quality gate.

#### Story 6.3: Multi-Stage Production Containerization and Unified Local Orchestration
- **intent:** Containerize the services using multi-stage production Dockerfiles and orchestrate them via Compose.
- **Acceptance Criteria:** Write secure backend Dockerfile (non-root run execution) and frontend Dockerfile (static asset compile with Nginx serving), orchestrated in a unified `docker-compose.yml`.
