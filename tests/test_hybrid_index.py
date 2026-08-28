
from src.retrieval.index import HybridEvidenceIndex


def test_index():
    index = HybridEvidenceIndex()
    res = index.search("query")
    assert len(res) == 1
