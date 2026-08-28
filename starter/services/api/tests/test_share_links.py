from fastapi.testclient import TestClient
from citetrace_api.main import app

client = TestClient(app)

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
