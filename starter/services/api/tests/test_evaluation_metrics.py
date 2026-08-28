from citetrace_api.evaluation.metrics import (
    citation_anchor_precision_recall,
    evidence_retrieval_recall_at_k,
    fabricated_quote_count,
    inaccessible_abstention_accuracy,
    reference_resolution_top1,
    relation_macro_f1,
    transformation_set_f1,
    unsupported_statement_rate,
)


def test_metrics() -> None:
    assert citation_anchor_precision_recall() == (1.0, 1.0)
    assert reference_resolution_top1() == 1.0
    assert evidence_retrieval_recall_at_k(5) == 1.0
    assert relation_macro_f1() == 1.0
    assert transformation_set_f1() == 1.0
    assert fabricated_quote_count() == 0
    assert unsupported_statement_rate() == 0.0
    assert inaccessible_abstention_accuracy() == 1.0
