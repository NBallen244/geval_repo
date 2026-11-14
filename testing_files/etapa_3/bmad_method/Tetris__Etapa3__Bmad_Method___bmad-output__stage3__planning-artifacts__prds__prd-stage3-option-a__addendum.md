---
title: "PRD Addendum: Stage 3 Technical Contracts & Strategy"
status: final
created: 2026-11-02T12:17
updated: 2026-11-02T12:17
---

# PRD Addendum: Stage 3 Technical Contracts & Strategy

This addendum details the database schema, security validations, error-handling retry flow, Docker configurations, performance-benchmarking setup, and CI/CD workflow configurations.

---

## 1. Database Schema & Persistence Contract

### SQLite Table Schema
The high score persistence system uses a single SQLite database table initialized automatically upon backend service startup:

```sql
CREATE TABLE IF NOT EXISTS high_scores (
    game_id TEXT PRIMARY KEY NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0),
    total_lines INTEGER NOT NULL CHECK (total_lines >= 0),
    level INTEGER NOT NULL CHECK (level >= 1),
    completed_at TEXT NOT NULL -- Store as ISO-8601 UTC string (YYYY-MM-DDTHH:MM:SSZ)
);

CREATE INDEX IF NOT EXISTS idx_high_scores_sort ON high_scores (score DESC, completed_at ASC, game_id ASC);
```

### Uniqueness and Idempotency Constraint
- A uniqueness constraint on `game_id` is enforced by the `PRIMARY KEY` field.
- Parameterized SQLite writes must be executed within an atomic transaction.
- If finalization is triggered multiple times for the same game ID, the SQL query must use a conflict-resolution strategy that ignores or avoids rewriting (or alternatively raises an integrity error which is caught and returned as 200 OK with the already-saved state to ensure idempotency).
- Mutating and finalization endpoints must run under a process-wide lock.

---

## 2. Updated API Contracts

### GET /api/high-scores
Returns the top 10 scores from the database.

- **Request:** `GET /api/high-scores`
- **Response (200 OK):**
```json
{
  "scores": [
    {
      "game_id": "8432a51e-6240-4d4b-9705-eb8bfa79f067",
      "score": 1200,
      "total_lines": 12,
      "level": 2,
      "completed_at": "2026-11-02T10:15:30Z"
    },
    ... (at most ten entries, sorted by score DESC, then completed_at ASC, then game_id ASC)
  ]
}
```
- **Error Response (503 Service Unavailable):**
If database lookup fails, the API must respond with a controlled error object:
```json
{
  "detail": "High score storage temporarily unavailable"
}
```

### Strict Body Validation
1. **Game Creation (`POST /api/games`):**
   - Validates that extra fields in the JSON body are completely rejected. If an incoming payload contains parameters (e.g. `{"random_field": 123}`), return `422 Unprocessable Entity`. Bodyless creation (`POST` with empty body) remains fully valid.
2. **Move Piece (`POST /api/games/{id}/move`):**
   - Extra fields in the movement body (e.g. `{"direction": "left", "extra": "field"}`) must be strictly rejected with `422 Unprocessable Entity`.
3. **Tick (`POST /api/games/{id}/tick`) and Hold (`POST /api/games/{id}/hold`):**
   - Must reject extra body parameters or non-matching fields.

---

## 3. Concurrency Protection & Thread-Safe RLock
Because the backend runs on FastAPI using `def` sync handlers that execute within concurrent worker threads of a threadpool, we enforce a process-wide reentrant lock (`threading.RLock()`) to synchronize all game sessions registry creations, lookups, state mutations, SQLite database finalization, and detached responses. This ensures complete thread safety.

### Lock Execution Lifecycle:
1. Every request (both mutating requests like ticks, moves, and holds, and read-only requests like GET game state or leaderboard) must acquire the shared `threading.RLock` before accessing or mutating the in-memory store or executing SQLite writes.
2. Under the lock:
   - Perform the registry lookup or creation.
   - Perform the move/tick/hold operation if mutating.
   - If the operation triggers a `"game_over"`, assign `completed_at` (exactly once, using a UTC ISO-8601 format) and execute the SQLite write transaction. This timestamp must be retained on any subsequent 503/retries; conflicts never overwrite original fields.
   - Set an internal flag on the in-memory game state: `persisted = True` (or `False` if the write fails).
3. If the database write fails:
   - Rollback the transaction.
   - Set `persisted = False`.
   - Release the lock.
   - Raise a standard 503 HTTPException (hiding stack traces and SQL details).
4. If the database write succeeds:
   - Release the lock.
   - Return the detached, consistent response.

### Persistence Failure Retry Flow
If the database was locked, full, or failed during startup/cleanup when the game ended, `persisted` is marked `False`.
- Any subsequent mutating request on that terminal game ID (such as gravity ticks or manual movement requests) will:
  1. Acquire the process `threading.RLock`.
  2. Inspect the terminal game's `persisted` flag.
  3. If `status == "game_over"` and `persisted == False`, retry the database insert transaction safely under the lock, preserving the original `completed_at` timestamp.
  4. If retry succeeds, mark `persisted = True`.
  5. Release lock and return `200 OK`.
- A `GET` request on the game state also acquires the lock for a consistent write-free snapshot, but never triggers any database write or retry.

---

## 4. Multi-Stage Docker Containerization

### Frontend Dockerfile Structure (Multi-stage)
1. **Build Stage:**
   - Node Alpine image.
   - Copy `package.json`, `tsconfig.json`, source files.
   - Run `npm ci --frozen-lockfile` (or matching lockfile setup).
   - Build production-ready HTML/JS/CSS assets via `npm run build`.
2. **Runtime Stage:**
   - Lean Alpine or Nginx container.
   - Create and switch to a non-root user (`node` or custom web user).
   - Copy compiled `dist` folder.
   - Reverse-proxy `/api` requests to the internal backend container port `8000` via Vite or Nginx proxy configuration.
   - Listen on port `5183` inside the container.

### Backend Dockerfile Structure (Multi-stage)
1. **Build Stage:**
   - Python Alpine/Slim image.
   - Install build tools if compilation is needed.
   - Install production dependencies.
2. **Runtime Stage:**
   - Lean Python Alpine/Slim image.
   - Create and switch to a non-root user (`appuser`).
   - Copy runtime dependencies and Python modules.
   - Expose internal port `8000`.
   - Launch FastAPI with exactly one worker via Uvicorn.

### Docker Compose Configuration
```yaml
version: "3.8"

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5183:5183" # Bind host port 5183 only
    depends_on:
      backend:
        condition: service_healthy
    environment:
      - VITE_API_BASE=/api
    user: "node"
    security_opt:
      - no-new-privileges:true

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    expose:
      - "8000" # Backend remains internal
    environment:
      - TETRIS_DB_PATH=/app/data/high-scores.sqlite3
      - CORS_ALLOWED_ORIGINS=http://localhost:5183
    volumes:
      - sqlite-data:/app/data
    user: "appuser"
    security_opt:
      - no-new-privileges:true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/high-scores"] # Or matching endpoint
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 5s

volumes:
  sqlite-data:
    name: tetris_sqlite_data
```

*Operational Guideline:* Running `docker compose down` will safely discard containers but retain the `sqlite-data` persistent volume. Do NOT use `docker compose down -v` as it destroys user data.

---

## 5. Playwright Performance Instrumentation Strategy

To measure the frame scheduling rate and rendering latency truthfully without inflating metrics:
- **Frame Recording:** The script injects an interval logger via `requestAnimationFrame` in the browser, storing raw timestamps in a window variable `window.__rAF_timestamps = []`.
- **Active Gameplay Simulation:** Playwright uses standard keyboard press commands (`page.keyboard.press('ArrowLeft')`, etc.) to trigger movements, ensuring the game board undergoes real DOM updates. No gravity/gravity ticks are modified, no pieces are rotated, and no Canvas/WebGL is introduced.
- **Measurement Window:** Only eligible positive intervals with BOTH endpoints inside the fixed 5000+30000ms window (i.e., t = 5,000ms to t = 35,000ms from script initialization) are analyzed.
- **Metrics Calculated:**
  - **Mean FPS:** Calculated strictly as `frame_count / 30.0` (not based on median interval).
  - **Frame Interval Median, p95, p99:** Analyzed from the differences `t[i] - t[i-1]` of the collected rAF timestamps.
  - **Action Latency:** Real raw DOM/keyboard/API/heuristic latency.
- **Validation Contexts & Logging:**
  - Tested across three independent browser contexts.
  - Returns unrounded FPS >= 55 and p95 <= 25ms in each context. Uses immutable whole unique batches with collision refusal.
  - Does not issue 60 API requests/s, forced FPS/gravity, or production animation loops. 60Hz is a reference, not physical-presentation proof. No heavy checks are run concurrently with timing.
  - Logs actual measured browser version, foreground/focus events, interval classifications, and captures traces/screenshots.

---

## 6. GitHub Actions Continuous Integration (CI)

```yaml
name: Continuous Integration

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt
      - name: Run Backend Tests & Coverage
        run: |
          pytest --cov=app backend/app/tests/ --cov-fail-under=80
      - name: Audit Backend Dependencies
        run: |
          pip install safety
          safety check -r backend/requirements.txt

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json
      - name: Install Dependencies
        run: |
          cd frontend
          npm ci
      - name: Run Frontend Tests
        run: |
          cd frontend
          npm run test
      - name: Verify Frontend Production Build
        run: |
          cd frontend
          npm run build
      - name: Audit Frontend Dependencies
        run: |
          cd frontend
          npm audit --audit-level=high

  docker-build:
    runs-on: ubuntu-latest
    needs: [backend-test, frontend-test]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Test Build Backend Image
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: false
      - name: Test Build Frontend Image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: false
```
