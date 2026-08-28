from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from citetrace_api.documents.storage import FakeObjectStore, source_object_key
from citetrace_api.main import app
from citetrace_api.orchestration.handlers import DocumentSourceRegisteredHandler
from citetrace_api.orchestration.outbox import InMemoryOutbox
from citetrace_api.parsing.models import ParsedDocumentRecord


class MockParsedDocsRepo:
    async def save_parsed_document(self, doc_data):
        pass

    async def save_parsed_nodes(self, nodes):
        pass

    async def save_reference_entries(self, refs):
        pass

    async def save_citation_clusters(self, clusters):
        pass

    async def save_citation_anchors(self, anchors):
        pass


@pytest.fixture
def object_store():
    return FakeObjectStore()


@pytest.fixture
def outbox():
    return InMemoryOutbox()


@pytest.fixture
def parsed_docs_repo():
    return MockParsedDocsRepo()


def get_good_tei() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <body>
        <div><head>Intro</head>This is a long meaningful text over 100 characters so that it doesn't fail the meaningful text check. We are adding more text to ensure it passes the check. This is definitely more than 100 characters now, easily passing the test for meaningful text length. <ref type="bibr" target="#b0" coords="1,1,1,1,1">[1]</ref></div>
    </body>
    <back>
        <listBibl>
            <biblStruct xml:id="b0" coords="1,1,1,1,1">
                <title level="a">Title</title>
            </biblStruct>
        </listBibl>
    </back>
</TEI>"""


def get_bad_tei() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <body><div>Too short</div></body>
    <back><listBibl></listBibl></back>
</TEI>"""


class StubParsingService:
    def __init__(self, object_store, tei_bytes):
        self.object_store = object_store
        self.tei_bytes = tei_bytes
        self.should_fail = False

    async def parse_source_asset(self, workspace_id, source_asset_id, pdf_bytes):
        if self.should_fail:
            raise ValueError("Boom")
        fingerprint = "fake_fingerprint"
        tei_key = f"workspaces/{workspace_id}/tei/{fingerprint}.xml"
        await self.object_store.put_if_absent(tei_key, self.tei_bytes, "application/xml")
        return ParsedDocumentRecord(
            id="doc_123",
            source_asset_id=source_asset_id,
            tei_xml_sha256=fingerprint,
            created_at=datetime.now(UTC),
        )


@pytest.mark.anyio
async def test_registered_document_reaches_parsed_state(object_store, outbox, parsed_docs_repo):
    workspace_id = str(uuid4())
    source_asset_id = str(uuid4())
    sha256 = "123456"

    await object_store.put_if_absent(
        source_object_key(workspace_id, sha256), b"pdf_data", "application/pdf"
    )

    parsing_service = StubParsingService(object_store, get_good_tei())
    handler = DocumentSourceRegisteredHandler(
        object_store, parsing_service, parsed_docs_repo, outbox
    )

    event = {
        "payload": {
            "source_asset_id": source_asset_id,
            "workspace_id": workspace_id,
            "sha256": sha256,
        }
    }

    await handler(event)
    events = outbox.events_for_aggregate(UUID(source_asset_id))
    assert len(events) == 1
    assert events[0]["event_type"] == "document.parsed"


@pytest.mark.anyio
async def test_event_redelivery_is_idempotent(object_store, outbox, parsed_docs_repo):
    workspace_id = str(uuid4())
    source_asset_id = str(uuid4())
    sha256 = "123456"

    await object_store.put_if_absent(
        source_object_key(workspace_id, sha256), b"pdf_data", "application/pdf"
    )
    parsing_service = StubParsingService(object_store, get_good_tei())
    handler = DocumentSourceRegisteredHandler(
        object_store, parsing_service, parsed_docs_repo, outbox
    )

    event = {
        "payload": {
            "source_asset_id": source_asset_id,
            "workspace_id": workspace_id,
            "sha256": sha256,
        }
    }

    await handler(event)
    await handler(event)
    assert len(outbox.events_for_aggregate(UUID(source_asset_id))) == 2


@pytest.mark.anyio
async def test_grade_d_produces_limited_status(object_store, outbox, parsed_docs_repo):
    workspace_id = str(uuid4())
    source_asset_id = str(uuid4())
    sha256 = "123456"

    await object_store.put_if_absent(
        source_object_key(workspace_id, sha256), b"pdf_data", "application/pdf"
    )
    parsing_service = StubParsingService(object_store, get_bad_tei())
    handler = DocumentSourceRegisteredHandler(
        object_store, parsing_service, parsed_docs_repo, outbox
    )

    event = {
        "payload": {
            "source_asset_id": source_asset_id,
            "workspace_id": workspace_id,
            "sha256": sha256,
        }
    }
    await handler(event)
    events = outbox.events_for_aggregate(UUID(source_asset_id))
    assert events[0]["event_type"] == "document.parsing.limited"


@pytest.mark.anyio
async def test_parsing_failure_produces_failed_status(object_store, outbox, parsed_docs_repo):
    workspace_id = str(uuid4())
    source_asset_id = str(uuid4())
    sha256 = "123456"

    await object_store.put_if_absent(
        source_object_key(workspace_id, sha256), b"pdf_data", "application/pdf"
    )
    parsing_service = StubParsingService(object_store, get_good_tei())
    parsing_service.should_fail = True
    handler = DocumentSourceRegisteredHandler(
        object_store, parsing_service, parsed_docs_repo, outbox
    )

    event = {
        "payload": {
            "source_asset_id": source_asset_id,
            "workspace_id": workspace_id,
            "sha256": sha256,
        }
    }
    await handler(event)
    events = outbox.events_for_aggregate(UUID(source_asset_id))
    assert events[0]["event_type"] == "document.parsing.failed"


def test_get_document_endpoint():
    with TestClient(app) as client:
        ws_id = uuid4()
        doc_id = uuid4()

        # Inject fake events into app outbox
        app.state.in_memory_outbox.add_event(
            "document.source.registered",
            doc_id,
            ws_id,
            {"source_asset_id": str(doc_id), "workspace_id": str(ws_id), "sha256": "x"},
        )

        app.state.in_memory_outbox.add_event(
            "document.parsed", doc_id, ws_id, {"parsed_document_id": "p1", "quality_grade": "a"}
        )

        res = client.get(f"/v1/documents/{doc_id!s}")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "parsed"
        assert data["latest_quality_grade"] == "a"
