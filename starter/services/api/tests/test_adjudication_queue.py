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

def test_get_adjudication_queue():
    client.post("/v1/feedback", json={
        "workspace_id": str(uuid4()),
        "evidence_link_id": str(uuid4()),
        "category": "source_evidence",
        "idempotency_key": "key1"
    })
    response = client.get("/v1/adjudication-queue")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["priority_score"] == 90.0
