import json
from pathlib import Path
from uuid import uuid4

import pytest
import respx

from citetrace_api.providers.http import ProviderHttpClient
from citetrace_api.providers.models import BibliographicQuery
from citetrace_api.providers.semantic_scholar import SemanticScholarProvider


@pytest.fixture
def semantic_scholar(mock_clock, mock_sleeper):
    client = ProviderHttpClient(clock=mock_clock, sleeper=mock_sleeper)
    return SemanticScholarProvider(http_client=client)


@pytest.fixture
def mock_clock():
    return lambda: 0.0


@pytest.fixture
def mock_sleeper():
    async def sleeper(seconds):
        pass

    return sleeper


@pytest.mark.anyio
@respx.mock
async def test_semantic_scholar_uses_exact_doi_before_title_search(
    semantic_scholar: SemanticScholarProvider,
) -> None:
    query = BibliographicQuery(
        reference_entry_id=uuid4(),
        title="Foundation Method",
        authors=("Jane Smith",),
        year=2024,
        venue=None,
        identifiers={"doi": "10.1000/foundation"},
        raw_reference="Smith ...",
    )

    fixture_path = Path(__file__).parent / "fixtures" / "provider" / "semantic-scholar-paper.json"
    with open(fixture_path) as f:
        data = json.load(f)

    exact_doi_route = respx.get(
        "https://api.semanticscholar.org/graph/v1/paper/DOI:10.1000/foundation"
    ).respond(json=data)
    title_search_route = respx.get("https://api.semanticscholar.org/graph/v1/paper/search").respond(
        json={"data": [data]}
    )

    candidates = await semantic_scholar.search(query, trace_id="trace-1")
    assert candidates[0].identifiers["doi"] == "10.1000/foundation"
    assert exact_doi_route.called
    assert title_search_route.called is False
