## 1. Backend Setup & Database Persistence

- [x] 1.1 Scaffold FastAPI project structure under `/backend` with virtual environment and `requirements.txt`
- [x] 1.2 Add backend packages: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`
- [x] 1.3 Initialize SQLite database schema (`accounts` and `transactions` tables)
- [x] 1.4 Write a database seeding script to insert Checking Account (5.000.000,00 COP), Savings Account (15.000.000,00 COP), and two completed transaction histories
- [x] 1.5 Implement database connection and raw SQL query execution helpers using Python's built-in `sqlite3` module

## 2. Backend Core API & Business Logic

- [x] 2.1 Implement `GET /api/accounts` returning the list of both Checking and Savings accounts with decimal string balances
- [x] 2.2 Implement `GET /api/history` returning the full list of transactions (incoming and outgoing) for the pre-authenticated user
- [x] 2.3 Implement the validation engine for own-account transfers: check for self-transfers, negative amounts, and sufficient source funds
- [x] 2.4 Add decimal string serialization/deserialization to guarantee precision safety during API payloads parsing

## 3. Backend Mock MFA Service

- [x] 3.1 Implement standard non-sensitive transfer routing (under COP 1,000,000) directly to immediate execution
- [x] 3.2 Implement sensitive transfer routing (>= COP 1,000,000) that intercepts and inserts a `PENDING_MFA` transaction record directly in the SQLite database
- [x] 3.3 Create the confirmation endpoint `POST /api/transfers/{tx_id}/confirm` validating: code is exactly `"123456"` (leaving status `PENDING_MFA` on error), timestamp is under 5 minutes (updating status to `EXPIRED` if timed out), and source balance remains sufficient (updating status to `FAILED` if depleted)
- [x] 3.4 Implement the atomic transfer execution in `sqlite3` to deduct the source, credit the destination, and update status to `COMPLETED`

## 4. Frontend Setup & Base Styling

- [x] 4.1 Initialize React + TypeScript project under `/frontend` using Vite
- [x] 4.2 Clean out default templates and configure Vite proxy settings for `/api` requests to backend
- [x] 4.3 Setup main CSS layout sheet with modern, polished Vanilla CSS (cards, buttons, alerts, and modal typography)
- [x] 4.4 Build API utility functions to fetch accounts, histories, and execute/confirm transfers with string decimal amounts

## 5. Frontend Dashboard & Ledger UI

- [x] 5.1 Build the Main Dashboard shell showing user profile details (Jane Doe) and account summary widgets
- [x] 5.2 Build individual Account detail cards showing checking vs savings with formatted COP balances
- [x] 5.3 Implement the transaction list history container showing recent actions
- [x] 5.4 Add filters to view all history or narrow down to a single account, displaying both its debit and credit movements

## 6. Frontend Transfer Forms & MFA Validation

- [x] 6.1 Implement the Account Transfer form allowing dropdown selection of source/destination and amount inputs
- [x] 6.2 Add client-side validations to block self-transfers, negative amounts, or transactions exceeding current balances
- [x] 6.3 Build the interactive MFA modal pop-up that prompts the user for a 6-digit confirmation code when status `PENDING_MFA` is returned
- [x] 6.4 Hook up the transfer confirmation API call to execute the transfer and refresh accounts/history views on success

## 7. Verification & Manual Testing

- [x] 7.1 Verify end-to-end happy path for a regular transfer under COP 1.000.000
- [x] 7.2 Verify end-to-end happy path for a sensitive transfer >= COP 1.000.000 with MFA code `"123456"`
- [x] 7.3 Verify rejection path when an incorrect code is entered (status remains `PENDING_MFA`) and when code is submitted after the 5-minute timeout (status transitions to `EXPIRED`)
- [x] 7.4 Verify error messages on the form for self-transfers, negative values, and overdraft attempts (or confirmation failures marking status as `FAILED`)
