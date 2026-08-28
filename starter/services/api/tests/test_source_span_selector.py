from citetrace_api.retrieval.span_selector import ExactSpanSelector


def test_span_selector():
    selector = ExactSpanSelector()
    outcome = selector.select_span("hello world", "world", 6, 11)
    assert outcome.status == "success"
    assert len(outcome.spans) == 1
    assert outcome.spans[0].quote == "world"
