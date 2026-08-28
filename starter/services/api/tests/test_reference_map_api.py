from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from citetrace_api.main import app

ANALYSIS_ID = uuid4()
WORKSPACE_ID = str(uuid4())

def auth_headers(workspace_id: str):
    return {"x-workspace-id": workspace_id}

@pytest.fixture
def client():
    with TestClient(app) as client:
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
