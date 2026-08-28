from uuid import uuid4
from fastapi.testclient import TestClient
from citetrace_api.main import app

client = TestClient(app)

def test_submit_feedback():
    response = client.post("/v1/feedback", json={
        "workspace_id": str(uuid4()),
        "evidence_link_id": str(uuid4()),
        "category": "source_evidence",
        "idempotency_key": "test_key"
    })
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["category"] == "source_evidence"
