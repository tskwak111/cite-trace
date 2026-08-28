from fastapi.testclient import TestClient
from citetrace_api.main import app

client = TestClient(app)

def test_export_analysis():
    response = client.post("/v1/analyses/123/export", json={"format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["provenance"] == "preserved"
