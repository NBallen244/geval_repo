---
title: 'Stage 2 Tetris Study (Option A)'
type: 'feature'
created: '2026-10-25'
status: 'in-progress'
baseline_commit: 'NO_VCS'
route: 'dispatch'
review_loop_iteration: 0
followup_review_recommended: false
context: [
  "_bmad-output/stage2/planning-artifacts/prds/prd-stage2-option-a/prd.md",
  "_bmad-output/stage2/planning-artifacts/prds/prd-stage2-option-a/addendum.md",
  "_bmad-output/stage2/planning-artifacts/architecture/stage2-option-a/ARCHITECTURE-SPINE.md",
  "_bmad-output/stage2/planning-artifacts/epics.md",
  "_bmad-output/stage2/implementation-artifacts/sprint-status.yaml"
]
warnings: []
deferred: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The existing Stage 1 Tetris prototype lacks a game progression system (Score, Cleared Lines, Level, Gravity Speedup), a next-piece preview queue, and a hold-piece slot, which are essential for testing stateful real-time synchronization under high-frequency frontend ticks.

**Approach:** Extend the Python FastAPI backend to statefully calculate scores, track cumulative cleared lines, compute progressive levels and gravity intervals, and support hold swaps and next previews in a single unified GameState payload. Build responsive frontend sidebar panels, a robust FIFO mutation queue, React StrictMode-safe generation ownership check, and keys/buttons for hold.

## Boundaries & Constraints

**Always:**
- Keep the board strictly 10 columns by 20 rows and preserve the original 7 unrotated tetromino shapes and coordinates.
- Maintain a single active client automatic timer for gravity, canceled immediately on mutation enqueuing, and rescheduled from the server's authoritative `gravity_interval_ms` when the queue becomes idle.
- Check monotonically increasing generation tokens inside all frontend callbacks (fetches, JSON, catches, finallys, timer events) to completely filter and discard obsolete session state mutations under React StrictMode.
- Ensure all 7 Stage 2 fields (`score`, `total_lines`, `level`, `gravity_interval_ms`, `next_piece`, `hold_piece`, `can_hold`) persist correctly across horizontal moves, successful soft drops, ticks, rejected moves, and holds.
- Distinguish invalid direction payloads (which return HTTP 422) from standard legal movements that are blocked by walls or blocks (which return HTTP 200 OK as a no-op) or blocked downwards (which lock, clear, and spawn under HTTP 200 OK).
- Set `active_piece` to `null` immediately under `"game_over"` status (especially due to obstructed spawns) to avoid rendering illegal overlapping active cells on the client.
- Test 3-row and 4-row clears without implementing piece rotation by placing canonical O pieces at origin `(15,4)` and `(14,4)` above precompleted bottom rows (N=3 and N=4). Preserve all 13 original Stage 1 tests.

**Never:**
- Implement piece rotation, wall kicks, T-Spins, ghost piece previews, local high scores, user persistence, or databases in this stage.
- Permit double-hold swaps within the same piece lifecycle (hold remains locked/disabled until that piece locks).
- Allow automatic gravity ticks to execute while manual movement requests or holds are still processing in the client-side FIFO mutation queue.
- Let old, obsolete, or falsy rejected API callbacks mutate the frontend state or trigger timers after the session has been restarted.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Restart / Fresh Start | POST `/api/games` | Returns 201 Created. `score`=0, `total_lines`=0, `level`=1, `gravity_interval_ms`=500, `hold_piece`=null, `can_hold`=true. `active_piece` spawned, `next_piece` drawn (exactly 2 RNG draws). | — |
| State Read Peek | GET `/api/games/{id}` | Returns 200 OK with unified state payload. Does NOT consume next preview or perform any RNG draws (0 draws). | Returns 404 if missing ID |
| Left/Right Move Collision | POST `/api/games/{id}/move` (left) next to col 0 | Returns 200 OK. Active piece stays in place (no-op). Payload is unmodified state with 0 draws. | Returns 404 if missing ID; 422 if invalid direction |
| Downward Lock & Score (Single Row Clear) | POST `/api/games/{id}/tick` on row 19 (1 row cleared), Level 1 | Returns 200 OK. Score increases by 100 points ($100 \times 1$). Level recalculated as 1. `gravity_interval_ms` remains 500. Next preview consumed for spawn, new preview drawn (exactly 1 draw). | Returns 404 if missing ID |
| Empty Hold Swap | POST `/api/games/{id}/hold`, Empty Hold, `active_piece`="O", `next_piece`="I" | Returns 200 OK. `"O"` stored in `hold_piece`, `"I"` spawned as active at origin, `can_hold` set to `false`. Exactly 1 new preview drawn. | Returns 404 if missing ID |
| Occupied Hold Swap | POST `/api/games/{id}/hold`, Occupied Hold="I", `active_piece`="O", `next_piece`="S" | Returns 200 OK. `"O"` stored in `hold_piece`, `"I"` spawned as active, `next_piece` remains `"S"` unchanged. Exactly zero (0) RNG draws. | Returns 404 if missing ID |
| Rejected Hold (Cooldown Active) | POST `/api/games/{id}/hold`, `can_hold` is `false` | Returns 200 OK with unchanged state unmodified. Performs exactly zero (0) RNG draws. | Returns 404 if missing ID |
| Obstructed Hold Re-entry Game Over | POST `/api/games/{id}/hold`, held="J", board blocked at spawn origin | Returns 200 OK. Status transitions to `"game_over"`. `active_piece` set to `null` to avoid overlapping blocks. | Returns 404 if missing ID |
| Terminal Action Lockout | Any action after game_over | Returns 200 OK with unchanged terminal state unmodified. Performs exactly zero (0) RNG draws. | Returns 404 if missing ID |

</frozen-after-approval>

## Open Questions

*None.*

## Code Map

- `backend/app/main.py` -- FastAPI router endpoints including the new `/hold` endpoint, CORS settings, UUID session maps.
- `backend/app/core/domain.py` -- Authoritative game engine: `GameState` structures, progression (scoring formulas, level thresholds, gravity calculations), RNG draw accounting, spawn rules, and hold-swap logic.
- `backend/app/tests/test_domain.py` -- Backend Pytest unit test suite containing progression multipliers, RNG draw validation, obstructed spawns, and non-rotational N=3/N=4 completed row clears.
- `frontend/src/App.tsx` -- Thin React controller: sidebar HUD UI elements, FIFO queue, strict-mode unique generation IDs, immediate automatic timer cancellations, and restart queue preemptions.
- `frontend/src/styles.css` -- Neon CSS visual specifications with distinct custom styling for HUD sidebars, previews, and holds.

## Tasks & Acceptance

**Execution:**
- [ ] `backend/app/core/domain.py` -- Extend GameState model with the 7 Stage 2 fields, implement Multi-Line Scoring (FR-35), Level Calculation (FR-32), Progressive Gravity (FR-33), and Hold/Swap (FR-40, FR-41, FR-42, FR-43). -- Guarantees backend is the sole authoritative state machine.
- [ ] `backend/app/main.py` -- Integrate `POST /api/games/{id}/hold` endpoint and ensure all endpoints return the unified 11-field schema and match the correct HTTP status codes (FR-38, FR-44). -- Exposes stable, compatible API contracts.
- [ ] `backend/app/tests/test_domain.py` -- Add automated unit tests verifying progression multipliers, strict RNG counts, obstructed spawn game-overs, and the non-rotational O-piece N=3 and N=4 clear fixtures (AD-13). -- Confirms technical integrity and prevents regressions.
- [ ] `frontend/src/App.tsx` -- Implement sidebar layout panels (score, lines, level, hold, next), C-key and Hold button listeners, the FIFO mutation queue, and strict generation checking (FR-34, AD-9, AD-10, AD-11). -- Ensures lag-free, strict-mode safe, sequential synchronization.
- [ ] `frontend/src/styles.css` -- Style HUD sidebar panels, disabled hold button visuals, and clear board cells. -- Delivers highly polished, readable aesthetic interfaces.

**Acceptance Criteria:**
- Given a running game session, when manual shifts or automatic ticks occur, then all 7 progression and queue fields persist correctly without resetting to defaults.
- Given a completed-row clearance, when points are calculated, then the score is added using the pre-lock level multiplier first, before updating levels and gravity speeds.
- Given a client mutation in-flight, when the player hits "Restart", then the old queue is completely bypassed/replaced, active timers are cleared, and a fresh lifecycle begins immediately without waiting for old responses.
- Given a game-over spawn obstruction, when state is returned, then `active_piece` is set to `null` to bypass overlapping cells in frontend rendering.

## Implementation Notes

## Spec Change Log

- **BMAD-QA-01 Quality Closure (Build 07)**:
  - Resolved Python S3776 (cognitive complexity in `move_piece` in `backend/app/core/domain.py`) by extracting downward locking and spawning logic into private helper `_lock_and_spawn_piece`, reducing nesting and lowering cognitive complexity below 15.
  - Resolved TypeScript S6759 by declaring `MiniGrid` props parameter as readonly.
  - Resolved TypeScript S4624 by replacing the nested template literal inside `MiniGrid` cells loop with a simple local `cellClass` variable.
  - Resolved TypeScript S6582 by converting logical checks on `currentGame` and `g` into clean optional chaining expressions across lines 104, 114, and 325 in `frontend/src/App.tsx`.
- **BMAD-QA-01 Regression and Remediation**:
  - Identified frontend queue ownership defect where stale callbacks or obsolete early branches inside `enqueueAction` decremented `pendingCountRef.current`, leading to negative queue counts (`-1`) and preventing gravity from resuming. Corrected `enqueueAction` to ensure that `pendingCountRef.current` is only decremented and timers rescheduled when the captured execution generation matches the active session generation.
  - Aligned Stage 2 backend RNG tests to use a canonical four-cell O piece at row 18 (origin 18,4) instead of a fake one-cell active piece, keeping original 13 tests intact and preserving original assertions.
  - Patched frontend npm package versions to resolve 2 dependency audit vulnerabilities, enabling a clean `npm ci` without any `legacy-peer-deps` or forced overrides.
  - Upgraded backend dependency `fastapi` to `0.162.0` (which installs `starlette==1.10.0`), `pytest` to `9.1.1`, and `certifi` to `>=2026.10.23` in `backend/requirements.txt` to completely resolve PyPI package audit security findings.
  - Updated the backend virtual environment packages and upgraded pip to resolve all local python venv audit warnings.
  - Created a custom `.coveragerc` file in the backend directory to correctly generate production-only coverage XML for Sonar scanner without test pollution.
  - Resolved Sonar code smells and testing issues in `frontend/src/App.test.tsx` by eliminating redundant `act()` wrappers around Testing Library interactions and adding explicit assertions to all test cases, ensuring 0 new Sonar violations.

## Review Triage Log

- **high** — Frontend queue ownership defect: stale callbacks or obsolete early branches corrupting `pendingCountRef.current` of new sessions, causing gravity timer failure. Resolved via strict generation checking on all queue decrements and terminations.
- **medium** — Backend RNG test fake-piece anomaly: Stage 2 RNG tests used a non-canonical one-cell piece, violating canonical fixture requirements. Resolved by substituting a canonical four-cell O piece.
- **low** — Frontend package vulnerabilities: Vite/Vitest devDependencies had minor audit issues. Resolved by upgrading to secure, compatible versions under React 18 and node actual peer constraints.

## Design Notes

### Non-Rotational 3/4 Row Clear Setup
The tests precomplete specific rows (17,18,19 for N=3; 16,17,18,19 for N=4) with columns `0..9` filled. Spawning an `"O"` piece at its canonical templates origin and letting it drop via down ticks causes a lock and simultaneous row clears without implementing rotation.

### React StrictMode and generation token
```typescript
let currentGen = useRef(0);
// After every fetch, we confirm:
if (fetchGen !== currentGen.current) return; // discard obsolete double run
```

## Verification

**Commands:**
- `pytest backend/app/tests/` -- expected: SUCCESS
- `npm run build` inside `frontend/` -- expected: SUCCESS
