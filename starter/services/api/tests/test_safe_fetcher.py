import pytest
import respx

from citetrace_api.acquisition.fetcher import SafeRemoteFetcher
from citetrace_api.acquisition.url_guard import (
    UrlDenialCode,
    UrlGuard,
    UrlValidationError,
)


@pytest.fixture
def guard():
    return UrlGuard(require_https=False)

@pytest.fixture
def mock_getaddrinfo(monkeypatch):
    # Mock DNS to avoid actual network calls
    async def fake_getaddrinfo(self, host, port, *args, **kwargs):
        if host == "example.com":
            return [(2, 1, 6, '', ('93.184.216.34', port))]
        elif host == "malicious.com":
            return [(2, 1, 6, '', ('127.0.0.1', port))]
        raise Exception("Host not found")
    monkeypatch.setattr('asyncio.base_events.BaseEventLoop.getaddrinfo', fake_getaddrinfo)

@pytest.mark.anyio
async def test_safe_fetch(guard, mock_getaddrinfo):
    loc = await guard.validate("http://example.com/file.pdf")
    fetcher = SafeRemoteFetcher(guard)
    
    with respx.mock:
        respx.get("http://example.com/file.pdf").respond(
            status_code=200,
            headers={"Content-Type": "application/pdf"},
            content=b"%PDF-1.4"
        )
        
        asset = await fetcher.fetch(loc)
        assert asset.media_type == "application/pdf"
        assert asset.byte_size == 8
        assert asset.final_url == "http://example.com/file.pdf"
        assert asset.data == b"%PDF-1.4"

@pytest.mark.anyio
async def test_safe_fetch_redirect_validation(guard, mock_getaddrinfo):
    loc = await guard.validate("http://example.com/redirect")
    fetcher = SafeRemoteFetcher(guard)
    
    with respx.mock:
        respx.get("http://example.com/redirect").respond(
            status_code=302,
            headers={"Location": "http://malicious.com/file.pdf"}
        )
        
        with pytest.raises(UrlValidationError) as exc_info:
            await fetcher.fetch(loc)
        assert exc_info.value.code == UrlDenialCode.PRIVATE_ADDRESS

@pytest.mark.anyio
async def test_safe_fetch_size_limit(guard, mock_getaddrinfo):
    loc = await guard.validate("http://example.com/large.pdf")
    fetcher = SafeRemoteFetcher(guard)
    
    with respx.mock:
        respx.get("http://example.com/large.pdf").respond(
            status_code=200,
            headers={"Content-Type": "application/pdf"},
            content=b"A" * 105
        )
        
        with pytest.raises(ValueError, match="Response exceeded maximum size"):
            await fetcher.fetch(loc, maximum_bytes=100)

@pytest.mark.anyio
async def test_safe_fetch_media_type(guard, mock_getaddrinfo):
    loc = await guard.validate("http://example.com/image.png")
    fetcher = SafeRemoteFetcher(guard)
    
    with respx.mock:
        respx.get("http://example.com/image.png").respond(
            status_code=200,
            headers={"Content-Type": "image/png"},
            content=b"image data"
        )
        
        with pytest.raises(ValueError, match="Content-Type image/png not in allowed media types"):
            await fetcher.fetch(loc)
