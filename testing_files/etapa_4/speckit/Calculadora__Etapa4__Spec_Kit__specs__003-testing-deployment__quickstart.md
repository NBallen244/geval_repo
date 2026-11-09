# Quickstart & Verification Guide

This guide provides runnable instructions to set up, test, and verify the Testing & Deployment Expansion end-to-end.

---

## 1. Prerequisites

Ensure you have the following installed on your host system:
- **Docker** & **Docker Compose** (for containerized deployment validation)
- **Python 3.11+** (for local backend validation)
- **Node.js 20+** & **npm** (for local frontend validation)

---

## 2. Local Testing & Verification

Before running containerized builds, verify that both codebases pass quality coverage gates locally.

### 2.1 Backend Unit Tests & Code Coverage
Navigate to the `backend/` directory, set up your environment, and execute the test runner:

```bash
cd backend
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies including pytest-cov
pip install -r requirements.txt
pip install pytest-cov

# Run test suite with branch coverage enforcement
pytest --cov=src --cov-report=term-missing --cov-report=html --cov-branch
```

**Expected Outcome**: All tests pass, and the statement and branch coverage percentages are displayed in the terminal. **Both metrics must be $\ge 80\%$**.

### 2.2 Frontend Unit Tests & Code Coverage
Navigate to the `frontend/` directory, install the required testing dependencies, and execute the test runner:

```bash
cd frontend
# Install dependencies (including new vitest and jsdom devDependencies)
npm install

# Run the test suite once and generate coverage
npm run test:run  # Or directly: npx vitest run --coverage
```

**Expected Outcome**: The test runner executes `Accessibility.test.tsx` and `Calculator.test.tsx`. All tests pass with **$\ge 80\%$ statement and branch coverage**.

---

## 3. Containerized Build & Orchestration

Verify the multi-container configuration and secure production packaging.

### 3.1 Launching the Services
From the repository root directory, run Docker Compose to build and start the application:

```bash
# Build secure images and start services in the foreground
docker compose up --build
```

**Expected Outcome**: 
1. Both `backend` and `frontend` images compile successfully.
2. The orchestrator sets up the `calculator-network` bridge.
3. The services start, and terminal outputs confirm Nginx (`frontend`) and FastAPI (`backend`) are running.

### 3.2 Verifying Frontend Static Serving
Open your browser and navigate to:
```text
http://localhost:80
```
*(Or your custom mapped port like http://localhost:8080 or http://localhost:3000)*

**Verification Checklist**:
- [ ] The desktop calculator UI renders correctly.
- [ ] Clicking the numeric keys and operator buttons updates the display correctly.
- [ ] Keyboard inputs (such as keys `0-9`, `+`, `-`, `*`, `/`, `Enter`, `Backspace`, `Escape`) register correctly.
- [ ] Screen readers read active elements and live display zones (Accessibility verification).

### 3.3 Verifying Backend API Reverse Proxy
Send an evaluation request to the backend service via the Nginx port to verify reverse-proxy routing and correct decimal mathematical precision.

Run the following `curl` command from a terminal:

```bash
curl -X POST http://localhost:80/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{"expression": "0.1 + 0.2"}'
```

**Expected Response**:
```json
{
  "expression": "0.1 + 0.2",
  "result": "0.3"
}
```

*Note: For the exact API contract schema, see the [Calculator API Contract](./contracts/calculator-api-contract.md).*

### 3.4 Auditing Container Security
Verify that both containers run as unprivileged users (non-root) to prevent security escalations:

```bash
# Verify the running user inside the backend container
docker compose exec backend whoami

# Verify the running user inside the frontend container
docker compose exec frontend whoami
```

**Expected Outcome**: 
- Backend user should return `appuser` (or UID `10001`).
- Frontend user should return `nginx`.

---

## 4. Teardown

To shut down the container environment and clean up network resources, execute:

```bash
docker compose down --volumes
```
