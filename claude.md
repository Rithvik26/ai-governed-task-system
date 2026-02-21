# claude.md — AI guidance for Task Tracker

This file tells an AI coding assistant how to work safely in this codebase.
Read it completely before making any change.

---

## What each layer owns

### `routes/projects.py`, `routes/tasks.py`
- Parse `request.get_json(silent=True)` — never access request data elsewhere.
- Pass raw dict to the relevant schema's `.load()`.
- Call model methods or `db.session` operations.
- Return `jsonify(schema.dump(obj)), status_code`.
- **Own nothing else.** No conditionals about domain state. No string comparisons against enum values.

### `schemas.py`
- Define the input and output contract for every endpoint.
- Use `@validates` for enum membership checks.
- Use `Meta.unknown = EXCLUDE` on every load schema.
- Import from `models.py` only for enum classes (`TaskStatus`, `TaskPriority`).
- **Never** import from `routes/` or call `db`.

### `models.py`
- Define `Project` and `Task` as SQLAlchemy models.
- `Task.transition_to(new_status: TaskStatus)` is the **only** way to change `task.status`.
- `VALID_TRANSITIONS` is the single definition of the state machine.
- Raise `StateTransitionError` (from `errors.py`) for illegal transitions.
- **Never** import from `routes/` or `schemas.py`.

### `errors.py`
- Define `AppError`, `NotFoundError`, `ValidationError`, `StateTransitionError`.
- Register Flask error handlers via `register_error_handlers(app)`.
- **Never** import from `models.py`, `schemas.py`, or `routes/`.

### `database.py`
- Contains only: `db = SQLAlchemy()`.
- Nothing else belongs here.

---

## Mandatory patterns

### Enum comparisons
```python
# CORRECT
if task.status == TaskStatus.done:
    ...

# FORBIDDEN
if task.status == "done":   # raw string comparison
    ...
```

### Status transitions
```python
# CORRECT — always use transition_to()
task.transition_to(TaskStatus.in_progress)

# FORBIDDEN — direct assignment bypasses the state machine
task.status = TaskStatus.in_progress
```

### Input validation
```python
# CORRECT — schema validates before touching the DB
data = task_create_schema.load(request.get_json(silent=True) or {})

# FORBIDDEN — using request data without schema validation
task = Task(title=request.json["title"])
```

### Response serialisation
```python
# CORRECT — always serialise through a schema
return jsonify(task_response_schema.dump(task)), 200

# FORBIDDEN — returning a raw dict
return jsonify({"id": task.id, "title": task.title}), 200
```

### Error responses
```python
# CORRECT — raise typed exceptions; the handler formats them
raise NotFoundError("Task 42 not found", code="TASK_NOT_FOUND")

# FORBIDDEN — ad-hoc error dicts bypass the standard format
return jsonify({"message": "not found"}), 404
```

---

## Forbidden patterns

| Pattern | Why it is forbidden |
|---|---|
| Business logic in routes | Routes become untestable; invariants scatter |
| `task.status = ...` (direct assign) | Bypasses `VALID_TRANSITIONS` |
| Raw string enum comparisons | Breaks silently when an enum value is renamed |
| Returning `model.__dict__` | Leaks SQLAlchemy internals; breaks on lazy loads |
| Catching all exceptions in routes | Hides bugs; the error handler already catches `AppError` |
| Importing Flask in `models.py` | Couples domain logic to the web framework |
| Adding fields to a schema without a `@validates` | Accepts garbage input |

---

## Checklist: adding a new feature

Work through these steps in order. Do not skip ahead.

1. [ ] Identify which layer(s) need to change.
2. [ ] If a new domain rule exists, add a method to the model. Write a test
       for it before touching the route.
3. [ ] If a new field is added to a model, add a column with a `nullable`
       default so existing rows are not broken.
4. [ ] Update `TaskCreateSchema` or `TaskUpdateSchema` with the new field.
       Add `@validates` if the field has constrained values.
5. [ ] Update `TaskResponseSchema` (or project equivalent) if the field
       should appear in responses.
6. [ ] Add or update the route — HTTP plumbing only.
7. [ ] Add tests: happy path, missing field, invalid value, edge cases.
8. [ ] Run `pytest` from `backend/`. All tests must pass.
9. [ ] Verify the error format for new failure modes matches
       `{"error": "...", "code": "..."}`.
10. [ ] Update this file if a new pattern or layer rule was introduced.

---

## Adding a new status

Example: adding `archived` after `done`.

1. Add `archived = "archived"` to `TaskStatus` enum in `models.py`.
2. Add `TaskStatus.done: frozenset({TaskStatus.archived})` to `VALID_TRANSITIONS`.
3. Add `archived` to `_VALID_STATUSES` in `schemas.py` — this is derived
   automatically from `[s.value for s in TaskStatus]`, so no change needed there.
4. Add tests: `done → archived` passes; `in_progress → archived` fails.
5. The frontend `NEXT_STATUSES` map in `TaskItem.jsx` must be updated to
   match — this is a **manual sync** and a common source of bugs.

---

## Marshmallow version note

This project uses **marshmallow 4.x**. In marshmallow 4, `@validates`
decorated methods are called with an additional `data_key` keyword argument.
All validator methods **must** accept `**kwargs`:

```python
# CORRECT for marshmallow 4
@validates("priority")
def validate_priority(self, value, **kwargs):
    ...

# BROKEN — marshmallow 4 will raise TypeError at runtime
@validates("priority")
def validate_priority(self, value):
    ...
```

This is a silent runtime failure, not a startup error. The test suite
catches it immediately — run `pytest` after every schema change.

---

## What AI must not do

- Do not add authentication, pagination, background workers, or caching
  without an explicit engineering decision recorded in README.md.
- Do not rename enum values without a database migration plan.
- Do not add a new endpoint without a corresponding schema and test.
- Do not generate code that imports `flask` inside `models.py`.
- Do not use `db.session.query(Model)` — prefer `Model.query` or
  `db.session.get(Model, pk)` for consistency with the existing code.
- Do not commit to `main` without running the test suite.
