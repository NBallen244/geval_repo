# Feature Specification: Shift Bank Stage 1 (Revised)

**Feature Branch**: `001-shift-bank-stage1`

**Created**: 2026-09-30

**Status**: Approved

**Input**: User description: "Revise the current Shift Bank Stage 1 specification to clarify the MFA lifecycle without changing any other approved requirements. Closing or cancelling the MFA modal must not execute the transfer, modify account balances, delete the transfer, or introduce a CANCELED state. The persisted transfer must remain PENDING_MFA and may still be confirmed while its five-minute MFA window is valid. MFA expiration does not require a background scheduler or worker. When a confirmation is attempted after the five-minute deadline, the backend must detect that the pending transfer has expired, persist its state as EXPIRED, reject the confirmation, and leave account balances unchanged. Preserve the existing four transfer states PENDING_MFA, COMPLETED, FAILED, and EXPIRED. Preserve all other approved requirements and do not implement code."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Account Overview & Balances (Priority: P1)

As an authenticated bank customer, I want to view all of my bank accounts and their current balances on a unified dashboard using friendly labels, so that I can immediately understand my overall financial standing without being distracted by account numbers or system identifiers.

**Why this priority**: Core value of the banking dashboard. Users must be able to see their holdings before executing transfers or checking histories.

**Independent Test**: Can be fully tested by loading the mock dashboard session and verifying that the Checking account displays a starting balance of COP 5,000,000 and the Savings account displays a starting balance of COP 15,000,000. No account numbers or IDs are shown in the UI.

**Acceptance Scenarios**:

1. **Given** the user is authenticated and on the dashboard page, **When** the account summary loads, **Then** the user sees exactly two accounts: one Checking account with a balance of COP 5,000,000 and one Savings account with a balance of COP 15,000,000.
2. **Given** the user is viewing their accounts, **When** they look at the UI, **Then** only friendly account names ("Checking", "Savings") are displayed, and no database or system account numbers/identifiers are visible.

---

### User Story 2 - Transfer Between Own Accounts (Priority: P1)

As an authenticated bank customer, I want to transfer money strictly between my Checking and Savings accounts, so that I can manage my funds.

**Why this priority**: Essential transactional feature for the application.

**Independent Test**: Can be fully tested by selecting Checking as the source, Savings as the destination, entering a valid transfer amount under COP 1,000,000 (which does not trigger MFA), and submitting, then verifying that both account balances update instantly and no same-account transfers can be submitted.

**Acceptance Scenarios**:

1. **Given** the user has a Checking balance of COP 5,000,000 and a Savings balance of COP 15,000,000, **When** they initiate a transfer of COP 500,000 from Checking to Savings, **Then** the COP 500,000 is deducted from Checking, added to Savings, and a transfer confirmation is shown instantly without triggering MFA.
2. **Given** the user has Checking selected as the source account, **When** they select Checking as the destination account and attempt to transfer, **Then** the system rejects the transfer with an error indicating that source and destination accounts must be different.
3. **Given** the user has a Checking balance of COP 50,000, **When** they try to transfer COP 100,000 from Checking to Savings, **Then** the system prevents the transfer and displays an "Insufficient Funds" error.

---

### User Story 3 - Transaction History & Pre-seeded Movements (Priority: P2)

As an authenticated bank customer, I want to review the transaction history (movements) associated with each of my accounts, focusing strictly on past transfers, so that I can keep track of all inter-account activity.

**Why this priority**: Focuses transaction history strictly on the Stage 1 scope (only transfers between own accounts) without introducing other payment or external systems.

**Independent Test**: Can be fully tested by selecting an account and verifying that exactly two historical transfers are pre-seeded with accurate directions, and that any new transfer adds an incoming/outgoing entry with no "resulting balance" column.

**Acceptance Scenarios**:

1. **Given** the user has launched the application, **When** they check the transaction history, **Then** they see exactly two pre-seeded historical transfers:
   - Transfer 1: COP 500,000 from Savings to Checking (represented as Incoming/Credit on Checking, Outgoing/Debit on Savings).
   - Transfer 2: COP 100,000 from Checking to Savings (represented as Outgoing/Debit on Checking, Incoming/Credit on Savings).
2. **Given** the user is viewing the transaction history, **When** they review the entries, **Then** the system displays the transaction date, amount, description, and direction (Incoming/Outgoing), but does NOT display or require storing a "resulting balance" after each transaction.

---

### User Story 4 - Mock Multi-Factor Authentication (MFA) & State Machine (Priority: P2)

As an authenticated bank customer executing a sensitive transfer operation (amount >= COP 1,000,000), I want to perform a mock multi-factor authentication (MFA) verification, with a clear state machine tracking the transaction status, so that my high-value transactions are protected.

**Why this priority**: Satisfies the security requirement for high-value operations by demonstrating simulated step-up verification and lifecycle states.

**Independent Test**: Can be fully tested by initiating a transfer of COP 1,500,000, submitting, entering the incorrect code to keep it `PENDING_MFA`, waiting 5 minutes to see it become `EXPIRED` on a confirmation attempt, or entering the correct code `123456` within 5 minutes to complete the transfer.

**Acceptance Scenarios**:

1. **Given** the user initiates a transfer of COP 1,200,000 from Savings to Checking, **When** they click submit, **Then** the system creates a transfer in `PENDING_MFA` state and displays the MFA code entry overlay.
2. **Given** the transfer is in `PENDING_MFA` state, **When** the user enters an incorrect MFA code, **Then** the system displays a verification error, keeps the transfer in the `PENDING_MFA` state, and allows the user to retry the code.
3. **Given** the transfer is in `PENDING_MFA` state, **When** the user closes or cancels the MFA modal, **Then** the transfer remains persisted as `PENDING_MFA` in the database, account balances remain unchanged, and the transfer can still be confirmed if the 5-minute active window has not passed.
4. **Given** the transfer has been in `PENDING_MFA` state for more than 5 minutes, **When** the user attempts to confirm the transfer, **Then** the backend detects that the pending transfer has expired, transitions its state to `EXPIRED`, rejects the confirmation, and leaves account balances unchanged.
5. **Given** the transfer is in `PENDING_MFA` state, **When** the user enters the correct code `123456` within the 5-minute window, **Then** the backend re-validates that the source account balance is still sufficient, and if sufficient:
   - The transfer is executed successfully.
   - The transfer state transitions to `COMPLETED`.
   - The account balances are updated.
6. **Given** the transfer is in `PENDING_MFA` state, **When** the user enters the correct code `123456` but the source balance is no longer sufficient (e.g., due to an overlapping action), **Then** the transfer transitions to the `FAILED` state and balances remain unchanged.

### Edge Cases

- What happens if a transfer is initiated for exactly COP 1,000,000? (This is a sensitive transfer and MUST transition to the `PENDING_MFA` state.)
- What happens if a transfer is submitted with a non-positive amount (e.g., COP 0 or negative)? (The system MUST reject the transfer immediately with an error before initiating any states or MFA prompts.)
- What happens if the mock MFA code entry modal is closed or cancelled by the user? (System MUST NOT delete the transfer, modify balances, or create a CANCELED state. The transfer remains `PENDING_MFA` and can be retrieved and completed as long as it has not expired.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display exactly two accounts for the pre-authenticated user: Checking account (starting balance COP 5,000,000) and Savings account (starting balance COP 15,000,000).
- **FR-002**: System MUST NOT display account numbers or internal identifiers in the user interface. Accounts must be identified in the UI solely by their friendly names ("Checking", "Savings").
- **FR-003**: System MUST allow transferring funds strictly between the user's Checking and Savings accounts.
- **FR-004**: System MUST explicitly reject transfers where the source and destination are the same account.
- **FR-005**: Overdraft is strictly NOT allowed; system MUST prevent and reject transfers that exceed the available source account balance.
- **FR-006**: System MUST reject any transfer amounts that are less than or equal to zero.
- **FR-007**: System MUST support a transaction history focusing exclusively on movements produced by transfers between the Checking and Savings accounts. No deposits, withdrawals, or other transaction types are supported.
- **FR-008**: System MUST pre-seed exactly two completed historical transfers:
  - Transfer 1: COP 500,000 from Savings to Checking
  - Transfer 2: COP 100,000 from Checking to Savings
- **FR-009**: System MUST display the direction (Incoming/Outgoing), date, amount, and description in the transaction history, but MUST NOT store or display the resulting balance after each transaction.
- **FR-010**: System MUST define an MFA State Machine for sensitive transfers (amount greater than or equal to COP 1,000,000) containing exactly four states: `PENDING_MFA`, `COMPLETED`, `FAILED`, and `EXPIRED`.
- **FR-011**: Closing or cancelling the MFA modal MUST NOT execute the transfer, modify account balances, delete the transfer record, or introduce a CANCELED state. The transfer record MUST remain `PENDING_MFA` and can still be confirmed during its active five-minute window.
- **FR-012**: MFA expiration MUST NOT require a background scheduler, worker, daemon, or active timer process. Instead, when a confirmation is attempted after the five-minute deadline, the backend MUST detect that the transfer has expired, transition its state to `EXPIRED`, reject the execution request, and leave account balances unchanged.
- **FR-013**: System MUST allow infinite retries of incorrect MFA codes during the 5-minute active window. Lockout is NOT required for Stage 1.
- **FR-014**: System MUST re-validate the source account balance at the exact moment of MFA confirmation.
- **FR-015**: System MUST persistently store all application state—including accounts, current balances, transaction histories, transfer records, transfer states, and pending MFA transfers—on the server side so that it persists across requests and server restarts.

### Key Entities *(include if feature involves data)*

- **Bank Account**: Represents a mock user's financial account. Attributes include: Internal ID (UUID/Integer, hidden from UI), Account Type (Checking, Savings), Current Balance, Currency (strictly COP).
- **Transfer**: Represents a transaction between Checking and Savings accounts. Attributes include: Internal ID, Source Account ID, Destination Account ID, Amount, Timestamp, State (`PENDING_MFA`, `COMPLETED`, `FAILED`, `EXPIRED`), MFA Expiration Timestamp (exactly 5 minutes after creation).
- **Transaction History Entry**: Represents a movement. Attributes include: ID, Account ID, Transfer ID, Direction (`Incoming`, `Outgoing`), Amount, Date, Description.

## Success Criteria *(mandatory)*

### Functional Completeness & Correctness

- **SC-001**: 100% of sensitive transfers (>= COP 1,000,000) correctly transition through `PENDING_MFA`, requiring the code `123456` for execution.
- **SC-002**: 100% of sensitive transfers left in `PENDING_MFA` for > 5 minutes transition to `EXPIRED` on-demand upon the next confirmation attempt, returning a clear error and preventing transfer execution. No active background daemon or worker is required.
- **SC-003**: 100% of cancelled or closed MFA modals keep the transfer as `PENDING_MFA` without balance modifications, deletions, or state changes, allowing subsequent valid confirmation until expiration.
- **SC-004**: 100% of transfers with incorrect MFA codes remain `PENDING_MFA` without balance changes and allow retries.
- **SC-005**: 100% of same-account transfers, non-positive amounts, or insufficient-fund transfers are strictly rejected with helpful, user-friendly error messages before any state transitions.
- **SC-006**: The transaction history displays exactly two pre-seeded historical transfers on initialization, maps incoming/outgoing directions accurately, and does not require or display a resulting balance column.
- **SC-007**: Both accounts and transaction histories are displayed in the UI strictly using friendly names without showing database keys, system UUIDs, or internal account numbers.
- **SC-008**: 100% of application state modifications (transfers, balance changes, histories, and states) are permanently saved on the server-side, with full recovery and consistency verified after server resets.

## Assumptions

- **A-001**: The user session is pre-authenticated with a hardcoded mock user; login, registration, and session timeouts are out of scope for Stage 1.
- **A-002**: The server-side state is persistent; however, the explicit database or storage engine technology is kept abstract in this specification to maintain technology neutrality.
- **A-003**: The Python backend and React/TypeScript frontend are selected technology constraints but spec remains focused on business-level deliverables.
