from citetrace_api.retrieval.query_planner import EvidenceQueryPlanner, ExtractedClaim


def test_query_planner():
    planner = EvidenceQueryPlanner()
    claim = ExtractedClaim(text="test", qualifiers=[], citation_intents=[])
    plan = planner.plan_queries(claim)
    assert plan.lexical_queries == ("test",)
