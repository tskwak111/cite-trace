from citetrace_api.providers.models import ProviderCandidate
from citetrace_api.resolution.decision import decide_resolution
from citetrace_api.resolution.features import ResolutionFeatures


def test_decide_resolution_resolved():
    cand = ProviderCandidate.from_provider(provider="x", provider_record_id="1", title="Test", authors=(), year=None, venue=None, identifiers={}, raw_snapshot={})
    feat = ResolutionFeatures(0,0,0,0,0,0,0,())
    scored = [(cand, 0.95, feat)]
    decision = decide_resolution(scored)
    assert decision.status == "resolved"
    assert decision.selected_candidate_id == "x:1"

def test_decide_resolution_ambiguous():
    cand1 = ProviderCandidate.from_provider(provider="x", provider_record_id="1", title="Test1", authors=(), year=None, venue=None, identifiers={}, raw_snapshot={})
    cand2 = ProviderCandidate.from_provider(provider="x", provider_record_id="2", title="Test2", authors=(), year=None, venue=None, identifiers={}, raw_snapshot={})
    feat = ResolutionFeatures(0,0,0,0,0,0,0,())
    scored = [(cand1, 0.85, feat), (cand2, 0.84, feat)]
    decision = decide_resolution(scored)
    assert decision.status == "ambiguous"
