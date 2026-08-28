from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from citetrace_api.documents.models import RegisterUpload
from citetrace_api.documents.registry import DocumentRegistry
from citetrace_api.documents.storage import FakeObjectStore

# Reusing the minimal valid PDF from test_pdf_validation
_MINIMAL_TEXT_PDF = b"""%PDF-1.4
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


@pytest.mark.anyio
async def test_put_if_absent_never_overwrites_different_bytes():
    store = FakeObjectStore()
    key = "test/key"
    res1 = await store.put_if_absent(key, b"data1", "application/pdf")
    assert res1.created is True

    res2 = await store.put_if_absent(key, b"data2", "application/pdf")
    assert res2.created is False

    read_data = await store.read(key)
    assert read_data == b"data1"


@pytest.mark.anyio
async def test_register_upload_stores_valid_pdf():
    store = FakeObjectStore()
    registry = DocumentRegistry(store)

    upload = RegisterUpload(
        workspace_id=uuid4(),
        original_filename="test.pdf",
        media_type="application/pdf",
        data=_MINIMAL_TEXT_PDF,
        retention_expires_at=datetime.now(UTC) + timedelta(days=30),
    )

    asset = await registry.register_upload(upload)

    assert asset.workspace_id == upload.workspace_id
    assert asset.byte_size == len(_MINIMAL_TEXT_PDF)

    # Verify it was stored
    stored_data = await store.read(asset.object_key)
    assert stored_data == _MINIMAL_TEXT_PDF


@pytest.mark.anyio
async def test_register_upload_rejects_invalid_pdf():
    store = FakeObjectStore()
    registry = DocumentRegistry(store)

    upload = RegisterUpload(
        workspace_id=uuid4(),
        original_filename="test.pdf",
        media_type="application/pdf",
        data=b"invalid pdf data",
        retention_expires_at=datetime.now(UTC) + timedelta(days=30),
    )

    with pytest.raises(ValueError, match="PDF validation failed"):
        await registry.register_upload(upload)


@pytest.mark.anyio
async def test_same_bytes_idempotent():
    store = FakeObjectStore()
    registry = DocumentRegistry(store)

    upload = RegisterUpload(
        workspace_id=uuid4(),
        original_filename="test.pdf",
        media_type="application/pdf",
        data=_MINIMAL_TEXT_PDF,
        retention_expires_at=datetime.now(UTC) + timedelta(days=30),
    )

    asset1 = await registry.register_upload(upload)
    asset2 = await registry.register_upload(upload)

    # In fake object store, the key will be the same and created=False internally
    assert asset1.sha256 == asset2.sha256
    assert asset1.object_key == asset2.object_key
