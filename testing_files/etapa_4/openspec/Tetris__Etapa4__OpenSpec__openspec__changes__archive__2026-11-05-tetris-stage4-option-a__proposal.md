# Proposal

## Why

This change extends the existing single-player Tetris game into Stage 4 Option A as a brownfield change. It introduces active piece rotation (Milestone 1), replaces the React DOM cell board with an HTML5 Canvas 2D component for rendering optimization (Milestone 2), and delivers a synchronized real-time two-player duel mode using FastAPI WebSockets and in-memory game rooms (Milestone 3). These changes are designed to provide a competitive, same-origin real-time multiplayer experience, consolidate rendering under a single canvas element, and maintain standard game mechanical integrity.

## What Changes

- **Active Piece Rotation (Milestone 1)**:
  - Add support for clockwise (ArrowUp) and counterclockwise (Z) 90-degree rotations in the authoritative Python engine.
  - Define deterministic pivots, four orientations, and unobstructed four-turn closure with the exact occupied cells specified for each piece. Spawning or retrieving from Hold spawns pieces in orientation 0.
  - Implement wall-kick retry logic with horizontal-only offsets in the priority order `0, -1, +1, -2, +2` relative to the piece's col position, without vertical kicks.
  - Ensure rotation does not advance gravity, trigger locks, alter counters, or affect next/held piece states.
  - Expose rotation actions via the existing backend API `/api/games/{game_id}/move` direction conventions (`"clockwise"` and `"counterclockwise"`).
  - Fully integrate ArrowUp (clockwise) and Z (counterclockwise) keyboard controls into the single-player UI during Milestone 1, retaining the React DOM-based board rendering until Milestone 2.
  - Implement robust unit, input, and integration tests for engine and keyboard controls in Milestone 1.

- **Canvas 2D Rendering (Milestone 2)**:
  - Replace the DOM-based board grid with an HTML5 Canvas 2D rendering board.
  - Draw occupied/settled cells and the active piece from the authoritative backend game state.
  - Implement scaling for device pixel ratio to maintain crisp block edges.
  - Retain the existing keyboard controls, score, level, lines, Hold, preview panel, leaderboard, game status modals, and stale-response protection.
  - Document and replace any DOM-based test assertions with appropriate state-level validation and Canvas mock tests.

- **Two-Player Duel via WebSockets (Milestone 3)**:
  - Implement a real-time two-player matchmaking and dueling room system using FastAPI WebSockets.
  - Require two players to join a room before a duel begins, enforcing a shared, deterministically generated piece sequence using a shared room seed.
  - Drive independent game progression for both players via server-managed gravity updates, independent of browser-side timers.
  - Define versioned, bounded JSON WebSocket messaging schemas with strict maximum UTF-8 frame, room count, and client connection limits.
  - Restrict player input ownership so a player can only affect their assigned seat/board.
  - Implement same-origin handshake validation, monotonic action sequence checks, and generation gates for stale input protection.
  - Group board tick evaluations under a room lock to support concurrent same-update draw and outcome resolution.
  - Cleanly cancel gravity tasks and WebSockets on client disconnects, server shutdown, or room inactivity.
  - Maintain an inactivity-based room sweeper that guarantees room release within 5 minutes of finalization or inactivity.
  - Keep duel data fully isolated from the solo SQLite leaderboard.

## Capabilities

### New Capabilities
- `duel`: Comprehensive specification covering the real-time two-player WebSocket communication model, same-origin validation, matchmaking/room state lifecycle, server-driven independent gravity, synchronized piece sequencing, seat authorization boundaries, duplicate/stale action protection, and game forfeit/draw outcomes.

### Modified Capabilities
- `tetris-core`: Extend core game mechanics to support clockwise and counterclockwise active piece rotation rules, spawning orientation, wall kick column sequences, and transition the board's frontend rendering contract from direct React DOM cell elements to an HTML5 Canvas 2D drawing implementation.

## Impact

- **Backend**:
  - `backend/models.py` will have `ActivePiece` and `GameState` extended with an `orientation` field, and new schemas for WebSocket message envelopes with strict validation and no extra fields.
  - `backend/engine.py` will contain the deterministic four-orientation coordinates for each tetromino type, and rotation engine methods applying horizontal-only kicks.
  - `backend/main.py` will support `"clockwise"` and `"counterclockwise"` move actions, alongside the new WebSockets endpoint `/api/ws/duel/{room_id}` and in-memory room management.
- **Frontend**:
  - `frontend/src/components/GridBoard.tsx` will be replaced with a Canvas-based rendering board with responsive size calculations and high-DPI scale adjustment.
  - `frontend/src/App.tsx` and custom hooks will incorporate keyboard event listeners for `Z` and `ArrowUp` (integrated during Milestone 1), support for WebSocket rooms, real-time matchmaking UI, duel status notifications, and simultaneous side-by-side rendering of the local board and opponent board.
- **Infrastructure & Tests**:
  - Unit tests in `backend/` and `frontend/` will be added to verify rotation offsets, canvas sizing, and Websocket message schema handling.
  - `docker-compose.yml` will run as a non-root isolated network with an internal backend (no host port exposure), exposing ONLY the production reverse proxy port (`5183`), mapping a persistent volume for SQLite, and proxying WebSocket upgrades correctly.
