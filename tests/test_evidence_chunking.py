
from src.retrieval.chunking import SourceChunker


def test_chunking():
    chunker = SourceChunker()
    chunks = chunker.chunk("text")
    assert len(chunks) == 1
