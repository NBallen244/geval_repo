# Quickstart Guide: Stage 3 Delivery, Caching, CI and Containers

Welcome to Stage 3 of the e-commerce system! This guide explains how to start, verify, and run tests on the upgraded system.

## Prerequisites

Ensure you have the following installed locally:
- **Python 3.10+**
- **Node.js 18+**
- **Docker & Docker Compose** (optional, for container runs)

---

## Local Development Startup

### 1. Backend Service

Navigate to the `backend/` directory, install dependencies, and launch the FastAPI server:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # On Windows PowerShell
pip install -r requirements.txt
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

The backend API will be available at `http://127.0.0.1:8000`.

### 2. Frontend Service

Navigate to the `frontend/` directory, install Node packages, and launch the development server:

```powershell
cd frontend
npm install
npm start
```

The React client will be available at `http://localhost:3000`.

---

## Local Verification and Testing

### 1. Backend Unit & Integration Tests

Run the Pytest suite with coverage collection:

```powershell
cd backend
pytest --cov=src --cov-report=xml:coverage.xml --cov-report=term
```

This command runs all unit tests (including the new caching behavior tests) and writes `coverage.xml` to the `backend/` folder.

### 2. Frontend Unit & Integration Tests

Run the Jest suite with coverage collection:

```powershell
cd frontend
npm test -- --coverage --watchAll=false
```

This will run all React unit and UX integration tests, generating coverage data in `frontend/coverage/lcov.info`.

### 3. Playwright End-to-End Tests

Ensure both frontend and backend local servers are fully running, then execute the E2E tests:

```powershell
cd e2e
npm install
npx playwright test
```

This verifies the purchasing journey, review moderation lifecycle, and access-denied safeguards.

---

## Orchestrated Run via Docker Compose

To launch the complete, orchestrated system inside container networks:

```powershell
# Build and run containers in the foreground
docker compose up --build

# Shutdown containers and remove volumes
docker compose down -v
```

Once running, the frontend is accessible at `http://localhost:3000` and proxies queries internally to the backend container at `http://backend:8000`.
