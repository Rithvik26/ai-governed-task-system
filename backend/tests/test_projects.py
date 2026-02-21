"""
Tests for project endpoints.

Focus: the API contract and error shapes, not internal implementation details.
"""


def test_create_project_returns_201_with_body(client):
    resp = client.post("/projects/", json={"name": "Alpha"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Alpha"
    assert "id" in data
    assert "created_at" in data


def test_create_project_with_description(client):
    resp = client.post(
        "/projects/", json={"name": "Beta", "description": "A test project"}
    )
    assert resp.status_code == 201
    assert resp.get_json()["description"] == "A test project"


def test_create_project_missing_name_returns_400(client):
    resp = client.post("/projects/", json={"description": "no name here"})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "error" in body


def test_create_project_empty_name_returns_400(client):
    resp = client.post("/projects/", json={"name": ""})
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "VALIDATION_ERROR"


def test_list_projects_returns_all(client):
    client.post("/projects/", json={"name": "P1"})
    client.post("/projects/", json={"name": "P2"})
    resp = client.get("/projects/")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2


def test_list_projects_empty(client):
    resp = client.get("/projects/")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_get_project_returns_200(client):
    project_id = client.post("/projects/", json={"name": "Gamma"}).get_json()["id"]
    resp = client.get(f"/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Gamma"


def test_get_project_not_found_returns_404(client):
    resp = client.get("/projects/9999")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["code"] == "PROJECT_NOT_FOUND"
    assert "error" in body


def test_delete_project_returns_204(client):
    project_id = client.post("/projects/", json={"name": "ToDelete"}).get_json()["id"]
    resp = client.delete(f"/projects/{project_id}")
    assert resp.status_code == 204


def test_delete_project_cascades_tasks(client):
    """Deleting a project must remove its tasks (cascade)."""
    project_id = client.post("/projects/", json={"name": "WithTasks"}).get_json()["id"]
    client.post(f"/projects/{project_id}/tasks", json={"title": "Orphan"})
    client.delete(f"/projects/{project_id}")
    # Project is gone; its tasks should also be gone (cascade delete-orphan)
    assert client.get(f"/projects/{project_id}").status_code == 404


def test_delete_nonexistent_project_returns_404(client):
    resp = client.delete("/projects/9999")
    assert resp.status_code == 404


def test_create_project_no_body_returns_400(client):
    """Sending an empty body must still produce a structured 400."""
    resp = client.post("/projects/", content_type="application/json", data="")
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "VALIDATION_ERROR"


def test_error_response_always_has_error_and_code_keys(client):
    """Every error response must contain both 'error' (str) and 'code' (str)."""
    error_responses = [
        client.get("/projects/9999"),
        client.post("/projects/", json={}),
        client.delete("/projects/9999"),
    ]
    for resp in error_responses:
        body = resp.get_json()
        assert "error" in body, f"Missing 'error' key: {body}"
        assert "code" in body, f"Missing 'code' key: {body}"
        assert isinstance(body["error"], str)
        assert isinstance(body["code"], str)
