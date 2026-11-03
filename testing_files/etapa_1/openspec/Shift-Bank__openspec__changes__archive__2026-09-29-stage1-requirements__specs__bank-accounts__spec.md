## Purpose

Provides a secure view of the bank accounts and current balances associated with the pre-authenticated user in Colombian Pesos (COP).

## ADDED Requirements

### Requirement: Display accounts and balances
The system MUST allow the mock authenticated user Jane Doe (User ID `usr_101`) to view exactly two accounts: a Checking Account (`Cuenta Corriente`) and a Savings Account (`Cuenta de Ahorros`), including their respective current persisted balances represented in COP. The balances of 5.000.000,00 COP for Checking and 15.000.000,00 COP for Savings are the initial seeded balances only; subsequent views MUST display updated balances reflecting completed transfers.

#### Scenario: User loads dashboard initially
- **WHEN** the user views the main accounts overview before any transfers are performed
- **THEN** the system displays "Cuenta Corriente" with initial balance 5.000.000,00 COP and "Cuenta de Ahorros" with initial balance 15.000.000,00 COP

#### Scenario: User views dashboard after a completed transfer
- **WHEN** a transfer of 1.000.000,00 COP from Savings to Checking is COMPLETED and the user views the main accounts overview
- **THEN** the system displays "Cuenta Corriente" with updated balance 6.000.000,00 COP and "Cuenta de Ahorros" with updated balance 14.000.000,00 COP
