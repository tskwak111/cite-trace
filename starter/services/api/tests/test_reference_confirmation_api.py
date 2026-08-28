from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from citetrace_api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_confirm_resolution(client):
    ref_id = str(uuid4())
    response = client.post(
        f"/v1/references/{ref_id}:confirm-resolution",
        json={"candidate_id": "test_id", "reason": "manual"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "user_confirmed"


def test_get_candidates(client):
    ref_id = str(uuid4())
    response = client.get(f"/v1/references/{ref_id}/candidates")
    assert response.status_code == 200
    assert "candidates" in response.json()
