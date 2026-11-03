# Technical Architecture Specification - Stage 1 E-Commerce Case

This document details the software architecture for Stage 1. It distinguishes strictly between the **Canonical Technical Requirements** established directly by the source seed, and the **Derived Implementation Decisions** made to complete the system structure.

---

## 1. Canonical Technical Requirements
These requirements represent the mandatory technical constraints and boundaries established by `especificacion-semilla-final-en.md`. They must be followed without exception:

- **Frontend Technology**: React and TypeScript.
- **Backend Technology**: Python and FastAPI.
- **Tier Separation**: Absolute separation between user interface (Frontend) and server-side logic (Backend). Presentation, business logic, and data access must not be mixed unnecessarily.
- **Communication Interface**: The frontend and backend communicate through a clear, decoupled interface (API) using standard HTTP protocols.
- **Independent Execution**: The project structure must allow the frontend and backend to be run and reviewed separately as independent components.
- **Demonstration Data Storage**: The product catalog and user account storage must use simple mechanisms appropriate for a demonstration environment.
- **Security Constraint**: User passwords must not be displayed or stored as readable plain text.
- **Language Requirement**: All source-code identifiers, comments, technical documentation, and user-facing copy must be written in English.
- **Stage Boundaries**: No containers (Docker), continuous integration or deployment (CI/CD) pipelines, mandatory end-to-end test runners, API caching, or distributed database configurations are included.

---

## 2. Repository and Directory Structure
The repository structure supports separate frontend and backend execution:

```
stage-1-root/
│
├── frontend/                     # React + TypeScript Frontend Application
└── backend/                      # Python + FastAPI Backend Application
```

---

## 3. Derived Implementation Decisions
The following choices are not mandated by the canonical seed but are necessary to build a working, concrete application. They are specified here to guide implementation without introducing any new fields, numerical limits, business logic, or quality targets not established in the seed:

### 3.1 Styling and UI Presentation
- **Decision**: Frontend styling is implemented using standard CSS (Vanilla CSS).
- **Rationale**: Provides maximum styling flexibility and responsive control on desktop and mobile screens while avoiding heavy dependencies or complex CSS builds.

### 3.2 Frontend State and Client Architecture
- **Decision**: React Context (or React state hooks) is used to track the local shopping cart and active session status.
- **Rationale**: Allows immediate, responsive visual updates across components when items are added/removed, quantities adjusted, or session states change, without requiring high-overhead external state managers.
- **Field Constraints**: No specific fields (e.g., email or confirmation parameters) are introduced here; states track only the minimum customer identification and item references necessary to fulfill the journey.

### 3.3 Backend Execution and Server Stack
- **Decision**: Uvicorn is selected as the ASGI server to run the FastAPI application.
- **Rationale**: Industry-standard, lightweight runner for Python FastAPI applications.

### 3.4 Storage Mechanism
- **Decision**: Catalog data is retrieved from a static data structure (such as a local JSON file or a hardcoded dictionary structure) on the backend. Account credentials are stored in-memory (re-initialized on server restart) or in a simple local SQLite file database.
- **Rationale**: Minimal complexity suitable for academic demonstrations.
- **Credential Storage Security**: Passwords are hashed on the server side using a standard Python cryptographic hashing utility before storage.

### 3.5 Interface Protocol (API contract placeholder)
- **Decision**: The communication interface implements simple REST-like JSON endpoints:
  - **Catalog Endpoint**: Returns a list of products with the mandatory fields (name, image, description, price, availability).
  - **Authentication Endpoints**: Accepts the minimum credentials required to register and sign in a customer, returning active session confirmations without disclosing plain-text secrets.
  - **Checkout Endpoint**: Accepts the summary list of items and quantities along with the minimum demonstration information necessary to finish the simulated checkout, returning a fictitious purchase confirmation.
- **Field Constraints**: No custom field types (such as address lists, tax rates, or gateway fields) are introduced. Endpoints deal only with abstract identifier structures matching the minimum needs of the seed.
