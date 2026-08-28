from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from citetrace_api.main import app

WORKSPACE_ID = UUID("11111111-1111-1111-1111-111111111111")

# --- Minimal born-digital PDF bytes
MINIMAL_TEXT_PDF = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 64 >>
stream
BT /F1 12 Tf 72 720 Td (Hello World This is some text for length) Tj ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f \r
0000000009 00000 n \r
0000000058 00000 n \r
0000000115 00000 n \r
0000000266 00000 n \r
0000000380 00000 n \r
trailer
<< /Size 6 /Root 1 0 R >>
startxref
451
%%EOF
"""




@pytest.fixture
def client() -> Generator[TestClient]:
    with TestClient(app) as client:
        yield client


@pytest.fixture
def pdf_bytes() -> bytes:
    return MINIMAL_TEXT_PDF


def test_upload_returns_201_and_source_asset(client: TestClient, pdf_bytes: bytes) -> None:
    response = client.post(
        "/v1/documents",
        headers={"Idempotency-Key": "upload-asset-001", "X-Workspace-Id": str(WORKSPACE_ID)},
        files={"file": ("paper.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["access_level"] == "user_private_full_text"
    assert body["security_scan_status"] == "clean"
    assert "sha256" in body
    assert body["workspace_id"] == str(WORKSPACE_ID)


def test_upload_rejects_non_pdf_content(client: TestClient) -> None:
    response = client.post(
        "/v1/documents",
        headers={"Idempotency-Key": "upload-asset-002", "X-Workspace-Id": str(WORKSPACE_ID)},
        files={"file": ("paper.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code in (400, 415, 422)


def test_upload_rejects_invalid_pdf_magic(client: TestClient) -> None:
    response = client.post(
        "/v1/documents",
        headers={"Idempotency-Key": "upload-asset-003", "X-Workspace-Id": str(WORKSPACE_ID)},
        files={"file": ("paper.pdf", b"not a pdf at all", "application/pdf")},
    )
    assert response.status_code == 422
    body = response.json()
    assert body.get("code") == "pdf_validation_failed"


def test_duplicate_upload_returns_200_with_same_id(client: TestClient, pdf_bytes: bytes) -> None:
    """Idempotent re-upload: same workspace+idempotency key returns existing resource."""
    r1 = client.post(
        "/v1/documents",
        headers={"Idempotency-Key": "upload-idem-001", "X-Workspace-Id": str(WORKSPACE_ID)},
        files={"file": ("paper.pdf", pdf_bytes, "application/pdf")},
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/v1/documents",
        headers={"Idempotency-Key": "upload-idem-001", "X-Workspace-Id": str(WORKSPACE_ID)},
        files={"file": ("paper.pdf", pdf_bytes, "application/pdf")},
    )
    # Second upload with same key: either 200 or 201 with same ID
    assert r2.status_code in (200, 201)
    assert r2.json()["id"] == r1.json()["id"]
