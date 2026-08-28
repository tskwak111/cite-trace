import pytest

from citetrace_api.parsing.models import GrobidParseResult
from citetrace_api.parsing.service import ObjectStoreProtocol, ParsingService


class FakeObjectStore(ObjectStoreProtocol):
    def __init__(self):
        self.store = {}
        
    async def put(self, key: str, data: bytes) -> None:
        self.store[key] = data
        
    async def get(self, key: str) -> bytes:
        return self.store.get(key)
        
    async def exists(self, key: str) -> bool:
        return key in self.store

class FakeGrobidClient:
    async def process_fulltext(self, pdf_bytes: bytes, trace_id: str = "") -> GrobidParseResult:
        return GrobidParseResult(tei_xml=b"<tei>parsed</tei>", status="success", timings_ms={"grobid_ms": 100})

@pytest.mark.anyio
async def test_parse_source_asset_new():
    store = FakeObjectStore()
    client = FakeGrobidClient()
    service = ParsingService(client, store)
    
    record = await service.parse_source_asset("ws1", "asset1", b"pdf data")
    
    assert record.source_asset_id == "asset1"
    assert record.tei_xml_sha256 is not None
    key = f"workspaces/ws1/tei/{record.tei_xml_sha256}.xml"
    assert await store.exists(key)
    assert await store.get(key) == b"<tei>parsed</tei>"

@pytest.mark.anyio
async def test_parse_source_asset_existing():
    store = FakeObjectStore()
    client = FakeGrobidClient()
    service = ParsingService(client, store)
    
    # Pre-populate store to simulate existing parse
    record1 = await service.parse_source_asset("ws1", "asset1", b"pdf data")
    
    # Should not call client again (we could mock to ensure, but FakeGrobidClient would return same anyway)
    # The record should match
    record2 = await service.parse_source_asset("ws1", "asset1", b"pdf data")
    
    assert record1.tei_xml_sha256 == record2.tei_xml_sha256
    assert record1.id == record2.id
