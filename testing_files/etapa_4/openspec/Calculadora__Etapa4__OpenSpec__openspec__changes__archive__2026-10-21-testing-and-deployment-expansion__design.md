## Context

See `proposal.md` for motivation. 

The current codebase state and constraints:
- **Backend**: Uses Python, FastAPI, and `pytest`. While some tests are defined in `backend/tests/test_calculator.py`, they lack coverage tracking and enforcement (`pytest-cov`).
- **Frontend**: Built on React 18, Vite, and TypeScript. No testing library or environment is currently configured, resulting in 0% frontend test coverage.
- **State Leakage / Race Conditions**: The live-preview `useEffect` in `App.tsx` lacks a mechanism (like `AbortController`) to cancel outstanding asynchronous fetch requests when the user types rapidly. Stale API responses can resolve out-of-order and overwrite the correct live result.
- **Containerization**: No Docker or Docker Compose infrastructure exists.

## Goals / Non-Goals

**Goals:**
- **High Test Quality**: Achieve $\ge 80\%$ statement and branch coverage in both frontend and backend layers.
- **Frontend Test Suite**: Configure Vitest, JSDOM, and React Testing Library to test component render, input handler, memory state, keyboard mappings, and history list.
- **Safe State Handling**: Fix the live-preview asynchronous race condition via a clean, native React solution.
- **Production-ready Containerization**: Multi-stage, secure Dockerfiles for the FastAPI backend (running as a non-root user) and React frontend (using Nginx for static serving), plus a unified `docker-compose.yml` for orchestration.

**Non-Goals:**
- Do NOT introduce any new math functions, keys, or operators (such as modulo `%`), adhering strictly to existing functionality.
- Do NOT rewrite or alter the AST parsing structure unless fixing existing bugs or safety vulnerabilities.

## Decisions

### 1. Frontend Testing Framework: Vitest with JSDOM
- **Options Considered**: Jest + ts-jest vs. Vitest.
- **Decision**: Choose Vitest because the frontend is built using Vite. Vitest shares Vite's config, provides extremely fast hot-module reloading, supports TypeScript natively, and has full compatibility with Jest's assertion style.
- **Libraries**: `@testing-library/react` for component testing, `@testing-library/jest-dom` for DOM matchers, and `jsdom` to emulate the browser environment.

### 2. Live-preview State Leakage Fix: AbortController in useEffect
- **Options Considered**: Debounce on-screen evaluation ONLY vs. using `AbortController` in the debounced fetch.
- **Decision**: Implement `AbortController` inside `useEffect`'s clean-up phase. If a new keystroke occurs before the previous API request completes, the controller aborts the previous fetch, preventing race conditions from out-of-order asynchronous completions.

### 3. Containerization Strategy
- **Backend Dockerfile**: Multi-stage build using `python:3.13-slim` as a base. Install dependencies in the build layer, copy them, and run as a non-root system user (`appuser` with UID 10001) in the production layer for container security.
- **Frontend Dockerfile**: Multi-stage build. Use `node:20-alpine` to install dependencies and run `npm run build` to generate static assets in `dist/`. Use `nginx:alpine` to host the compiled assets with custom static configuration handling client-side routing.
- **Orchestration**: A top-level `docker-compose.yml` defining `backend` (port 8000) and `frontend` (port 3000) services with appropriate volume maps or environments.

## Risks / Trade-offs

- **[Risk]** Vitest vs browser-level input events. Physical keyboard bindings in React are sometimes tricky to test inside simulated environment JSDOM.
  - *Mitigation*: We will mock or fire custom keyboard events (`fireEvent.keyDown`) on the `window` to thoroughly assert keyboard interaction coverage.
- **[Risk]** CORS conflicts in Docker local environments if frontend makes requests to `localhost:8000` but is running on a different port or in a different network.
  - *Mitigation*: Configure the backend container with appropriate CORS headers (retaining existing development settings but documented for deployment) and keep backend URL configurable if necessary (defaulting to the local host port 8000 for standard local testing).
