## Why

The Scientific Web Calculator app currently lacks automated test suites for the frontend and containerization for both services. To transition the application to production-ready quality and facilitate continuous integration, we must enforce a strict code coverage threshold of at least 80% across all layers and orchestrate multi-container deployment using Docker and Docker Compose.

## What Changes

- **Testing Infrastructure Expansion**:
  - Set up and configure frontend testing framework (Vitest) and utility libraries (React Testing Library, jsdom) to enable comprehensive unit and component testing.
  - Integrate backend coverage reporting with `pytest-cov` to track and enforce the $\ge 80\%$ statement and branch coverage metrics.
- **Bug Fixes and Audits**:
  - Address state leakage / race conditions in the frontend's live-preview feature by implementing a debounce-linked `AbortController` to cancel stale, out-of-order asynchronous API evaluation requests.
  - Document pre-existing audit findings from Stages 1 & 2 before starting execution.
- **Containerization**:
  - Add a multi-stage, secure, production-ready `Dockerfile` for the Python FastAPI backend running as a non-root user.
  - Add a multi-stage, optimized `Dockerfile` for the React static asset serving using Nginx.
  - Add a root-level `docker-compose.yml` to orchestrate both services locally.

## Capabilities

### New Capabilities

None (No new capabilities are being introduced in this stage as the focus is purely on quality assurance, test expansion, and containerization).

### Modified Capabilities

None (Existing capability requirements remain unmodified. Only implementation quality and deployment packaging are changed).

## Impact

- **Frontend (`/frontend`)**: Will add dependencies (`vitest`, `@testing-library/react`, `jsdom`, etc.) in `package.json`, a new test file, and an updated live-preview state-handling architecture.
- **Backend (`/backend`)**: Will add dependencies (`pytest-cov`) to `requirements.txt` and expand `tests/test_calculator.py` with more rigorous unit tests.
- **CI / Deployment**: Adds `Dockerfile` (frontend & backend) and `docker-compose.yml` configurations at the workspace level.
