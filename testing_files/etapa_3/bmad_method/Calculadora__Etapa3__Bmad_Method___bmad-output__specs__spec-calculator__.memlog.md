---
topic: Basic Web Calculator Spec-Kernel
goal: provide the single unified specification of truth (SPEC.md) with absolute capabilities and system constraints
updated: 2026-09-28T20:56
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
