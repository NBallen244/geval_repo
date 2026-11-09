# Tasks: Testing & Deployment Expansion

**Input**: Design documents from `/specs/003-testing-deployment/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test validation suites are a mandatory component of this expansion to satisfy the $\ge 80\%$ statement/branch coverage threshold.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Path Conventions

- Multi-tier web app layout:
  - Backend files: `backend/`
  - Frontend files: `frontend/`
  - Root orchestrator: `docker-compose.yml`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic testing tools configurations

- [X] T001 Install and configure frontend testing devDependencies (`vitest`, `jsdom`, `@testing-library/react`, `@testing-library/jest-dom`) in `frontend/package.json`
- [X] T002 Install and configure backend coverage dependencies (`pytest-cov`) in `backend/requirements.txt`
- [X] T003 [P] Add unit testing scripts (`test:run` and `test:coverage`) to `frontend/package.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core configurations that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Configure base Vitest runner configuration in `frontend/vite.config.ts` to enable TypeScript resolution and JSDOM environment
- [X] T005 [P] Configure default Pytest command coverage options in `backend/pyproject.toml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reliable Calculation Execution & Robust Validation (Priority: P1) 🎯 MVP

**Goal**: Implement comprehensive mathematical edge case testing, frontend accessibility state verification, and keyboard input testing, achieving $\ge 80\%$ coverage.

**Independent Test**: Execute `pytest --cov=src` and `vitest run --coverage` and verify all tests pass with code coverage $\ge 80\%$.

### Implementation & Testing for User Story 1

- [X] T006 [P] [US1] Implement comprehensive backend unit tests for math edge cases (division by zero, negative logs/sqrt, trigonometric domains like $|x| > 1$ for `arcsin`) in `backend/tests/unit/test_evaluator.py`
- [X] T007 [P] [US1] Implement backend API integration tests validating calculation requests and mathematical error payload structures in `backend/tests/contract/test_evaluate_api.py`
- [X] T008 [US1] Implement frontend component unit tests for standard and mathematical edge case button click interactions in `frontend/src/tests/Calculator.test.tsx`
- [X] T009 [US1] Implement frontend integration tests for keyboard event handling and history rendering in `frontend/src/tests/Accessibility.test.tsx`
- [X] T010 [US1] Execute and verify backend test suite coverage is strictly $\ge 80\%$ statement and branch in `backend/`
- [X] T011 [US1] Execute and verify frontend test suite coverage is strictly $\ge 80\%$ statement and branch in `frontend/`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Uniform & Seamless Container Orchestration (Priority: P2)

**Goal**: Package and orchestrate the entire multi-tiered application services using Docker Compose.

**Independent Test**: Running `docker compose up --build` builds both services, networks them together, and renders the operational app.

### Implementation & Testing for User Story 2

- [X] T012 [P] [US2] Create basic multi-stage Dockerfile and configure `.dockerignore` for FastAPI backend in `backend/Dockerfile`
- [X] T013 [P] [US2] Create basic production multi-stage Dockerfile and configure `.dockerignore` for React frontend using Nginx in `frontend/Dockerfile`
- [X] T014 [US2] Create unified container orchestration configuration in `docker-compose.yml`
- [X] T015 [US2] Verify unified service initialization and basic communication inside container network using `docker compose up`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Secure & Optimized Production Deployment (Priority: P3)

**Goal**: Harden Docker images to run under unprivileged users and set up Nginx reverse proxying to solve CORS.

**Independent Test**: Running `whoami` inside executing containers returns non-root values, and API requests proxied via Nginx port 80 successfully compute expressions.

### Implementation & Testing for User Story 3

- [X] T016 [P] [US3] Configure backend Dockerfile to run under a secure non-root `appuser` (UID 10001) in `backend/Dockerfile`
- [X] T017 [P] [US3] Implement custom Nginx configuration file supporting unprivileged execution (port 8080) and SPA fallback (routing 404 errors back to index.html) in `frontend/nginx.conf`
- [X] T018 [US3] Configure frontend Dockerfile to use unprivileged Alpine Nginx base image and incorporate custom Nginx config in `frontend/Dockerfile`
- [X] T019 [US3] Add Nginx reverse-proxy routes mapping `/api/` directly to `backend:8000` to resolve CORS in `frontend/nginx.conf`
- [X] T020 [US3] Verify secure production runtimes and unprivileged ownership structures using container audit checks

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T021 [P] Update developer documentation and API endpoint schema references in `README.md`
- [X] T022 [P] Clean up any temporary or residual container build artifacts from the workspace
- [X] T023 Run and fully validate all end-to-end scenarios listed in `quickstart.md` and verify all tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phases 3-5)**: All depend on Foundational phase completion.
  - User stories can then proceed in parallel (if staffed).
  - Or sequentially in priority order (P1 → P2 → P3).
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Depends on Phase 2, but also requires individual basic Dockerfile targets.
- **User Story 3 (P3)**: Depends on User Story 2 Docker base configs, but implements security hardening and production proxying.

### Within Each User Story
- Tests must be run and fail before implementing (TDD approach).
- Low-level files/configs before high-level orchestration/routes.
- Story complete and verified before moving to next priority.

### Parallel Opportunities

- Setup tasks T001, T002, T003 can run in parallel.
- Foundational tasks T004, T005 can run in parallel.
- Once Foundational phase completes:
  - Developer A can work on backend unit/contract tests (T006, T007) [P].
  - Developer B can work on frontend unit/integration tests (T008, T009) [P].
- Dockerfile creations for backend (T012) and frontend (T013) can start in parallel.
- Security hardening for backend (T016) and Nginx config (T017) can be done in parallel.

---

## Parallel Example: User Story 1

```bash
# Launch backend test suite tasks:
Task: "Implement comprehensive backend unit tests in backend/tests/unit/test_evaluator.py"
Task: "Implement backend API integration tests in backend/tests/contract/test_evaluate_api.py"

# Simultaneously, launch frontend test suite tasks:
Task: "Implement frontend component unit tests in frontend/src/tests/Calculator.test.tsx"
Task: "Implement frontend integration tests in frontend/src/tests/Accessibility.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Testing suite & Coverage verification)
4. **STOP and VALIDATE**: Verify that code coverage $\ge 80\%$ is fully met on both layers.

### Incremental Delivery

1. Complete Setup + Foundational → Testing & build foundation ready.
2. Add User Story 1 → Test independently → Verify code quality.
3. Add User Story 2 → Run Compose configuration → Operational web application.
4. Add User Story 3 → Apply non-root container permissions and Nginx routing → Production-ready delivery.
5. Polish → Document and release.

### Parallel Team Strategy

With multiple developers:
1. Team completes Setup + Foundational together.
2. Once Foundational is done:
   - Developer A: Implements and verifies backend coverage.
   - Developer B: Implements and verifies frontend coverage.
3. Once coverage meets criteria:
   - Developer A: Sets up backend container packaging and security.
   - Developer B: Sets up frontend container Nginx routing and unprivileged config.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story for traceability.
- Each user story is designed to be independently completable and testable.
- Commit after each task or logical group.
