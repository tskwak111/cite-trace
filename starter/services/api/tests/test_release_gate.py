from citetrace_api.evaluation.release_gate import EvaluationReport, evaluate_release


def test_evaluate_release() -> None:
    report = evaluate_release()
    assert isinstance(report, EvaluationReport)
    assert report.passed is True
