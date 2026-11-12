# Quickstart Guide: Stage 4 Microservices Migration

This guide outlines the steps to run and verify the migrated Stage 4 microservices-based e-commerce platform with resilient RabbitMQ messaging and dead-letter queues.

---

## 1. Local Native Startup (PowerShell)

To launch all four services natively on Windows:

```powershell
# In the repository root:
.\Start-Services.ps1
```

This script:
1. Validates that the local RabbitMQ instance is listening.
2. Starts the **Identity**, **Commerce**, **Reviews**, and **Gateway** microservices on their designated ports (`18601`, `18602`, `18603`, `18600`).
3. Launches their respective background publisher/consumer threads.
4. Performs health checks on each service.

### Full Stack Startup (with Frontend)

To launch the full stack, including the React frontend on Port `18700` with the correct API Gateway routing mapping, in a single command:

```powershell
.\Start-Services.ps1 -Frontend
```

To stop all natively running services:

```powershell
.\Stop-Services.ps1
```

*Note:* Database files (`identity.db`, `commerce.db`, `reviews.db`) are persisted inside the `backend` folder and **survive stop and restart operations**, preserving user accounts, purchase logs, outboxes, and review projections.

---

## 2. Default Demo Credentials

The platform is seeded with the following credentials upon initial startup:

- **Moderator Account:**
  - **Identifier:** `moderator`
  - **Password:** `moderator`
  - *Role:* Moderator (Access to Moderation Dashboard and Review status controls)

- **Standard Customer Accounts:**
  - Standard customer accounts can be dynamically registered in the UI or E2E tests using any custom name and password.

---

## 3. Running the Tests

### Backend Unit & Integration Tests

To execute the unit and integration tests (including the new multi-process acceptance suite), run:

```powershell
cd backend
python -m pytest
```

### Multi-Process Acceptance Test Suite

To run only the multi-process integration and recovery suite (which programmatically spawns and orchestrates services, validates access denial, tests transactional outbox survival under network partition, tests idempotency, and verifies poison-message dead-letter queue routing):

```powershell
cd backend
python -m pytest tests/test_acceptance.py -s
```

### Playwright End-to-End Tests

Ensure the services and frontend are active (`.\Start-Services.ps1 -Frontend`), then execute:

```powershell
cd e2e
npx playwright test
```

This verifies:
1. **E-Commerce Purchasing Journey:** Full guest checkout, registration, login, and disclaimers.
2. **E-Commerce Reviews and Moderation Lifecycle:** Review submission, pending review visibility, moderator dashboard approval, cache invalidation, and public visibility.
3. **Moderation Access Control Safeguards:** Proof of role-based access denial for standard customer accounts.

---

## 4. Frontend Code Coverage Generation

To generate the frontend test coverage `lcov.info` file:

```powershell
cd frontend
npm run test:coverage
```

This populates `frontend/coverage/lcov.info`.

---

## 5. Deployment Notes

- **Docker Compose:** Docker is currently unperformed/unconfigured in this environment.
- **GitHub Actions / Remote Execution:** Pipeline checks remain unperformed remotely; local execution of all tests (26 backend tests + 3 E2E specs) is verified and passing on Windows 32/64.
