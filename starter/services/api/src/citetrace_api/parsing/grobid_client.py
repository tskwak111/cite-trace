import asyncio
import time

import httpx

from citetrace_api.config import get_settings
from citetrace_api.parsing.models import GrobidParseResult


class GrobidClientError(Exception):
    pass

class GrobidClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.url = f"{self.settings.grobid_url}/api/processFulltextDocument"
    
    async def process_fulltext(self, pdf_bytes: bytes, trace_id: str = "") -> GrobidParseResult:
        timeout = httpx.Timeout(
            self.settings.grobid_connect_timeout_seconds,
            read=self.settings.grobid_read_timeout_seconds
        )
        files = {"input": ("document.pdf", pdf_bytes, "application/pdf")}
        data = {
            "consolidateHeader": "0",
            "consolidateCitations": "0",
            "teiCoordinates": ["ref", "biblStruct", "p", "head", "figure", "formula"]
        }
        
        attempt = 0
        max_attempts = self.settings.grobid_max_attempts
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            while attempt < max_attempts:
                attempt += 1
                try:
                    start_time = time.monotonic()
                    response = await client.post(self.url, data=data, files=files)
                    elapsed_ms = int((time.monotonic() - start_time) * 1000)
                    
                    if response.status_code == 200:
                        content = response.content
                        if len(content) > self.settings.grobid_max_response_bytes:
                            raise GrobidClientError(f"Response exceeds maximum allowed bytes: {len(content)}")
                        return GrobidParseResult(
                            tei_xml=content,
                            status="success",
                            timings_ms={"grobid_ms": elapsed_ms}
                        )
                    
                    if response.status_code == 503:
                        if attempt >= max_attempts:
                            raise GrobidClientError(f"GROBID service unavailable after {max_attempts} attempts")
                        
                        retry_after = response.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            await asyncio.sleep(int(retry_after))
                        else:
                            await asyncio.sleep(2 ** attempt)
                        continue
                        
                    if response.status_code == 400:
                        raise GrobidClientError(f"Bad request to GROBID: {response.text}")
                    
                    if response.status_code >= 500:
                        if attempt >= max_attempts:
                            raise GrobidClientError(f"GROBID server error {response.status_code}")
                        await asyncio.sleep(2 ** attempt)
                        continue
                        
                    response.raise_for_status()
                    
                except httpx.RequestError as e:
                    if attempt >= max_attempts:
                        raise GrobidClientError(f"Failed to connect to GROBID: {e}") from e
                    await asyncio.sleep(2 ** attempt)
            
        raise GrobidClientError("Unexpected loop exit")
