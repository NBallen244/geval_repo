---
title: 'Stage 1 Greenfield Decoupled Tetris Study MVP'
type: 'feature'
created: '2026-10-05'
status: 'done'
baseline_revision: 'NO_VCS'
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
deferred: []
---

## Intent

**Problem:** There is no existing codebase for the browser-based Tetris study, and the non-functional performance requirements (NFRs) contained unsupported constraints that could lead to erratic client-timer behaviors.

**Approach:** Correct the NFRs to standard approximately-500ms intervals, remove 15-minute background session eviction, and build a decoupled authoritative Python FastAPI backend and a React/TypeScript frontend.

## Boundaries & Constraints

**Always:**
- Follow the 10 columns by 20 rows board size.
- Validate all movements and ticks statefully on the backend.
- Render settled cells as static solid neon blocks mapped to colors 1-7, and active falling cells as pulsing/glowing neon blocks.
- Keep the backend core domain logic completely decoupled from FastAPI framework imports.
- Use English exclusively for all specifications, UI text, comments, variables, and logs.

**Never:**
- Implement piece rotation, SRS, hold slots, next piece previews, or ghost silhouettes.
- Implement any 15-minute idle background session cleanup or active background eviction.
- Use external heavy CSS/UI frameworks like TailwindCSS (prefer Vanilla CSS).
- Stage or commit any local code changes.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Game Initialization | POST `/api/games` | 201 Created. Returns UUID, board with 20x10 elements of 0s, active piece shape, origin, and block coordinates centered at top. | Returns 422 if payload is malformed |
| Valid Shift Left | POST `/api/games/{id}/move` (left) | 200 OK. Active piece coordinates decrease by 1 column. | Returns 404 if session not found |
| Collision Left Blocked | POST `/api/games/{id}/move` (left) near col 0 | 200 OK. Active piece position remains unchanged (left shift is blocked by boundary). | Returns 404 if session not found |
| Downward Lock & Spawn | POST `/api/games/{id}/tick` on row 19 | 200 OK. Active piece baked into board grid. Completed rows removed and shifted down. New random piece spawned. | Returns 404 if session not found |
| Spawning Collision Game Over | New piece spawned overlaps with settled blocks | 200 OK. Status transitions to `"game_over"`. All subsequent move/tick requests on session are ignored. | Returns 404 if session not found |

## Code Map

- `backend/app/main.py` -- FastAPI main routers, CORS settings, and in-memory session registry.
- `backend/app/core/domain.py` -- Decoupled game board states, Tetromino shapes, boundary checks, locking and line-clear mechanics.
- `backend/app/tests/test_domain.py` -- Backend Pytest unit tests.
- `frontend/src/App.tsx` -- Main React board component driving fetches, keyboard arrow event binders, and client gravity timers.
- `frontend/src/styles.css` -- Neon charcoal CSS stylesheet with pulsing/glowing keyframes.

## Tasks & Acceptance

**Execution:**
- `backend/app/core/domain.py` -- Implement core board logic, random spawning, coordinate shifting, collisions, locking, line clears, and game over states. -- Ensure highly testable, decoupled domain layer.
- `backend/app/main.py` -- Establish routers, CORS configuration allowing `http://localhost:5173`, and local session storage. -- Securely delivers State payloads to the UI layer.
- `backend/app/tests/test_domain.py` -- Implement pytest tests covering edge cases in domain.py. -- Ensures correctness and prevents regressions.
- `frontend/src/styles.css` -- Implement charcoal `#121212` canvas background, `#2A2A2A` subtle borders, neon indexing (1-7), and pulse borders. -- Guarantees high-fidelity aesthetic.
- `frontend/src/App.tsx` -- Build keyboard event binders, 500ms client ticks (`setInterval`), overlay blocks in English, and start/restart buttons. -- Integrates the thin-client visual with the backend authoritative session.

**Acceptance Criteria:**
- Given an active game session, when arrow key movements or gravity intervals occur, then the backend statefully processes collisions and locked configurations.
- Given a game-over status, when keyboard shifts are triggered, then the frontend ignores manual inputs, locks out gameplay, and renders a prominent English "Game Over" screen.

## Spec Change Log

*None.*

## Review Triage Log

*None.*

## Design Notes

No rotation physics are required. Spawning coordinate offsets center the shape on row 0 (or rows 0 and 1 depending on vertical depth). Standard random choices drive the next Tetromino shape.

## Verification

**Commands:**
- `pytest backend/app/tests/test_domain.py` -- expected: SUCCESS
- `npm run build` inside `frontend/` -- expected: SUCCESS
