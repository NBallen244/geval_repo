# Data Model & State Machine Design: Shift Bank Stage 1 (Revised)

This document specifies the SQLite database schema, atomic transaction rules, and the transfer multi-factor authentication (MFA) state machine.

---

## 1. Database Schema (SQLite)

The database consists of exactly two tables, designed with strict constraints to ensure financial correctness and tool-neutral persistence. All currency values are calculated using `decimal.Decimal` and stored as `TEXT` to preserve exact precision in SQLite.

### 1.1 `accounts` Table

Represents the mock user's financial accounts.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | TEXT | PRIMARY KEY | Unique account identifier (UUID as string, hidden in UI). |
| `name` | TEXT | UNIQUE, NOT NULL | Friendly label (either `'Checking'` or `'Savings'`). |
| `balance` | TEXT | NOT NULL | Account balance stored as exact decimal string. |
| `currency` | TEXT | NOT NULL, DEFAULT `'COP'` | Strict COP currency restriction. |

#### Database Initialization Seed:
```sql
INSERT INTO accounts (id, name, balance, currency) VALUES
('acc_checking_123', 'Checking', '5000000.00', 'COP'),
('acc_savings_456', 'Savings', '15000000.00', 'COP');
```

---

### 1.2 `transfers` Table

Tracks all completed and pending transaction movements between the Checking and Savings accounts.

To maintain correct datatypes and domain boundaries:
- `expires_at` is **nullable** because standard transfers (amount < COP 1,000,000) and pre-seeded `COMPLETED` transfers do not trigger MFA and must not require artificial expiration timestamps. It is populated only for transfers that transition through the `PENDING_MFA` state.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | TEXT | PRIMARY KEY | Unique transfer identifier (UUID). |
| `source_account_id` | TEXT | FOREIGN KEY, NOT NULL | References `accounts(id)`. |
| `destination_account_id` | TEXT | FOREIGN KEY, NOT NULL | References `accounts(id)`. |
| `amount` | TEXT | NOT NULL | Transfer amount stored as exact decimal string. |
| `status` | TEXT | NOT NULL | State machine status (`PENDING_MFA`, `COMPLETED`, `FAILED`, `EXPIRED`). |
| `created_at` | TEXT | NOT NULL | ISO 8601 UTC timestamp of creation. |
| `expires_at` | TEXT | NULL | ISO 8601 UTC timestamp of MFA expiration (creation + 5 mins). Null when MFA is not applicable. |

#### Database Pre-seeded Movements (2 completed transfers):
Note that the pre-seeded completed historical transfers have `expires_at` set to `NULL` since they do not involve active MFA.

```sql
INSERT INTO transfers (id, source_account_id, destination_account_id, amount, status, created_at, expires_at) VALUES
('tr_seeded_1', 'acc_savings_456', 'acc_checking_123', '500000.00', 'COMPLETED', '2026-09-30T10:00:00Z', NULL),
('tr_seeded_2', 'acc_checking_123', 'acc_savings_456', '100000.00', 'COMPLETED', '2026-09-30T10:05:00Z', NULL);
```

---

## 2. Database Transaction & Atomicity Rules

Every successful transfer execution must be strictly atomic at the database level. 

To prevent precision loss and ensure perfect consistency, **monetary arithmetic must never be performed using SQLite REAL, floating-point casts, or SQL arithmetic on monetary values.** All monetary calculations must be performed on the backend in Python using `decimal.Decimal`.

The backend MUST execute the transaction using the following sequence:

1. **Start Transaction**: Open an explicit SQLite transaction (e.g., executing `BEGIN TRANSACTION;` or setting the connection's autocommit mode to False).
2. **Read Current Balances**: Query the database to retrieve the persisted decimal-string balances for both source and destination accounts:
   ```sql
   SELECT id, balance FROM accounts WHERE id IN (?, ?);
   ```
3. **Calculate and Validate in Python**:
   - Convert retrieved balance strings to Python `decimal.Decimal`.
   - **Check Balance**:
     - **If Sufficient**:
       - Subtract the amount from the source balance and add it to the destination balance using Python `decimal.Decimal` operations.
       - Convert the resulting values back to canonical decimal strings (with exactly two decimal places).
       - Write the updated balances back to the database using parameterized UPDATE statements:
         ```sql
         UPDATE accounts SET balance = ? WHERE id = ?;
         UPDATE accounts SET balance = ? WHERE id = ?;
         ```
       - Update transfer status to `'COMPLETED'`:
         ```sql
         UPDATE transfers SET status = 'COMPLETED' WHERE id = ?;
         ```
       - **Commit**: Execute **`COMMIT;`** to finalize the transaction atomically.
     - **If Insufficient**:
       - Do NOT write any balance updates to accounts.
       - Update transfer status to `'FAILED'`:
         ```sql
         UPDATE transfers SET status = 'FAILED' WHERE id = ?;
         ```
       - **Commit**: Execute **`COMMIT;`** to persist the `FAILED` state change. Do NOT roll back this business-level state transition.
4. **Rollback Handling**:
   - If any unexpected database or technical failure occurs (e.g., SQLite constraint violation, connection timeout, query crash) where the intended transaction sequence cannot be safely completed, execute **`ROLLBACK;`** immediately to prevent partial database writes or data corruption.

---

## 3. MFA State Machine & Lifecycles

Sensitive transfers (amount $\ge$ COP 1,000,000) go through step-up security verification.

### 3.1 States Defined

1. **`PENDING_MFA`**:
   - The transfer has been recorded in the database with status `PENDING_MFA` and an `expires_at` timestamp. Balances are unchanged.
   - Closing or cancelling the frontend MFA modal **leaves the transfer persisted in `PENDING_MFA`**. It is NOT deleted, balances are NOT modified, and NO `CANCELED` state is introduced. The user can still confirm it later within its active 5-minute window.
2. **`COMPLETED`**:
   - Transitioned strictly when a valid code `123456` is submitted within the 5-minute window AND source balance re-validation passes.
3. **`EXPIRED`**:
   - No background scheduler or daemon process runs. Expiration is evaluated **on-demand** when a confirmation request is attempted after the 5-minute deadline has passed.
   - The backend detects that `current_time > expires_at`, writes the status to the database as `EXPIRED`, rejects the request, and leaves account balances unchanged.
4. **`FAILED`**:
   - Transitioned if the code `123456` is valid, but the source balance is insufficient at the exact moment of confirmation (re-validation).

### 3.2 Transition Rules

```text
[Initiate Transfer]
       │
       ▼
   Amount >= COP 1,000,000?
       ├── No ──► [Immediate DB Atomic Transaction (Python Math)] ──► COMPLETED (Balances update)
       │
       └── Yes ──► Create PENDING_MFA (expires_at = creation + 5m)
                     │
                     ├── User Closes UI modal ──► Remains PENDING_MFA (Balances unchanged, valid for retry)
                     │
                     └── User Submits Confirmation Request
                           │
                           ├── Current Time > expires_at? ──Yes──► Write EXPIRED ──► Reject
                           │
                           └── Current Time <= expires_at? ──Yes──► Validate Code
                                 ├── Code != "123456" ──► Reject, Remains PENDING_MFA (Infinite retries allowed)
                                 └── Code == "123456" ──► Re-validate Source Balance
                                       ├── Sufficient ──► [DB Atomic Transaction (Python Math)] ──► COMPLETED
                                       └── Insufficient ──► Write FAILED ──► Reject
```
- **Code Retries**: Submitting an incorrect code does NOT trigger lockout or state changes. The transfer remains `PENDING_MFA` allowing retry until expiration.
