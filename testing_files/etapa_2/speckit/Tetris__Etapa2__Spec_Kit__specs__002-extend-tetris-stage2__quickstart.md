# Quickstart & E2E Validation Guide: Extend Tetris to Stage 2

This guide outlines instructions to set up, run, and validate the Stage 2 single-player Tetris system (Score, Level, Hold, Next Preview) once implemented. It contains runnable validation scenarios to prove that the features work end-to-end.

---

## 1. Prerequisites & Environment Setup

Verify that the following are installed:
- **Python**: Version 3.12 or higher
- **Node.js**: Version 18.0 or higher
- **PowerShell**: Version 7.x (or standard Windows PowerShell 5.1)

### Backend Setup
1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Activate your virtual environment and install dependencies:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate

   pip install -r requirements.txt
   ```
3. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --port 8000 --reload
   ```
   Interactive Swagger UI will be available at `http://localhost:8000/docs`.

### Frontend Setup
1. Navigate to the frontend directory in another terminal:
   ```bash
   cd frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open the browser at `http://localhost:5173`.

---

## 2. Automated Test Execution

Once implemented, you can verify correct operation by running the test suites.

### Running Backend Tests
From the `backend` directory, execute pytest:
```bash
pytest
```
This runs all unit and integration tests (including Stage 1 and Stage 2 test files).

### Running Frontend Tests
From the `frontend` directory, execute vitest:
```bash
npm run test
```
This runs the React UI components and custom hooks tests.

---

## 3. End-to-End Manual Validation Scenarios

Follow these scenarios to verify the system behavior authoritatively using the Web UI or a REST Client.

### Scenario A: Initialization & Default State
1. **Action**: Open the browser at `http://localhost:5173` or send a `POST` request to `/api/games`.
2. **Expected Outcome**:
   - The UI dashboard displays: `Score: 0`, `Lines Cleared: 0`, `Level: 1`.
   - The "Hold Piece" slot is completely blank/empty.
   - The "Next Piece" slot renders a preview of the upcoming piece.
   - The backend timer ticks every 500 ms (as defined by `gravity_interval_ms` = 500).
   - See [api-contract.md](contracts/api-contract.md) for detail on the response structure.

### Scenario B: Clearing Rows & Level/Speed Up
1. **Action**: Play the game or simulate horizontal line fills using a test harness, so that rows lock and clear.
2. **Expected Outcome**:
   - Clearing 1 line awards `100 * Level` (100 points on Level 1).
   - Clearing 2 lines awards `300 * Level` (300 points on Level 1).
   - Clearing 3 lines awards `500 * Level` (500 points on Level 1).
   - Clearing 4 lines awards `800 * Level` (800 points on Level 1).
   - Clearing 10 total cumulative rows increases the level from 1 to 2.
   - Upon transition to Level 2:
     - The displayed level changes to `2`.
     - The automatic tick timer on the client reschedules instantly and ticks every 450 ms (`gravity_interval_ms = 500 - 50 * (2 - 1) = 450`).
   - For mathematical formula references, consult [data-model.md](data-model.md).

### Scenario C: Piece Holding & Swapping
1. **Action**: Press the **C** key or click the **Hold** button.
2. **Expected Outcome**:
   - The first press stores the current falling piece type in the "Hold" slot. The active piece is replaced by the "Next" piece, and a new "Next" piece is generated.
   - The "Hold" slot displays the held tetromino.
   - Subsequent presses of **C** before the piece locks are ignored (ignored by the server, as `can_hold` is `false`).
   - After a piece locks and settles on the board, `can_hold` is reset to `true`.
   - Pressing **C** now swaps the active piece with the held piece. The previously held piece spawns at the top-center in its initial unrotated state, and the active piece goes into the Hold slot.

### Scenario D: Immediate Overlap Game Over
1. **Action**: Swap a piece to the Hold slot. Wait for settled blocks to pile up to the top-center spawn origin. Press **C** to swap the held piece in.
2. **Expected Outcome**:
   - The swapped piece spawns at the top-center and immediately collides with the settled blocks.
   - The game status transitions to `"game_over"` instantly, the timer stops, and a game over modal appears. No subsequent movements are accepted.
