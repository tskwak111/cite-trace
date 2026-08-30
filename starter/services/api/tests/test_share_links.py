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

def test_share_lifecycle():
    res = client.post("/v1/shares", json={"target_id": "123", "permissions": ["read"]})
    assert res.status_code == 201
    share_data = res.json()
    token = share_data["token"]
    share_id = share_data["id"]

    res2 = client.get(f"/v1/shares/{token}")
    assert res2.status_code == 200
    assert res2.json()["target_id"] == "123"

    res3 = client.delete(f"/v1/shares/{share_id}")
    assert res3.status_code == 200
