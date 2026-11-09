---
scope: Calculator Architecture
purpose: define invariants for high-precision math parser and responsive web layout
altitude: system
updated: 2026-09-28T20:21
---

- (decision by coach) Decided on a layered client-server paradigm with FastAPI backend and React TypeScript frontend
- (decision by coach) AD-1: AST math engine using Python standard ast and decimal modules to guarantee security and precision
- (decision by coach) AD-2: Stateless POST /api/v1/evaluate REST API endpoint
- (decision by coach) AD-3: Global keyboard interception with focus trapping on the web container
- (decision by coach) AD-4: Standardized JSON error response structure with custom error types
- (decision by coach) AD-5: Debounced (300ms) live preview calculations using brackets balance checks
- (decision by coach) Architecture Spine (ARCHITECTURE-SPINE.md) drafted and saved to output folder
