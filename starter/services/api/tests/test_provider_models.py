from citetrace_api.providers.models import ProviderCandidate


def test_candidate_normalizes_doi_and_preserves_raw_snapshot() -> None:
    candidate = ProviderCandidate.from_provider(
        provider="crossref",
        provider_record_id="10.1000/ABC",
        title="  A   Foundation Method ",
        authors=("Smith, Jane", "Lee, Min"),
        year=2024,
        venue=None,
        identifiers={"doi": "https://doi.org/10.1000/ABC"},
        raw_snapshot={"DOI": "10.1000/ABC"},
    )
    assert candidate.normalized_title == "a foundation method"
    assert candidate.identifiers["doi"] == "10.1000/abc"
    assert candidate.raw_snapshot["DOI"] == "10.1000/ABC"
