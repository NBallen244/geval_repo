## Purpose

Enables secure monetary transfers exclusively between the mock authenticated user's own accounts using precise, decimal-safe arithmetic.

## ADDED Requirements

### Requirement: Transfer between own accounts
The system MUST allow the user to transfer funds from one of their accounts to the other (e.g., Checking to Savings or Savings to Checking) using decimal-safe monetary representation.

#### Scenario: Successful transfer under sensitive limit
- **WHEN** user requests a transfer of 150.000,00 COP from Checking to Savings
- **THEN** the system immediately debits 150.000,00 COP from Checking, credits 150.000,00 COP to Savings, and marks the transfer as COMPLETED

### Requirement: Validate transfers and reject invalid requests
The system MUST validate transfer inputs and reject requests that attempt self-transfers, use non-positive amounts, or exceed the available balance of the source account.

#### Scenario: Transfer to same account is rejected
- **WHEN** user requests a transfer with Checking as both source and destination
- **THEN** the system rejects the request and throws an error indicating self-transfer is forbidden

#### Scenario: Transfer with negative amount is rejected
- **WHEN** user requests a transfer with an amount of -50.000,00 COP
- **THEN** the system rejects the request and throws an error indicating amount must be positive

#### Scenario: Transfer with insufficient funds is rejected
- **WHEN** user requests a transfer of 6.000.000,00 COP from Checking which only has 5.000.000,00 COP
- **THEN** the system rejects the request and throws an error indicating insufficient funds

### Requirement: Source balance revalidation on confirmation
The system MUST re-evaluate the source account's available balance at the exact moment of transfer execution or MFA confirmation, rejecting the execution if the available balance has become insufficient.

#### Scenario: Balance depleted during pending MFA
- **WHEN** user confirms a pending transfer of 1.500.000,00 COP, but a separate concurrent transfer has already depleted the source account's balance below 1.500.000,00 COP
- **THEN** the system rejects the confirmation and marks the transfer as FAILED due to insufficient funds
