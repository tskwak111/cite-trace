import datetime
from dataclasses import dataclass


@dataclass
class GrobidParseResult:
    tei_xml: bytes
    status: str
    timings_ms: dict[str, int]


@dataclass
class ParsedDocumentRecord:
    id: str
    source_asset_id: str
    tei_xml_sha256: str
    created_at: datetime.datetime
