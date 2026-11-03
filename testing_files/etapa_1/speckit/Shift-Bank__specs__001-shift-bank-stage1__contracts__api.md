# API Interface Contracts: Shift Bank Stage 1 (Revised)

This document defines the REST API endpoints exposed by the Python FastAPI backend to the React frontend. 

All monetary values are parsed as `decimal.Decimal` on the server and are represented as exact **decimal strings** in JSON request and response payloads to prevent binary floating-point rounding errors.

---

## 1. Get Bank Accounts
Retrieves the user's accounts with their balances. The UI only displays the friendly name, but the API provides the ID for frontend logic.

- **Endpoint**: `GET /api/accounts`
- **Response Code**: `200 OK`
- **Response Payload**:
  ```json
  [
    {
      "id": "acc_checking_123",
      "name": "Checking",
      "balance": "5000000.00",
      "currency": "COP"
    },
    {
      "id": "acc_savings_456",
      "name": "Savings",
      "balance": "15000000.00",
      "currency": "COP"
    }
  ]
  ```

---

## 2. Get Account Transaction History
Retrieves the chronological list of completed transfers for a specific account. The list is obtained by searching the `transfers` table for matching source or destination IDs with status `COMPLETED`.

- **Endpoint**: `GET /api/accounts/{account_id}/history`
- **Response Code**: `200 OK`
- **Response Payload**:
  ```json
  [
    {
      "id": "tr_seeded_2",
      "direction": "outgoing",
      "amount": "100000.00",
      "description": "Transfer to Savings",
      "date": "2026-09-30T10:05:00Z"
    },
    {
      "id": "tr_seeded_1",
      "direction": "incoming",
      "amount": "500000.00",
      "description": "Transfer from Savings",
      "date": "2026-09-30T10:00:00Z"
    }
  ]
  ```

---

## 3. Initiate Transfer
Submits a request to transfer funds. 

- **Endpoint**: `POST /api/transfers`
- **Request Payload**:
  ```json
  {
    "source_account_id": "acc_checking_123",
    "destination_account_id": "acc_savings_456",
    "amount": "1500000.00"
  }
  ```

### 3.1 Response (Standard Transfer - Amount < COP 1,000,000)
Executes immediately. No `expires_at` is generated or returned since MFA is not applicable (returned as `null`).
- **Response Code**: `200 OK`
- **Response Payload**:
  ```json
  {
    "id": "tr_new_789",
    "source_account": "Checking",
    "destination_account": "Savings",
    "amount": "100000.00",
    "status": "COMPLETED",
    "created_at": "2026-09-30T12:00:00Z",
    "expires_at": null
  }
  ```

### 3.2 Response (Sensitive Transfer - Amount >= COP 1,000,000)
Requires step-up MFA verification. `expires_at` is filled with creation + 5 minutes.
- **Response Code**: `202 Accepted`
- **Response Payload**:
  ```json
  {
    "id": "tr_new_456",
    "source_account": "Checking",
    "destination_account": "Savings",
    "amount": "1500000.00",
    "status": "PENDING_MFA",
    "created_at": "2026-09-30T12:05:00Z",
    "expires_at": "2026-09-30T12:10:00Z"
  }
  ```

### 3.3 Response (Immediate Errors)
Same-account, non-positive amount, or insufficient funds.
- **Response Code**: `400 Bad Request`
- **Response Payload**:
  ```json
  {
    "detail": "Source and destination accounts must be different."
  }
  ```

---

## 4. Confirm MFA Code
Submits the six-digit MFA code to execute a sensitive transfer. Expiration is validated **on-demand** at this step. Balance is **re-validated** at this step. Successful execution is fully **atomic** using Python `decimal.Decimal` math.

- **Endpoint**: `POST /api/transfers/{transfer_id}/mfa`
- **Request Payload**:
  ```json
  {
    "code": "123456"
  }
  ```

### 4.1 Response (Successful Completion)
- **Response Code**: `200 OK`
- **Response Payload**:
  ```json
  {
    "id": "tr_new_456",
    "status": "COMPLETED",
    "message": "Transfer executed successfully"
  }
  ```

### 4.2 Response (MFA Invalid - Retry Allowed)
The transfer stays as `PENDING_MFA`.
- **Response Code**: `401 Unauthorized`
- **Response Payload**:
  ```json
  {
    "id": "tr_new_456",
    "status": "PENDING_MFA",
    "detail": "Invalid MFA verification code. Please retry."
  }
  ```

### 4.3 Response (Transfer Expired - Evaluated On-Demand)
- **Response Code**: `410 Gone`
- **Response Payload**:
  ```json
  {
    "id": "tr_new_456",
    "status": "EXPIRED",
    "detail": "MFA verification window has expired."
  }
  ```

### 4.4 Response (Transfer Failed - Insufficient Balance at Confirmation)
- **Response Code**: `409 Conflict`
- **Response Payload**:
  ```json
  {
    "id": "tr_new_456",
    "status": "FAILED",
    "detail": "Insufficient funds at confirmation time."
  }
  ```
