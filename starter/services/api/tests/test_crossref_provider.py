import json
from uuid import uuid4

import pytest
import respx

from citetrace_api.providers.crossref import CrossrefProvider
from citetrace_api.providers.http import ProviderHttpClient
from citetrace_api.providers.models import BibliographicQuery


@pytest.fixture
def crossref(mock_clock, mock_sleeper):
    client = ProviderHttpClient(clock=mock_clock, sleeper=mock_sleeper)
    return CrossrefProvider(http_client=client)


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
async def test_crossref_uses_exact_doi_before_title_search(crossref: CrossrefProvider) -> None:
    query = BibliographicQuery(
        reference_entry_id=uuid4(),
        title="Foundation Method",
        authors=("Jane Smith",),
        year=2024,
        venue=None,
        identifiers={"doi": "10.1000/foundation"},
        raw_reference="Smith ...",
    )

    with open("tests/fixtures/provider/crossref-title.json") as f:
        data = json.load(f)

    exact_data = {"status": "ok", "message": data["message"]["items"][0]}

    exact_doi_route = respx.get("https://api.crossref.org/works/10.1000/foundation").respond(
        json=exact_data
    )
    title_search_route = respx.get("https://api.crossref.org/works").respond(json=data)

    candidates = await crossref.search(query, trace_id="trace-1")
    assert candidates[0].identifiers["doi"] == "10.1000/foundation"
    assert exact_doi_route.called
    assert title_search_route.called is False
