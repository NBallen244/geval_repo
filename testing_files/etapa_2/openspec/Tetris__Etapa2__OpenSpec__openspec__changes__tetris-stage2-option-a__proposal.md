# Proposal

## Why

This change transitions the application from a greenfield Stage 1 prototype to a polished, high-progression Stage 2 (Option A) research application. It introduces scoring, leveling, progressive gravity, next-piece previews, and a hold mechanic to provide the gameplay depth and instrumentation required for higher-signal gameplay study, while retaining state authority on the backend.

## What Changes

- **Expanded Game State:** The backend state response now exposes score, total cleared lines, active game level, dynamic gravity interval, next piece queue, hold slot piece, and hold action availability.
- **Score System:** Introduces game scoring based on number of simultaneously cleared lines and the level immediately before the clear.
- **Progression System:** Level updates dynamically for every 10 lines cleared, progressively reducing the gravity interval.
- **Next Piece Queue:** Spawns pull from the queued piece, and players can preview it in the UI. Peeking at state does not consume the queued piece.
- **Hold Mechanic:** Players can hold one active piece per turn and swap it back later. Swapping re-enters the piece at spawning coordinates.
- **Dynamic Gravity Tick:** Frontend dynamically reschedules gravity timers from backend-returned timing payload.
- **Stale Response Protection:** Frontend ignores out-of-order API responses to maintain robust state rendering.

## Capabilities

### New Capabilities

<!-- None -->

### Modified Capabilities

- `tetris-core`: Update backend state structure and modify game-loop logic to incorporate score, total lines, levels, progressive gravity, next-piece previews, and a hold piece mechanic.

## Impact

- **Backend:** Models updated in `backend/models.py`; session initialization and game mechanics updated in `backend/engine.py`; API controllers and router endpoints modified in `backend/main.py` (including a new `POST /api/games/{id}/hold` endpoint).
- **Frontend:** API interfaces updated in `frontend/src/api.ts`; rendering panels and controls updated in `frontend/src/App.tsx` and `frontend/src/components/GridBoard.tsx`.
- **API and Contracts:** Incorporates hold actions and returns seven new metadata fields for game state.
