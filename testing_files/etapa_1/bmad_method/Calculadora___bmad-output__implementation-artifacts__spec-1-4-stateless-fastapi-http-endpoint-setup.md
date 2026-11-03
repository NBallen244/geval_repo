---
title: Stateless FastAPI HTTP Endpoint Setup
type: feature
created: 2026-09-28
status: done
route: oneshot
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The mathematical engine is a local Python library and lacks an HTTP endpoint, meaning the frontend client cannot execute expression calculations remotely or display live previews over standard web protocols.

**Approach:** Build a stateless FastAPI application exposing the REST endpoint `POST /api/v1/evaluate`. It will receive mathematical expression payloads, validate them, invoke our safe decimal parsing engine, and serialize exact responses back as structured JSON payloads (returning HTTP 200 for successes and standardized HTTP 422 error structures for math/syntax exceptions).

</frozen-after-approval>

## Implementation Notes

- **Decisions Made:** Implemented a stateless FastAPI application featuring explicit CORS wildcard configurations, a root `/` GET monitoring health-check, Pydantic validation error interception overrides (prefixing all standard missing fields or type errors with `Error: `), and a dedicated `/api/v1/evaluate` POST route returning fully flattened, unnested JSON payloads. Used Pydantic `Literal` fields for strict API response status typings.
- **Files Touched/Created:**
  - `backend/app/main.py` - FastAPI app shell with global CORS, root health endpoints, and request exception handlers.
  - `backend/app/routers/evaluate.py` - Standardized REST endpoint router and schema definitions.
  - `backend/tests/test_api.py` - Completed endpoint integration tests (success, zeros, unbalanced, whitespace, validation format, and health endpoints).
- **Surprises:** Standard FastAPI `HTTPException` wraps error contents under a nested `"detail"` response key by default. To output the clean, flat `ErrorResponse` schema directly, we refactored evaluate.py's error branch to return flat `JSONResponse` payloads instead.

## Review Triage Log

| Finding | Verdict | Evidence |
| :--- | :--- | :--- |
| **Wildcard CORS Origins allowed** | `low` | Intended for a local responsive web prototype. CORS configurations are documented for production-bound restrictions. |
| **`errors()[0]` IndexError risk** | `low` | **Patched!** Added explicit length checks inside the validation handler before array indexing. |
| **No request size or complexity boundaries (DoS)** | `low` | Inputs are browser-typed, standard web servers and python environments provide default stack boundaries. |
| **Slightly different schema formats on Validation Handler vs ErrorResponse** | `low` | Standard and acceptable for distinguishing custom mathematical errors from Pydantic input body schema parsing failures. |
| **Brittle exception substring checks** | `low` | The math engine raises strictly standardized error messages controlled inside our private library, preventing silent drift. |
| **Missing root healthcheck endpoint** | `medium` | **Patched!** Appended GET `/` health check route returning standard API status metadata. |
| **Response status schemas are open strings rather than strict literal typings** | `high` | **Patched!** Refactored schemas to utilize strict Pydantic `Literal["success"]` and `Literal["error"]` properties. |
| **No rate limiting or timeouts** | `low` | Computational load is minimal for a standard desktop calculator MVP. |
| **No structured logging library** | `low` | Output streaming via standard FastAPI console logs is sufficient for prototype audits. |

