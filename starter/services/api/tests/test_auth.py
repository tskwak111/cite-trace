"""Contract test: multi-tenant bearer auth (ADR-0018).

The auth module issues and verifies HS256 JWTs. The
contract test signs a token with a known secret, verifies
that `current_principal` returns the right
WorkspacePrincipal, and asserts that expired or
malformed tokens raise 401.

A FastAPI integration test mounts a tiny app that
depends on `current_principal` and asserts the dep
behaves correctly when called via the test client. The
production router wiring is the v2.0 migration; this
test pins the auth surface.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from citetrace_api.security.auth import (
    WorkspacePrincipal,
    current_principal,
    issue_token,
    verify_bearer_token,
)

TEST_SECRET = "test-secret-do-not-use-in-prod-0123456789"


@pytest.fixture(autouse=True)
def _set_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CITETRACE_AUTH_SECRET", TEST_SECRET)


def test_round_trip_issue_and_verify() -> None:
    workspace = uuid4()
    token = issue_token(workspace, "annotator", TEST_SECRET, ttl_seconds=60)
    principal = verify_bearer_token(token, TEST_SECRET)
    assert isinstance(principal, WorkspacePrincipal)
    assert principal.workspace_id == workspace
    assert principal.role == "annotator"
    assert principal.has_role("annotator")
    assert not principal.has_role("adjudicator")
    assert not principal.has_role("admin")


def test_expired_token_is_rejected() -> None:
    workspace = uuid4()
    token = issue_token(workspace, "annotator", TEST_SECRET, ttl_seconds=-10)
    with pytest.raises(HTTPException) as exc_info:
        verify_bearer_token(token, TEST_SECRET)
    assert exc_info.value.status_code == 401
    assert "expired" in str(exc_info.value.detail).lower() or "invalid" in str(exc_info.value.detail).lower()


def test_malformed_token_is_rejected() -> None:
    with pytest.raises(HTTPException) as exc_info:
        verify_bearer_token("not.a.jwt", TEST_SECRET)
    assert exc_info.value.status_code == 401


def test_signature_mismatch_is_rejected() -> None:
    workspace = uuid4()
    token = issue_token(workspace, "annotator", TEST_SECRET, ttl_seconds=60)
    bad_signature_token = token[:-2] + "AA"
    with pytest.raises(HTTPException) as exc_info:
        verify_bearer_token(bad_signature_token, TEST_SECRET)
    assert exc_info.value.status_code == 401


def test_wrong_secret_is_rejected() -> None:
    workspace = uuid4()
    token = issue_token(workspace, "annotator", TEST_SECRET, ttl_seconds=60)
    with pytest.raises(HTTPException):
        verify_bearer_token(token, "different-secret")


def test_invalid_role_is_rejected() -> None:
    """A token whose `role` claim is not one of the known
    roles must be rejected at verify time so a forged
    payload cannot masquerade as a higher-privilege
    role."""
    workspace = uuid4()
    bad_token = issue_token(workspace, "superuser", TEST_SECRET, ttl_seconds=60)
    with pytest.raises(HTTPException):
        verify_bearer_token(bad_token, TEST_SECRET)


def test_current_principal_dependency_via_test_client() -> None:
    """The FastAPI dep reads the Authorization header and
    returns a WorkspacePrincipal. The test client uses
    FastAPI's dependency_overrides to wire a known
    secret into the dep so the test is offline-clean."""
    app = FastAPI()

    @app.get("/who")
    def who(principal: WorkspacePrincipal = Depends(current_principal)) -> dict:
        return {"workspace_id": str(principal.workspace_id), "role": principal.role}

    workspace = uuid4()
    token = issue_token(workspace, "adjudicator", TEST_SECRET, ttl_seconds=60)

    with TestClient(app) as client:
        response = client.get("/who", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        body = response.json()
        assert body["workspace_id"] == str(workspace)
        assert body["role"] == "adjudicator"

        missing = client.get("/who")
        assert missing.status_code == 401
        assert missing.headers.get("WWW-Authenticate") == "Bearer"

        bad = client.get("/who", headers={"Authorization": "Bearer not.a.jwt"})
        assert bad.status_code == 401


def test_missing_secret_raises_500(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CITETRACE_AUTH_SECRET", raising=False)
    app = FastAPI()

    @app.get("/who")
    def who(principal: WorkspacePrincipal = Depends(current_principal)) -> dict:
        return {"workspace_id": str(principal.workspace_id)}

    with TestClient(app) as client:
        response = client.get("/who", headers={"Authorization": "Bearer abc.def.ghi"})
        assert response.status_code == 500
