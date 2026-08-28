from citetrace_api.retrieval.reranker import EvidenceReranker


def test_reranker():
    reranker = EvidenceReranker()
    ranked = reranker.rank_candidates([], [1, 2])
    assert ranked == [1, 2]
