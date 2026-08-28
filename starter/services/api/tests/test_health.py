from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "citetrace-api",
        "version": "0.1.0",
    }
