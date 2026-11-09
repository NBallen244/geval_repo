# Research: Testing & Deployment Expansion

This document presents the research, tool selection, and containerization design for the Web Calculator application, resolving all unknowns identified in the implementation plan.

---

## 1. Resolved Unknowns & Tool Selection

### 1.1 Frontend Testing Stack (Resolving NEEDS CLARIFICATION 1)
- **Decision**: Adopting **Vitest** as the test runner with **jsdom** as the browser environment and **@testing-library/react** for component mounting and event simulation.
- **Rationale**:
  - The project utilizes Vite as the build tool (`vite.config.ts` is present). Vitest is built specifically for Vite, leveraging the same build pipeline and plugins, which ensures TypeScript compilation works out-of-the-box without separate Jest configuration.
  - Vitest is extremely fast and matches the Jest API (e.g., `describe`, `test`, `expect`), requiring zero changes to the existing `Accessibility.test.tsx` and `Calculator.test.tsx` file structures.
- **Required DevDependencies**:
  - `vitest`
  - `jsdom`
  - `@testing-library/react`
  - `@testing-library/jest-dom` (for fluent DOM assertions)
- **Script Command**: `vitest run --coverage` to execute tests and output coverage report.

### 1.2 Backend Coverage Configuration (Resolving NEEDS CLARIFICATION 2)
- **Decision**: Adopting **pytest-cov** to measure branch and statement coverage.
- **Rationale**: `pytest-cov` integrates seamlessly with the existing `pytest` framework listed in `backend/requirements.txt`. It generates standardized HTML and XML coverage reports.
- **Required Dependency**: `pytest-cov>=4.1.0` (to be added to `backend/requirements.txt`).
- **Script Command**: `pytest --cov=src --cov-report=term-missing --cov-report=html --cov-branch` to enforce branch coverage calculations.

---

## 2. Containerization Architecture

### 2.1 Backend Dockerfile Design
To ensure high security and minimal size:
- **Base Image**: `python:3.11-slim`
- **Security Practices**:
  - **Multi-stage build**: Use a `builder` stage to install dependencies (compiling wheels if necessary) and a separate minimal runtime stage.
  - **Non-root Execution**: Create a system group and user `appuser` (UID/GID 10001) to run the application, ensuring zero root privilege risk.
  - **Read-only Filesystem**: Keep application files owned by root and readable by `appuser`, while exposing only necessary temporary writable folders (like `/tmp`) if needed.
- **Port**: Exposes `8000`.

### 2.2 Frontend Dockerfile & Web Server Design
To serve the static application securely and performantly:
- **Base Image**: Multi-stage build:
  - **Build Stage**: `node:20-alpine` to execute `npm run build` (Vite).
  - **Runtime Stage**: `nginxinc/nginx-unprivileged:stable-alpine` (pre-configured to run as non-root user `nginx` on non-privileged port `8080`).
- **Nginx Configuration**:
  - **SPA Fallback**: Configured with `try_files $uri $uri/ /index.html` to support React Router or client-side routing.
  - **Reverse Proxy**: Nginx will proxy all API calls from `/api/` directly to `http://backend:8000/api/` inside the container network. This completely resolves CORS (Cross-Origin Resource Sharing) problems and eliminates the need to hardcode host ports/IPs in the React build.
- **Port**: Exposes `8080` (internally mapped from Nginx) and mapped to port `80` (or `3000`) on the host.

### 2.3 Unified Orchestration (Docker Compose)
A root-level `docker-compose.yml` will tie the services together:
- **Services**:
  - `backend`: Builds the backend Dockerfile, exposes port `8000`.
  - `frontend`: Builds the frontend Dockerfile, exposes port `80` mapping to internal container port `8080`.
- **Networking**: Custom bridge network `calculator-network` ensuring the frontend container can communicate with the backend container using the DNS name `backend`.

---

## 3. Alternatives Considered & Rejected

### Alternative 1: Jest for Frontend Testing
- **Why Considered**: Industry-standard React test runner.
- **Why Rejected**: Requires extensive configuration (Babel or ts-jest) to parse Vite assets and TSX files correctly under modern ES modules. Vitest handles Vite assets natively and executes faster.

### Alternative 2: Standard Root-based Nginx Docker Image
- **Why Considered**: Simplest Dockerfile configuration.
- **Why Rejected**: Runs the Nginx master process as `root`, violating container security compliance. Using an unprivileged Nginx image enforces safety out-of-the-box.
