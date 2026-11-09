---
topic: Basic Web Calculator Spec-Kernel
goal: provide the single unified specification of truth (SPEC.md) with absolute capabilities and system constraints
updated: 2026-10-27T15:38
---

- (event by coach) Spec workspace initialized from PRD, UX, and Architecture outputs
- (decision by coach) Spec-Kernel (SPEC.md) and Glossary companion (glossary.md) drafted and saved to output folder
- (event) Stage 3 initiated following SEED-3.md instructions
- (decision) Added Epic 6 and individual stories (Story 6.1, 6.2, 6.3) to represent audit, high-coverage testing, and Docker containerization
- (decision) Identified and reported a memory register priority bug during code inspection (reported in code-inspection-report-stage-3.md)
- (decision) Refactored useEvaluate.ts to prioritize active inputs during memory operations when typing, completely resolving the pre-existing state priority bug
- (decision) Implemented a complete frontend unit & integration test suite in vitest, achieving 88.94% code coverage across components and custom state controllers
- (decision) Verified 91% backend code coverage across AST parsing and FastAPI endpoint routes using pytest and pytest-cov
- (decision) Generated secure multi-stage Dockerfiles for python FastAPI and Nginx static web assets serving
- (decision) Orchestrated services in a unified local docker-compose.yml configuration
- (decision) Generated new Spec capabilities (CAP-10 and CAP-11) representing automated edge case verification and multi-container deployment
- (event) Stage 3 implementation verified with 100% test success rate on both layers
- (event) Stage 4 initiated following SEED-4.md instructions
- (decision) Refactoring core mathematical evaluation engine to support Reverse Polish Notation (RPN) stack-based evaluation with arbitrary precision decimal math
- (decision) Updating standard infix mode to utilize the Shunting Yard Algorithm to parse standard mathematical expressions into Postfix (RPN) tokens, then evaluate via the RPN engine
- (decision) Adding direct RPN Mode with an active visual stack display in real-time and an ENTER key in the React UI
- (decision) Refactoring backend and frontend test suites to assert RPN and Shunting-Yard conversion, maintaining code coverage >= 80%
- (event) Updated SPEC.md with CAP-1, CAP-12, and RPN constraints representing the Stage 4 RPN Engine and UI dual-mode adaptation
- (decision) Completed backend RPN and Shunting-Yard engine refactoring, verified backwards-compatibility of standard infix mathematical evaluations under pytest with 100% success rate
- (event) Stage 4 RPN migration completely implemented, fully verified with 100% test success across 22 frontend and 31 backend assertions, coverage maintained well above 80%
