---
scope: Stage 1 gameplay grid, tick execution, controls, and session state
purpose: build-substrate
altitude: feature
topic: Stage 1 Tetris Study Architecture Spine
goal: Establish invariants and rules for the decoupled greenfield Tetris application
updated: 2026-10-05T23:54
---

- (decision) Adopted decoupled client-server design with authoritative FastAPI backend and thin React TypeScript frontend.
- (decision) Enforced strict single source of truth: backend is sole validator for collisions, locking, line clears, and game over.
- (decision) Defined stateless frontend rendering layered with client-side 500ms gravity timer for automatic ticks.
- (decision) Enforced strict 10x20 grid coordinates using standard 0-indexed layout.
- (decision) Excluded rotation, hold, next-piece queue, ghost piece, and scoring in Stage 1.
- (decision) Restricted manual keyboard movement inputs strictly to ArrowLeft, ArrowRight, and ArrowDown; restart via prominent screen button only.
- (decision) Implemented ephemeral in-memory session dictionaries without databases or authentication.
- (event) spine finalized
