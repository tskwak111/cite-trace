from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import citetrace_api.main
from citetrace_api.security.auth import WorkspacePrincipal, issue_token

_AUTH_SECRET = "test-secret-do-not-use-in-prod-0123456789"
_citetrace_api_main_app = citetrace_api.main.app


def _make_auth_client():
    import uuid

    workspace = uuid.uuid4()
    token = issue_token(workspace, "admin", _AUTH_SECRET, ttl_seconds=3600)
    principal = WorkspacePrincipal(workspace_id=workspace, role="admin")
    from citetrace_api.security.auth import current_principal

    _citetrace_api_main_app.dependency_overrides[current_principal] = lambda: principal
    client = TestClient(_citetrace_api_main_app)
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def client():
    return _make_auth_client()


def test_confirm_resolution(client):
    ref_id = str(uuid4())
    response = client.post(
        f"/v1/references/{ref_id}:confirm-resolution",
        json={"candidate_id": "test_id", "reason": "manual"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "user_confirmed"


def test_get_candidates(client):
    ref_id = str(uuid4())
    response = client.get(f"/v1/references/{ref_id}/candidates")
    assert response.status_code == 200
    assert "candidates" in response.json()
