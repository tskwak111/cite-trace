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


ANALYSIS_ID = uuid4()
WORKSPACE_ID = str(uuid4())


def auth_headers(workspace_id: str):
    return {"x-workspace-id": workspace_id}


@pytest.fixture
def client():
    with _make_auth_client() as client:
        yield client

def test_reference_map_returns_expected_fields(client: TestClient) -> None:
    response = client.get(
        f"/v1/analyses/{ANALYSIS_ID}/reference-map",
        headers=auth_headers(WORKSPACE_ID),
    )
    assert response.status_code == 200
    body = response.json()
    assert "total_count" in body
    assert "in_scope_count" in body
