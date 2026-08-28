import pytest
from fastapi.testclient import TestClient
from citetrace_api.main import app
from uuid import uuid4

ANALYSIS_ID = uuid4()
WORKSPACE_ID = str(uuid4())

def auth_headers(workspace_id: str):
    return {"x-workspace-id": workspace_id}

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

def test_list_returns_only_publishable_evidence_links(client: TestClient) -> None:
    response = client.get(
        f"/v1/analyses/{ANALYSIS_ID}/evidence-links?status=verified&limit=20",
        headers=auth_headers(WORKSPACE_ID),
    )
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert all(item["status"] == "verified" for item in body["items"])
    assert all(item.get("audit_status") in {"passed", "passed_with_warnings"} for item in body["items"])
    assert all("object_key" not in item for item in body["items"])
