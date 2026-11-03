## Purpose

Maintains and displays a chronological ledger of all completed and pending transfers, showing incoming and outgoing movements per account.

## ADDED Requirements

### Requirement: Chronological ledger of movements
The system MUST record all transfers and make them queryable as a historical ledger of movements. Each record includes unique ID, source account, destination account, amount, timestamp, and status.

#### Scenario: User views transaction history
- **WHEN** user requests transaction history
- **THEN** the system returns a chronological list of recent transfers, including pre-seeded transactions and newly completed ones

### Requirement: Show both incoming and outgoing movements for each account
The system MUST retrieve and filter transactions such that viewing an individual account shows all movements where that account was either the source (outgoing debit) or the destination (incoming credit).

#### Scenario: User filters movements for Checking account
- **WHEN** user views movements specifically for the Checking Account (`Cuenta Corriente`)
- **THEN** the system displays all transactions where Checking Account is the source OR Checking Account is the destination
