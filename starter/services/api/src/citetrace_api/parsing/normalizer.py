import hashlib
import unicodedata
from dataclasses import dataclass

from citetrace_api.parsing.tei_reader import TeiCitationCluster


@dataclass
class OffsetMapping:
    normalized_start: int
    normalized_end: int
    tei_node_id: str
    page: str | None
    bounding_boxes: str | None

@dataclass
class NormalizedDocument:
    normalized_text: str
    text_sha256: str
    offset_mappings: list[OffsetMapping]

class DocumentNormalizer:
    def normalize_text(self, text: str) -> str:
        # Unicode NFC, collapse layout-only whitespace
        text = unicodedata.normalize('NFC', text)
        return " ".join(text.split())

    def process(self, raw_text: str, clusters: list[TeiCitationCluster]) -> NormalizedDocument:
        normalized_text = self.normalize_text(raw_text)
        
        sha256 = hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()
        
        mappings = []
        for cluster in clusters:
            anchor = self.normalize_text(cluster.anchor_text)
            start = normalized_text.find(anchor)
            if start != -1:
                end = start + len(anchor)
                
                page = None
                if cluster.coordinates:
                    page = cluster.coordinates.split(',')[0]
                    
                mappings.append(OffsetMapping(
                    normalized_start=start,
                    normalized_end=end,
                    tei_node_id=cluster.context_node_xml_id or "",
                    page=page,
                    bounding_boxes=cluster.coordinates
                ))
                
        return NormalizedDocument(
            normalized_text=normalized_text,
            text_sha256=sha256,
            offset_mappings=mappings
        )
