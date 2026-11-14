---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories", "step-04-final-validation"]
inputDocuments: ["_bmad-output/stage3/planning-artifacts/prds/prd-stage3-option-a/prd.md", "_bmad-output/stage3/planning-artifacts/prds/prd-stage3-option-a/addendum.md", "_bmad-output/stage3/planning-artifacts/architecture/stage3-option-a/ARCHITECTURE-SPINE.md"]
---

# Tetris Stage 3 Option A - Epic Breakdown

## Overview
This document outlines the complete epic and story breakdown for Tetris Stage 3 Option A, decomposing the requirements from our Stage 3 PRD, Technical Addendum, and Architecture Spine into an implementation-ready backlog with traced acceptance criteria, technical tasks, and test verification strategies.

---

## Requirements Inventory

### Functional Requirements
- **FR-55:** Persistent Database Path and Initialization at `TETRIS_DB_PATH` defaulting to `./data/high-scores.sqlite3`.
- **FR-56:** High Score Eligibility strictly upon authoritative backend `game_over` (including zero scores, excluding restarts/abandons).
- **FR-57:** Uniqueness constraint on `game_id` with atomic parameterized SQL writes (completed_at assigned once and immutable).
- **FR-58:** Thread-safe backend RLock synchronization (`threading.RLock`) for all sessions registry, mutations, and database finalization.
- **FR-59:** Read-only `GET /api/high-scores` leaderboard (top 10 descending, write-free RLock snapshot, GET never retries).
- **FR-60:** Strict request payload validation on game creation and moves (reject extra fields with HTTP 422).
- **FR-61:** Controlled storage failure error handling (controlled HTTP 503 JSON without path/SQL leakage).
- **FR-62:** Terminal persistence failure mutation retry under the RLock, while GET never retries.
- **FR-63:** Frontend High Scores sidebar panel with visually distinct Loading, Empty, and Error states.
- **FR-64:** Configurable same-origin `/api` API base URL, bypassing compile-time VITE env lookup limitations.
- **FR-65:** Restrictive, configurable CORS policy (no wildcard origins with credentials enabled).
- **FR-66:** Reproducible multi-stage non-root Docker packaging for frontend and backend images.
- **FR-67:** Double-isolated Docker Compose orchestration (frontend published on port 5183, persistent SQLite named volume).
- **FR-68:** Automated Playwright Chromium performance benchmark (3 runs, 5s warmup + 30s analysis, 5-35s window, mean FPS, p95 interval).
- **FR-69:** Pinned GitHub Actions Continuous Integration workflow (Node 20, Python 3.11, reproducible locks, audits).

---

## Epic List
- **Epic 1: Thread-Safe SQLite Persistence & Authoritative Leaderboard** (Governs FR-55, FR-56, FR-57, FR-58, FR-59, FR-60, FR-61, FR-62)
- **Epic 2: Frontend High Scores panel & Configurable Same-Origin Routing** (Governs FR-63, FR-64, FR-65)
- **Epic 3: Portable Containerization & Automated Performance Verification** (Governs FR-66, FR-67, FR-68, FR-69)

---

## Epic 1: Thread-Safe SQLite Persistence & Authoritative Leaderboard
Deploys an embedded SQLite database using Python's standard `sqlite3` module. It wraps all sessions registry creation, lookups, mutations, and SQLite writes under a process-wide `threading.RLock` to guarantee thread safety inside FastAPI's threadpool. It enforces strict payload field validation and controlled 503 error handling with write retries on subsequent terminal mutations.

### Story 1.1: Database Schema Initialization & Parameterized SQLite writes
As a Study Reviewer,
I want a persistent database that initializes safely on backend startup and writes completed games,
So that high scores are saved reliably without SQL injection vulnerabilities.

**Acceptance Criteria:**
- **Given** the backend service is launching,
- **When** the service initializes,
- **Then** it reads `TETRIS_DB_PATH` (defaulting to `./data/high-scores.sqlite3`), creates parent folders if missing, and creates the `high_scores` table idempotently.
- **Given** a game session transitions to `"game_over"` for the first time,
- **When** the backend finalizes the session,
- **Then** it inserts `game_id`, `score`, `total_lines`, `level`, and `completed_at` (UTC ISO-8601) using atomic, parameterized queries, and restarts or active games never create database records.

**Technical Tasks:**
- Read `TETRIS_DB_PATH` env variable and initialize SQLite schema.
- Write raw parameterized SQL query to execute atomic insert into `high_scores`.
- Prevent active/restarted game IDs from inserting records.

**Test Evidence:**
- Verification script that initiates database, completes a game, and inspects SQLite database directly to confirm schema, parameterized writes, and uniqueness.

---

### Story 1.2: Thread-Safe RLock Concurrency Guard
As a Software Architect,
I want a process-wide reentrant lock guarding all backend registry access and state transitions,
So that concurrent threadpool handlers do not trigger race conditions or duplicate entries.

**Acceptance Criteria:**
- **Given** multiple concurrent threadpool requests targeting the same or separate game sessions,
- **When** requests execute,
- **Then** they acquire a shared `threading.RLock()` to synchronize registry creation, session lookup, state mutations, and SQLite writes.
- **And** multiple simultaneous finalizations for the same `game_id` are blocked and rejected by unique SQLite constraints.

**Technical Tasks:**
- Implement global thread-safe `threading.RLock` in backend sessions registry.
- Wrap all route handlers (`POST /api/games`, ticks, moves, holds, GET state) with lock acquisition.

**Test Evidence:**
- Concurrent stress-testing script issuing 100 simultaneous requests to mutate and finalize game sessions, confirming zero race conditions or duplicate database entries.

---

### Story 1.3: Read-only GET Leaderboard
As a Player,
I want to retrieve the top 10 scores sorted correctly,
So that I can see the authoritative high scores list.

**Acceptance Criteria:**
- **Given** clients query `GET /api/high-scores`,
- **When** the backend queries SQLite under the `threading.RLock`,
- **Then** it returns at most ten scores ordered by score descending, then completed_at ascending, then game_id ascending.
- **And** this GET endpoint is strictly read-only, executes zero writes, and never retries failed database writes.

**Technical Tasks:**
- Implement `GET /api/high-scores` endpoint.
- Query SQLite under `threading.RLock` with a clean write-free snapshot query.

**Test Evidence:**
- Unit test asserting correct ordering for ties, zero scores, and maximum of 10 entries.

---

### Story 1.4: Strict Payload Body Validation and Safe 503/Retry Mechanics
As a DevOps Engineer,
I want strict body field checking and fail-safe database error handling,
So that malicious clients cannot inject scores and database locking failures produce controlled 503 JSON.

**Acceptance Criteria:**
- **Given** clients send game creation or move request bodies,
- **When** the payload contains extra or unexpected fields,
- **Then** the API rejects them with `HTTP 422 Unprocessable Entity` immediately.
- **Given** SQLite writes fail on game over (locked/full),
- **When** finalization is interrupted,
- **Then** the backend returns `HTTP 503 Service Unavailable` hiding SQL/file paths and preserves in-memory game state with `persisted = False`.
- **And** subsequent movement or tick mutations retry persistence under the lock, while GET never retries.

**Technical Tasks:**
- Configure Pydantic validation rules to forbid extra payload fields (`extra = "forbid"`).
- Implement database try-except blocks catching SQLite write exceptions.
- Implement mutating retry mechanics for terminal sessions marked `persisted = False`.

**Test Evidence:**
- Unit tests validating rejection of extra fields, simulation of database write lock returning 503, and subsequent tick triggering successful finalization retry.

---

## Epic 2: Frontend High Scores Panel & Configurable Same-Origin Routing
Adds a modern, state-driven "High Scores" panel to the React frontend. It triggers fetches on initial load and after game over without tick polling. It establishes same-origin `/api` proxy configurations to support portable deployments.

### Story 2.1: Modern React High Scores Panel
As a Player,
I want to view high scores in an integrated UI panel,
So that I can see my achievements immediately upon game over.

**Acceptance Criteria:**
- **Given** the frontend is active,
- **When** the page loads, and immediately after a `"game_over"` event transitions,
- **Then** the frontend dispatches a fetch to the leaderboard endpoint.
- **And** the panel renders visually distinct Loading, Empty (no scores), and Error (503 response) states.

**Technical Tasks:**
- Develop React High Scores panel component matching the classic dark arcade theme.
- Implement loading, empty, and error state transitions using simple React UI state.

**Test Evidence:**
- Vitest component tests verifying that the sidebar correctly shows loading spinner, empty placeholder, and error alert based on mock API responses.

---

### Story 2.2: Same-Origin Proxy and Restrictive CORS
As a Security Architect,
I want the client to use a same-origin API proxy and the backend to enforce a tight CORS policy,
So that we do not expose hardcoded localhost URLs or authorize wildcards.

**Acceptance Criteria:**
- **Given** frontend API requests are made,
- **When** running in production or Docker,
- **Then** the client targets the same-origin `/api` default base, proxied to the backend.
- **Given** CORS options are configured on the backend,
- **When** origins are validated on startup,
- **Then** the backend enforces a configurable CORS policy that prohibits wildcard (`*`) origins when credentials are enabled.

**Technical Tasks:**
- Configure Vite proxy config for `/api` mapping.
- Implement FastAPI CORS middleware using restricted origins read from an environment variable.

**Test Evidence:**
- Integration test validating that CORS pre-flight requests from unauthorized origins are rejected, and that same-origin relative URLs are resolved correctly.

---

## Epic 3: Portable Containerization & Automated Performance Verification
Packages frontend and backend into multi-stage, non-root Docker images and coordinates them with Docker Compose. It adds an automated Playwright performance benchmark to verify scheduling rates, and establishes a pinned GitHub Actions CI workflow.

### Story 3.1: Multi-Stage Non-Root Dockerization & Compose
As a DevOps Engineer,
I want containerized builds that run as non-root on port 5183,
So that local deployment is secure, isolated, and persistent.

**Acceptance Criteria:**
- **Given** the services are packaged,
- **When** Docker images build,
- **Then** they use multi-stage layers, copy only production dependencies, and run as non-root users (`appuser` / `node`).
- **And** Docker Compose exposes ONLY host port 5183, mounts a persistent SQLite named volume `tetris_sqlite_data` with write permissions, and uses built-in health checks.

**Technical Tasks:**
- Create multi-stage `Dockerfile` files for frontend and backend.
- Configure `compose.yaml` with non-root security options, health checks, and named volumes.
- Add `.dockerignore` files for both context directories.

**Test Evidence:**
- Script checking that `docker compose up` starts both services, that backend database survives container restart, and that backend port 8000 is isolated from the host.

---

### Story 3.2: Playwright Performance Benchmark
As a QA Engineer,
I want an automated Playwright Chromium performance benchmark,
So that frame rate and input latency are measured empirically during physical play.

**Acceptance Criteria:**
- **Given** the benchmark script runs,
- **When** executing 3 independent runs of 5s warmup + 30s monotonic measurement,
- **Then** it analyzes frame intervals strictly inside the fixed `5000+30000ms` window (recording intervals where BOTH endpoints fall inside).
- **And** calculates mean FPS as `frame_count / 30.0` (target `>= 55 FPS`) and p95 interval (`<= 25 ms`), logging actual browser version, focus events, raw DOM, and keyboard latencies.

**Technical Tasks:**
- Author `frontend/tests/perf.spec.ts` using Playwright.
- Inject rAF listeners to capture precise rendering intervals.
- Analyze collected data strictly between t=5,000ms and t=35,000ms.

**Test Evidence:**
- Benchmark execution report displaying unrounded FPS and p95 results for each run, confirming that gameplay was maintained without gravity modifications.

---

### Story 3.3: Pinned GHA Continuous Integration Workflow
As a DevOps Engineer,
I want a pinned GHA continuous integration pipeline,
So that all tests, builds, and audits are checked automatically.

**Acceptance Criteria:**
- **Given** the CI pipeline runs,
- **When** a push or PR is processed,
- **Then** it pins Node 20 and Python 3.11, uses reproducible lockfile installs, executes tests with coverage, and runs supported public security audits without `|| true` bypass shortcuts.

**Technical Tasks:**
- Write `.github/workflows/ci.yml`.
- Configure pytest-cov for backend coverage checking.
- Configure NPM audits and Python safety audits.

**Test Evidence:**
- Validation of CI configuration format using local lint tools and verifying pipeline logic runs flawlessly in sandboxed local environments.
