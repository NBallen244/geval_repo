---
title: Epic 7 - Reverse Polish Notation (RPN) Stack Migration Context
type: context
created: 2026-10-27
status: done
review_loop_iteration: 0
context: []
---

## Context Overview

Epic 7 transitions the entire high-precision Scientific Web Calculator codebase from a standard Abstract Syntax Tree (AST) evaluator into a robust, high-speed **Reverse Polish Notation (RPN)** stack-based execution architecture. It addresses the need for professional, mouse-free calculation speed by introducing direct stack pushes, visual registers ($T, Z, Y, X$), and an arbitrary-precision Postfix evaluator, while preserving 100% backward compatibility for debounced Standard Mode inputs.

## Stories

- **Story 7.1: Shunting Yard Translation and Decimal RPN Engine**
- **Story 7.2: Interactive Dual-Mode Bezel Display and Tactile RPN Keypad**
- **Story 7.3: RPN Test Suite Expansion and Quality Assurance Enforcement**

## Requirements & Constraints

- **Exact Decimal RPN Stack:** All push, pop, and operator execution operations must calculate via Python's standard `decimal` module without conversion leakage (FR-3).
- **Stateless Stack Payloads:** The FastAPI route `POST /api/v1/evaluate` must accept stack payloads representing registers and format settings, updating them statelessly (FR-1, FR-13).
- **Dual-Mode Visual Bezel:** Render active register levels $T, Z, Y, X$ vertically and clearly when the active Mode is toggled to RPN (FR-6, FR-14).
- **Keyboard & ENTER Interceptions:** Map numerical pad ENTER keys globally to execute pushes and duplication flows in RPN mode (FR-7).
- **Coverage Preservation:** Statement and branch code coverage must continue to exceed the **80%** threshold across both the frontend and backend layers (FR-12).

## Technical Decisions

- **Infix Postfix Parser:** Implement a safe, standard Shunting Yard Algorithm tokenizer converting infix tokens into equivalent postfix sequences prior to evaluation.
- **Unified API Route:** Maintain a single stateless API route, utilizing Pydantic `expr_format: Literal["infix", "postfix"]` fields to handle standard and stack operations gracefully.
- **V8 Coverage Profiling:** Verify quality gates under Vitest and Pytest-cov inside production multi-stage environments.
