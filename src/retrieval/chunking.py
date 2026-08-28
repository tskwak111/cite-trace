
from enum import Enum

from pydantic import BaseModel


class EvidenceType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"

class SourceChunkDraft(BaseModel):
    text: str

class SourceChunker:
    def chunk(self, text: str) -> list[SourceChunkDraft]:
        return [SourceChunkDraft(text=text)]
