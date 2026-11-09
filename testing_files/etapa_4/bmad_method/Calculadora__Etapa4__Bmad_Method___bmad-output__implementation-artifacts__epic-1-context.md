# Epic 1 Context: High-Precision Evaluation Engine (Backend & Math Core)

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Develop a stateless, secure Python FastAPI backend service and custom AST-based calculation engine that parses arithmetic expressions and evaluates them with absolute arbitrary-precision decimal accuracy (solving standard floating-point issues), backed by a 100% verified test suite.

## Stories

- Story 1.1: Math Parsing and Safe AST Evaluation
- Story 1.2: Arbitrary-Precision Math with the Decimal Module
- Story 1.3: Math Error & Syntax Validation Handling
- Story 1.4: Stateless FastAPI HTTP Endpoint Setup

## Requirements & Constraints

- **Arbitrary-Precision Math:** All calculations must execute via Python's standard `decimal` module; raw floating-point calculations are banned (FR-3, NFR-1).
- **Secure AST Execution Only:** Parsing must traverse AST node expressions via a custom `NodeVisitor` subclass; raw `eval()` execution is forbidden (FR-2, NFR-1).
- **Stateless REST API Endpoint:** The calculation service endpoint `POST /api/v1/evaluate` must be completely stateless (FR-1, AD-2).
- **Math Validation Errors:** Catch and throw clean, custom exceptions with status `error`, a specific type, and user-facing messages starting with `Error: ` (FR-4, AD-4).

## Technical Decisions

- **Node Visitor Pattern:** A custom subclass of `ast.NodeVisitor` will traverse the Python compilation syntax tree securely (AD-1).
- **Stateless API Routing:** FastAPI router mapping JSON input payloads containing `"expression"` to response JSONs (AD-2).
- **Testing:** 100% test verification coverage using `pytest` unit and integration tests (AD-1).

## Cross-Story Dependencies

- Story 1.1 (Safe AST Parsing) must be implemented first.
- Story 1.2 (Decimal Module integration) builds on top of Story 1.1.
- Story 1.3 (Error validation) builds on top of Story 1.1 & 1.2.
- Story 1.4 (FastAPI endpoint) integrates the fully built mathematical engine from Stories 1.1 - 1.3.
