# Implementation Plan: Tetris Stage 4 Option A - Rotation, Canvas 2D Board, and Real-Time WebSockets Duel

**Branch**: `004-tetris-stage4-option-a` | **Date**: Tuesday, November 3, 2026 | **Spec**: [specs/004-tetris-stage4-option-a/spec.md](spec.md)

## Summary
The goal of Stage 4 Option A is to expand the existing Tetris application to include deterministic 90-degree tetromino rotation with a custom wall-kick mechanism in the authoritative backend engine, replace the front-end DOM cell-grid with a high-performance Canvas 2D board, and add a same-origin real-time two-player WebSocket-based duel mode. 

The implementation will be completed as a brownfield change under the directory `specs/004-tetris-stage4-option-a/` while preserving Stage 3 code and behaviors. The three key milestones (Rotation, Canvas, Duel) will be developed and verified sequentially.

## Technical Context

**Language/Version**: Python 3.11 (inherited CI and containers baseline) / Python 3.12.4 (independent Windows verification runtime), TypeScript 5.0+ / React 18+ / Node 24 (Vite frontend)

**Primary Dependencies**: 
- Backend: `fastapi`, `uvicorn`, `pydantic` v2, `sqlite3`, `websockets==12.0` (pinned WebSocket library compatible with our ASGI server)
- Frontend: `react`, `react-dom`, `typescript`, `vite`

**Storage**: SQLite database (using standard `sqlite3` module) for persistent solo high scores, configured via the `TETRIS_DB_PATH` environment variable. Duel results do not write to SQLite.

**Testing**: 
- Backend: `pytest` (standard unit tests), `asyncio` for controlled event loops (using FastAPI's `TestClient` or standard `asyncio` mock loops; no additional `pytest-asyncio` is proposed since existing TestClient and controlled asyncio suffice)
- Frontend: `vitest` / React Testing Library, Playwright Chromium for browser benchmarking and integration test flows

**Target Platform**: Docker / Linux Container (non-root execution), compatible with standard modern web browsers supporting HTML5 Canvas 2D and WebSocket APIs.

**Project Type**: Containerized Full-stack Web Application (Web service backend + React Single-Page Application frontend)

**Performance Goals [PERF-01]**:
- High frame-scheduling rates with scheduling-only targets of mean scheduling rate >= 55 FPS and p95 interval <= 25 ms across 3x30-second trials.
- Sharp, crystal-clear visual scaling using Device Pixel Ratio (DPR) calculation.
- Low-overhead memory-safe room and event-loop cleanup for duels.

**Constraints [INF-01]**:
- Same-origin reverse proxy (Nginx container routing `/api` and `/api/duel/ws` to backend, static files for frontend).
- Single-worker backend FastAPI process with thread-safe in-memory room storage.
- Standard REST API body validations (strict extra forbidden keys, empty body allowed on create).

**Scale/Scope [NET-01, NET-02, NET-03]**: 
- Max 2 players per duel room.
- 5-minute bounded room retention policy.
- Bounded 1KB WebSocket payloads.
- Maximum server capacity limit of 100 concurrent active rooms.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Rule | Status | Justification / Notes |
|------------------|--------|-----------------------|
| 1. Authoritative Backend | PASS | All rotation, movements, gravity, score, and state transitions are computed authoritatively on the server. |
| 2. Strictly Preserved Behavior | PASS | Stage 1-3 features (soft-drop, blocked manual down no-op, SQLite schema, leaderboards) are perfectly retained. |
| 3. High-DPI Canvas Rendering | PASS | Completely replaces React DOM cell board with high-DPI Canvas 2D using device pixel ratio. |
| 4. WebSocket Security & Isolation | PASS | Employs same-origin WS checks, room boundaries, seat ownership validation, and bounded payloads. |
| 5. Three Independent Milestones | PASS | Phase-specific verification gates, snapshots, and execution order (Rotation -> Canvas -> Duel) strictly followed. |

## Project Structure

### Documentation (this feature)

```text
specs/004-tetris-stage4-option-a/
├── plan.md              # This file
├── research.md          # Technical specifications and decisions
├── data-model.md        # Extended entity mappings and attributes
├── quickstart.md        # Verification scripts, guidelines, and procedures
├── contracts/           # API and WS schemas
│   ├── api-contract.md  # Extended HTTP REST contract
│   └── ws-contract.md   # Versioned WebSocket contract and sequence rules
└── checklists/
    └── requirements.md  # Verification and checklist requirements
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                    # App entry point, mounting WS endpoints and CORS/Origin rules
│   ├── api/
│   │   ├── endpoints.py           # Solo API REST endpoints and WS connections
│   │   └── ws_duel.py             # Duel WebSocket router, connection manager, and state sync
│   ├── models/
│   │   └── schemas.py             # REST schemas and versioned WS message models
│   └── services/
│       ├── database.py            # SQLite score storage and finalization retry logic
│       ├── game_engine.py         # Authoritative engine (updated with 90-deg rotation & kick offsets)
│       └── duel_manager.py        # In-memory room manager, server gravity loops, and cleanup timers
└── tests/
    ├── unit/
    │   ├── test_game_engine_us1.py  # Rotation unit tests
    │   └── test_duel_manager.py     # Duel state, validation, and seat ownership tests
    └── integration/
        └── test_api_ws.py           # WebSocket connection, handshake origin, and malformed messages

frontend/
├── src/
│   ├── components/
│   │   ├── Board.tsx              # Replaced with Canvas 2D drawing + DPR logic
│   │   ├── DuelBoard.tsx          # Side-by-side Canvas boards for duel mode
│   │   └── GameControls.tsx       # Standard and WS Controls
│   ├── hooks/
│   │   ├── useGame.ts             # Solo game loop controller
│   │   └── useDuel.ts             # WS-driven duel room connector and action emitter
│   └── types.ts                   # Frontend types (matching backend absolute cells)
└── tests/
    ├── App.test.tsx               # Decommissioned div.cell and grid selectors, asserting canvas element
    └── performance-benchmark.ts   # Six-trial Playwright protocol with frozen seed and raw distribution capture
```

**Structure Decision**: Option 2: Web application (existing frontend and backend structure) is retained. Code changes are confined strictly to Stage 4 requirements as a brownfield extension.

## Complexity Tracking

*No violations of the core principles exist. Complete alignment with requirements is maintained.*

---

## 5. Workflow Findings and Repair Strategy

The following architectural and implementation strategies will be followed to resolve the 8 recorded defects:

1. **Terminal Atomicity**: We will decommission per-seat gravity tasks and the 10ms grace window. Instead, we will implement a centralized room scheduler using an event-loop run loop or centralized callback tracking independent per-seat due times. During each tick/update, we will batch and process all due seats before running the outcome evaluation logic. Single/individual terminal actions will immediately decide the winner (e.g., if Player 1 tops out, Player 2 wins instantly). A same-batch double top-out will evaluate as a Draw. This ensures deterministic terminal atomicity and cleans up room tasks safely.
2. **Continued Sequence**: We will enhance the room's sequence generation logic. If a client attempts to retrieve a piece beyond the current pre-generated sequence length (e.g., `next_piece_index >= len(piece_sequence)`), the sequence will be deterministically extended on-demand (e.g., using a random-seeded generator or by appending/repeating batches) to ensure infinite uninterrupted play with equal piece order.
3. **Waiting Disconnect**: We will monitor connection state. If the sole waiting player disconnects from the room before a second player joins, the room will be immediately released, and all associated resources cleaned up. Bounded terminal retention (keeping finished rooms for up to 5 minutes) and active disconnect forfeit will be preserved. No background tasks will be spawned during Python module imports.
4. **Frontend Stale Protection**: In the frontend React app and Canvas hooks, we will generate a unique session/socket identity upon WebSocket connection. Each message callback will be guarded to check if it originates from the current active socket session. The client will also enforce monotonic increasing state revision checks (`payload.revision > last_revision`) and reset room states cleanly on fresh-room triggers to discard stale or late frames.
5. **Contract Synchronization**: We will update the `ws-contract.md` to use `status` instead of `room_status` in the JSON payload schemas and examples to align with the canonical server/frontend implementation.
6. **Strict Payload Validation**: We will implement a robust input validation filter on the server.
   - Restrict incoming payloads to a maximum of 1024 UTF-8 bytes.
   - Enforce schema validation to reject any unknown properties in the JSON envelope or payloads.
   - Prevent injection of client-controlled values (scores, boards, seats, or player IDs).
   - Reject invalid types (such as boolean values inside integer fields), out-of-safe-range values for sequence/generation, and malformed actions.
   - Explicitly validate the browser's `Origin` header against the allowlist during the upgrade handshake.
7. **Serialization and Delivery**: We will ensure that every state update broadcast explicitly preserves the seat, action sequence number, active piece generation, and state revision number. Orderly serialization will prevent racing between user action broadcasts and gravity-driven updates.
8. **Production Isolation**: We will remove the fixed volume name `db-data` (or similar historical names) from `docker-compose.yml` to let Compose create a project-scoped volume. We will retain default frontend port 5183, backend internal port, and 1 FastAPI worker process.

