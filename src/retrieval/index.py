

from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    text: str
    score: float

class HybridEvidenceIndex:
    def search(self, query: str) -> list[RetrievedChunk]:
        return [RetrievedChunk(text="result", score=0.9)]
