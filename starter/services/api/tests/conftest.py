import sys
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = REPO_ROOT / "scripts"
for path in (REPO_ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from citetrace_api.main import app  # noqa: E402
from citetrace_api.security.auth import (  # noqa: E402
    WorkspacePrincipal,
    current_principal,
    issue_token,
)

AUTH_SECRET = "test-secret-do-not-use-in-prod-0123456789"


@pytest.fixture(autouse=True)
def _set_auth_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CITETRACE_AUTH_SECRET", AUTH_SECRET)


@pytest.fixture
def auth_client() -> Iterator[TestClient]:
    workspace = uuid4()
    token = issue_token(workspace, "admin", AUTH_SECRET, ttl_seconds=3600)

    def _override() -> WorkspacePrincipal:
        return WorkspacePrincipal(workspace_id=workspace, role="admin")

    app.dependency_overrides[current_principal] = _override
    with TestClient(app, raise_server_exceptions=True) as test_client:
        test_client.headers["Authorization"] = f"Bearer {token}"
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def client(auth_client: TestClient) -> TestClient:
    return auth_client
