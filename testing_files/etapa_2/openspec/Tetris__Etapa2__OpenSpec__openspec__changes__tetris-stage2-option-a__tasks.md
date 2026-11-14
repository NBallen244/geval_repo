# Tasks

## 1. Backend State Models & Engine Updates

- [x] 1.1 Upgrade Pydantic data models in `backend/models.py` with `score`, `total_lines`, `level`, `gravity_interval_ms`, `next_piece`, `hold_piece`, and `can_hold`. Verify by running Pydantic class parsing on `GameState` in python and ensuring no validation errors are raised.
- [x] 1.2 Implement the initialization of Stage 2 state metrics in the `GameSession` constructor inside `backend/engine.py`. Verify by running python unit tests that initialize a new session and inspect starting values.
- [x] 1.3 Implement piece-locking scoring logic, line accumulation, dynamic level progression, and progressive gravity interval calculations in `backend/engine.py`. Verify by running engine level calculation assertions in unit tests.
- [x] 1.4 Refactor piece spawning to pull the next piece from the queue and generate a new random piece in `backend/engine.py`. Verify by checking spawn sequence lists in unit tests.
- [x] 1.5 Implement hold/swap transitions (`hold` method) including empty vs occupied holds, spawn centers, coordinate validation, and overlap game-overs. Verify by testing swap behaviors and game over status triggers in unit tests.

## 2. API Endpoints & Backend Verification

- [x] 2.1 Implement the `/api/games/{id}/hold` POST endpoint in `backend/main.py`. Verify by triggering mock request and asserting correct schema response.
- [x] 2.2 Preserve the existing restart flow through POST `/api/games`, which creates a new session. Verify that the new session has a different ID and resets all Stage 2 counters and the Hold slot.
- [x] 2.3 Write complete unit tests in `backend/test_engine.py` using `pytest` verifying scoring rules (including 4-row control scenario), levels, gravity timers, hold operations, peeks, and restarts. Verify by running `pytest` on backend.

## 3. Frontend Client & Timing Guard

- [x] 3.1 Update TypeScript interfaces in `frontend/src/api.ts` to include the seven new state fields, and implement the `holdGame` service. Verify by compiling `api.ts` without errors.
- [x] 3.2 Refactor the gravity tick hook in `frontend/src/App.tsx` to dynamically clear and reschedule timers whenever `gravity_interval_ms` changes. Verify by observing the interval before and after a controlled level change.
- [x] 3.3 Add request sequence tracking (`requestId` ref) to protect against out-of-order responses reversing visible state in `frontend/src/App.tsx`. Verify with delayed/reordered responses that visible state is not rolled back.

## 4. Frontend UI Panel & Controls

- [x] 4.1 Bind the "C" keydown and a clickable "Hold" button to dispatch `holdGame` calls in `frontend/src/App.tsx`. Verify both input paths in the browser.
- [x] 4.2 Render score, level, lines, next preview, and hold preview in `frontend/src/components/GridBoard.tsx`. Verify by visual inspection in browser that elements exist and reflect state.
- [x] 4.3 Add visual cooldown indicators (such as grayscale styling) on the hold preview whenever `can_hold` is false in `frontend/src/components/GridBoard.tsx`. Verify by triggering Hold in the browser and checking the disabled control and visible cooldown.

## 5. Integration Validation

- [x] 5.1 Run full integration manual checks (restart resets counters, clearing lines increments score/level, hold swaps accurately, overlapping spawns trigger game over). Record which scenarios are browser-observed and which use controlled domain fixtures.
- [x] 5.2 Build the React frontend production bundle using `npm run build` inside `frontend/` and verify that the build completes with zero lint errors or type compilation warnings.

## 6. SonarQube Quality Follow-up

- [x] 6.1 Replace tetromino selection through `random.choice` with equivalent `secrets.choice` calls, then verify score, preview, and Hold behavior is unchanged. Resolve all `python:S2245` findings.
- [x] 6.2 Reduce FastAPI code smells by centralizing repeated error text and documenting 400/404 responses on routes that raise them.
- [x] 6.3 Resolve frontend SonarQube code smells, including contrast, stable list keys, readonly props, simple optional chains, and nested template literals, without changing controls or rules.
- [x] 6.4 Re-run backend tests with application-only coverage, frontend production build, external acceptance checks, and the same SonarQube project. Retain both scan reports and record the final findings.
- [x] 6.5 Verify the frontend timer and stale-response behavior using controlled client tests; produce frontend coverage in LCOV format for SonarQube and retain the raw test output.
