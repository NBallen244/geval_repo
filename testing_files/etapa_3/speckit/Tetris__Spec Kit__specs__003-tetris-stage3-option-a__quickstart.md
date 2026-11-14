# Quickstart Validation Guide: Tetris Stage 3 Persistent High Scores & Leaderboard

This document serves as the runnable verification guide for verifying all Stage 3 Option A features end-to-end, including local execution, testing, containerized Docker Compose setups, Playwright rendering performance benchmarking, and GHA workflows.

---

## 1. Prerequisites & Setup

Ensure the following runtimes and tools are installed on your workstation:
- **Python**: Major version `3.11`
- **Node.js**: Major version `24LTS` (and `npm` package manager)
- **Docker & Docker Compose**: Capable of building Linux-based multi-stage container images and managing non-root execution.
- **Operating System**: macOS, Windows (PowerShell), or Linux.

### Dependency Clean Install
To install dependencies cleanly and reproducibly using lockfiles:

```bash
# Backend Setup
cd backend
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt

# Frontend Setup
cd ../frontend
npm ci
```

---

## 2. Local Verification Scenarios

### Scenario A: Running Unit & Integration Tests (SQLite, Isolation, Idempotency)
Verify the newly created database schema initialization, transaction safety, and race/concurrency locks.

```bash
# From 'backend' directory with virtual environment active
pytest -v
```
- **Expected Outcome**: 100% of unit/integration tests pass. Tests explicitly cover database schema creation, zero score finalization, atomic parameterized inputs, SQL injection immunity, retry mechanism upon lock, and thread-safe concurrency lock checks.

### Scenario B: Launching and Playing locally
Run both servers locally in development mode.

```bash
# Terminal 1: Backend
cd backend
# Activate virtual environment
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev -- --port 5173
```
- **Expected Outcome**: Open `http://localhost:5173` in a web browser. The high scores board loads, displaying "No high scores yet" (empty state). Complete a game to transition to game-over: the leaderboard updates immediately with your UUID, score, lines, and level. Restarting or closing mid-game does NOT create a high score record.

---

## 3. Containerized Docker Compose Validation

Validate reproducible containerized packaging with a persistent volume, closed backend port, and non-root users.

### 1. Build and Start the Environment
```bash
# From project root
docker compose up --build -d
```

### 2. Verify Port Isolation
- Access `http://localhost:5183` from your host web browser. The game must load and run smoothly.
- Access `http://localhost:8000/api/high-scores` from your host. It **MUST be blocked** or unreachable because host port 8000 is closed, keeping the backend internal.

### 3. Verify Non-Root User Execution
```bash
# Check backend user
docker compose exec backend whoami
# Must NOT return 'root'

# Check frontend user
docker compose exec frontend whoami
# Must NOT return 'root'
```

### 4. Verify Persistent SQLite Named Volume
1. Open `http://localhost:5183` and complete a game to write a score to the database.
2. Shutdown and completely destroy the containers:
   ```bash
   docker compose down
   ```
3. Start the containers again:
   ```bash
   docker compose up -d
   ```
4. Refresh `http://localhost:5183`. The high score **MUST survive** and be displayed on the panel, proving database writes persist in the named volume.

---

## 4. Playwright Rendering Performance Benchmark

Execute an automated chromium rendering cadence trace against the production frontend.

### 1. Run the Performance Benchmark
```bash
cd frontend
# Ensure dependencies and browsers are installed
npx playwright install chromium

# Start production build locally to benchmark against
npm run build
npm run preview -- --port 5173 &

# Execute the performance script (manual benchmark job command)
npm run benchmark
```
- **Expected Outcome**: Playwright launches Chromium at `1280x900` with device scale factor 1. It warms up for 5 seconds, then runs three independent 30-second trials of gameplay (moving pieces and restarting as needed). It outputs median/p95/p99 intervals, FPS, slow frames count, and records raw traces with screenshots under `frontend/tests/evidence/`.
- **Target Performance**: Mean scheduling rate >= 55 FPS, p95 frame intervals <= 25 ms.
- **Unsupported/Headless Environment**: If run in a headless environment (like some standard CI runners or environments lacking a graphical display server), the benchmark script will automatically and gracefully fall back to headless execution, record this constraint honestly in the raw summaries, and output results without failing the task.

---

## 5. Continuous Integration (GitHub Actions)

The project includes a secret-free GitHub Actions workflow configured in `.github/workflows/ci.yml`. On every push and pull request, the workflow performs:
1. **Backend Jobs (Python 3.11)**:
   - Sets up Python 3.11 environment.
   - Restores/manages dependencies.
   - Runs a secure, automated dependency vulnerability audit via `pip-audit`.
   - Executes the full backend test suite (`pytest`) with terminal-missing and XML coverage reporting.
2. **Frontend Jobs (Node 24)**:
   - Sets up Node 24.
   - Installs packages reproducibly via `npm ci`.
   - Runs a dependency security audit via `npm audit`.
   - Executes frontend unit tests with Vitest.
   - Compiles production-ready static assets using TypeScript and Vite compiler (`npm run build`).
3. **Docker Image Builds**:
   - Uses GitHub Actions multi-stage buildx to verify that separate backend and frontend `Dockerfiles` build correctly without secrets or hardcoded dependencies.

To simulate the GitHub Actions pipeline locally, you can run:
```bash
# Backend Test & Audit
cd backend
python -m pip_audit -r requirements.txt
pytest --cov=app

# Frontend Test & Audit
cd ../frontend
npm audit
npm run test
npm run build
```
