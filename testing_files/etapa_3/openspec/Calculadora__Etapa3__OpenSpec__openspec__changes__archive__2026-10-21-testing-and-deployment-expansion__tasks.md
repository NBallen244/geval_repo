## 1. Audit & Preparation

- [x] 1.1 Document all pre-existing codebase audit findings (bugs, race conditions, edge case omissions) from Stages 1 and 2 into a dedicated markdown audit file `docs/audit_findings.md` and verify the file is saved and complete.

## 2. Backend Quality Assurance (Coverage >= 80%)

- [x] 2.1 Add `pytest-cov` to `backend/requirements.txt` and verify dependencies install successfully via pip.
- [x] 2.2 Expand the pytest suite in `backend/tests/test_calculator.py` with unit tests for all mathematical edge cases (e.g., division by zero, invalid trigonometric domains like arcsin outside [-1, 1], negative values in square roots/logarithms, overflow, and invalid syntax sequences). Verify tests pass by running `pytest`.
- [x] 2.3 Run backend tests with coverage and verify that statement and branch code coverage strictly meet or exceed 80% using `pytest --cov=app --cov-branch --cov-report=term-missing`.

## 3. Frontend Quality Assurance (Race Condition Fix & Coverage >= 80%)

- [x] 3.1 Fix the live-preview asynchronous race condition in `frontend/src/App.tsx` by implementing an `AbortController` inside `useEffect`'s cleanup to abort outstanding fetch requests when expressions update rapidly. Verify by typing rapidly and ensuring older asynchronous fetch promises are properly aborted in network requests/console.
- [x] 3.2 Install and configure Vitest, JSDOM, and React Testing Library dependencies in `frontend/package.json` (adding a `vitest.config.ts` configuration file and adding a test/coverage run script). Verify configuration by running a dummy test using `npm run test`.
- [x] 3.3 Write exhaustive unit and component tests in `frontend/src/App.test.tsx` (or a dedicated tests folder) verifying screen rendering, input handling, memory state operations (MC, MR, M+, M-), keyboard shortcuts, and interactive history panel click triggers. Verify tests pass successfully.
- [x] 3.4 Run frontend tests with coverage using Vitest and verify that statement and branch code coverage meets or exceeds 80%.

## 4. Containerization & Orchestration

- [x] 4.1 Write a multi-stage production `Dockerfile` for the Python FastAPI backend using `python:3.13-slim`, setting up a secure, non-root system user (`appuser`), and verify successful image build with `docker build -t calculator-backend ./backend`.
- [x] 4.2 Write a multi-stage production `Dockerfile` for the React frontend, utilizing `node:20-alpine` for the build stage and `nginx:alpine` to serve static assets, and verify successful image build with `docker build -t calculator-frontend ./frontend`.
- [x] 4.3 Create a root-level `docker-compose.yml` to orchestrate both services, exposing frontend on port 3000 and backend on port 8000. Verify the multi-container environment spins up successfully with `docker compose up -d` and both the UI and API are fully operational.
