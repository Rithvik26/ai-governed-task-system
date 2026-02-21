"""
Tests for task endpoints.

The primary purpose of this suite is to prove that the system prevents bad states:
invalid field values are rejected, and illegal status transitions are blocked.
"""
import pytest


@pytest.fixture
def project(client):
    """A freshly created project for use in task tests."""
    return client.post("/projects/", json={"name": "Test Project"}).get_json()


# ---------------------------------------------------------------------------
# Task creation
# ---------------------------------------------------------------------------


def test_create_task_valid(client, project):
    resp = client.post(
        f"/projects/{project['id']}/tasks",
        json={"title": "My Task", "priority": "high"},
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["title"] == "My Task"
    assert data["status"] == "todo"   # default status
    assert data["priority"] == "high"
    assert data["project_id"] == project["id"]
    assert "id" in data


def test_create_task_default_priority_is_medium(client, project):
    resp = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Default Priority"}
    )
    assert resp.status_code == 201
    assert resp.get_json()["priority"] == "medium"


def test_create_task_missing_title_returns_400(client, project):
    """A missing required field must produce a 400 with VALIDATION_ERROR."""
    resp = client.post(
        f"/projects/{project['id']}/tasks", json={"priority": "low"}
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "error" in body


def test_create_task_invalid_priority_returns_400(client, project):
    """An unrecognised enum value must produce a 400 with VALIDATION_ERROR."""
    resp = client.post(
        f"/projects/{project['id']}/tasks",
        json={"title": "Bad Priority", "priority": "urgent"},
    )
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "VALIDATION_ERROR"


def test_create_task_in_nonexistent_project_returns_404(client):
    resp = client.post("/projects/9999/tasks", json={"title": "Ghost"})
    assert resp.status_code == 404
    assert resp.get_json()["code"] == "PROJECT_NOT_FOUND"


# ---------------------------------------------------------------------------
# Status transitions — valid paths
# ---------------------------------------------------------------------------


def test_valid_transition_todo_to_in_progress(client, project):
    task_id = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "T1"}
    ).get_json()["id"]

    resp = client.put(f"/tasks/{task_id}", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "in_progress"


def test_valid_transition_in_progress_to_done(client, project):
    task_id = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "T2"}
    ).get_json()["id"]

    client.put(f"/tasks/{task_id}", json={"status": "in_progress"})
    resp = client.put(f"/tasks/{task_id}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "done"


# ---------------------------------------------------------------------------
# Status transitions — invalid paths (the core invariant of the system)
# ---------------------------------------------------------------------------


def test_invalid_transition_todo_to_done_returns_400(client, project):
    """Skipping in_progress is forbidden."""
    task_id = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Skip"}
    ).get_json()["id"]

    resp = client.put(f"/tasks/{task_id}", json={"status": "done"})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code"] == "INVALID_STATUS_TRANSITION"
    assert "error" in body


def test_invalid_backward_transition_in_progress_to_todo(client, project):
    """Backward moves are forbidden."""
    task_id = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Backward"}
    ).get_json()["id"]

    client.put(f"/tasks/{task_id}", json={"status": "in_progress"})
    resp = client.put(f"/tasks/{task_id}", json={"status": "todo"})
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "INVALID_STATUS_TRANSITION"


def test_invalid_transition_done_to_any(client, project):
    """A completed task cannot be re-opened."""
    task_id = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Done"}
    ).get_json()["id"]

    client.put(f"/tasks/{task_id}", json={"status": "in_progress"})
    client.put(f"/tasks/{task_id}", json={"status": "done"})

    for attempt in ("todo", "in_progress"):
        resp = client.put(f"/tasks/{task_id}", json={"status": attempt})
        assert resp.status_code == 400, f"Expected 400 for done → {attempt}"
        assert resp.get_json()["code"] == "INVALID_STATUS_TRANSITION"


def test_invalid_status_value_returns_400(client, project):
    """A completely unknown status string must fail validation, not transition logic."""
    task_id = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Bad Status"}
    ).get_json()["id"]

    resp = client.put(f"/tasks/{task_id}", json={"status": "cancelled"})
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def test_filter_tasks_by_project(client, project):
    """Tasks from other projects must not appear in a project's task list."""
    other = client.post("/projects/", json={"name": "Other"}).get_json()

    client.post(f"/projects/{project['id']}/tasks", json={"title": "Task A"})
    client.post(f"/projects/{project['id']}/tasks", json={"title": "Task B"})
    client.post(f"/projects/{other['id']}/tasks", json={"title": "Task C"})

    resp = client.get(f"/projects/{project['id']}/tasks")
    tasks = resp.get_json()
    assert len(tasks) == 2
    assert all(t["project_id"] == project["id"] for t in tasks)


def test_filter_tasks_by_status(client, project):
    resp_a = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Task A"}
    )
    task_a_id = resp_a.get_json()["id"]
    client.post(f"/projects/{project['id']}/tasks", json={"title": "Task B"})

    client.put(f"/tasks/{task_a_id}", json={"status": "in_progress"})

    resp = client.get(f"/projects/{project['id']}/tasks?status=in_progress")
    tasks = resp.get_json()
    assert len(tasks) == 1
    assert tasks[0]["status"] == "in_progress"


def test_filter_tasks_by_invalid_status_returns_400(client, project):
    resp = client.get(f"/projects/{project['id']}/tasks?status=nonsense")
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Task retrieval
# ---------------------------------------------------------------------------


def test_get_task_not_found_returns_404(client):
    resp = client.get("/tasks/9999")
    assert resp.status_code == 404
    assert resp.get_json()["code"] == "TASK_NOT_FOUND"


def test_update_task_title_and_priority(client, project):
    task_id = client.post(
        f"/projects/{project['id']}/tasks",
        json={"title": "Original", "priority": "low"},
    ).get_json()["id"]

    resp = client.put(
        f"/tasks/{task_id}", json={"title": "Updated", "priority": "high"}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["title"] == "Updated"
    assert data["priority"] == "high"


def test_create_task_no_body_returns_400(client, project):
    """Sending an empty body must produce VALIDATION_ERROR, not a 500."""
    resp = client.post(
        f"/projects/{project['id']}/tasks",
        content_type="application/json",
        data="",
    )
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "VALIDATION_ERROR"


def test_transition_error_message_names_both_statuses(client, project):
    """The error message for a bad transition must name both the from and to status."""
    task_id = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Msg"}
    ).get_json()["id"]

    body = client.put(f"/tasks/{task_id}", json={"status": "done"}).get_json()
    assert "todo" in body["error"]
    assert "done" in body["error"]


def test_updated_at_changes_after_transition(client, project):
    """updated_at must be a timestamp >= original after a status change."""
    task = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Timestamps"}
    ).get_json()

    updated = client.put(
        f"/tasks/{task['id']}", json={"status": "in_progress"}
    ).get_json()
    assert updated["updated_at"] >= task["updated_at"]


def test_task_response_contains_all_required_fields(client, project):
    """Every task response must expose the complete schema surface."""
    task = client.post(
        f"/projects/{project['id']}/tasks",
        json={"title": "Shape", "priority": "high"},
    ).get_json()
    required = ("id", "project_id", "title", "description", "status",
                 "priority", "created_at", "updated_at")
    for field in required:
        assert field in task, f"Missing field '{field}' in task response"
