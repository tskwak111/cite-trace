from citetrace_api.verification.intents import CitationIntent


def test_intent():
    assert CitationIntent.background.value == "background"
