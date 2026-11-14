# Design Document

## Overview

Stage 3, Option A extends the existing Stage 2 two-tier application (Python FastAPI backend in `backend/`, React + TypeScript client in `frontend/`) as a brownfield change. The backend remains the single authoritative owner of all game state and rules; the frontend renders backend state and forwards controls. Live game state stays in memory for the lifetime of a single backend worker.

Stage 3 adds, entirely alongside the existing layered backend and the existing frontend structure:

- a **high-score persistence module** backed by SQLite (Python standard-library `sqlite3`), initialized on application startup, that stores a one-row summary (`High_Score_Record`) per completed game (Requirements 1-4, 7);
- **finalization** at the controller/service boundary when a game's authoritative status first transitions to `game_over`, performed at most once per `game_id`. At that first terminal transition an immutable pending finalization record (`game_id`, `score`, `total_lines`, `level`, and `completed_at`, with `completed_at` generated once at terminal time) is captured on the in-memory game **before** any storage write is attempted; retries reuse that same captured record and never regenerate `completed_at`. A single consistent single-process locking boundary and a pending-finalization retry path guard the write (Requirements 2, 3, 7);
- a **leaderboard endpoint** `GET /api/high-scores` returning the top ten records in a fixed order (Requirement 5);
- **body-validation hardening** so public endpoints reject client-supplied score/metadata and unexpected fields while keeping the Stage 2 bodyless-create and valid-move contracts (Requirement 6);
- a **controlled JSON 503** for storage failures that leaks no internals (Requirement 7);
- a **frontend High Scores panel** with loading/empty/error states that fetches once on load and again on game-over only, a configurable same-origin API base, and restrictive configurable CORS (Requirements 8-10);
- **Docker packaging** (multi-stage backend and frontend images, `.dockerignore`, Compose with a named volume, non-root users, health checks, frontend-only published port) (Requirements 11-12);
- a **Playwright-driven browser benchmark harness** kept out of ordinary unit CI (Requirements 13-15);
- **continuous-integration** workflows for backend/frontend/build/image checks plus a separate manual performance job (Requirement 16).

This document states WHAT will be built and HOW. It does not claim that any build, test, audit, container run, CI run, or performance measurement has been executed.

### Preserved Stage 1 / Stage 2 contracts (baseline, unchanged)

Stage 3 preserves every inherited contract. These are inputs, not features to re-derive:

- `POST /api/games` returns **HTTP 200** (not 201) and still accepts a bodyless request.
- The JSON board is a 20x10 array of integer codes (`0` empty, `I=1, O=2, T=3, S=4, Z=5, J=6, L=7`).
- The active piece is exposed under the key `active_piece` with `type`, `origin`, `cells`.
- Spawn origin is `(row 0, column 3)`; pieces are the seven standard tetrominoes in initial (unrotated) orientation only.
- The piece generator is a seeded deterministic shuffled 7-bag; exactly one preview piece is exposed.
- Lock ordering is settle -> clear lines -> score/level/gravity using the pre-lock level -> spawn.
- Every state response includes `score`, `total_lines`, `level`, `gravity_interval_ms`, `next_piece`, `hold_piece`, `can_hold`. Scoring is `{0:0, 1:100, 2:300, 3:500, 4:800} * pre_lock_level`; `level = 1 + floor(total_lines / 10)`; `gravity_interval_ms = max(100, 500 - 50 * (level - 1))`.
- The frontend R1-R5 request-ordering and lifecycle guarantees in `useGame.ts` (generation tokens, per-generation FIFO serialization of all mutations, coalesced per-generation automatic-tick scheduler, dynamic gravity scheduling, stale-response discarding after both `fetch` and `response.json()` resolve, exact timeout cancellation/reschedule, StrictMode safety) are preserved.
- The engine functions in `app/rules/engine.py` remain pure (no FastAPI/`sqlite3` imports) so rules stay unit-testable.

## Architecture

```
                         Host
                           |
                   publish 5183 (frontend ONLY)
                           v
+--------------------------------------------------------------+
|  Docker Compose internal network (backend not published)     |
|                                                              |
|  +-------------------------+      /api proxy      +--------+ |
|  | frontend container      | ------------------->  | backend| |
|  | (multi-stage:           |                       | cont.  | |
|  |  node build -> nginx)   |   serves production    |        | |
|  | non-root user A         |   build of frontend/src|        | |
|  +-------------------------+                       +---+----+ |
|                                                        |      |
|                                   named volume (SQLite dir)   |
|                                     TETRIS_DB_PATH            |
+--------------------------------------------------------------+

Frontend (React + TS, frontend/src)
  |  HTTP JSON (configurable API base, default same-origin "/api")
  v
FastAPI app (backend/app)
  |-- main.py                 # app + lifespan: init High_Score_Store on startup;
  |                           #   restrictive configurable CORS; /health
  |-- api/games.py            # existing game routes; finalization wired here
  |                           #   (controller/service boundary, engine stays pure)
  |-- api/high_scores.py      # NEW controller: GET /api/high-scores
  |-- api/schemas.py          # MoveRequest/GameStateOut (extra="forbid");
  |                           #   NEW HighScoreEntryOut / HighScoresOut
  |-- service/finalization.py # NEW service: lock + finalize-on-game_over + retry
  |-- persistence/store.py    # NEW High_Score_Store (stdlib sqlite3)
  |-- store.py                # in-memory game repository (adds finalization marks)
  |-- rules/engine.py         # UNCHANGED pure rules (new_game/spawn/lock/tick/move/hold)
  |-- rules/pieces.py         # UNCHANGED shapes + seeded 7-bag
  +-- domain/models.py        # Game gains finalized / pending_finalization / completed_at

Out-of-band tooling (not shipped in runtime images, not in ordinary unit CI):
  perf/                       # Playwright-Chromium benchmark harness
  .github/workflows/ci.yml    # backend tests+coverage, frontend tests+build, image builds
  .github/workflows/perf.yml  # SEPARATE manual/explicit performance job
```

### Request flow (Stage 3 additions in **bold**)

1. `POST /api/games` -> `store.create()` -> `engine.new_game(seed)`; **rejects unexpected body fields (`extra="forbid"`)**; returns serialized state (unchanged shape), HTTP 200.
2. `GET /api/games/{id}` -> acquire the single-process lock, fetch; 404 if missing; **take a coherent read-only snapshot and serialize it under the same lock** with **no side effects: no generator draw, no counter change, no finalization record capture, no finalization, no finalization retry** (Requirements 3.3, 7.9).
3. `POST /api/games/{id}/tick` / `/move` / `/hold` -> acquire the single-process lock **once**, run the pure engine mutator, **then, if the authoritative status is now `game_over`, capture the immutable pending finalization record (on the first terminal transition only) and run finalization, or retry the already-captured pending finalization**, and **serialize the response while still holding that same lock** so the serialized response is a coherent immutable snapshot, then release the lock (Requirements 2, 3, 7).
4. **`GET /api/high-scores` -> `High_Score_Store.top_ten()`; returns `{"scores": [...]}`; storage failure -> controlled 503 (Requirement 5, 7).**

## Components and Interfaces

### High-score persistence module (`app/persistence/store.py`, new)

A thin wrapper over stdlib `sqlite3`. Chosen module path: `app/persistence/store.py` (new `app/persistence/` package), keeping persistence separate from the in-memory game `store.py`.

Responsibilities and interface:

```python
class StorageError(Exception):
    """Raised for any storage failure that must surface as a controlled 503.

    Carries no sensitive detail in its string representation that is forwarded
    to clients; the controller maps it to a generic message.
    """

class HighScoreStore:
    def __init__(self, db_path: str) -> None: ...

    @classmethod
    def from_env(cls) -> "HighScoreStore":
        # Resolve TETRIS_DB_PATH; default "./data/high-scores.sqlite3" (Req 1.1, 1.2).
        ...

    def initialize(self) -> None:
        # Create parent dir if missing (Req 1.3); CREATE TABLE IF NOT EXISTS
        # with UNIQUE(game_id) (Req 1.4, 1.6, 1.7); never clears existing rows
        # (Req 1.5, 4.4).
        ...

    def finalize(self, record: HighScoreRecord) -> bool:
        # Parameterized, all-or-nothing INSERT inside one transaction, using a
        # game_id-targeted conflict clause:
        #   INSERT INTO high_scores (...) VALUES (...)
        #   ON CONFLICT(game_id) DO NOTHING
        # Returns True when a row is inserted; returns False ONLY when the
        # conflict is specifically on the game_id UNIQUE constraint (idempotent
        # duplicate, not an error) (Req 2.1, 2.5, 3.2). Any OTHER integrity or
        # storage failure raises StorageError and leaves no partial row (Req 2.9,
        # 7.2) -- it is NEVER silently reclassified as a successful duplicate.
        # Every connection is opened with closing(sqlite3.connect(...)) and the
        # transaction uses `with conn:` INSIDE that, so the transaction commits
        # or rolls back AND the connection is explicitly closed.
        ...

    def top_ten(self) -> list[HighScoreRecord]:
        # SELECT ... ORDER BY score DESC, completed_at ASC, game_id ASC LIMIT 10
        # (Req 5.2, 5.3). Opens with closing(sqlite3.connect(...)) so the
        # connection is explicitly closed. Any failure raises StorageError
        # (Req 7.1).
        ...
```

Design details:

- **Path resolution (Req 1.1, 1.2).** `from_env` reads `TETRIS_DB_PATH`; when unset or empty it uses `./data/high-scores.sqlite3`.
- **Safe startup (Req 1.3, 1.4, 1.5).** `initialize()` computes the parent directory of the resolved path and creates it with `os.makedirs(parent, exist_ok=True)` before opening the connection, then runs `CREATE TABLE IF NOT EXISTS`. Existing rows are never deleted or reinitialized; opening an existing file reads prior rows as-is (Req 4.1, 4.4).
- **Schema (Req 1.6, 1.7).** One table with a `UNIQUE` constraint on `game_id` (see Data Models). The UNIQUE constraint is the final backstop that guarantees at most one record per game (Req 2.5, 3.2).
- **Atomic write (Req 2.1, 2.9).** `finalize` uses a single parameterized `INSERT ... ON CONFLICT(game_id) DO NOTHING` inside a transaction (`with conn:`), so a failure rolls back and no partial row persists. A duplicate is detected specifically through the `game_id` conflict clause (a zero-rows-affected result, or alternatively `sqlite3.IntegrityError` caught **only** when it is the `game_id` UNIQUE constraint), and reported as "already finalized" (`return False`), not a `StorageError`. An integrity or operational error on any other constraint or cause is **not** treated as a duplicate; it is raised as a `StorageError`.
- **Connection model (explicit close).** A short-lived connection per operation keeps the module simple and avoids cross-thread connection sharing. Each operation opens the connection with `with closing(sqlite3.connect(db_path)) as conn:` and runs the transaction with a nested `with conn:`; this matters because `with conn:` only commits or rolls back the transaction and does **not** close the connection, so the `closing(...)` wrapper (equivalently a `try/finally` with an explicit `conn.close()`) is what guarantees the connection is always closed. All writes are additionally serialized by the service-layer lock (below), so single-process concurrency is safe (Req 3.5).
- **Read purity (Req 3.4, 7.9).** `top_ten` only issues a `SELECT`; it never writes.

### Finalization service (`app/service/finalization.py`, new)

Finalization is wired at the **controller/service boundary, not inside the engine**. Rationale: `app/rules/engine.py` is deliberately pure and framework-free so the rules stay unit-testable in isolation (confirmed: it imports only `random`, typing, and domain/pieces/scoring). Injecting SQLite I/O or a FastAPI concern into the engine would break that purity and the existing rules tests. The service layer owns the side effect; the engine only computes the authoritative `game_over` status.

A single module-level **non-reentrant** `threading.Lock` establishes one consistent single-process locking boundary. The mutation, the finalization, **and** the serialization of the response all occur inside that one boundary. The lock is acquired **once per request**; the service functions below assume the caller already holds the lock and therefore MUST NOT re-acquire it (re-acquiring a non-reentrant `Lock` already held by the same thread deadlocks). The controller takes the lock exactly once, calls `run_mutation`, then serializes while still holding it.

```python
_LOCK = threading.Lock()  # non-reentrant; single in-memory game worker (Req 3.5, 4.5, 12.4)

# NOTE: _LOCK is acquired ONCE per request by the controller. The functions
# below run while that lock is held and MUST NOT acquire _LOCK again. Taking a
# non-reentrant Lock a second time on the same thread would deadlock.

def run_mutation(game: Game, mutate: Callable[[Game], None], store: HighScoreStore) -> None:
    # Precondition: caller holds _LOCK. Does NOT acquire _LOCK.
    mutate(game)                          # pure engine call: tick / move / hold
    if game.status == "game_over":
        _finalize_if_needed(game, store)

def _finalize_if_needed(game: Game, store: HighScoreStore) -> None:
    # Precondition: caller holds _LOCK. Does NOT acquire _LOCK.
    if game.finalized:
        return                            # idempotent: already persisted (Req 3.1)

    # (1) Capture the immutable pending record ONCE, at the first terminal
    #     transition, BEFORE any storage write is attempted. completed_at is
    #     generated here (terminal time) and never regenerated on retry.
    if game.finalization_record is None:
        game.completed_at = _utc_now_iso()            # set once, at terminal time
        game.finalization_record = HighScoreRecord(   # frozen dataclass (immutable)
            game_id=game.id,
            score=game.score,             # server-authoritative (Req 6.1)
            total_lines=game.total_lines,
            level=game.level,
            completed_at=game.completed_at,
        )

    record = game.finalization_record     # reuse the SAME captured record on every retry

    # (2) Attempt the storage write using the captured record.
    inserted = store.finalize(record)     # True=inserted, False=duplicate; may raise StorageError

    # (3) store.finalize raised -> control never reaches here; see except below.
    # (4) On success (insert or idempotent duplicate) mark finalized, clear pending.
    game.finalized = True
    game.pending_finalization = False
```

The controller wraps the storage attempt so a `StorageError` leaves the captured record and terminal state intact and marks the game pending for a later retry:

```python
    try:
        _finalize_if_needed(game, store)
    except StorageError:
        game.pending_finalization = True  # keep game.finalization_record unchanged
        raise                             # controller maps to 503 (Req 7.2)
```

`game.finalization_record` is never cleared or regenerated once set; `game.completed_at` is written exactly once, at the first terminal transition, and never changed by any later retry or action.

Behavior mapped to requirements:

- **First transition to `game_over` finalizes exactly once** (Req 2.1). Because the lock serializes mutations and `finalized` gates the write, repeated terminal mutating requests keep exactly one record with its original fields (Req 3.1). Two attempts for the same `game_id` resolve to one row via the gate plus the UNIQUE backstop (Req 3.2, 2.5).
- **Zero score still finalizes** (Req 2.2); there is no guard on `score > 0`.
- **All game-over causes use the same path** (Req 2.4): gravity tick, soft drop, and obstructed Hold all set `status == "game_over"` in the engine, and `run_mutation` finalizes uniformly.
- **`completed_at` is recorded at the first terminal transition** (Req 2.6, 6 timestamp rule): it is generated once (terminal time) when the immutable pending record is captured, before any storage write; it is captured into that frozen record and is never regenerated or changed by a later retry or any subsequent action, even if the first write failed and recovery happens much later.
- **Still-playing games are never recorded** (Req 2.7); a client that restarts (creates a new game) while a previous game is still `playing` triggers no finalization for the abandoned game (Req 2.8), because finalization only runs when a mutation drives the authoritative status to `game_over`.
- **Failure and safe retry** (Req 2.9, 7.2, 7.6, 7.7, 7.8). The immutable pending record (including `completed_at`) is captured before the write. On a non-duplicate storage failure, `store.finalize` raises `StorageError` before `game.finalized` is set; the controller sets `game.pending_finalization = True`, keeps `game.finalization_record` and `game.completed_at` unchanged, preserves the terminal `game_over` state and the game's `board`, `score`, `level`, `total_lines`, and active piece unchanged, and re-raises so the controller returns 503 (Req 7.2). On a later mutating request to that terminal game, `run_mutation` re-enters `_finalize_if_needed`, which reuses the SAME captured record (it does not re-generate `completed_at` or re-read terminal state) and retries the write; a successful retry persists exactly one record with the original single `completed_at` and clears the marker (Req 7.7, 7.8).
- **GET never retries or captures** (Req 7.9, 3.3). Read controllers never call `run_mutation`/`_finalize_if_needed`; a `GET` on a terminal pending game takes a coherent read-only snapshot under the lock, returns current state, captures no record, mutates nothing, and leaves the pending status unchanged.
- **Single-process race protection and a single locking boundary** (Req 3.5): the module-level non-reentrant `threading.Lock` guards mutation, finalization, **and** serialization together as one consistent boundary, so concurrent requests to the same game cannot interleave a mutation, a finalization, and a read of a half-updated state; the serialized response is an immutable coherent snapshot. The lock is acquired exactly once per request and never re-acquired by a nested call, avoiding self-deadlock on the non-reentrant lock. This is scoped to exactly one in-memory game worker (Req 4.5, 12.4); multiple-worker support for in-memory games is not claimed.

The controllers in `api/games.py` change only to route the engine call through `run_mutation` **and to take the single lock once per request, holding it across mutation, finalization, and serialization**, for example:

```python
@router.post("/{game_id}/tick", response_model=GameStateOut)
def tick_game(game_id: str) -> GameStateOut:
    with _LOCK:                               # single boundary, acquired ONCE
        game = _get_or_404(game_id)           # 404 contract unchanged
        try:
            run_mutation(game, engine.tick, high_score_store)   # does NOT re-acquire _LOCK
        except StorageError:
            raise HTTPException(status_code=503, detail=STORAGE_UNAVAILABLE_MESSAGE)
        return serialize(game)                # serialized INSIDE the lock = coherent snapshot
```

`/move` and `/hold` follow the same shape; `_get_or_404` and the serialized shape are unchanged, so Stage 2 behavior and the 404 contract are preserved (Req 6.7). Serializing while the lock is still held makes the response an immutable coherent snapshot and prevents a concurrent request from observing or producing a half-updated state. The read controller for `GET /api/games/{id}` likewise takes `_LOCK` once, resolves the game (404 if missing), and serializes a coherent read-only snapshot under the same boundary without mutating or finalizing. `run_mutation`/`_finalize_if_needed` never re-acquire `_LOCK`, so the non-reentrant lock cannot self-deadlock.

### Leaderboard controller (`app/api/high_scores.py`, new)

```python
router = APIRouter(prefix="/api/high-scores", tags=["high-scores"])

@router.get("", response_model=HighScoresOut)
def read_high_scores() -> HighScoresOut:
    try:
        records = high_score_store.top_ten()
    except StorageError:
        raise HTTPException(status_code=503, detail=STORAGE_UNAVAILABLE_MESSAGE)
    return HighScoresOut(scores=[HighScoreEntryOut(**r.__dict__) for r in records])
```

- Returns an object with a `scores` array (Req 5.1), at most ten entries (Req 5.2), ordered `score` DESC, `completed_at` ASC, `game_id` ASC by the SQL query (Req 5.3). Each entry contains exactly `game_id`, `score`, `total_lines`, `level`, `completed_at` (Req 5.4). When no rows exist, `scores` is an empty array (Req 5.5). The read performs no state mutation and creates no record (Req 3.4).

### Code-quality corrections (Sonar candidate 27ef1e41, new findings only)

These seven NEW findings are corrected without exclusions, suppressions, threshold, or baseline changes; researcher Sonar helpers/config are untouched and the researcher rescans fresh coverage afterward:

- **python:S8415** (`api/games.py` mutating routes; `api/high_scores.py`): the routes reach a controlled `HTTPException(status_code=503, ...)`, so each decorated route documents the `503` response in its `responses=` metadata (a documentation-only addition that does not change behavior or the response body).
- **python:S8409** (`api/games.py` mutating routes; `api/high_scores.py`): the `response_model=` argument duplicates the function return-type annotation, so it is removed; FastAPI continues to use the return annotation as the response model, preserving the exact serialized contract.
- **python:S1192** (`persistence/store.py`): the literal `"high-score storage is unavailable"` repeated in three `StorageError(...)` raises is replaced by a single module-level constant; the exception text is unchanged and still carries no path/SQL/stack detail.
- **python:S5778** (`tests/test_stage3_finalization.py`): the exception test keeps only the single intended throwing invocation inside `pytest.raises`, moving non-throwing setup outside, without weakening the assertions.
- **typescript:S6759** (`HighScores.tsx`): the component props are marked `readonly`.

### API schema changes (`app/api/schemas.py`)

Add strict body validation and the new response models while preserving every existing serialized field:

```python
class MoveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")   # reject extra fields (Req 6.3)
    direction: Literal["left", "right", "down"]

class CreateGameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")   # reject injected score metadata (Req 6.2)
    # intentionally no fields

class HighScoreEntryOut(BaseModel):
    game_id: str
    score: int
    total_lines: int
    level: int
    completed_at: str

class HighScoresOut(BaseModel):
    scores: List[HighScoreEntryOut]
```

- `extra="forbid"` makes a `move` body with fields beyond `direction`, and a `POST /api/games` body with any fields, fail validation with HTTP 422 (a documented 4xx), so no client-supplied `score`, `total_lines`, `level`, `completed_at`, or arbitrary `game_id` can influence persistence (Req 6.1, 6.2, 6.3).
- A valid bodyless `POST /api/games` still creates a game and returns HTTP 200: the create controller keeps accepting no body (an empty body is not parsed against `CreateGameRequest` unless a body is supplied), preserving the Stage 2 contract (Req 6.4). A valid `move` body with `direction` in `{left, right, down}` behaves exactly as Stage 2 (Req 6.5); a missing/invalid `direction` yields 422 (Req 6.6).
- `GameStateOut` is unchanged (same keys, integer board, `active_piece`), so the Stage 2 serialized contract and its regression tests are preserved.

### Controlled 503 storage-error contract (`app/api/` + a shared message)

- A single module-level constant `STORAGE_UNAVAILABLE_MESSAGE` holds a generic, human-readable English message that indicates a storage failure and contains no filesystem path, SQL text, exception or class name, or stack trace (Req 7.4, 7.5).
- `StorageError` raised by the persistence layer is caught at the controller boundary (leaderboard read and each mutating route) and translated to `HTTPException(status_code=503, detail=STORAGE_UNAVAILABLE_MESSAGE)`. FastAPI serializes `HTTPException` as `application/json` with a JSON body, satisfying the content-type and valid-JSON-body requirements (Req 7.1, 7.2, 7.3).
- The exception string is never forwarded to the client; only the constant message is returned.

### Backend CORS and app wiring (`app/main.py`)

- Replace the hardcoded `allow_origins` list with a **restrictive, configurable** policy driven by an environment variable (e.g. `TETRIS_ALLOWED_ORIGINS`, comma-separated), defaulting to the local dev origins. The policy never combines `allow_credentials=True` with a wildcard `*` origin (Req 10.3, 10.4).
- **Wildcard-with-credentials is rejected (fail closed) (Req 10.4, 10.5).** `_resolve_allowed_origins` parses the comma-separated value, trims blanks, and inspects the resulting list. Because `allow_credentials=True` is always enabled, a literal `*` in the resolved list — whether the whole value is `*` or a mixed list such as `"https://app.example,*"` — is an INVALID credentialed configuration and raises a `ValueError` at resolution time (startup) rather than being passed through to `CORSMiddleware`. This fails closed: a credentialed response can never be granted to an arbitrary reflected origin. A resolved list of only concrete explicit origins is returned as-is and keeps credentials enabled (Req 10.6); an unset or empty value falls back to the restrictive local-dev default (Req 10.7). This corrects a verified defect where the prior implementation split the value and returned `*` unchanged, so Starlette reflected an arbitrary `Origin` with `Access-Control-Allow-Credentials: true`. The change affects only CORS configuration resolution; controlled generic API errors and all existing response fields are unchanged.
- Use a FastAPI **lifespan** (or `startup`) handler to construct `HighScoreStore.from_env()` and call `initialize()` once at startup, then share the instance with the controllers (Req 1.1-1.4).

- **Store availability without lifespan (inherited-test correction).** The process-wide `HighScoreStore` is installed on startup by the lifespan handler for production, AND the shared accessor (`get_high_score_store`) **lazily self-initializes** a default store via `HighScoreStore.from_env()` + `initialize()` on first use IF the lifespan has not already installed one. This corrects a defect: the inherited Stage 2 API regression tests construct the client at module scope as `client = TestClient(app)` WITHOUT a `with TestClient(app) as client:` block, so Starlette does NOT run the lifespan startup for those tests; if store access were gated solely on lifespan init, the inherited mutating-endpoint tests would fail with a `RuntimeError` because the store was never installed. Because the inherited test assertions MUST NOT be changed, the application wiring is corrected instead: the lazy fallback guarantees the store is always available — including for inherited Stage 2 tests that use a module-level `TestClient(app)` without triggering the lifespan — without weakening any behavior. The lazily created store resolves the same `TETRIS_DB_PATH` (default `./data/high-scores.sqlite3`) and the same schema as the lifespan path, and tests that need an isolated database set `TETRIS_DB_PATH` or inject a store before first use.
- This lazy fallback is **idempotent** and the explicit lifespan init remains the **primary** path in production; the fallback only covers the "lifespan never ran" case. It never clears or reinitializes existing rows (`CREATE TABLE IF NOT EXISTS`), consistent with the safe-startup rules (Req 1.3-1.5, 4.4).
- The `/health` endpoint is retained for container health checks.
- No authentication is added and no player names are collected (Req 10.5).

### Frontend changes (`frontend/src`)

**`types.ts`** -- add leaderboard types without touching `GameState`:

```ts
export interface HighScoreEntry {
  game_id: string;
  score: number;
  total_lines: number;
  level: number;
  completed_at: string;
}
export interface HighScoresResponse { scores: HighScoreEntry[]; }
```

**`api.ts`** -- change the base and add the leaderboard fetch:

```ts
// Configurable API base; default is the same-origin path prefix "/api".
const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export async function getHighScores(): Promise<HighScoresResponse> {
  const r = await fetch(`${API_BASE}/high-scores`);
  if (!r.ok) throw new Error(`Request failed with status ${r.status}`);
  return (await r.json()) as HighScoresResponse;
}
```

The default base becomes the same-origin `/api` so the production build never hardcodes `localhost`; the existing game functions are rebased onto the same prefix (Req 10.1, 10.2). (The existing game calls keep their paths relative to `API_BASE`.)

**`HighScores.tsx`** (new component) -- renders the panel with explicit states (Req 8.1-8.4, 8.8):

- `loading`: shown while a leaderboard request is in flight (Req 8.2).
- `error`: shown if the request fails, without crashing the page (Req 8.4).
- `empty`: shown when `scores` is an empty array (Req 8.3).
- `loaded`: a list where each entry displays `score`, `total_lines`, and `level` (Req 8.1).
- All visible labels, statuses, and messages are in English (Req 8.8).

**Leaderboard fetching -- isolation from the game lifecycle (Req 8.5-8.7, 9.3, 9.4).** The leaderboard is fetched by a small dedicated hook/effect (`useHighScores`) that is independent of the `useGame` generation/FIFO/tick machinery:

- Fetch **once on initial mount** (Req 8.5).
- Fetch **again on each real `playing -> game_over` transition** -- triggered by observing `state.status` change from `playing` to `game_over` in `App.tsx`, not on every render and **not on every tick** (no per-tick polling) (Req 8.6, 8.7).
- **Stale-guard placement (Req 9.3).** `useHighScores` carries its own request-generation counter (independent of the game generation). The generation is captured when a leaderboard request starts, and the stale check is applied **after BOTH the `fetch` promise AND the awaited `response.json()` promise resolve** -- not only after `fetch` -- before any state is committed. A response whose captured generation no longer matches the current generation is discarded, whether it resolved as a **success** or as an **error** (stale errors never overwrite a newer result or the current state). A `finally`/cleanup path runs on restart, unmount, and StrictMode teardown, invalidating the captured generation so no in-flight response can commit after cleanup.
- **Game-over refresh while the initial fetch is still in flight (Req 8.6).** A required game-over refresh must not be silently dropped by a naive in-flight boolean. The hook therefore does **not** gate the game-over refresh behind "is a request already running"; instead, starting the refresh bumps the request generation so the still-pending initial request becomes stale and is invalidated when it resolves, while the newer game-over request is the one allowed to commit. (Equivalently, the refresh may be queued so it still runs after the initial request settles.) Either way the mandated game-over refresh always runs and reflects the latest leaderboard.
- **StrictMode honesty.** React 18 StrictMode intentionally mounts, cleans up, and re-mounts effects in development. The cleanup from the first (discarded) setup invalidates that run's captured generation so its in-flight response cannot commit; the second setup performs the real fetch. No duplicate committed state results.
- **Isolation from the game machinery (Req 9.4).** The leaderboard fetch **must not** call `cancelTick`, touch `queueRef`/`timeoutRef`/`tickBusyRef`, or enqueue onto the per-generation FIFO, so it cannot clear, block, or reschedule the automatic-tick scheduler or the manual FIFO queue. All Stage 2 controls, Hold restrictions, and R1-R5 protections in `useGame.ts` are left intact (Req 9.1, 9.2).
- **Restart invalidation signal (Req 8.8, 8.9, 9.3) -- corrected defect.** The prior `useHighScores` bumped its request generation only on `load()` (initial fetch / game-over refresh) and on unmount/StrictMode teardown; it exposed NO restart signal, and `App.tsx` passed the raw `useGame.restart` to the Restart button. A restart therefore did not invalidate an in-flight leaderboard request, so in the production bundle an initial DELAYED response could commit a stale score (e.g. `1111`) over a freshly created game, and an old DELAYED rejection could show "Could not load high scores." after restart. The corrected hook exposes an `invalidate()` signal that **synchronously bumps the request generation** (the same counter that gates both the `fetch` resolution and the awaited `response.json()` resolution, on the success, error, AND cleanup/`finally` paths) and sets the panel to a neutral current state. Because the stale check is applied after BOTH promises resolve, any delayed fetch and any delayed JSON captured before the restart are discarded and cannot commit afterward. `App.tsx` wraps `useGame.restart` so the Restart button and keyboard restart first call `highScores.invalidate()` and then the game restart; the two are independent, so the game FIFO/timers and the per-generation automatic-tick scheduler are untouched (Req 9.4). The mandated initial fetch still runs, and a game-over refresh fired while the initial read is still pending is never dropped because the refresh bumps the generation and is the request allowed to commit (Req 8.10).

**`App.tsx`** -- render `<HighScores />` in the layout and wire the game-over-edge fetch; keep all existing controls, labels (English), and Stage 2 sidebar. Detect the `playing -> game_over` edge with a ref so the fetch fires once per transition. Wrap the game restart so the Restart button (and the inherited keyboard restart path, if any) first invalidates the leaderboard generation via `highScores.invalidate()` and then calls `useGame.restart`, ensuring no pre-restart leaderboard response commits after a new game is created.

## Data Models

### `High_Score_Record` SQLite schema (persistence)

```sql
CREATE TABLE IF NOT EXISTS high_scores (
    game_id      TEXT    NOT NULL UNIQUE,   -- at most one record per game (Req 1.6)
    score        INTEGER NOT NULL,          -- non-negative (Req 2.3)
    total_lines  INTEGER NOT NULL,          -- non-negative (Req 2.3)
    level        INTEGER NOT NULL,          -- >= 1 (Req 2.3)
    completed_at TEXT    NOT NULL           -- UTC ISO-8601 string, fixed at terminal time (Req 2.3, 2.6)
);
```

- Exactly the five fields required (Req 1.7, 5.4). `game_id` carries the `UNIQUE` constraint (Req 1.6). Value invariants (`score >= 0`, `total_lines >= 0`, `level >= 1`, `completed_at` a UTC ISO-8601 string) are guaranteed by the server-authoritative engine state at finalization time (Req 2.3).

Python record carrier:

```python
@dataclass(frozen=True)
class HighScoreRecord:
    game_id: str
    score: int
    total_lines: int
    level: int
    completed_at: str
```

### In-memory `Game` additions (`app/domain/models.py`)

```python
@dataclass
class Game:
    # ... existing Stage 1/2 fields unchanged ...
    # --- Stage 3 finalization bookkeeping (in memory only) ---
    finalized: bool = False                               # a record has been persisted for this game
    pending_finalization: bool = False                    # terminal but not yet persisted (retry later)
    completed_at: Optional[str] = None                    # UTC ISO-8601, written once at the first terminal transition
    finalization_record: Optional[HighScoreRecord] = None # immutable snapshot captured once at terminal time
```

These fields live only in memory and are never persisted as game state; only the `High_Score_Record` summary is persisted (Req 18.4). They exist to enforce finalize-once, the pending-retry path, and the write-once `completed_at` (Req 2.6, 3.1, 7.6-7.8).

`finalization_record` holds the frozen `HighScoreRecord` captured **exactly once** at the first terminal transition (status first becomes `game_over`), **before** any storage I/O is attempted. Its `completed_at` is generated once at that terminal time. Every finalization attempt and every retry reuses this same immutable record, so a storage failure on the first write can never cause a later retry to regenerate `completed_at` or re-read authoritative state; the recorded completion time is fixed at terminal time, not at recovery/retry time. `completed_at` on the game mirrors the captured record's value and is likewise written once and never changed. A terminal game is never re-mutated by finalization: finalization only reads the already-captured immutable record and attempts the storage write; it does not touch `board`, `score`, `level`, `total_lines`, or the active piece. These four guarantees — the four finalization bookkeeping fields, the capture-once-before-any-I/O rule, the retry-reuses-the-same-record / `completed_at`-never-regenerated rule, and the single non-reentrant lock boundary described in the Finalization service above (acquired exactly once per request and held across mutation, finalization, and serialization; never re-acquired by `run_mutation`/`_finalize_if_needed`; GET takes the same lock once for a coherent read-only snapshot without mutating, finalizing, or retrying) — are the precise contract that the finalization implementation tasks reference.

### New Pydantic models (API)

`HighScoreEntryOut`, `HighScoresOut`, and the strict `MoveRequest` / `CreateGameRequest` (`extra="forbid"`) described under Components and Interfaces.

## Error Handling

- Unknown game id on any game-scoped route -> HTTP 404 via `_get_or_404` (Req 6.7), unchanged from Stage 2.
- Invalid/missing `direction` on `move`, or any unexpected body field on `move` or `POST /api/games` -> HTTP 422 via Pydantic `extra="forbid"` (Req 6.2, 6.3, 6.6).
- Storage failure while serving `GET /api/high-scores` -> controlled JSON **503** with the generic message (Req 7.1, 7.3-7.5).
- Storage failure during finalization triggered by a mutating request -> controlled JSON **503**; the game stays terminal and is marked pending for a later retry, and the immutable pending record (with its `completed_at` fixed at terminal time) is retained unchanged so the retry reuses it (Req 7.2, 7.6, 7.7). `completed_at` is recorded once at the first terminal transition and is never regenerated by the retry.
- A duplicate specifically on the `game_id` UNIQUE constraint is treated as success-equivalent idempotency (`finalize` returns `False`), never a 503. Any other integrity or storage failure is **not** reclassified as a duplicate; it raises `StorageError` and surfaces as a controlled 503.
- `GET` on a terminal pending game -> returns a coherent read-only snapshot of the current terminal state under the shared lock, captures no record, performs no retry, and does not change pending status (Req 7.9).
- Frontend: a failed leaderboard fetch sets the panel error state without crashing the page (Req 8.4); game-fetch error handling and the R1-R5 stale-response discipline are unchanged (Req 9.3).

## Deployment and Packaging (Docker)

### Backend image (`backend/Dockerfile`)

- Multi-stage: a build/deps stage installs **runtime-only** dependencies, and a slim runtime stage (`python:3.12-slim`) copies the app and the installed runtime packages (Req 11.1, 12.5 -- no dev deps, no baked credentials).
- **Runtime-only dependency set vs dev/audit set (Req 12.5).** The inherited `backend/requirements.txt` currently mixes runtime packages (`fastapi`, `uvicorn`, `pydantic`) with development/test packages (`pytest`, `httpx`), and `requirements-dev.txt` adds `pytest-cov`. Installing that file wholesale into the runtime image contradicts "no development dependencies". Stage 3 therefore defines a **coherent split**, without editing any manifest in this spec-only design pass:
  - a **runtime set** containing only `fastapi`, `uvicorn`, `pydantic`, plus their exact resolved transitive locks -- this is what the runtime image installs;
  - a **dev/audit set** layered on top for local work and CI only, containing `pytest`, `httpx`, `pytest-cov`, `pip-audit`, and their transitive locks -- never installed into the runtime image.
  The inherited test assertions stay intact because `pytest` and `httpx` remain available at dev/CI time through the dev/audit set.
- **Reproducible, auditable locks (concrete selections recorded below).** The exact direct selected versions and the resolved lock strategy are now recorded in the dedicated subsection "Dependency security remediation (selected versions and lock strategy)" immediately below, **before** any manifest or lockfile is changed and before any install (Req 19.5). The fully-resolved transitive lock files for both sets are generated and installed into the owned Python 3.12 environment during implementation and verified with `pip check` and `pip-audit`; this design records the direct selected versions and the strategy here and does **not** assert that any install, audit, or test has actually been executed. Any justified backend security update is recorded in the spec before any manifest or lock is changed.

### Dependency security remediation (selected versions and lock strategy)

This subsection records the EXACT selected versions and the resolved lock strategy required by Requirement 19, documented here **before** any dependency manifest or lockfile change and before any install. The owned implementation runtime is **Python 3.12.14**. These selections were verified against official PyPI metadata; this design does **not** assert that any install, audit, or test has actually been executed.

**Baseline audit (pip-audit `2.10.1` against the immutable inherited `backend/requirements.txt`).** 18 packages resolved; 16 raw advisory entries representing **8 UNIQUE findings** (Req 19.1, 19.3):

- `pytest` `8.3.4` — `PYSEC-2026-1845` (alias `CVE-2025-71176`), fixed in `9.0.3`.
- `starlette` `0.41.3` (transitive via `fastapi`, not pinned directly in the inherited manifest — Req 19.2):
  - `PYSEC-2026-1941`, fixed in `0.47.2`;
  - `PYSEC-2026-1942`, fixed in `0.49.1`;
  - `PYSEC-2026-161`, fixed in `1.0.1`;
  - `PYSEC-2026-2280/2281` (a single finding with two aliases), fixed in `1.1.0`;
  - `PYSEC-2026-248`, fixed in `1.3.0`;
  - `PYSEC-2026-249`, fixed in `1.3.1`.

Duplicate raw advisory entries are not treated as distinct defects, and no additional advisories are invented (Req 19.3).

**Selected production RUNTIME set (explicitly pinned, no floating transitives) (Req 19.4, 19.6):**

- `fastapi==0.137.2` — upgraded from `0.115.6`. Rationale: inherited `fastapi` `0.115.6` pins `starlette<0.42`, so a fixed `starlette` (`>=0.47.2`, and `>=1.3.1` to clear ALL seven starlette advisories) is impossible without upgrading FastAPI. `fastapi` `0.137.2` declares `starlette>=0.46.0` and `pydantic>=2.9.0` and requires Python `>=3.10` (supports 3.12). It is the compatible supported FastAPI that admits `starlette` `1.3.1`.
- `starlette==1.3.1` — explicitly pinned (NOT floated). It is the minimum `starlette` that clears ALL seven enumerated starlette advisories (the highest required fix is `PYSEC-2026-249` -> `1.3.1`); requires Python `>=3.10`; satisfies `fastapi` `0.137.2`'s `starlette>=0.46.0`. Pinning it explicitly (rather than relying on fastapi's floor) guarantees the audited, remediated version is the one installed — no floating/unpinned runtime transitive.
- `pydantic==2.10.4` — PRESERVED unchanged. No advisory against it; satisfies `fastapi` `0.137.2`'s `pydantic>=2.9.0`; preserves inherited Pydantic v2 behaviors and the inherited test assertions.
- `uvicorn==0.34.0` — PRESERVED unchanged. No advisory against it; requires Python `>=3.9`; compatible.

**Selected DEV/TEST/AUDIT set (layered on the runtime set, never in the runtime image) (Req 19.4, 19.6):**

- `pytest==9.0.3` — upgraded from `8.3.4` to clear `PYSEC-2026-1845` / `CVE-2025-71176`; requires Python `>=3.10` (supports 3.12).
- `httpx==0.28.1` — PRESERVED unchanged. No advisory; compatible with `fastapi` `0.137.2`'s `TestClient` usage (fastapi standard pins `httpx<1.0.0,>=0.23.0`).
- `pytest-cov` — currently pinned `6.0.0` in `requirements-dev.txt`. `pytest-cov` MUST be confirmed compatible with `pytest` `9.0.3` via `pip check` during implementation; IF `pip check` or collection reveals an incompatibility, it SHALL be bumped to the nearest compatible supported release (e.g. a `pytest-cov` 7.x that declares `pytest>=9` support) and that exact chosen version recorded, remediating by a compatible upgrade rather than pinning back `pytest`. No specific `pytest-cov` version that has not been confirmed is invented here; this conditional is recorded explicitly.
- `pip-audit==2.10.1` — the audit tool used; part of the dev/audit set.

**Lock strategy (recorded explicitly) (Req 19.5, 19.6):** two coherent explicitly-pinned requirement sets — the production RUNTIME set (`fastapi`/`starlette`/`pydantic`/`uvicorn` plus their exact resolved transitive locks) installed into the runtime image and the owned Python 3.12 environment, and a DEV/AUDIT set layered on top (`pytest`/`httpx`/`pytest-cov`/`pip-audit` plus transitive locks) for local/CI only. Every runtime transitive is pinned (no floating). `starlette` is pinned directly even though it is a `fastapi` transitive, precisely so the remediated version is guaranteed. Remediation is by compatible supported upgrades only — NO ignore lists, NO suppression, NO floating runtime transitives, NO arbitrary overrides (Req 19.6). The exact fully-resolved transitive lock files are generated and installed into the owned Python `3.12.14` environment during implementation and verified with `pip check` and `pip-audit`; this design records the direct selected versions and the strategy here, **before** any manifest or lock edit (Req 19.5). This design does NOT assert that any install, audit, or test has actually been executed (Req 19.9).

**Public API-surface preservation.** FastAPI `0.137.2` keeps the same public API surface the app uses (`APIRouter`, the `FastAPI` app, `HTTPException`, `CORSMiddleware`, lifespan, and Pydantic v2 models with `ConfigDict(extra="forbid")`), so inherited Stage 1/2 behaviors and test assertions remain satisfied (Req 19.7). Any behavioral delta discovered during implementation must first be reflected in the spec and then remediated by a compatible upgrade. The existing frontend pins passed the baseline npm audit and are preserved unless an actual compatibility or security finding justifies a change (Req 19.8).

### Complete resolved dependency locks: inputs vs. locks (Req 16.3, 19.10, 19.11) — corrected defect

The prior manifests pinned only four DIRECT runtime packages (`backend/requirements.txt`) and four DIRECT dev tools (`backend/requirements-dev.txt`); every transitive dependency still floated and there were no complete resolved lock files, contrary to the comments in those manifests. Stage 3 corrects this by distinguishing INPUT manifests from RESOLVED locks:

- **Input manifests (human-authored, direct pins):** `backend/requirements.txt` (runtime direct) and `backend/requirements-dev.txt` (dev direct, `-r requirements.txt`). These remain the editable source of intent and keep the compatible direct pins recorded above. They are NOT the install target for reproducible environments.
- **Resolved locks (complete, exact, every transitive pinned):** `backend/requirements.lock.txt` (production RUNTIME lock) and `backend/requirements-dev.lock.txt` (DEV/TEST/AUDIT lock). Each is produced by resolving the corresponding input manifest in the owned Python `3.12.14` environment with `pip freeze` (or an equivalent resolver), so every transitive package and version is pinned, with valid platform/environment markers where the resolver emits them. The dev lock is a superset of the runtime lock (it layers the dev/audit tools and their transitives on top). No lock is copied from another tool's project or source.
- **Install targets:** the backend runtime Docker image installs ONLY `requirements.lock.txt` (no dev/test/audit packages); local development, CI tests, and both audits install `requirements-dev.lock.txt`. `backend/README.md` documents which files are inputs and which are resolved locks and the exact commands.
- **Validation (performed in implementation, reported under `docs/native-checks/04/`):** a fresh install of each lock, `pip check`, the native backend tests, and `pip-audit` on BOTH the runtime and dev sets. The actual resolved packages are reported; no blanket reproducibility claim is made. The frontend pins are preserved unless an actual `npm audit`/compatibility finding requires a change, and the performance harness dependency set (`perf/`) is audited too. The inherited `.stage2.bak` files are history, not runtime inputs, and are not installed.
- Runs as a **non-root user** (Req 11.5).
- Starts exactly **one** uvicorn worker: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1` (Req 12.4).
- `TETRIS_DB_PATH` points at a directory on the mounted named volume so the SQLite file is durable (Req 12.1, 12.2).
- Health check hits `/health` (Req 12.3).

### Frontend image (`frontend/Dockerfile`)

- Multi-stage: a **node build stage** runs `npm ci` + `npm run build` (the existing `tsc && vite build`), producing the static production bundle of `frontend/src`; a **runtime stage** (e.g. `nginx:alpine`) serves the built assets and **reverse-proxies `/api` to the backend** container over the internal network (Req 11.1, 11.4).
- Runs as a **non-root user**, distinct from the backend's non-root user (Req 11.5). The runtime stage contains no dev dependencies or source toolchain (Req 12.5).
- Health check against the served frontend (Req 12.3).

### `.dockerignore`

- Excludes `node_modules`, `.venv`, test/coverage artifacts, `docs/`, `perf/`, local `data/`, and VCS metadata so they are not copied into build context/images (Req 11.2, 12.5).

### Compose (`docker-compose.yml`)

- Defines `backend` and `frontend` services on an internal network; publishes **only** the frontend on host port **5183**, with the backend reachable only inside the network (Req 11.3, 11.6).
- Mounts a **named volume** with write permissions for the backend SQLite directory; `TETRIS_DB_PATH` resolves inside that volume (Req 12.1, 12.2).
- Each service defines a health check (Req 12.3); the backend runs exactly one worker (Req 12.4); the two services use distinct non-root users (Req 11.5).

### Documentation and measurement honesty

- Stage 3 documents the exact commands to build the images, start the stack, stop the stack, and verify persistence across a container restart (Req 12.6).
- Image sizes and build time are **measured and reported only when Docker is available** (Req 12.7); where Docker is unavailable, Stage 3 reports that the measurement could not be executed and fabricates no values (Req 12.8). No optimization percentage or arbitrary size limit is invented.

## Performance Benchmark Harness

Location: a separate `perf/` directory, outside the shipped runtime images and outside ordinary unit CI (Req 15.5, 16.7).

- **Driver (Req 13.1):** Playwright drives the **production** frontend (built production assets and the actual in-game controls, no test-only shims) in a **real Chromium** browser. Each of the three runs uses a **fresh headed Chromium session with the normal sandbox enabled** (no `--no-sandbox`, no reused profile).
- **Separated measurements (Req 13.2, 14.5):** the harness records browser frame scheduling (via `requestAnimationFrame` interval sampling) **separately** from actual game DOM updates (via `MutationObserver` / `PerformanceObserver` on the board grid) **separately** from API timing. `requestAnimationFrame` frequency alone is never treated as proof of rendering throughput, nor as physical display presentation.
- **Concrete auditable evidence (Req 13.2, 13.3), not summary counts.** The harness retains, per run:
  - **Raw time-stamped frame samples** -- every individual `requestAnimationFrame` timestamp and the derived interval, not only aggregates.
  - **Exact measurement window selection** -- the recorded start and end timestamps of each 30-second measured run and an explicit flag on every sample indicating whether it falls inside that window and therefore counts toward that run (warm-up and between-run samples are retained but marked excluded).
  - **Timestamped DOM mutation batches** -- each board-grid update batch with its page-clock timestamp, the **complete board signature** before and after, and the recorded transition between signatures.
  - **Action records** -- each injected input carries an **action identifier** and the before/after board state and signatures it produced.
  - **Action -> DOM association on the page clock** -- each action is associated with the resulting visible DOM update using the page clock; samples that are ambiguous or show no board change are **excluded from latency statistics AND reported** as excluded (count and reason), never silently dropped.
  - **API timings on a separately identified clock** -- request/response timings recorded and labeled on a clock distinct from the frame/DOM page clock, so API latency is never conflated with frame scheduling or DOM throughput.
  - **Throughout-the-interval input-focus and board-geometry evidence** -- focus state and 10x20 board-visibility geometry are sampled across the whole measured interval, not captured only as a single final screenshot.
- **Screenshot-bearing traces (Req 13.3):** a browser performance trace that includes **real screenshot frames** (PNG images or screenshot-bearing traces) is retained for each run.
- **Scenario (Req 13.4, 13.5, 13.6):** a **visible foreground** Chromium window at **1280x900, device scale factor 1**, a recorded **60 Hz** target, a **5-second warm-up**, and exactly **three independent measured runs of 30 seconds each**, each in its own fresh sandboxed headed session. The harness captures geometry evidence that the full 10x20 board stays visible and evidence that the page has input focus throughout each run, and exercises real **left / right / soft-drop** movements plus **restart** to keep gameplay active -- without adding gameplay features, rotating pieces, or inflating `requestAnimationFrame` or request rates.
- **Reporting (Req 14.1, 14.2):** records browser, runtime, OS, hardware, display configuration, headless-vs-foreground mode, and scenario parameters; reports frame-interval **median, p95, p99**, an approximate FPS, the count of intervals above **33.34 ms**, and action latency.
- **Targets (Req 14.3, 14.4):** the operational target is a mean frame-scheduling rate of at least **55 FPS** and a p95 frame interval of at most **25 ms** in **every** run, explicitly framed as a tolerance around a 60 Hz scheduling target and **not** a guarantee of physical display presentation.
- **Honesty (Req 14.6):** an unsupported environment or an unmet target is reported honestly; no passing result is fabricated.
- **Local manual command and hosted-run caveat (Req 15.5, 14.4):** the benchmark is invoked through a documented **local manual command** run on a real machine with a physical foreground display. The spec states explicitly that running this job on a hosted/CI runner (even via a manual workflow) does **not** establish an actual physical foreground display; a hosted manual run is a convenience trigger only, not evidence of real display presentation. Frame scheduling, game DOM throughput, and physical display presentation remain reported separately.
- **Integrity / isolation (Req 15.1-15.4):** the harness does not change game gravity, does not add a permanent animation loop whose sole purpose is to inflate the frame-rate metric, does not rotate pieces, does not migrate board rendering from React DOM to Canvas/WebGL, and does not issue sixty API requests per second.

### Benchmark harness corrected defects (Req 13.7-13.9, 14.7-14.11, 15.6)

The prior `perf/benchmark.mjs` was statically REJECTED before any timing (evidence retained under `docs/native-checks/03/task-perf-harness-check.txt` and the rejected source archive). The corrected harness addresses each verified defect; gameplay, gravity, piece set (unrotated), and rendering (React DOM) are unchanged, and no inflation loop or 60 Hz API traffic is added.

1. **Full-board signature (Req 13.7).** The prior `boardSignature` truncated each cell's style string to its first 4 characters; because every own cell's inline style begins with `width...`, the signature collapsed all cells to a constant and could stay unchanged despite real movement. The corrected signature reads the 200 board cells in a stable order and encodes the COMPLETE, unambiguous per-cell displayed state (the full occupancy/color/state marker for both active and settled cells), with no lossy truncation, and retains the full 200-length array plus a compact digest. DOM mutation batches retain their page-clock timestamp, count, and the complete before/after signatures.
2. **Observe the board after it exists (Req 13.8).** The prior init script called `mo.observe(document.body, ...)` in `addInitScript`, before `document.body` may exist. The corrected harness waits for document readiness and for the full 10x20 board element (all 200 cells) to be present before installing the observer and before warm-up, without altering gameplay.
3. **Sandbox and browser channel (Req 13.9).** The prior launch used `chromium.launch({ headless: false })`, which does not explicitly enable Playwright's Chromium sandbox. The corrected launch sets `chromiumSandbox: true` and retains the headed launch configuration. A documented `PERF_BROWSER_CHANNEL` env var (for example `chrome`) lets the host use its installed stable Chrome; the default bundled Chromium is used only when actually available. The report records the actual `browserName`, `browser.version()`, the channel used, and the Playwright version — never a hard-coded constant for sandbox/foreground.
4. **Fixed page-clock window (Req 14.7).** The prior `windowEnd` was set after a Node wall-clock driving loop, so it was not a fixed 30000 ms page-clock window. The corrected harness marks `windowStart` on the page clock and computes `windowEnd = windowStart + 30000` on that same clock. Each frame sample keeps its timestamp and the previous-frame timestamp; an interval counts only when BOTH endpoints lie inside `[windowStart, windowEnd]`. Boundary and warm-up samples are retained but flagged excluded. The action, focus, geometry, DOM, and API summaries all use this same measured window and never aggregate warm-up activity.
5. **Causal action -> visible update (Req 14.8, 14.9).** The prior `__perfCompleteAction` ran immediately after the keypress, before any async API/DOM completion, and latency used the first later mutation as if causal. The corrected flow records an action id and the before signature/state, then AWAITS the relevant authoritative response and an actual visible board-signature transition before completing the action and recording the after signature/state and the page-clock dispatch/update timestamps, associating action/request/response. Ambiguous, unchanged, censored, or out-of-window samples are EXCLUDED from latency statistics and REPORTED with a reason (count + cause); delayed/overlapping gravity updates are guarded; warm-up actions are never mixed into measured latency. Resource Timing is treated as the SAME page performance clock and labeled as a separate measurement stream on that clock; any Node-side request->response timing is a separately identified stream with no cross-domain timestamp subtraction.
6. **Validity vs. numeric targets (Req 14.10, 14.11).** The prior `overallTargetsMet` ignored focus/geometry/evidence and could pass an invalid capture. The corrected evaluation reports two SEPARATE verdicts: a numeric `targetsMet` (mean >= 55 FPS and p95 <= 25 ms) and a `qualified` measurement-validity gate that requires measured input focus throughout the window, full and unclipped 20x10 board geometry throughout, non-empty frame/DOM samples, and a retained screenshot-bearing trace plus real viewport PNGs. A run that is not `qualified` fails honestly regardless of its numeric values. The report records the actual browser/Playwright/Node/OS/CPU/RAM and available GPU/display configuration and states explicitly that unobservable physical display presentation remains unknown.
7. **Robust finally and cleanup (Req 15.6).** The prior `catch` exited with console output only, losing partial samples. The corrected `runOnce`/`main` use a `finally` that persists partial raw datasets, failure metadata, and exception details even when a run throws; it closes only the browser and context it owns, stops the focus/geometry sampler after capture, and leaves no orphaned child processes. The harness remains a documented manual command separated from unit CI; this round does NOT execute the timing-sensitive benchmark.

### Benchmark harness corrected defects (Round 06, Req 20)

A focused benchmark review (QA intent `kiro-stage3-performance-02`) verified that six real defects remained present in `perf/benchmark.mjs` even after the round-04 corrections above (which remain valid and are preserved exactly). The corrections below are surgical: gameplay, gravity, the unrotated piece set, React DOM rendering, pacing, and the preserved experimental controls are all unchanged, and no inflation loop or 60 Hz API traffic is added.

1. **Run-wide unique action ids (Req 20.1).** DEFECT: `driveGameplay` reset its loop counter `i` to `0` on every outer measured sub-call, so action ids (`"m0"`, `"m1"`, ...) repeated across sub-calls; `Array.find` then matched the earliest stale record, so every action effectively reused `m0` and completed the wrong record. FIX: action ids are generated from a single run-wide monotonically increasing counter that persists across all driving sub-calls, so each dispatched action carries a globally unique id. The dispatch/update association is retained per unique id in a map keyed by that id (not a linear `find` over a shared array), and a sample already completed for an id is never overwritten by a later record — ids are never reused, so stale-record matching is impossible.

2. **Real API response + DOM transition association, no gravity attribution (Req 20.2).** DEFECT: `__perfTryCompleteAction` completed an action on ANY later board-signature change, so an ordinary gravity tick landing between dispatch and poll could complete a key, and nothing tied completion to the authoritative API response. FIX: an action completes only when BOTH (a) the matching real successful authoritative API response for that specific action is observed AND (b) a displayed board-state DOM transition attributable to that action is observed. The harness preserves, per action, the raw request/response ids, HTTP method, route, action payload, response status, request/response timestamps, the response state identity, and the before/after DOM-signature evidence. Ambiguous, overlapping, no-op, and timed-out samples are excluded from latency statistics and reported with explicit reasons rather than being attributed to an arbitrary gravity update; it is acceptable to report an explicitly limited eligible-action subset together with the exclusion reasons. Input pacing stays at most four actions per second under ordinary gravity using the real keyboard controls, with no fabricated game responses. Node-side API round-trip timing lives on its own monotonic clock and is kept strictly separate from the page-clock dispatch-to-DOM stream, with NO cross-clock timestamp subtraction. The harness does not alter the application's request bodies or request queues.

3. **Both-endpoint window eligibility for latency (Req 20.3).** DEFECT: latency eligibility considered only the dispatch timestamp's in-window flag and did not require the matched update to fall inside the window. FIX: a latency sample is eligible only when BOTH the dispatch timestamp AND the matched update timestamp fall inside the same fixed page-clock window `[windowStart, windowStart + 30000]` ms. Samples that straddle a window boundary are retained (not discarded) and reported with an exclusion reason.

4. **Sampler lifecycle, capture end, 200-cell and batch-count qualification (Req 20.4).** DEFECT: the `requestAnimationFrame` frame sampler was never stopped, no real capture-end was recorded, qualification did not require exactly 200 visible board cells or an adequate valid-sample count, and the DOM "batch count" semantics were unpinned. FIX: all passive samplers — the re-armed `requestAnimationFrame` frame-scheduling sampler and the focus/geometry interval sampler — are explicitly stopped and released at capture end. The actual capture-end timestamp is recorded separately, and a capture is marked unqualified if the full fixed window was not actually observed. Qualification requires exactly 200 visible board cells and an adequate count of valid samples for every claimed measured stream. The DOM batch count is defined as the number of changed-signature observer batches, never a count of individual cell mutations. All raw timestamps and the full 200-cell signatures are preserved.

5. **Failure telemetry before close, honest trace flag, artifact verification (Req 20.5).** DEFECT: on failure the harness did not re-pull surviving page telemetry before closing the page, set `traceTaken = true` even when `tracing.stop` was swallowed, and never verified artifact existence or size. FIX: on ANY failure the harness fetches best-effort partial telemetry from the surviving page BEFORE closing it; it always persists the raw data, the exception, and the REAL success flags for the viewport PNG and the trace; it sets the trace-taken and screenshot-taken flags only after the corresponding operation actually succeeded (never on a swallowed `tracing.stop` failure); and it verifies each artifact's existence and non-zero size before claiming that the evidence exists. The researcher independently inspects the retained ZIP, trace frames, and PNGs.

6. **Truthful batch/per-run `startedAt` and `finishedAt` (Req 20.6).** DEFECT: the report set both `startedAt` and `finishedAt` to `new Date()` at the same point after completion, so both boundaries collapsed to the finish time. FIX: `startedAt` is captured at the real start of the batch/run and `finishedAt` at the real finish, so the reported timestamps reflect the true boundaries.

The accepted core application, its tests, the dependency sets, the Docker packaging, the CI/performance workflows, and the earlier-stage specs are all unchanged; only `perf/benchmark.mjs`, `perf/README.md`, and a concise native evidence note under `docs/native-checks/06` are changed. The preserved experimental controls remain exactly as before: three fresh headed sandboxed Chromium sessions, a 1280x900 viewport at device scale factor 1, a 60 Hz target, a warm-up of at least five seconds excluded from latency, fixed 30-second measured windows, `requestAnimationFrame` both-endpoint window filtering, full 200-cell board signatures, input-focus and board-geometry evidence sampled throughout each window, screenshot-bearing traces plus a final viewport PNG per trial, `PERF_BROWSER_CHANNEL` support, numeric targets (mean >= 55 FPS and p95 <= 25 ms) reported separately from the measurement-validity qualification gate, a failing exit on an invalid capture or unmet targets, and an honest "physical display presentation unknown" statement. This round does NOT execute the timing-sensitive benchmark; final performance execution remains unexecuted and is not marked complete.

### Benchmark harness corrected defects (Round 07, Req 21)

A focused follow-up benchmark review (same QA intent `kiro-stage3-performance-02`; researcher note `docs/researcher-review-07-causal.json`) confirmed that two real defects remained present in `perf/benchmark.mjs` even after the round-06 corrections above (which remain valid and are preserved exactly). The round-07 corrections are surgical and change only `perf/benchmark.mjs`, `perf/README.md`, and an optional concise native evidence note under `docs/native-checks/07`; gameplay, gravity, the unrotated piece set, React DOM rendering, input pacing, and every preserved experimental control are unchanged, and no inflation loop or 60-per-second API traffic is added. No timing run is executed this round.

1. **Genuine action-to-visible association (Req 21.1-21.11).** DEFECT: round-06 completion used `matchingApiCount('/move')` — a rising count of successful URL-suffix matches — together with ANY changed board signature. That is not a real action-to-visible association: a delayed move response plus an unrelated ordinary-gravity DOM transition arriving after the matching response headers but before that move's own state renders could satisfy completion. No per-action request id, direction, or response state was retained; `apiStatus` stayed `null`; the Node API rows lacked ids, payload, and response state. The round-06 claim that "ordinary gravity never completes an action" was therefore too strong. FIX:
   - A PASSIVE Playwright request/response observer (`page.on('request')`, `page.on('requestfinished')`, `page.on('requestfailed')`) assigns each observed `/api/.../move` request a unique per-run id and records its HTTP method, URL, the direction parsed from its POST body (`left`/`right`/`down`), the response status, and the successful response JSON state identity (the game `id` plus a hash/representation of `board` and `active_piece`). It also records Node monotonic request-to-body-end timestamps via `process.hrtime.bigint()`. It never reads or clones the application's `fetch` body in page context and never alters request bodies or request queues; the response JSON used to compute the expected signature is obtained from the Playwright `Response` object on the Node side (`response.json()`), which does not consume the page's body stream.
   - For a dispatched key, the harness selects the SINGLE new `/move` request whose parsed direction matches the dispatched key and whose lifecycle begins after the action is dispatched. It explicitly EXCLUDES the action when there is no candidate request, more than one candidate, an overlapping candidate, or a failed / no-op / timed-out response, reporting the exclusion reason; it never attributes the action to an arbitrary later gravity transition.
   - The harness reads the matched response's `board` (20x10 of codes `0..7`) and `active_piece` (`type` plus absolute `cells`) and computes the EXPECTED full 200-cell displayed signature exactly as the production `Board` component renders it: copy the settled board, overlay the `active_piece` cells with the piece type code (`I=1, O=2, T=3, S=4, Z=5, J=6, L=7`), map each code to the `Board` `COLORS` hex (`0=#111827, 1=#22d3ee, 2=#facc15, 3=#a855f7, 4=#22c55e, 5=#ef4444, 6=#3b82f6, 7=#f97316`), and build the per-cell token in the same format the in-page `cellCode()` uses, with a shared color-normalization applied to BOTH the expected and the observed signatures so CSSOM hex serialization differences never cause spurious mismatches.
   - Completion requires the observed in-page DOM board signature to EQUAL that specific expected 200-cell signature, not merely to differ from the pre-dispatch signature. A coalesced state never actually observed in the DOM is excluded and is never assigned an arbitrary later gravity transition.
   - Each completed action retains the matched request id, the expected and observed signatures, and the page-clock dispatch and observed-update timestamps. API round-trip time stays entirely on the Node monotonic clock and dispatch-to-observed-DOM latency stays entirely on the page clock; the two are never subtracted. Observer and polling overhead is documented, and the measurement is explicitly stated to be dispatch-to-observed-DOM latency, not input-to-photon or physical display presentation latency.

2. **Nonempty valid-sample qualification and strict window observation (Req 21.12-21.15).** DEFECT: round-06 `qualified` could be `true` with zero valid action-latency samples, and `fullWindowObserved` allowed `captureEndAt < windowEnd` by a tolerance, so a short capture could pass even though a fixed 30-second window must actually be observed; directional coverage was not required. FIX: a run qualifies only when it has a nonempty set of valid action-latency samples AND those valid samples cover actual left, right, and soft-drop actions; every excluded sample is reported with its reason; and `fullWindowObserved` now requires `captureEndAt >= windowEnd` STRICTLY (the earlier-stop tolerance is removed), with any actual late stop retained separately.

All other round-04 and round-06 controls are preserved exactly: three fresh headed sandboxed Chromium sessions, a 1280x900 viewport at device scale factor 1, a recorded 60 Hz target, a warm-up of at least five seconds excluded from latency, fixed 30-second measured windows, `requestAnimationFrame` both-endpoint window filtering, full 200-cell signatures and changed-batch counts, input-focus and full-board geometry evidence sampled throughout each window, a screenshot-bearing trace plus a final viewport PNG per trial, truthful failure partials and timestamps, `PERF_BROWSER_CHANNEL` / Chrome channel support, at most four keyboard actions per second, unchanged gravity, real application responses, and numeric targets (mean >= 55 FPS and p95 <= 25 ms) kept separate from qualification. The accepted application code, its tests, the dependency sets, the Docker packaging, the CI/performance workflows, and the earlier-stage specs are all unchanged. This round does NOT execute the timing-sensitive benchmark; final performance execution remains unexecuted and is not marked complete, and manual measured execution remains pending.

### Benchmark harness corrected defects (Round 08, Req 22)

A focused follow-up benchmark review confirmed that two real, independently reproduced defects remained in `perf/benchmark.mjs` even after the round-07 corrections above (which remain valid and are preserved exactly). Both defects are in the harness only; neither touches gameplay, gravity, the unrotated piece set, React DOM rendering, input pacing, or any preserved experimental control, and no inflation loop or 60-per-second API traffic is added. No timing-sensitive run is executed this round.

1. **Template-literal regex escape loss in the injected instrumentation (Req 22.1-22.7).** DEFECT (compile-time, browser-side): `perf/benchmark.mjs` builds its injected instrumentation as a normal JavaScript template literal, `const INSTRUMENT = \`...\``, and passes the cooked string to Playwright `addInitScript`. A normal template literal evaluates backslash escape sequences while cooking, so regex backslashes written in the source — `\(`, `\s`, `\d` in the `rgb`/`rgba` color-normalization matcher — are stripped from the COOKED injected string. The cooked color-normalization line degrades to `const rgb = v.match(/rgba?(s*(d+)s*,s*(d+)s*,s*(d+)/);`, which is an invalid regular expression with an unterminated group. When the browser compiles the injected script it throws `SyntaxError: Invalid regular expression: Unterminated group`, so the entire instrumentation IIFE fails to install: `window.__perf`, the passive observers, the frame sampler, and every `window.__perf*` board-signature helper never exist. Because round-07 validated the harness only with `node --check` on the OUTER file (which parses fine — the defect lives purely in the cooked INNER string), the broken cooked regex was not caught, and in a real run every board-signature, action-association, focus, and geometry call would reject silently. FIX — escape preservation in the cooked script:
   - The injected instrumentation is constructed so that every regex backslash survives cooking. The chosen approach is a `String.raw` tagged template for the instrumentation body (`const INSTRUMENT = String.raw\`...\``) so that `\(`, `\s`, `\d`, `[0-9a-f]`, and the `#rgb`/`#rrggbb` hex matchers, the `background[^;]*` style matcher, and the `#[0-9a-fA-F]{3,6}|rgba?\(...\)` extractor all appear in the cooked string with their backslashes intact and compile to valid regular expressions in the browser. (Equivalently, correctly doubling every backslash in a normal template literal would preserve the same cooked bytes; `String.raw` is chosen because it keeps the source regexes readable and avoids silent re-introduction of the same defect on future edits.)
   - Because `String.raw` suppresses ALL escape processing, the `\u0001` signature-join separator would otherwise cook to the literal six-character sequence `\u0001` rather than a single U+0001 code unit. The fix therefore does NOT write `\u0001` as a raw escape inside the template. Instead the separator is produced as a real U+0001 character through an interpolated sentinel constant: a Node-side `const SIG_SEP = String.fromCharCode(1);` is interpolated into the raw template as `${SIG_SEP}` at every join/split site, so the cooked script embeds exactly one real U+0001 code unit while the surrounding regex backslashes remain raw. This is the explicit coexistence rule: regex backslashes stay raw via `String.raw`, and the single-character U+0001 separator (plus the `${BOARD_CELLS}` and `${MEASURE_MS}` numeric interpolations) are injected through `${...}` interpolation, which `String.raw` still evaluates. The `${BOARD_CELLS}` and `${MEASURE_MS}` interpolations and every other regex in the template are preserved unchanged by this approach.
   - VALIDATION — a non-timing check that exercises the ACTUAL cooked output (not a replica). The check imports or reads the REAL native `perf/benchmark.mjs`, extracts the actual `INSTRUMENT` string exactly as the harness constructs it, and compiles that real cooked script separately (for example via `new Function(cooked)` or a `vm` context) under a minimal inert stub providing `window`, `document`, and `requestAnimationFrame`, with no browser and no measured timing. It then invokes the real cooked color-normalization and signature functions and asserts that `rgb(17,24,39)` and `#111827` normalize to the identical token, and that a full 200-cell board whose cells are expressed in those two equivalent forms produces identical normalized tokens across all 200 cells (confirming the join separator and per-cell normalization survive cooking). This check MUST NOT copy or re-declare the instrumentation function bodies inside the test — copying the code is exactly what let the round-07 validation pass while the real cooked string was broken; it must compile and run the harness's own cooked output. The native evidence note for this check is recorded under `docs/native-checks/08`.

2. **Observation body-readiness race in `/move` candidate selection (Req 22.8-22.12).** DEFECT (selection correctness, Node-side): in the passive `/move` request/response observer, the `requestfinished` handler sets `observation.endNs` (the Node monotonic request-to-body-end timestamp) BEFORE the subsequent `await resp.json()` resolves and fills `observation.colorGrid`/`stateId`. `selectMoveCandidate` treats `endNs !== null` as "finished" and then, finding `colorGrid` still `null` for a successful HTTP 200 whose body is still parsing, classifies the observation as `status: "failed"` ("matched /move response not a usable success"). A genuinely successful move whose body has simply not finished parsing is therefore falsely rejected and its action excluded, under-counting valid directional samples and skewing qualification. FIX — explicit body-ready completion flag:
   - The observation carries an explicit completion flag (for example `bodyReady`) that is set ONLY after body parsing settles, inside a `finally` stage that runs whether parsing succeeded or threw. On success the `finally` records the parsed `colorGrid`/`stateId` and marks `ok: true`; on a genuine parse failure or unreadable body it records a real error flag (for example `ok: false` with `bodyError`) so a truly unusable response is still distinguishable from one that is merely still parsing. The Node monotonic request-to-body-delivery RTT continues to be recorded on the existing Node monotonic clock (`process.hrtime.bigint()`), with no cross-clock mixing against the page clock.
   - `selectMoveCandidate` keys readiness off that explicit `bodyReady`/completion flag and the explicit failure flags, NOT off the presence of `endNs` or `colorGrid`. A candidate whose body is still parsing (not yet `bodyReady`) is treated as "not finished yet" and the harness keeps waiting within the action settle deadline rather than rejecting it; a candidate is classified `failed` only when an explicit failure flag is set (network failure, non-2xx status, or a real unreadable-body error), and `one` only when it is `bodyReady`, `ok`, and carries a usable `colorGrid`. This removes the false rejection of still-parsing successful 200s while preserving round-07's honest no-op exclusion, the exact expected-vs-observed 200-cell signature match, the required left/right/soft-drop directional coverage, and the strict fixed 30-second window where `captureEndAt >= windowEnd`.

Change scope and status (Req 22.13-22.14): the round-08 corrections modify ONLY `perf/benchmark.mjs` and `perf/README.md`, plus the native evidence note under `docs/native-checks/08`. The accepted application code, its tests, the dependency input manifests and resolved locks, the Docker packaging, the CI/performance workflows, and the earlier-stage specifications are all unchanged. Because no timing-sensitive benchmark run is executed this round, the performance measurement status stays PENDING: final performance execution is not marked complete, no frame-rate, latency, or other performance numbers are claimed, and real performance evidence still does not exist.

### Benchmark execution and Stage 3 closure (actual measured results)

Unlike rounds 06, 07, and 08 — which each corrected harness defects and deliberately executed no timing run — the measured benchmark has now actually been executed. After the round-08 harness fixes landed, the researcher-agent ran the unchanged, byte-identical manual benchmark command on the local machine, and Stage 3 is now closed with real recorded evidence rather than a pending status. All numbers below come solely from the authoritative researcher facts file (`docs/researcher-final-results-before-docs.json`); none is fabricated, and the warm-up boundary timestamps, token/cost/credit figures, and optimization percentages that the harness does not record are not invented here.

The measured harness is frozen and byte-identical: `perf/benchmark.mjs` has SHA256 `1E6343476E8CA813E404E547F4E9486929D9686083128C91D2448847F8F0952C`. It was run exactly as documented, with no edits to application code, tests, dependency manifests or locks, Docker, CI, or the performance harness, its validator, or its `package.json`.

The run captured three independent fresh headed sandboxed Chrome sessions (browser channel `chrome`, version `156.0.8078.80`, Playwright `1.56.0`) at a 1280x900 viewport with device scale factor 1. The recorded frame target was 60 Hz, the configured physical display ran at 165 Hz, each run used a configured 5000 ms active warm-up, and each measured window was an exact 30000 ms page-clock window.

Per-run scheduling was effectively locked to the display: approximate FPS was 165.0068, 164.9724, and 165.0063 across runs 1, 2, and 3 respectively (approximately 165 each). The frame-interval p95 was 6.2 ms in every run; p99 was 6.2 ms, 6.2 ms, and 6.3 ms; the median was 6.1 ms in every run; and slowFrames (frame intervals above 33.34 ms) were 0 in every run. The numeric operational targets — a mean of at least 55 FPS and a p95 of at most 25 ms — were met in every run.

Frame samples per run were 4949, 4948, and 4949. Changed-signature DOM batches were 100, 99, and 98 — these are explicitly changed-signature observer batches, not per-cell mutation counts. Valid action-latency samples were 100, 99, and 98, with excluded action samples of 0, 0, and 1; the single exclusion in run 3 was a dispatch and/or observed update that fell outside the fixed window, and it was retained together with its recorded reason rather than discarded. Input-focus and board-geometry samples were captured throughout each run, and the full 10x20 board was visible in all three retained final PNGs.

An independent raw audit passed 52 checks spanning raw frames, DOM batches, API actions, focus, geometry, traces, and PNGs, and a separate visual review covered the 3 PNG images.

Additional successful game creates after the initial one were 0 in all three runs, so the conditional restart path was NOT exercised by these timing trials. Restart behavior and persistence are verified separately by the backend API tests and synthetic fixtures, not by the benchmark.

API round-trip timing was recorded on its own Node monotonic clock (`api_node_completed_observations` of 123, 122, and 122 across the three runs) and was never subtracted against the page-clock dispatch-to-observed-DOM stream.

Honest limits, carried over in meaning from the researcher facts: the rAF scheduling stream, the changed-signature DOM-batch stream, and the Node API stream are separate streams, and none of them establishes physical display presentation; the 165 Hz OS display is distinct from the recorded 60 Hz target. Dispatch-to-observed-DOM latency includes observer, passive-observation, and approximate polling overhead and is NOT input-to-photon or physical presentation. Focus and geometry are timestamped samples, not continuous proof of physical visibility. Native percentiles use `sorted[floor(p*n)]`, with linear-interpolated alternates and the fixed-window callback rate separately retained for later analysis. The late capture stops of 220.0 ms, 246 ms, and 310.3 ms are retained as `lateStopMs`, while every statistic uses only the exact 30000 ms windows. The 5000 ms warm-up boundary timestamps are not separately persisted by the harness and are not invented here.

Broader Stage 3 acceptance that the researcher recorded is stated here as researcher-run local evidence — not hosted CI and not human approval. The backend, frontend, API, and FX test suites passed. The SonarQube quality gate was OK with new-code coverage 97.3%, 0 new issues, and 0 new duplication, alongside global coverage 94.8%, 0 bugs, 0 vulnerabilities, 0 security hotspots, and 5 inherited open smells. Local Python 3.12 and Node 24 clean-equivalent CI checks passed. The Docker stack was verified healthy, running non-root, frontend-only on port 5183 with an internal backend and its own persistent named volume. The production dependency audit found 13 installed application packages, all pinned and with no advisories. Ordinary hosted GitHub Actions execution was NOT performed: the authored workflow files together with the local clean-equivalent runs are what passed, and no human approval is claimed.

Scope note: round-08 added a permanent non-timing validation utility, `perf/validate-instrument.mjs`, and an `npm validate:instrument` command, beyond the originally narrow requested file list. The researcher accepted an exact script-only metadata/support-file exception after a full source review, and the original strict-binding rejection is retained. This is not a retrospective exact-file-list-compliance claim; the application and core locks and the full performance timing source remain byte-identical.

## Continuous Integration

Location: `.github/workflows/`. The workflow files are configuration artifacts only; their presence is **not** claimed as evidence of a hosted Actions run (Req 16.6).

### Ordinary CI (`.github/workflows/ci.yml`)

- **Jobs:** backend tests **with coverage** (install the dev/audit set, which layers `pytest`, `httpx`, and `pytest-cov` on top of the runtime set, then run `pytest --cov=app --cov-report=xml`), frontend tests (`npm ci`, `npm run test -- --coverage`), the frontend **production build** (`npm run build`), and the **Docker image builds** for backend and frontend (Req 16.1). The runtime image build installs only the runtime set, so CI exercises the same no-dev-deps runtime image the deployment uses.
- **Runtime pinning:** pins **Python 3.12** (the Python major version) and **Node 24** (the Node major version) (Req 16.2). These are the explicit supported majors selected for both CI and the Docker images; the backend runtime base is `python:3.12-slim`.
- **Reproducible install:** documents reproducible installation and preserves/updates lockfiles coherently using the two concrete explicitly-pinned sets recorded under "Dependency security remediation (selected versions and lock strategy)" -- the production RUNTIME set (`fastapi==0.137.2`, `starlette==1.3.1`, `pydantic==2.10.4`, `uvicorn==0.34.0`, plus their exact resolved transitive locks) installed into the runtime image, and the DEV/AUDIT set (`pytest==9.0.3`, `httpx==0.28.1`, `pytest-cov` confirmed/bumped for `pytest` `9.0.3` compatibility, `pip-audit==2.10.1`, plus transitive locks) layered on top for CI only; every runtime transitive is pinned (no floating), with `starlette` pinned directly to guarantee the remediated version. Frontend installs via `npm ci` against the committed lockfile (Req 16.3). Compatible frontend pins are preserved unless an actual audit or compatibility finding requires a change.
- **No secrets:** the backend, frontend, build, and image checks require no private secrets (Req 16.4).
- **Dependency audit:** runs basic audit commands (`pip-audit` for Python, `npm audit` for the frontend) and reports the actual findings without suppression (Req 16.5).
- **Separation:** ordinary unit/build/image checks are separated from the timing-sensitive performance checks (Req 16.7, 15.5).

### Manual performance job (`.github/workflows/perf.yml`)

- A **separate, explicitly triggered** (manual / `workflow_dispatch`) job that runs the `perf/` benchmark; it is never part of the ordinary unit pipeline (Req 15.5, 16.7).

## Testing Strategy

No property-based testing section is included: the Stage 3 additions are I/O-bound persistence, an HTTP contract, Docker/CI configuration, a browser benchmark, and UI rendering/fetch orchestration. These are best verified with example-based unit tests, integration tests, concurrency tests, snapshot/config checks, and browser-driven tests rather than universally-quantified properties. The synthetic multi-row-clear fixtures reuse the existing Stage 2 pure-rules path (the real `engine.tick` / `engine.lock` -> `clear_lines` production entry) and are example-based; the engine exposes no standalone line-clear API that takes a synthetic shape, so the fixtures drive the unchanged production path rather than a fabricated API.

This section states WHAT will be tested and HOW. It does **not** assert that any test, build, audit, container run, CI run, or benchmark has been executed.

### Backend (`pytest`, extending `backend/tests/` without altering inherited assertions)

- **Persistence happy path:** a game driven to `game_over` writes exactly one `High_Score_Record` with the server-authoritative `score`, `total_lines`, `level`, and a UTC ISO-8601 `completed_at` (Req 2.1, 2.3).
- **Zero score:** a game that reaches `game_over` with `score == 0` is still finalized (Req 2.2).
- **Idempotency:** repeated terminal mutating requests keep exactly one record with unchanged `score`/`total_lines`/`level`/`completed_at` (Req 3.1, 17.4).
- **UNIQUE dedup / concurrency (meaningful, through the controller/service boundary):** the primary concurrency test issues **concurrent mutating requests through the controller/service boundary** (not only direct duplicate `INSERT` calls against the store) to a game driven terminal, asserting exactly one `High_Score_Record` results via the single-lock boundary plus the service gate plus the `game_id` UNIQUE backstop. A targeted store-level duplicate test complements it but does not replace the controller-level concurrency test (Req 2.5, 3.2, 3.5, 17.3). A separate test asserts that a non-`game_id` integrity/storage failure is **not** swallowed as a duplicate but surfaces as a `StorageError` -> 503.
- **Failure and recovery (frozen snapshot):** an injected storage failure during finalization yields a controlled 503 with `application/json`, a valid JSON body, a human-readable storage message, and no path/SQL/exception-name/stack trace; the game stays terminal and pending; the captured immutable pending record (including its `completed_at`) is retained; a later mutating request retries and succeeds with a single record whose `completed_at` equals the value captured at the first terminal transition (asserting it was **not** regenerated at retry time); a `GET` on the pending terminal game never retries, never captures a record, and never changes pending status (Req 2.6, 2.9, 7.1-7.9, 17.1).
- **503 on read:** a storage failure while serving `GET /api/high-scores` yields the same controlled 503 contract (Req 7.1, 7.3-7.5, 17.8).
- **Tie-break ordering:** equal `score` values order by `completed_at` ascending, then `game_id` ascending; the array is capped at ten (Req 5.2, 5.3, 17.2).
- **Exact leaderboard contract:** `GET /api/high-scores` returns `{"scores": [...]}` with each entry containing exactly the five fields, and an empty array when no rows exist (Req 5.1, 5.4, 5.5, 17.8).
- **Injection-like inputs rejected:** extra body fields on `POST /api/games` and `POST /api/games/{id}/move`, and arbitrary `game_id`/score metadata, are rejected (422) or ignored for persistence; bodyless create still returns 200 and valid moves behave as Stage 2 (Req 6.1-6.6, 17.5).
- **Persistence across a new store instance:** a freshly constructed `HighScoreStore` opening the same database file reads the previously persisted rows without reinitializing or clearing them (Req 4.1, 4.4, 17.6).
- **Synthetic 3-row and 4-row clears (real engine symbols only):** the engine's real API is the pure functions `new_game`, `spawn`, `clear_lines`, `lock`, `tick`, `move`, and `hold` operating on a `Game`; there is **no** standalone line-clear function that takes a synthetic shape. `lock(game)` settles the active piece and then calls `clear_lines(game)`, and `clear_lines(game)` operates on `game.board`. The fixtures therefore prefill complete rows **directly on `game.board`**, position a controlled canonical **unrotated** piece, and drive the **unchanged production path** by calling `engine.tick`/`engine.lock` on the real `Game`, which runs `clear_lines` and the real scoring to verify awards and the resulting `total_lines`/`level`/`gravity_interval_ms`. They reference no nonexistent API and no changed engine shape, do not rotate pieces, and do not invent gameplay pieces. Three- and four-line clears remain explicitly **unreachable through ordinary unrotated gameplay**, which is precisely why these are synthetic fixtures over the real path (Req 17.7).
- **Startup:** `initialize()` creates a missing parent directory and the schema, leaves existing rows intact, and enforces `UNIQUE(game_id)` (Req 1.3-1.6).

### Frontend (Vitest + Testing Library, extending `frontend/src/*.test.*`)

- **Panel states:** loading, empty, error, and loaded rendering of `score`/`total_lines`/`level`, with all visible text in English (Req 8.1-8.4, 8.8).
- **Fetch cadence:** the leaderboard is fetched **once on initial mount** and **again on each real `playing -> game_over` transition**, and **not** on every automatic tick (Req 8.5, 8.6, 8.7).
- **Fetch ownership and stale-guard:** tests cover (a) a **delayed `fetch`** whose response is invalidated when the request is superseded; (b) a **delayed `response.json()`** confirming the stale check runs after BOTH promises resolve, not only after `fetch`; (c) a **stale (old) error** not overwriting a newer result or the current state, and the `finally`/cleanup path running on restart, unmount, and StrictMode teardown; (d) the **game-over refresh arriving while the initial fetch is still unresolved**, asserting the required game-over refresh still runs and commits the latest leaderboard rather than being silently dropped by a naive in-flight boolean (Req 8.4, 9.3).
- **Lifecycle non-disturbance:** adding the leaderboard fetch does not clear, block, or reschedule the per-generation automatic-tick scheduler or the manual FIFO queue (explicitly asserting the game FIFO/timers are preserved), and the Stage 2 controls, Hold restrictions, stale-response/generation protections, and R1-R5 guarantees still hold (Req 9.1-9.4, 17.9).
- **Configurable base:** the client uses the configurable API base (default same-origin `/api`) and the production path never hardcodes `localhost` (Req 10.1, 10.2).

### Regression, coverage, and evidence discipline

- **All inherited Stage 1 and Stage 2 backend and frontend regression tests must continue to pass unchanged**, including the detailed Stage 2 frontend request-ordering/lifecycle tests (`useGame.test.tsx`, `useGame.races.test.tsx`, `useGame.queued-timers.test.tsx`) and the backend rules/scoring/API tests (Req 18.1, 18.3).
- **Coverage includes all production files** with no exclusions of production modules, on both backend (`app/`) and frontend (`frontend/src/`), consistent with the pinned `@vitest/coverage-v8` and `pytest-cov` tooling; audit findings are reported without suppression (Req 16.5, baseline dependency rules).
- **Isolated-domain evidence** (engine/persistence fixtures, including synthetic 3-/4-row clears) is kept separate from **user-visible / browser evidence** (frontend tests and the benchmark harness) in any recorded results.
- **Retained exclusions** (Req 18.2): no rotation, wall kicks, ghost piece, T-Spins, time attack, achievements, saved/resumable games, PostgreSQL, authentication, multiplayer, global real-time leaderboards, or cloud deployment. **No commits, pushes, image publishing, or external deployment** are performed by this stage (Req 18.5). The inherited specs under `.kiro/specs/tetris-stage1-option-a/` and `.kiro/specs/tetris-stage2-option-a/` remain unchanged (Req 18.3). No completed approvals, checks, metrics, CI runs, tokens, costs, screenshots, Docker successes, or performance results are fabricated by this specification (Req 18.6).
