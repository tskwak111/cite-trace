from uuid import uuid4

import pytest

from citetrace_api.providers.models import BibliographicQuery, ProviderCandidate
from citetrace_api.providers.protocols import ScholarlyMetadataProvider
from citetrace_api.resolution.service import ReferenceResolutionService


class MockProvider(ScholarlyMetadataProvider):
    def __init__(self, name: str, candidates: list[ProviderCandidate]):
        self._name = name
        self.candidates = candidates

    @property
    def name(self) -> str:
        return self._name

    async def search(self, query: BibliographicQuery, trace_id: str) -> list[ProviderCandidate]:
        return self.candidates

@pytest.mark.anyio
async def test_resolve_service():
    cand = ProviderCandidate.from_provider(provider="x", provider_record_id="1", title="Exact Match", authors=("Smith",), year=2020, venue=None, identifiers={"doi": "10.1000/123"}, raw_snapshot={})
    svc = ReferenceResolutionService([MockProvider("x", [cand])])

    query = BibliographicQuery(reference_entry_id=uuid4(), title="Exact Match", authors=("Smith",), year=2020, venue=None, identifiers={"doi": "10.1000/123"}, raw_reference="")

    decision, cands = await svc.resolve(query)
    assert decision.status == "resolved"
    assert len(cands) == 1
