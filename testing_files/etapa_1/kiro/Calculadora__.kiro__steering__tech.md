# Tech Stack & Commands

## Backend

- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Server:** uvicorn (`uvicorn[standard]`)
- **Validation/models:** Pydantic v2 (`pydantic>=2.6`)
- **Arithmetic:** the standard-library `decimal` module (exact decimal, never `float`)
- **Testing:** pytest + Hypothesis (property-based); httpx for the FastAPI TestClient
- **Config:** `backend/pyproject.toml` (dependencies, pytest config)

### Backend commands

Run from `backend/`. A virtual environment lives at `backend/.venv`.

```powershell
# One-time setup
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"

# Run the API (dev)
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Run tests
.\.venv\Scripts\python.exe -m pytest -q
```

## Frontend

- **Language:** TypeScript (strict mode)
- **Framework:** React 18
- **Build tool:** Vite 5
- **Testing:** Vitest + React Testing Library (jsdom), MSW for network mocking
- **Linting:** ESLint (flat config) with `@typescript-eslint/no-explicit-any: error`
  over `src/**`
- **Config:** `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig*.json`,
  `frontend/eslint.config.js`

### Frontend commands

Run from `frontend/`.

```powershell
npm install         # install dependencies
npm run dev         # Vite dev server (proxies /api -> http://localhost:8000)
npm run build       # tsc --noEmit && vite build
npm run typecheck   # tsc --noEmit
npm run lint        # eslint .
npm run test        # vitest run (single pass)
```

> Note: do not launch long-running dev servers as blocking commands in automation.
> Run `npm run dev` / uvicorn `--reload` manually in a terminal.

## Local wiring

The Vite dev server proxies any `/api` request to the FastAPI backend at
`http://localhost:8000`, so the frontend calls the relative path
`/api/v1/evaluate`. CORS on the backend also allows the Vite origins
(`localhost:5173`, `localhost:3000`).

## Verification expectations

- After backend changes: run pytest; confirm the API returns correct results and
  4xx errors via the TestClient.
- After frontend changes: `npm run build` (type-check + build) and `npm run lint`
  must pass clean. No `any` in client code.
