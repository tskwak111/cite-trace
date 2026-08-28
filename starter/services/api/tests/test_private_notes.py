from uuid import uuid4
from fastapi.testclient import TestClient
from citetrace_api.main import app

client = TestClient(app)

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
