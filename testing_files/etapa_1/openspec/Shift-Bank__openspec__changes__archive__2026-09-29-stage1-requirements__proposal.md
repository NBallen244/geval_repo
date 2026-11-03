## Why

Shift Bank is a basic banking application designed for pre-authenticated mock users. Currently, there is no system in place to allow these users to manage their accounts, review transactions, or make secure transfers. This stage establishes the foundational core banking capabilities—specifically account balance viewing, transaction history tracking, self-account transfers, and mock multi-factor authentication (MFA)—using a clean, precise, and secure architecture with FastAPI and React.

## What Changes

- **Account Overview**: A new capability to view bank accounts (one checking and one savings) with pre-seeded COP balances. After any transfer is executed, subsequent views on the dashboard will display the current persisted balances from the SQLite database.
- **Own-Account Transfers**: Capability to transfer money between checking and savings accounts with strict validations (no self-transfers, non-positive amounts, or insufficient balances) and decimal-safe arithmetic.
- **Transaction Ledger**: Historical ledger view displaying all completed transfer actions, with support for filtering or viewing movements per individual account.
- **Mock MFA Verification**: Sensitive operations (transfers greater than or equal to COP 1,000,000) are routed through a 2-step verification mechanism requiring a fixed 6-digit code `123456` with a 5-minute expiration period.

## Capabilities

### New Capabilities
- `bank-accounts`: Supports retrieving and displaying accounts and their current balances in COP.
- `transfers`: Supports transferring money between checking and savings accounts securely, using decimal-safe calculations.
- `transaction-history`: Supports listing recent transfers/movements associated with each account, showing both incoming and outgoing records.
- `mfa`: Supports mock multi-factor authentication for sensitive transfers >= COP 1,000,000.

### Modified Capabilities

## Impact

- **Database**: Creates SQLite tables for accounts and transactions with seeds using Python's built-in `sqlite3` module.
- **APIs**: Introduces endpoints under `/api/accounts`, `/api/history`, and `/api/transfers`.
- **Backend (FastAPI)**: Implements business logic, validations, decimal calculations, and SQLite-backed `PENDING_MFA` transaction records (no in-memory store).
- **Frontend (React/TS/Vite)**: Installs a clean dashboard dashboard showing accounts, historical movements, transfer forms, and confirmation modals.
