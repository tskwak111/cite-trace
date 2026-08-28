from uuid import uuid4
from fastapi.testclient import TestClient
from citetrace_api.main import app

client = TestClient(app)

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
