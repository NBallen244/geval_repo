# Data Model & Configuration Entities

This document defines the structured data entities and configuration schemas required for the Testing & Deployment Expansion.

---

## 1. Test Coverage Report (Conceptual Entity)

This entity represents the collected code coverage results from the backend (`pytest-cov`) and frontend (`vitest`) test runners. It is used to validate the quality gate ($\ge 80\%$ coverage) before deployment.

### Attributes
- **`timestamp`** (DateTime): When the coverage check was executed.
- **`layer`** (String): Either `frontend` or `backend`.
- **`statements_total`** (Integer): Total number of executable lines of code.
- **`statements_covered`** (Integer): Number of covered lines of code.
- **`statements_percentage`** (Float): Percentage of statement coverage (`(statements_covered / statements_total) * 100`). Must be $\ge 80.0\%$.
- **`branches_total`** (Integer): Total number of conditional branches in logic.
- **`branches_covered`** (Integer): Number of executed conditional paths.
- **`branches_percentage`** (Float): Percentage of branch coverage (`(branches_covered / branches_total) * 100`). Must be $\ge 80.0\%$.

### Validation Rules
- **Rule-01 (Coverage Gate)**: The build process must FAIL if `statements_percentage` < 80.0% OR `branches_percentage` < 80.0%.

---

## 2. Container Infrastructure Configuration (System Configuration Entity)

This entity defines the multi-container topology and environments for both development and production deployment.

### Service 1: Backend Container (`backend`)
- **Base Image**: `python:3.11-slim`
- **Exposed Port**: `8000`
- **Execution User**: `appuser` (UID: 10001, GID: 10001)
- **Environment Variables**:
  - `PORT` (Integer, Default: `8000`)
  - `ENV` (String, Default: `production`)

### Service 2: Frontend Container (`frontend`)
- **Base Image**: `node:20-alpine` (for build) $\rightarrow$ `nginxinc/nginx-unprivileged:stable-alpine` (for runtime)
- **Exposed Port**: `8080` (internally), mapped to `80` (on host)
- **Execution User**: `nginx` (non-root)
- **Routing Fallback**: `try_files $uri $uri/ /index.html` (SPA routing)
- **Reverse Proxy Path**: `/api/` maps to `http://backend:8000/api/`

### Service Orchestrator (`docker-compose.yml`)
- **Network**: `calculator-network` (bridge network)
- **Volumes**:
  - Dev volumes (for hot reloading): Optional. Out of scope for secure production image packaging.
- **Dependency Map**: `frontend` service depends on `backend` service being healthy.
