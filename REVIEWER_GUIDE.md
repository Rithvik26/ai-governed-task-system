# Reviewer Guide

Thank you for reviewing this assessment.

This project is intentionally small. The goal is not feature richness but
demonstrating: prevention of invalid states, safe system evolution, and
controlled AI-assisted development.

---

## Where to look first (5-minute review)

**[backend/models.py](backend/models.py)**
`Task.transition_to()` is the single enforcement point for the task lifecycle.
`VALID_TRANSITIONS` is the explicit state machine table.
No other code may set `task.status` directly.

**[backend/schemas.py](backend/schemas.py)**
Every request body passes through a Marshmallow schema before touching the
database. Enum values are validated here, not in routes or models.

**[backend/tests/test_tasks.py](backend/tests/test_tasks.py)**
Tests deliberately attempt illegal transitions and invalid input. The purpose
is to prove that bad states cannot occur, not just that happy paths work.

**[claude.md](claude.md)**
Defines the rules an AI agent must follow when modifying this codebase:
mandatory patterns, forbidden patterns, and a step-by-step checklist for
adding a new feature safely.

**[agents.md](agents.md)**
Documents exactly how AI was used, what risks that introduces in this specific
codebase, and the human review checklist before accepting AI-generated code.

---

## What this demonstrates

The system is designed so that:

- Invalid task states cannot occur even if a new route is added by a future
  engineer who doesn't know the state machine exists — `transition_to()`
  enforces it regardless.
- Incorrect AI-generated changes are caught by the test suite immediately,
  not discovered in production.
- Future features follow a predictable, auditable extension pattern defined
  in `claude.md`.

---

## Suggested quick verification

**1. Run the tests — they all pass:**
```bash
cd backend
source .venv/bin/activate
pytest -v
```

**2. Break the enforcement, prove the tests catch it:**

In `backend/models.py`, comment out the guard in `transition_to()`:

```python
def transition_to(self, new_status: TaskStatus) -> None:
    # allowed = VALID_TRANSITIONS.get(self.status, frozenset())
    # if new_status not in allowed:
    #     raise StateTransitionError(self.status, new_status)
    self.status = new_status
    self.updated_at = _now()
```

Run `pytest` again — **8 tests fail immediately**, including:
- `test_invalid_transition_todo_to_done_returns_400`
- `test_invalid_backward_transition_in_progress_to_todo`
- `test_invalid_transition_done_to_any`
- `test_transition_error_message_names_both_statuses`

This shows correctness is enforced by design, not by convention or trust.

---

## Intentional omissions

The following were explicitly excluded to keep the system small and correct:

- Authentication / users
- Pagination
- Background workers
- Caching
- Docker
- Database migrations (SQLite only)

These are documented tradeoffs in [README.md](README.md), not oversights.
