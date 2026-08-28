import httpx
import pytest
import respx

from citetrace_api.config import get_settings
from citetrace_api.parsing.grobid_client import GrobidClient, GrobidClientError


@pytest.fixture
def grobid_url():
    return f"{get_settings().grobid_url}/api/processFulltextDocument"

@pytest.mark.anyio
@respx.mock
async def test_process_fulltext_success(grobid_url):
    route = respx.post(grobid_url).respond(200, content=b"<tei>success</tei>")
    client = GrobidClient()
    result = await client.process_fulltext(b"fake pdf")
    
    assert result.tei_xml == b"<tei>success</tei>"
    assert result.status == "success"
    assert "grobid_ms" in result.timings_ms
    
    request = route.calls.last.request
    # content is a multipart form, let's just check the method and url
    assert request.method == "POST"
    assert request.url == grobid_url

@pytest.mark.anyio
@respx.mock
async def test_process_fulltext_retry_503(grobid_url):
    route = respx.post(grobid_url)
    route.side_effect = [
        httpx.Response(503, headers={"Retry-After": "0"}),
        httpx.Response(503, headers={"Retry-After": "0"}),
        httpx.Response(200, content=b"<tei>success</tei>")
    ]
    
    client = GrobidClient()
    result = await client.process_fulltext(b"fake pdf")
    assert result.tei_xml == b"<tei>success</tei>"
    assert route.call_count == 3

@pytest.mark.anyio
@respx.mock
async def test_process_fulltext_400_no_retry(grobid_url):
    route = respx.post(grobid_url).respond(400, text="Bad Request")
    
    client = GrobidClient()
    with pytest.raises(GrobidClientError, match="Bad request"):
        await client.process_fulltext(b"fake pdf")
    
    assert route.call_count == 1

@pytest.mark.anyio
@respx.mock
async def test_process_fulltext_max_response_bytes(grobid_url, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "grobid_max_response_bytes", 10)
    
    respx.post(grobid_url).respond(200, content=b"12345678901") # 11 bytes
    client = GrobidClient()
    client.settings = settings
    
    with pytest.raises(GrobidClientError, match="Response exceeds maximum allowed bytes"):
        await client.process_fulltext(b"fake pdf")
