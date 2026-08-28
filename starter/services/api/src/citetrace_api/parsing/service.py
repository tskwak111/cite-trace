import datetime
import hashlib
from typing import Protocol

from citetrace_api.parsing.grobid_client import GrobidClient
from citetrace_api.parsing.models import ParsedDocumentRecord


class ObjectStoreProtocol(Protocol):
    async def put(self, key: str, data: bytes) -> None: ...
        
    async def get(self, key: str) -> bytes: ...
        
    async def exists(self, key: str) -> bool: ...

class ParsingService:
    def __init__(self, grobid_client: GrobidClient, object_store: ObjectStoreProtocol):
        self.grobid_client = grobid_client
        self.object_store = object_store
        
    def _compute_fingerprint(self, pdf_bytes: bytes, parser_details: str) -> str:
        h = hashlib.sha256()
        h.update(pdf_bytes)
        h.update(parser_details.encode('utf-8'))
        return h.hexdigest()

    async def parse_source_asset(
        self, 
        workspace_id: str, 
        source_asset_id: str, 
        pdf_bytes: bytes
    ) -> ParsedDocumentRecord:
        parser_details = "grobid-client-v1"
        fingerprint = self._compute_fingerprint(pdf_bytes, parser_details)
        
        tei_key = f"workspaces/{workspace_id}/tei/{fingerprint}.xml"
        
        if not await self.object_store.exists(tei_key):
            result = await self.grobid_client.process_fulltext(pdf_bytes)
            await self.object_store.put(tei_key, result.tei_xml)
            
        return ParsedDocumentRecord(
            id=f"doc_{fingerprint[:16]}",
            source_asset_id=source_asset_id,
            tei_xml_sha256=fingerprint,
            created_at=datetime.datetime.now(datetime.UTC)
        )
