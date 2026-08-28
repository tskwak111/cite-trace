from uuid import uuid4

from citetrace_api.providers.models import BibliographicQuery, ProviderCandidate
from citetrace_api.resolution.features import compare_reference_to_candidate


def test_compare_reference_to_candidate_exact_doi():
    query = BibliographicQuery(reference_entry_id=uuid4(), title="Test", authors=("A",), year=2020, venue=None, identifiers={"doi": "10.1000/123"}, raw_reference="")
    cand = ProviderCandidate.from_provider(provider="x", provider_record_id="1", title="Test", authors=("A",), year=2020, venue=None, identifiers={"doi": "10.1000/123"}, raw_snapshot={})

    feat = compare_reference_to_candidate(query, cand)
    assert feat.identifier_score == 1.0
    assert "doi_conflict" not in feat.hard_conflicts

def test_compare_reference_to_candidate_doi_conflict():
    query = BibliographicQuery(reference_entry_id=uuid4(), title="Test", authors=("A",), year=2020, venue=None, identifiers={"doi": "10.1000/123"}, raw_reference="")
    cand = ProviderCandidate.from_provider(provider="x", provider_record_id="1", title="Test", authors=("A",), year=2020, venue=None, identifiers={"doi": "10.1000/456"}, raw_snapshot={})

    feat = compare_reference_to_candidate(query, cand)
    assert feat.identifier_score == 0.0
    assert "doi_conflict" in feat.hard_conflicts
