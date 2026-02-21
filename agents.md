# agents.md — AI governance for Task Tracker

This document records how AI was used during development of this codebase,
what risks that introduces, and the review checklist a human must complete
before accepting AI-generated code.

---

## How AI was used

AI (Claude) was used to generate the initial implementation of this project
from a structured specification. This includes:

- All backend Python files (`models.py`, `schemas.py`, `routes/`, `app.py`,
  `errors.py`, `config.py`, `database.py`)
- All test files in `backend/tests/`
- All frontend files (`App.jsx`, component files, `api/client.js`)
- This documentation (`README.md`, `claude.md`, `agents.md`)

AI was **not** used to:
- Define the architectural rules (those came from the specification)
- Run or validate the tests
- Make deployment or infrastructure decisions

---

## Risks AI introduces in this codebase

### 1. State machine drift (high risk)
The `NEXT_STATUSES` map in `frontend/src/components/TaskItem.jsx` is a
manual copy of `VALID_TRANSITIONS` in `backend/models.py`. AI may update one
without updating the other. The backend will still reject illegal transitions,
but the UI will show incorrect buttons.

**Mitigation:** Any change to `VALID_TRANSITIONS` must be accompanied by a
matching update to `TaskItem.jsx`. Add a comment in both files pointing to
the other.

### 2. Bypassing the state machine (critical risk)
AI may generate code that sets `task.status = TaskStatus.done` directly
instead of calling `task.transition_to(TaskStatus.done)`. This silently
bypasses all transition validation and is the most likely way to introduce
data corruption.

**Mitigation:** The human review checklist includes a grep for direct
`task.status =` assignments outside `transition_to()`.

### 3. Business logic in routes (medium risk)
AI tends to inline business logic in routes because it is faster to generate.
This violates the layer contract and makes the logic untestable in isolation.

**Mitigation:** Review every route function. Any logic that goes beyond
parsing + schema + model call + response is a violation.

### 4. Missing `@validates` on new schema fields (medium risk)
AI may add a new field to a schema without adding the corresponding
`@validates` decorator for enum membership or range checks. This accepts
garbage input.

**Mitigation:** Every new field with constrained values must have a
`@validates` test in the test suite (the test file structure makes this
auditable).

### 5. Error format violations (low risk)
AI may introduce a route that returns `{"message": "..."}` instead of
`{"error": "...", "code": "..."}`, which breaks any client expecting the
standard format.

**Mitigation:** The review checklist includes checking all new `jsonify()`
calls in routes.

### 6. Test completeness (medium risk)
AI may generate tests for the happy path only. Tests that verify rejection of
bad states are more important in this codebase than tests that verify success.

**Mitigation:** Every new endpoint must have at minimum: a missing-field test,
an invalid-enum test, and (for state-mutating endpoints) an invalid-transition
test.

### 7. Hallucinated API compatibility (low risk)
AI may generate code using a different version of a library's API
(e.g., SQLAlchemy 1.x `Query.get()` vs 2.x `db.session.get()`).

**Mitigation:** Pin dependency versions in `requirements.txt` and run the
test suite after any AI-generated change.

---

## Human review checklist

Complete every item before merging AI-generated code.

### Structure
- [ ] No business logic in routes (`routes/*.py`) — only HTTP parsing,
      schema calls, model calls, and response assembly.
- [ ] No `flask` imports in `models.py`.
- [ ] No database calls in `schemas.py`.
- [ ] All new exceptions are subclasses of `AppError` (in `errors.py`).

### State machine
- [ ] No direct `task.status = ...` assignments outside `Task.transition_to()`.
      Run: `grep -n "task\.status\s*=" backend/models.py backend/routes/*.py`
      — only the line inside `transition_to()` is acceptable.
- [ ] If `VALID_TRANSITIONS` changed, `TaskItem.jsx` `NEXT_STATUSES` was
      updated to match.

### Validation
- [ ] Every new input field with constrained values has a `@validates`
      decorator in the schema.
- [ ] Every new schema uses `Meta.unknown = EXCLUDE`.
- [ ] No route reads from `request.json` or `request.form` without going
      through a schema first.

### Responses
- [ ] All success responses use `jsonify(schema.dump(obj))`.
- [ ] No `jsonify(obj.__dict__)` or manual dict construction.
- [ ] All error responses are raised as `AppError` subclasses, not returned
      as ad-hoc dicts.

### Tests
- [ ] New endpoint has: happy-path test, missing-field test, invalid-enum
      test, not-found test.
- [ ] New state transition (if any) has: valid-path test, invalid-path test,
      backward-move test.
- [ ] `pytest` runs with exit code 0.

### Logging
- [ ] Validation errors are logged at WARNING before raising.
- [ ] No exception is silently caught without logging.

---

## Ongoing governance

AI assistance is appropriate for:
- Generating new routes that follow the established pattern.
- Generating schema fields and `@validates` validators.
- Writing test cases for new endpoints.
- Drafting documentation updates.

AI assistance requires extra scrutiny for:
- Any change to `models.py` (state machine, invariants).
- Any change to `errors.py` (error codes, handler registration).
- Any change to `config.py` or `database.py` (affects all tests).
- Anything that removes or weakens a `@validates` decorator.

Human sign-off is required for:
- Introducing a new dependency.
- Changing the error response format.
- Adding a new task status or modifying `VALID_TRANSITIONS`.
- Any schema migration that could corrupt existing data.
