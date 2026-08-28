from citetrace_api.evaluation.export import EvaluationCaseRecord, EvaluationExporter, ExportPolicy


def test_evaluation_export_format():
    policy = ExportPolicy(include_private_quotes=False, anonymize_users=True)
    exporter = EvaluationExporter(policy)
    
    mock_case = {
        "case_id": "case-123",
        "citing_claim": {"text": "A claim"},
        "cited_source": {"text": "Source text"},
        "citation_intents": ["background"],
        "evidence_relation": "supports",
        "transformations": ["none"],
        "confidence_vector": {"score": 0.9},
        "audit_status": "pass",
        "limitations": []
    }
    
    records = exporter.export([mock_case])
    assert len(records) == 1
    assert isinstance(records[0], EvaluationCaseRecord)
    assert records[0].case_id == "case-123"
