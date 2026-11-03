## Context

See `proposal.md` for the motivation and business goals of this change.
The application will be developed using FastAPI (Python) for the backend, SQLite for relational persistence (accessed directly via Python's built-in `sqlite3` module), and React (TypeScript + Vite) with Vanilla CSS for the frontend. The system must operate with strict decimal safety for all monetary transactions and support a 2-step mock MFA challenge for sensitive transfer operations.

## Goals / Non-Goals

**Goals:**
- Design a relational SQLite schema for banking accounts and transaction logs.
- Provide a robust FastAPI endpoint structure for loading accounts, history, and executing own-account transfers.
- Implement an in-memory/DB-backed pending MFA transaction store with a 5-minute timeout.
- Secure transactions against self-transfers, negative values, and insufficient funds.
- Format and display financial data cleanly in a React UI using pure Vanilla CSS.

**Non-Goals:**
- Do not implement user signup, login, password recovery, or sessions (use a single hardcoded pre-authenticated user `usr_101`).
- Do not connect to real MFA services (SMS/Email/TOTP); rely strictly on the mock fixed code `123456`.
- Do not calculate or display resulting balances on historical ledger records.
- Do not support currency conversions (use COP strictly).

## Decisions

### 1. Database Schema (SQLite)
We will use a relational database with two main tables: `accounts` and `transactions`.

```
+------------------------------------+
|             accounts               |
+------------------------------------+
| id (TEXT, PK)                      |
| name (TEXT)                        |
| balance (TEXT) - stored as string  |
+------------------------------------+

+------------------------------------+
|           transactions             |
+------------------------------------+
| id (TEXT, PK)                      |
| source_account_id (TEXT, FK)       |
| destination_account_id (TEXT, FK)  |
| amount (TEXT) - stored as string   |
| timestamp (TEXT)                   |
| status (TEXT)                      |
+------------------------------------+
```
*Rationale:* Storing balances and transfer amounts as strings in SQLite guarantees that we do not suffer floating-point representation drift during SQL reads/writes.

### 2. Precise Decimal Safe Arithmetic
*Decision:* All API payloads representing monetary amounts will transmit money as strings (e.g., `"1000000.00"`). The backend will parse them into Python's `decimal.Decimal` and perform balance checks and arithmetic using this type.
*Alternatives Considered:* Floats (rejected due to binary rounding issues), integers representing cents (viable, but decimal strings map more naturally to COP currency where centavo units are rarely used and decimal string conversion is direct and clean).

### 3. Two-Step MFA State Machine
*Decision:*
All sensitive operations (`amount >= 1.000.000,00 COP`) are serialized and stored directly in the SQLite `transactions` table with a status of `PENDING_MFA`. We use direct database records to persist this state, avoiding in-memory stores completely.

When a transfer of amount `>= 1.000.000,00 COP` is requested:
1.  Backend creates a record in `transactions` with status `PENDING_MFA` and returns `202 Accepted` along with the transaction ID.
2.  The frontend displays the MFA modal and tracks the pending transaction ID.
3.  When the user submits the code, the frontend calls `POST /api/transfers/{tx_id}/confirm`.
4.  The backend verifies:
    - If the transaction exists and has `PENDING_MFA` status.
    - If the creation timestamp is within 5 minutes. If it exceeds 5 minutes, status is updated to `EXPIRED` and execution is rejected.
    - If the submitted code is exactly `"123456"`. If incorrect, execution is rejected with a validation error, and the transaction remains in `PENDING_MFA` status (allowing retry until expiration).
    - If the source account still has sufficient funds. If insufficient, status is updated to `FAILED` and execution is rejected.
5.  If validation passes, the backend executes the transfer in a single atomic database transaction (using `sqlite3` transactional blocks), updating both account balances and marking the transaction as `COMPLETED`.

*Alternatives Considered:* 
- Storing pending transfers in an in-memory dictionary (rejected, as SQLite-backed `PENDING_MFA` transaction records keep the API stateless and persistent).
- Using SQLAlchemy ORM (rejected, as Python's built-in `sqlite3` module provides direct, low-overhead database access and transaction control).

### 4. Seed Data Execution
*Decision:* A seeding script will initialize the SQLite database with:
- `acc_checking`: "Cuenta Corriente" with `5000000.00`
- `acc_savings`: "Cuenta de Ahorros" with `15000000.00`
- Two pre-seeded historical completed transactions (Transfer of 500.000 from savings to checking, and transfer of 100.000 from checking to savings).

## Risks / Trade-offs

- **[Risk] Parallel confirmation race condition:** A user initiates an MFA transfer, then performs a rapid succession of non-MFA transfers that deplete the balance, then confirms the MFA transfer.
  - *Mitigation:* The confirmation endpoint MUST execute a fresh database query to check the source balance and modify balances within an isolated transaction.
- **[Risk] Memory or record leaks for expired MFA transfers:** PENDING_MFA records might remain abandoned forever if the user closes their browser.
  - *Mitigation:* The backend will automatically treat any `PENDING_MFA` transfer older than 5 minutes as expired upon any query/confirm attempt, and we can optionally run a startup/periodic cleanup or simply filter them out of active checks.
