from uuid import uuid4

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


client = _make_auth_client()

def test_create_note():
    response = client.post("/v1/notes", json={
        "workspace_id": str(uuid4()),
        "actor_user_id": str(uuid4()),
        "target_type": "analysis",
        "target_id": str(uuid4()),
        "visibility": "private",
        "markdown": "<script>alert(1)</script>Safe Note",
        "idempotency_key": "key1"
    })
    assert response.status_code == 201
    data = response.json()
    assert "<script>" not in data["markdown"]
    assert "Safe Note" in data["markdown"]
