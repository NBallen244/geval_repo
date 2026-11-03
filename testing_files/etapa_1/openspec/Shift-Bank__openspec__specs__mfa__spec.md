# mfa Specification

## Purpose
Protects sensitive transfers equal to or exceeding COP 1,000,000 by requiring verification with a mock multi-factor authentication (MFA) code within a 5-minute expiration window.

## Requirements

### Requirement: Sensitive transfers threshold
The system MUST intercept any transfer request with an amount greater than or equal to 1.000.000,00 COP, marking its initial status as PENDING_MFA and requiring explicit confirmation with an MFA code.

#### Scenario: Sensitive transfer initiated
- **WHEN** user initiates a transfer of 1.200.000,00 COP from Savings to Checking
- **THEN** the system does not immediately execute the transfer, but responds with a PENDING_MFA status and requests verification

### Requirement: Mock MFA verification code
The system MUST validate sensitive transfers using a fixed six-digit verification code of `123456`, refusing execution for any other submitted code.

#### Scenario: Confirming sensitive transfer with correct code
- **WHEN** user confirms a pending transfer of 1.200.000,00 COP with code "123456"
- **THEN** the system executes the transfer, debits the source, credits the destination, and marks status as COMPLETED

#### Scenario: Confirming sensitive transfer with incorrect code
- **WHEN** user confirms a pending transfer of 1.200.000,00 COP with code "999999"
- **THEN** the system rejects the confirmation with an invalid code error, leaves the transfer status as PENDING_MFA, and allows the user to re-attempt verification until the 5-minute window expires

### Requirement: Pending MFA expiration
The system MUST automatically expire a transfer in PENDING_MFA status if 5 minutes have elapsed since its initiation without a successful verification.

#### Scenario: Verification code submitted after 5 minutes
- **WHEN** user submits the correct code "123456" for a transfer initiated 6 minutes ago
- **THEN** the system rejects the confirmation indicating that the MFA session has expired, and marks the transfer status as EXPIRED
