# API and Event Contracts: Stage 4 Microservices Migration

This document outlines the external REST interface presented by the HTTP Gateway, the internal microservice endpoints, and the AMQP integration contract.

---

## 1. Gateway Routing Table (Port 18600)

The Gateway maps external client requests on Port `18600` directly to the underlying internal microservices. No business operations are processed inside the Gateway; it acts as a transparent proxy.

| External Endpoint | HTTP Method | Target Service URL | Authenticated? |
| :--- | :--- | :--- | :--- |
| `/api/register` | `POST` | `http://127.0.0.1:18601/api/register` | No |
| `/api/signin` | `POST` | `http://127.0.0.1:18601/api/signin` | No |
| `/api/signout` | `POST` | `http://127.0.0.1:18601/api/signout` | Yes (Bearer token) |
| `/api/products` | `GET` | `http://127.0.0.1:18602/api/products` | No (Cached) |
| `/api/products/{id}/reviews` | `GET` | `http://127.0.0.1:18602/api/products/{id}/reviews` | No (Cached) |
| `/api/checkout` | `POST` | `http://127.0.0.1:18602/api/checkout` | Yes (Bearer token) |
| `/api/reviews` | `POST` | `http://127.0.0.1:18603/api/reviews` | Yes (Bearer token) |
| `/api/moderation/reviews` | `GET` | `http://127.0.0.1:18603/api/moderation/reviews` | Yes (Moderator Only) |
| `/api/moderation/reviews/{id}/status` | `POST` | `http://127.0.0.1:18603/api/moderation/reviews/{id}/status` | Yes (Moderator Only) |

---

## 2. Microservice REST Endpoints

### Identity Service (Port 18601)

#### `POST /api/register`
Registers a user account.
- **Request Body**:
  ```json
  {
    "identifier": "customer_username",
    "password": "secure_password"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "message": "Account successfully registered."
  }
  ```

#### `POST /api/signin`
Validates credentials and returns a cryptographically signed JWT.
- **Request Body**:
  ```json
  {
    "identifier": "customer_username",
    "password": "secure_password"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjdXN0b21lcl91c2VybmFtZSIsInJvbGUiOiJjdXN0b21lciIsImV4cCI6MTgwMDAwMDAwMH0..."
  }
  ```

#### `POST /api/signout`
Invalidates session (handled statelessly by client token disposal, but logged on backend).
- **Headers**: `Authorization: Bearer <token>`
- **Response** (`200 OK`):
  ```json
  {
    "message": "Session successfully terminated."
  }
  ```

---

### Commerce Service (Port 18602)

#### `GET /api/products`
Retrieves product list (seeded from catalog). Cached for 60s.
- **Response** (`200 OK`):
  ```json
  [
    {
      "product_id": "keyboard",
      "name": "Mechanical Keyboard",
      "representative_image": "...",
      "short_description": "...",
      "price": 89.99,
      "general_availability": "Yes"
    }
  ]
  ```

#### `GET /api/products/{product_id}/reviews`
Retrieves approved reviews from the local projection database. Cached for 60s.
- **Response** (`200 OK`):
  ```json
  [
    {
      "review_id": "r-1234",
      "product_id": "keyboard",
      "user_id": "some_user",
      "rating": 5,
      "comment": "Incredible keyboard!",
      "image_base64": null,
      "created_at": "2026-11-07T12:00:00Z"
    }
  ]
  ```

#### `POST /api/checkout`
Processes simulated checkout. Checks user role and token.
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "items": [
      {
        "product_id": "keyboard",
        "quantity": 1
      }
    ],
    "demonstration_info": {
      "address": "123 Main St",
      "accept_academic_disclaimer": "Yes"
    }
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "message": "Simulated purchase confirmed! No real payment gateway was contacted...",
    "purchase_summary": {
      "items": [
        {
          "product_id": "keyboard",
          "name": "Mechanical Keyboard",
          "quantity": 1,
          "unit_price": 89.99,
          "subtotal": 89.99
        }
      ],
      "accumulated_total": 89.99
    }
  }
  ```

---

### Reviews Service (Port 18603)

#### `POST /api/reviews`
Submits product review for moderation. Saves with `pending` status.
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "product_id": "keyboard",
    "rating": 5,
    "comment": "Highly recommend!",
    "image_base64": null
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "message": "Review submitted successfully and is pending moderation.",
    "review": {
      "review_id": "r-1234",
      "product_id": "keyboard",
      "user_id": "some_user",
      "rating": 5,
      "comment": "Highly recommend!",
      "image_base64": null,
      "status": "pending",
      "created_at": "2026-11-07T12:30:00Z"
    }
  }
  ```

#### `GET /api/moderation/reviews`
Lists all submitted reviews. Moderator only.
- **Headers**: `Authorization: Bearer <token>`
- **Response** (`200 OK`):
  ```json
  [
    {
      "review_id": "r-1234",
      "product_id": "keyboard",
      "user_id": "some_user",
      "rating": 5,
      "comment": "Highly recommend!",
      "image_base64": null,
      "status": "pending",
      "created_at": "2026-11-07T12:30:00Z"
    }
  ]
  ```

#### `POST /api/moderation/reviews/{review_id}/status`
Updates moderation status of a review. If status changes to `approved` or `rejected`, publishes integration event via Transactional Outbox.
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "status": "approved"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "message": "Review status updated successfully to 'approved'.",
    "review": {
      "review_id": "r-1234",
      "status": "approved"
    }
  }
  ```

---

## 3. RabbitMQ Event Contracts

### AMQP Configuration
- **Exchange**: `stage4.speckit.reviews` (Direct exchange, durable)
- **Routing Key**: `review.moderated`
- **Queue**: `stage4.speckit.commerce.reviews` (Durable, bound to the exchange with routing key `review.moderated`)

### Event Message Payload Schema
Every event published to RabbitMQ contains standard metadata wrappers for correlation, tracking, and consumer idempotency.

- **Event Type**: `review_moderated`
- **JSON Structure**:
  ```json
  {
    "event_id": "e674b2ca-5339-44d4-9fc2-6c24b9c9f28d",
    "correlation_id": "f5f5c947-66a9-4676-963b-6e9f5287f39b",
    "event_type": "review_moderated",
    "timestamp": "2026-11-07T12:35:00.123456Z",
    "payload": {
      "review_id": "r-1234",
      "product_id": "keyboard",
      "user_id": "some_user",
      "rating": 5,
      "comment": "Highly recommend!",
      "image_base64": null,
      "status": "approved",
      "created_at": "2026-11-07T12:30:00Z"
    }
  }
  ```
