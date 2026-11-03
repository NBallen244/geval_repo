# Research Log: Shift Bank Stage 1 (Revised)

This document consolidates the key architecture choices, rationales, and alternatives evaluated for the Shift Bank Stage 1 technical baseline, synchronized with the latest approved specifications.

---

### Decision 1: Backend Framework
- **Chosen**: Python 3.13 with FastAPI.
- **Rationale**: FastAPI is high-performance, easy to document, and natively supports Pydantic models for request/response validation. It matches the Python 3.13 constraint perfectly.
- **Alternatives Considered**: Flask (rejected because it requires manual validation boilerplate and lacks built-in async support; FastAPI is more proportional and robust for simple REST boundaries).

---

### Decision 2: Persistence Layer & ORM Exclusion
- **Chosen**: SQLite using Python's built-in `sqlite3` module directly (no ORMs).
- **Rationale**: Direct SQL execution using the built-in module avoids external library overhead (SQLAlchemy, Peewee) and aligns with the mandate to keep the Stage 1 architecture simple and proportional.
- **Alternatives Considered**: SQLAlchemy / SQLModel (rejected because they introduce unnecessary layers of complexity, abstraction, and dependencies not proportional to a simple two-table Stage 1 design).

---

### Decision 3: Financial Calculations & API Representation
- **Chosen**: Python's `decimal.Decimal` module for all calculations. API inputs and outputs are strictly represented as decimal strings (e.g., `"1500000.00"`).
- **Rationale**: Binary floating-point representation (IEEE 754 float types) inherently suffers from rounding issues, which is unacceptable for financial software. Storing and exposing decimals as strings ensures exact precision across client/server boundaries.
- **Alternatives Considered**: Floating-point values (rejected due to precision loss); Integer Cents representation (rejected because Decimal strings are more readable and robust for a Colombian Peso (COP) currency with zero decimal subdivisions but standard decimal API conventions).

---

### Decision 4: UI Styling
- **Chosen**: Vanilla CSS only.
- **Rationale**: Prevents package bloat, maintains pure standards-based web layouts, and stays 100% tool-neutral.
- **Alternatives Considered**: Tailwind CSS / Bootstrap (rejected because adding an external compilation utility or heavy framework goes against the tool-neutral and stage-proportional mandate).

---

### Decision 5: MFA Expiration Strategy (On-Demand)
- **Chosen**: Expiration detection occurs entirely **on-demand** at verification time, storing the state persistently as `EXPIRED` in the database once detected during a confirmation request.
- **Rationale**: Eliminates the need for a background scheduler, worker thread, cron, daemon, or active browser-timer, significantly reducing system complexity and remaining 100% compliant with Stage 1's lightweight, minimal architecture requirements.
- **Alternatives Considered**: Background Scheduler/Celery (rejected as over-engineered and non-proportional); Client-only timers (rejected as insecure since the server must strictly enforce the 5-minute active validation window).

---

### Decision 6: Atomic Database Transactions & Python Decimal Math
- **Chosen**: Explicit transaction blocks where all monetary arithmetic is performed on the server inside Python using `decimal.Decimal` (never using SQL casts, SQL arithmetic, or SQLite REAL).
- **Rationale**:
  - Direct SQL CASTs to `REAL` or SQL-level math introduce IEEE-754 floating-point rounding errors at the database layer.
  - Within a single transaction (`BEGIN TRANSACTION` -> `COMMIT`), the backend queries the persisted decimal strings, parses them as `decimal.Decimal` in Python, executes the math, formats the results back to decimal strings, and updates SQLite using parameterized `UPDATE accounts SET balance = ? WHERE id = ?` statements.
  - If confirmation fails because source funds are insufficient (a business-level rule), account balances are NOT modified; instead, the transfer state transitions to `FAILED` and this state transition is permanently committed. ROLLBACK is strictly reserved for unexpected technical or database-level exceptions (e.g., syntax errors, connection drops, SQLite locks) where safe transaction completion is impossible.
- **Alternatives Considered**: SQL CAST arithmetic (rejected due to precision loss risks); DB-level triggers (rejected as unnecessary complexity).

---

### Decision 7: Minimal Dev-Time Communication Strategy
- **Chosen**: FastAPI's native **CORS Middleware** (`fastapi.middleware.cors.CORSMiddleware`) configured to explicitly allow origin `http://localhost:5173`.
- **Rationale**:
  - Provides a single, deterministic, zero-infrastructure communication strategy appropriate for Stage 1.
  - It does not introduce any API gateways, Nginx proxies, service meshes, or additional container/network layers.
  - Eliminates alternative Vite local proxies to keep the strategy fully deterministic.
- **Alternatives Considered**: Vite Server Proxy (rejected to maintain a single deterministic approach and avoid local configuration discrepancies); Nginx reverse proxy (rejected as unnecessary infrastructure overhead).
