# Design

## Context

We are implementing a greenfield Stage 1 e-commerce application with a strict separation between user interface and server-side logic. The frontend and backend run as completely separate components, communicating exclusively via a clear HTTP/JSON RESTful interface. 

See `proposal.md` for overall motivation and goals, and `specs/stage-1-ecommerce/spec.md` for functional requirements.

## Goals / Non-Goals

**Goals:**
- Provide a clean, separate folder structure for `frontend` and `backend` that can be started and reviewed independently.
- Implement a robust, instant-responsiveness client-side local cart using React state management.
- Establish a lightweight, reliable database persistence mechanism for catalog products and registered users.
- Apply secure password hashing practices appropriate for academic scope (no plain text passwords).
- Structure forms with robust validations and clear feedback.
- Strictly write all user-facing interface text, source-code identifiers, code comments, and technical documentation in English.

**Non-Goals:**
- Production infrastructure setups, containers (Docker), or CI/CD pipelines.
- Multi-factor authentication, third-party authentication providers, or password recovery.
- Real-time inventory tracking, dynamic shipping, or actual payment gateway integrations.
- Production-grade relational database servers (e.g., PostgreSQL, MySQL) or advanced connection pooling.
- Durable shopping cart persistence across browser restarts.

## Decisions

### Decision 1: Frontend Tooling & Framework
- **Choice:** Vite + React (TypeScript template)
- **Rationale:** Vite provides an ultra-fast, modern development server, hot module replacement, and excellent TypeScript support out-of-the-box. It keeps the bundle extremely lightweight and adheres perfectly to the React and TypeScript frontend requirement.
- **Alternatives Considered:** Create React App (slower, deprecated), Next.js (adds server-side rendering complexity which would blur the line of the requested pure backend/frontend separation).

### Decision 2: Backend Persistence Mechanism
- **Choice:** SQLite (via SQLAlchemy ORM in Python)
- **Rationale:** SQLite is a self-contained, serverless database engine included natively with Python. This eliminates the need for any local database installation or external services, making the application highly portable and easy to run during evaluation, while still supporting real registration, login, and catalog persistence.
- **Alternatives Considered:** In-memory Python dictionaries (resets data on every server restart, making registration/login testing cumbersome), PostgreSQL (requires external system dependencies and setup).

### Decision 3: Local Shopping Cart Management
- **Choice:** React Context API + Local State
- **Rationale:** The Context API provides a lightweight, native React pattern to share the cart state (add, update, remove, totals) across catalog, navigation header, and checkout screens. This ensures consistent quantities and prices across all views in real time.
- **Alternatives Considered:** Redux Toolkit or Zustand (unnecessary boilerplate for a Stage 1 application), pure prop-drilling (creates highly coupled and brittle component interfaces).

### Decision 4: Academic Security & Authentication
- **Choice:** Bcrypt hashing (via `passlib`) and in-memory Token-based Session management (e.g., HTTP Authorization header)
- **Rationale:** Fulfills the security mandate by hashing user passwords using bcrypt before storage. Login returns a session token which the frontend stores strictly in memory (within React state/context) and sends in the `Authorization` header for protected checkout requests. No durable client-side token persistence (such as `localStorage` or persistent cookies) is used, ensuring sessions do not persist across page reloads or browser restarts.
- **Alternatives Considered:** Plain-text comparison (unacceptable security risk even for academic demonstration), external identity providers like Auth0 (violates offline/simplicity goals).

## Risks / Trade-offs

- **[Risk: DB File Lock in SQLite]** → Because SQLite uses file-level locking, concurrent writes can cause locking.
  - **Mitigation:** Since this is a single-user demonstration application, the concurrent load will be negligible. We will configure SQLAlchemy connection pools with `check_same_thread=False` and use scoped sessions safely.
- **[Risk: Cross-Origin Resource Sharing (CORS) issues]** → The separate frontend and backend run on different ports (e.g., 5173 and 8000), causing browser CORS blocks.
  - **Mitigation:** Configure FastAPI's `CORSMiddleware` explicitly in the backend to allow requests from the frontend development server origin.
