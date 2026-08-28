import json
from uuid import uuid4

import pytest
import respx

from citetrace_api.providers.http import ProviderHttpClient
from citetrace_api.providers.models import BibliographicQuery
from citetrace_api.providers.openalex import OpenAlexProvider


@pytest.fixture
def openalex(mock_clock, mock_sleeper):
    client = ProviderHttpClient(clock=mock_clock, sleeper=mock_sleeper)
    return OpenAlexProvider(http_client=client)


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
async def test_openalex_uses_exact_doi_before_title_search(openalex: OpenAlexProvider) -> None:
    query = BibliographicQuery(
        reference_entry_id=uuid4(),
        title="Foundation Method",
        authors=("Jane Smith",),
        year=2024,
        venue=None,
        identifiers={"doi": "10.1000/foundation"},
        raw_reference="Smith ...",
    )

    with open("tests/fixtures/provider/openalex-work.json") as f:
        data = json.load(f)

    exact_doi_route = respx.get("https://api.openalex.org/works/doi:10.1000/foundation").respond(
        json=data
    )
    title_search_route = respx.get("https://api.openalex.org/works").respond(
        json={"results": [data]}
    )

    candidates = await openalex.search(query, trace_id="trace-1")
    assert candidates[0].identifiers["doi"] == "10.1000/foundation"
    assert exact_doi_route.called
    assert title_search_route.called is False
