# Implementation Plan

- [ ] 1. Scaffold backend project structure
  - Create `backend/` with `app/`, `app/domain/`, `app/rules/`, `app/api/`, and `tests/` packages
  - Add `requirements.txt` with FastAPI, Uvicorn, Pydantic, and pytest (with httpx for TestClient)
  - _Requirements: 27, 28_

- [ ] 2. Implement domain models
  - Define `PieceType`, `Status`, `ActivePiece`, and `Game` dataclasses in `app/domain/models.py`
  - Board is a 20x10 grid of optional piece types
  - _Requirements: 1, 6, 25_

- [ ] 3. Implement tetromino definitions and seeded generator
  - Add `SHAPES`, `SPAWN_ROW`, `SPAWN_COLUMN` in `app/rules/pieces.py`
  - Implement a seeded 7-bag `PieceGenerator` for determinism and full coverage
  - _Requirements: 3, 4, 5_

- [ ] 4. Implement core rule helpers
  - Implement `_absolute_cells` and `_is_valid` (bounds + stack overlap) in `app/rules/engine.py`
  - _Requirements: 12, 13, 14, 15_

- [ ] 5. Implement spawn and new_game
  - Implement `spawn` (game-over on spawn overlap) and `new_game` (empty board, first spawn)
  - _Requirements: 2, 5, 17, 22, 24_

- [ ] 6. Implement move handling
  - Implement `move` for `left`, `right`, `down`; reject illegal horizontal moves; lock on blocked soft drop
  - _Requirements: 9, 10, 11, 12, 13_

- [ ] 7. Implement gravity tick and locking
  - Implement `tick` (move down or lock) and `lock` (settle cells, clear lines, spawn)
  - _Requirements: 8, 11, 16, 17_

- [ ] 8. Implement line clearing
  - Implement `clear_lines` removing full rows, shifting down, inserting empty rows at top; single and multi-line
  - Ensure clearing occurs before spawn
  - _Requirements: 18, 19, 20, 21_

- [ ] 9. Implement game-over handling
  - Set status `game_over` and clear active piece when spawn overlaps; make tick/move no-ops afterward
  - _Requirements: 22, 23_

- [ ] 10. Implement in-memory store
  - Implement `store.py` with `create(seed)` (uuid id) and `get(id)`
  - _Requirements: 2, 27_

- [ ] 11. Implement API schemas and serialization
  - Define `MoveRequest`, `ActivePieceOut`, `GameStateOut`; map board to integer codes; letter type on active piece
  - _Requirements: 6, 25, 26_

- [ ] 12. Implement HTTP controllers and app wiring
  - Implement `api/games.py` router with the four endpoints and 404 handling; wire `app/main.py` with CORS
  - _Requirements: 2, 7, 8, 9, 10, 11, 26, 28_

- [ ] 13. Write backend rule tests
  - Cover board size, spawn, determinism, moves, collisions, locking, clears, ordering, game over
  - _Requirements: 1, 3, 4, 5, 9-22_

- [ ] 14. Write backend API tests
  - Cover creation, read, 404, 422, and payload shape via FastAPI TestClient
  - _Requirements: 2, 7, 25, 26_

- [ ] 15. Run backend tests
  - Execute `pytest` and ensure all pass
  - _Requirements: 35_

- [ ] 16. Scaffold frontend project
  - Create `frontend/` Vite React + TypeScript project with `package.json`, `tsconfig`, `index.html`
  - _Requirements: 29, 35_

- [ ] 17. Implement API client and types
  - Implement `src/types.ts` and `src/api.ts` for the four endpoints
  - _Requirements: 29_

- [ ] 18. Implement game hook with 500ms gravity
  - Implement `src/useGame.ts` with a 500 ms tick interval while playing, stopping on game over; expose `move` and `restart`
  - _Requirements: 30, 31, 32_

- [ ] 19. Implement board rendering
  - Implement `src/Board.tsx` rendering the 20x10 grid and overlaying active piece cells; no local rule logic
  - _Requirements: 29_

- [ ] 20. Implement app shell, controls, and messages
  - Implement `src/App.tsx` with keyboard controls, Restart button, English labels, and game-over message
  - _Requirements: 31, 32, 33, 34_

- [ ] 21. Run frontend build
  - Execute `npm run build` and ensure it completes without errors
  - _Requirements: 35_

- [ ] 22. Document run and test commands
  - Add README files documenting install, run, test, and build commands and the fixed seed
  - _Requirements: 35_
