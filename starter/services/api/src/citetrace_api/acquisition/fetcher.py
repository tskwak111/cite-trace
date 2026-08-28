import hashlib

import httpx

from .url_guard import UrlDenialCode, UrlGuard, UrlValidationError, ValidatedRemoteLocation


class FetchedRemoteAsset:
    def __init__(self, data: bytes, sha256: str, media_type: str, byte_size: int, final_url: str, headers: dict[str, str], status_code: int):
        self.data = data
        self.sha256 = sha256
        self.media_type = media_type
        self.byte_size = byte_size
        self.final_url = final_url
        self.headers = headers
        self.status_code = status_code

class SafeRemoteFetcher:
    def __init__(self, guard: UrlGuard | None = None, client: httpx.AsyncClient | None = None):
        self.guard = guard or UrlGuard()
        self.client = client

    async def fetch(self, location: ValidatedRemoteLocation, *, maximum_bytes: int = 104_857_600, allowed_media_types: frozenset[str] = frozenset({"application/pdf"}), trace_id: str = "", max_redirects: int = 5) -> FetchedRemoteAsset:
        current_location = location
        redirects = 0
        
        # We need an async client. If one isn't provided, use a context manager to create one.
        async with httpx.AsyncClient() if self.client is None else _AsyncClientContextManager(self.client) as client:
            while True:
                # Do a stream request so we can check headers and stream body
                async with client.stream("GET", current_location.url, headers={"X-Trace-Id": trace_id} if trace_id else {}) as response:
                    if 300 <= response.status_code < 400:
                        if redirects >= max_redirects:
                            raise UrlValidationError(UrlDenialCode.REDIRECT_LIMIT_EXCEEDED, "Too many redirects")
                            
                        location_header = response.headers.get("location")
                        if not location_header:
                            raise RuntimeError("Redirect missing location header")
                            
                        # Handle relative URLs in location header
                        from urllib.parse import urljoin
                        next_url = urljoin(current_location.url, location_header)
                        
                        current_location = await self.guard.validate(next_url)
                        redirects += 1
                        continue
                        
                    response.raise_for_status()
                    
                    # Validate content type
                    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
                    if content_type not in allowed_media_types:
                        raise ValueError(f"Content-Type {content_type} not in allowed media types")
                        
                    # Stream the body
                    body = bytearray()
                    hasher = hashlib.sha256()
                    
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        hasher.update(chunk)
                        if len(body) > maximum_bytes:
                            raise ValueError(f"Response exceeded maximum size of {maximum_bytes} bytes")
                            
                    return FetchedRemoteAsset(
                        data=bytes(body),
                        sha256=hasher.hexdigest(),
                        media_type=content_type,
                        byte_size=len(body),
                        final_url=current_location.url,
                        headers=dict(response.headers),
                        status_code=response.status_code
                    )

class _AsyncClientContextManager:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        
    async def __aenter__(self) -> httpx.AsyncClient:
        return self.client
        
    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass
