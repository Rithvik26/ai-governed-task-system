# AI-Governed Task Lifecycle System

A deliberately small system designed to demonstrate state correctness, safe
evolution, and controlled AI-assisted development — built as an engineering
assessment.

The goal is not feature richness. Every decision optimises for: preventing
invalid states, clear layer boundaries, testability, and explicit AI
governance.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Browser  (React 18 / Vite 5)                                    │
│                                                                  │
│  ProjectList ──▶ ProjectDetail ──▶ TaskItem                      │
│                       │                                          │
│              api/client.js  (fetch wrapper, no hardcoded URLs)   │
└──────────────────────────┬───────────────────────────────────────┘
                           │  HTTP JSON  (Vite proxy → 127.0.0.1:5001)
┌──────────────────────────▼───────────────────────────────────────┐
│  Flask 3  (app.py — application factory)                         │
│                                                                  │
│  routes/projects.py        routes/tasks.py                       │
│  HTTP only: parse ─▶ schema ─▶ model/db ─▶ schema ─▶ respond    │
│       │                         │                                │
│       ▼                         ▼                                │
│  schemas.py  ── validates all input, serialises all output       │
│       │                         │                                │
│       ▼                         ▼                                │
│  models.py  ── Project, Task, VALID_TRANSITIONS, transition_to() │
│       │                                                          │
│       ▼                                                          │
│  database.py  ── SQLAlchemy db + SQLite PRAGMA foreign_keys=ON   │
│       │                                                          │
│       ▼                                                          │
│  tasktracker.db  (SQLite, FK constraints enforced at DB level)   │
└──────────────────────────────────────────────────────────────────┘

Observability (app.py hooks):
  before_request  →  record wall-clock start time
  after_request   →  log method, path, status, latency (ms)
  AppError        →  logged WARNING/ERROR with machine code
  Exception       →  logged ERROR with full traceback
```

---

## Layer ownership (strict)

| Layer | Owns | Must not |
|---|---|---|
| `routes/` | Parse HTTP, call schema, call model/db, return status code | Contain business logic or raw dict responses |
| `schemas.py` | Validate input shape and enum values, serialise output | Touch the database or know about HTTP |
| `models.py` | Enforce domain invariants (state machine, field rules) | Know about HTTP, schemas, or serialisation |
| `database.py` | `db` SQLAlchemy instance + SQLite FK enforcement PRAGMA | Contain any logic |
| `errors.py` | Typed exceptions + Flask error handler registration | Be imported by models or schemas |

---

## Task lifecycle

```
  ┌──────┐      ┌─────────────┐      ┌──────┐
  │ todo │ ───▶ │ in_progress │ ───▶ │ done │
  └──────┘      └─────────────┘      └──────┘

  All other moves (skip, reverse, re-open) are rejected with 400.
```

Enforcement lives exclusively in `Task.transition_to()` in
[backend/models.py](backend/models.py). No route, test helper, or future
worker may set `task.status` directly.

---

## Key design decisions

### Why validation is schema-based

Every request body passes through a Marshmallow schema before any model or
database code runs:

1. **Single input contract.** The schema is the machine-readable spec of what
   the API accepts. One file tells you everything the endpoint will accept.
2. **Unknown fields are dropped.** `Meta.unknown = EXCLUDE` prevents parameter
   pollution without raising an error.
3. **Enum values coerced at the boundary.** Invalid priority/status strings are
   rejected with `VALIDATION_ERROR` before the model sees the data. The model
   only ever receives valid Python enum values.

Putting validation in route handlers scatters the contract and makes it easy
to miss cases when a second route is added.

### Why lifecycle rules live in the model

`Task.transition_to(new_status)` is the single enforcement point. It raises
`StateTransitionError` for any illegal move. No other code may set
`task.status` directly.

The invariant is impossible to bypass from a route, a test helper, or a future
background job — they all pass through the same method and the same
`VALID_TRANSITIONS` table. If the rule lived in a route, a second route could
silently skip the check.

### Why SQLite FK enforcement is explicit

SQLite does not enforce foreign key constraints by default. Without
`PRAGMA foreign_keys=ON`, deleting a project while tasks still reference it
would silently succeed at the database level (even though the application
cascade handles it). The event listener in `database.py` enables FK
enforcement for every new connection so the database is a second safety net,
not just the application layer.

---

## Error format

Every error response uses a consistent structure:

```json
{
  "error": "Human readable description of what went wrong",
  "code":  "MACHINE_CODE_FOR_CLIENTS"
}
```

Codes: `VALIDATION_ERROR`, `INVALID_STATUS_TRANSITION`, `PROJECT_NOT_FOUND`,
`TASK_NOT_FOUND`, `NOT_FOUND`, `INTERNAL_ERROR`.

---

## Observability

| Event | Log level | Content |
|---|---|---|
| Every HTTP request | INFO | method, path, status, latency ms |
| Schema validation failure | WARNING | field error dict |
| Rejected state transition | WARNING | from status, to status, code |
| Unhandled exception | ERROR | exception message + full traceback |

Nothing is swallowed. `LOG_LEVEL` env var controls verbosity (default: INFO).

---

## Running locally

### Prerequisites

- Python 3.11+
- Node 18+

> **macOS note:** AirPlay Receiver occupies port 5000 on macOS Monterey and
> later. The backend binds explicitly to `127.0.0.1:5001` to avoid this.
> The Vite proxy is configured to target `http://127.0.0.1:5001`.

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py          # listens on 127.0.0.1:5001
```

### Frontend

```bash
cd frontend
npm install
npm run dev            # proxies /projects and /tasks to 127.0.0.1:5001
```

Vite will print the URL — typically `http://localhost:3000`.

### Environment variables

See `.env.example` at the repo root. Copy it to `backend/.env` if you need to
override `DATABASE_URL` or `LOG_LEVEL`. The app works without any `.env` file
using defaults.

---

## Running tests

```bash
cd backend
source .venv/bin/activate
pytest                          # all 32 tests
pytest -v                       # verbose
pytest tests/test_tasks.py -v   # single file
```

Tests use **in-memory SQLite** via `TestConfig`. Every test function receives
a fresh database from the `db` fixture in `tests/conftest.py`.

The suite is structured to prove the system **prevents bad states**:

- Missing required field → `400 VALIDATION_ERROR`
- Invalid enum value → `400 VALIDATION_ERROR`
- Empty request body → `400 VALIDATION_ERROR`
- Skipping a status step → `400 INVALID_STATUS_TRANSITION`
- Reversing a status → `400 INVALID_STATUS_TRANSITION`
- Re-opening a done task → `400 INVALID_STATUS_TRANSITION`
- Transition error message names both from and to status
- `updated_at` advances after a transition
- Tasks from other projects not returned (isolation)
- Every error response has `error` and `code` keys

---

## Tradeoffs

| Decision | Benefit | Cost |
|---|---|---|
| SQLite | Zero-config, portable | Cannot serve concurrent writers; replace with Postgres for production |
| Flask-SQLAlchemy | Clean Flask integration | Couples models to Flask app context |
| Marshmallow 4 | Mature, explicit load/dump separation | `@validates` must accept `**kwargs` in v4; more verbose than Pydantic |
| No auth | Scope is clearly bounded | Not safe to deploy as a multi-user service |
| No pagination | Routes stay thin | Will break under large datasets |
| SQLite FK PRAGMA | DB-level FK enforcement | Must be reapplied per connection via event listener |
| Vite proxy | No CORS config needed | Frontend and backend must run together locally |
| Port 5001 | Avoids macOS AirPlay conflict | Non-standard; must be documented |

---

## How to extend safely

1. **Model first.** Add the new field or method. Write a direct test for the
   model behaviour before touching routes.
2. **Schema second.** Add the field with a `@validates` decorator if it has
   constrained values. In marshmallow 4, validators must accept `**kwargs`.
3. **Route last.** HTTP parsing only — delegate entirely to schema and model.
4. **Tests required.** Happy path + missing field + invalid value.
5. Run `pytest`. All tests must pass before committing.

See [claude.md](claude.md) for the AI-specific version of this checklist.
