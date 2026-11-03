# Technical Design - Stage 1 E-Commerce

This document provides a minimal, high-level technical design for Stage 1. It is directly traceable to the canonical seed and avoids prescribing unestablished details.

## 1. Architectural Style & Separation of Concerns
The application is structured as a decoupled client-server architecture consisting of:
1. **Frontend Component**: A single-page application built using React and TypeScript. Responsible for rendering the user interface, managing local shopping cart state, and capturing user actions.
2. **Backend Component**: A server-side application built using Python and FastAPI. Responsible for serving product catalog data, managing user registration/sessions, and validating checkout requests.

*Traceability: REQ-TEC-1, REQ-TEC-2, REQ-TEC-3, REQ-TEC-4.*

## 2. Component Layout & Execution Model
- **Structure**: The project directory will separate the frontend and backend into individual root-level subdirectories to ensure they can be run and reviewed independently.
- **Build & Run**: Each component will contain its own instructions/scripts so that the frontend developer can run the UI, and the backend developer can run the server separately.

*Traceability: REQ-TEC-4.*

## 3. Communication Interface
- **Mechanism (Derived Decision)**: To communicate between the client and server, the React frontend and FastAPI backend will interact using standard HTTP REST endpoints with JSON payloads. This derived decision is the minimal standard mechanism to support a decoupled client-server setup.
- **Endpoints (High-Level)**:
  - **Catalog**: The backend will expose a read-only catalog interface to fetch products.
  - **Authentication**: The backend will expose interfaces for customer registration and session verification (sign-in, sign-out).
  - **Checkout**: The backend will expose a fictitious checkout validation interface.

*Traceability: REQ-TEC-3, REQ-CAT-1, REQ-ATH-1, REQ-ATH-3, REQ-CHK-1.*

## 4. Data Persistence & Demonstration Mechanisms
- **Demonstration Data Store (Derived Decision)**: As established by the seed, the application does not require a production database or persistent database management system.
- **Implementation Strategy**:
  - **Catalog Data**: Hardcoded or loaded from a simple JSON file on the backend server.
  - **Account Data**: Stored using a simple server-side in-memory mechanism (e.g., in-memory dictionaries or lists). Data will persist for the duration of the active backend process lifecycle.
  - **Cart Data**: Managed completely in-memory on the frontend (local state), satisfying the requirement that durable persistence across browser closures is not mandatory.

*Traceability: REQ-TEC-5, REQ-CRT-5.*

## 5. Security & Academic Constraints
- **Password Security**: Passwords sent during registration/login must never be logged or stored in plain text. The backend will hash passwords using a standard hashing algorithm before saving them in the simple demo data store.
- **Error Handling**: Forms and API validation will return meaningful errors to the user but will omit internal system stack traces or sensitive environment variables.

*Traceability: REQ-ATH-4, REQ-ATH-5.*
