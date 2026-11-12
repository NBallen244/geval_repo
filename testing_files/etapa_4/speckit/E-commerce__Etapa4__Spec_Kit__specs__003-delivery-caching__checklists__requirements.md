# Requirements Checklist: Stage 3 Delivery, Caching, CI and Containers

This checklist acts as the gatekeeper for confirming that the Stage 3 implementation meets all criteria defined in `SEED-3.md`.

## Requirements Verification

| Requirement ID | Description | Verification Status | Verification Method |
| :--- | :--- | :---: | :--- |
| **FR-001** | Public response caching for `/api/products` | [ ] | Backend integration tests & E2E suite |
| **FR-002** | Public response caching for `/api/products/{id}/reviews` | [ ] | Backend integration tests & E2E suite |
| **FR-003** | Configurable Time-To-Live (TTL) defaulting to 60s | [ ] | Backend integration tests |
| **FR-004** | Automatic review cache invalidation on status updates | [ ] | Backend integration tests & E2E suite |
| **FR-005** | No public caching for authenticated endpoints/queues | [ ] | Backend architecture review |
| **FR-006** | Real, unmocked Playwright E2E suite against running stack | [ ] | Playwright E2E execution |
| **FR-007** | E2E Customer purchasing journey check | [ ] | `purchasing-journey.spec.ts` |
| **FR-008** | E2E Product review submission and visibility lifecycle | [ ] | `review-lifecycle.spec.ts` |
| **FR-009** | E2E Access denied check for customer viewing dashboard | [ ] | `moderation-access.spec.ts` |
| **FR-010** | Multi-stage Dockerfile configurations | [ ] | Docker build execution |
| **FR-011** | Orchestrated compose local run with container network | [ ] | Docker Compose execution |
| **FR-012** | Container health/readiness checks | [ ] | `docker compose ps` / health state |
| **FR-013** | Automated GitHub Actions CI pipeline configuration | [ ] | `.github/workflows/ci.yml` syntax check |
| **FR-014** | Backend coverage generation (`coverage.xml`) | [ ] | Pytest coverage output |
| **FR-015** | Frontend coverage generation (`lcov.info`) | [ ] | Jest coverage output |
