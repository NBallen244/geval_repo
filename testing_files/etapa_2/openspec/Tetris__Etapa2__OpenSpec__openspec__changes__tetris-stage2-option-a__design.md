# Design

## Context

See `proposal.md` for background and motivations. The existing Stage 1 application implements a decoupled, state-authoritative backend in Python FastAPI (`backend/`) and a React/TypeScript frontend SPA (`frontend/`). We must migrate this system to Stage 2, adding score, total lines, levels, progressive gravity, next-piece previews, and piece hold capability. The key constraint is preserving the 10x20 board layout and unrotated tetromino definitions while adding hold/swap state transitions and progressive speed intervals seamlessly without breaking existing APIs.

## Goals / Non-Goals

**Goals:**
- Upgrade backend state models with 7 new properties (`score`, `total_lines`, `level`, `gravity_interval_ms`, `next_piece`, `hold_piece`, `can_hold`).
- Define exact, deterministic state transitions for scoring, level calculations, and gravity intervals.
- Implement a hold mechanism with precise swap conditions (empty hold vs. occupied hold slot).
- Bind "C" key and "Hold" button to execute a HTTP POST to `/api/games/{id}/hold`.
- Dynamically reschedule the frontend gravity loop interval when the backend reports changes to `gravity_interval_ms`.
- Prevent stale, out-of-order API responses from updating frontend state.

**Non-Goals:**
- Adding piece rotation or wall-kick systems.
- Persistent databases, multi-piece holds, or advanced graphics/effects.

## Decisions

### Decision 1: Backend Session State Storage
- **Decision:** Extend the existing `GameSession` in-memory state object rather than introducing an external database.
- **Rationale:** Keeps the architecture stateless across service boundaries and conforms to Stage 1 constraints. Simple, robust, and performs highly in memory for active sessions.
- **Alternatives Considered:** SQLite database. Rejected as unnecessary overhead and violates the in-memory state constraint.

### Decision 2: Hold State Transitions
- **Decision:** Use a single nullable `hold_piece` property in `GameSession`. When Hold is triggered:
  - If `hold_piece` is empty: Place current active piece into `hold_piece`, spawn `next_piece` at origin `[0,3]`, and generate a new random `next_piece`.
  - If `hold_piece` is occupied: Swap active piece type with `hold_piece` type, and spawn the new active piece (previously held) at origin `[0, 3]`.
  - In both paths, mark `can_hold = False`.
- **Rationale:** Direct, unambiguous implementation of standard Tetris hold slot rules.
- **Alternatives Considered:** Spawning held pieces at local relative offsets. Rejected because standard behavior specifies spawning a held piece in its default orientation centered at origin `[0, 3]`.

### Decision 3: Dynamic Frontend Timing Interval
- **Decision:** Use a React `useEffect` with `gameState.id` and `gameState.gravity_interval_ms` in its dependency array. Inside, instantiate a fresh `setInterval` timer and store its reference to clear it on cleanup/updates.
- **Rationale:** React's dependency tracking automatically cleans up old intervals and creates new ones with correct timing whenever the gravity interval changes from backend payload, preventing timer accumulation.
- **Alternatives Considered:** A continuous polling mechanism with `setTimeout`. Rejected as more complex and harder to synchronize reliably.

### Decision 4: Out-of-Order API Response Filter
- **Decision:** Maintain a numeric `requestId` counter in a React `useRef` on the frontend. Increment this ref before every REST request, and attach the incremented count to the request context. Only update `gameState` if the resolving response's ID is greater than or equal to the latest processed ID.
- **Rationale:** Extremely lightweight and reliable client-side sequence protection without needing transactional backend protocol extensions.
- **Alternatives Considered:** Debouncing keyboard inputs. Rejected because it can cause input lag and still doesn't protect against network jitter.

## Risks / Trade-offs

### Quality follow-up from the first Stage 2 SonarQube scan

The first local scan (`docs/sonar-summary.json`, project `tetris-stage2-openspec`) passed its quality gate but reported five `python:S2245` findings and 23 code smells. Preserve the same uniform tetromino selection behavior while using `secrets.choice` to avoid the weak-randomness finding. Improve FastAPI error constants and response documentation, frontend contrast, list keys, readonly props, and simple TypeScript expressions without changing the Stage 2 game rules. Re-run tests, the frontend build, acceptance checks, and SonarQube after these focused corrections. Keep both scans as evidence.

- **[Risk] Obstructed Spawn Collision during Hold** → Spawning a piece from hold or next piece at origin `[0, 3]` could overlap with settled blocks, causing an unexpected crash or infinite loop.
  - *Mitigation:* Explicitly check for collisions after hold spawn. If invalid, instantly transition `status` to `"game_over"`.
- **[Risk] State Reversals due to Keyboard Inputs and Ticks colliding** → Simultaneous user movements and gravity ticks could trigger concurrent state transitions.
  - *Mitigation:* The backend engine operates synchronously per session. Frontend request tracking ensures only the latest authoritative state response is accepted.
