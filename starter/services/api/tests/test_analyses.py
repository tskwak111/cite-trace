from uuid import uuid4

from fastapi.testclient import TestClient


def _command() -> dict[str, object]:
    return {
        "workspace_id": str(uuid4()),
        "document_id": str(uuid4()),
        "mode": "understand",
        "scope": {"kind": "whole_document"},
        "audience": "beginner",
        "source_policy_profile": "lawful-open-or-user-upload",
    }


def test_create_get_and_cancel_analysis(client: TestClient) -> None:
    command = _command()
    create = client.post(
        "/v1/analyses",
        headers={"Idempotency-Key": "create-analysis-001"},
        json=command,
    )

    assert create.status_code == 202
    assert create.headers["Idempotent-Replay"] == "false"
    created = create.json()
    assert created["status"] == "created"
    assert created["progress"]["percent"] == 0

    get = client.get(f"/v1/analyses/{created['id']}")
    assert get.status_code == 200
    assert get.json()["id"] == created["id"]

    cancel = client.post(
        f"/v1/analyses/{created['id']}:cancel",
        headers={"Idempotency-Key": "cancel-analysis-001"},
    )
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"
    assert cancel.json()["completed_at"] is not None


def test_create_is_idempotent_for_same_body(client: TestClient) -> None:
    command = _command()
    headers = {"Idempotency-Key": "same-request-key"}

    first = client.post("/v1/analyses", headers=headers, json=command)
    second = client.post("/v1/analyses", headers=headers, json=command)

    assert first.status_code == 202
    assert second.status_code == 202
    assert second.headers["Idempotent-Replay"] == "true"
    assert first.json()["id"] == second.json()["id"]


def test_reusing_idempotency_key_with_different_body_conflicts(client: TestClient) -> None:
    first_command = _command()
    second_command = {**first_command, "mode": "review"}
    headers = {"Idempotency-Key": "conflicting-key"}

    first = client.post("/v1/analyses", headers=headers, json=first_command)
    second = client.post("/v1/analyses", headers=headers, json=second_command)

    assert first.status_code == 202
    assert second.status_code == 409
    assert second.json()["code"] == "idempotency_conflict"


def test_create_rejects_unknown_fields(client: TestClient) -> None:
    command = {**_command(), "unsafe_override": True}
    response = client.post(
        "/v1/analyses",
        headers={"Idempotency-Key": "unknown-field-key"},
        json=command,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "request_validation_failed"
