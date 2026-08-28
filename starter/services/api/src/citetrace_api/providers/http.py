import asyncio
import hashlib
import time
from collections.abc import Awaitable, Callable, Mapping

import httpx

from citetrace_api.providers.models import ProviderJsonResponse


class ProviderHttpClient:
    def __init__(
        self, 
        client: httpx.AsyncClient | None = None, 
        clock: Callable[[], float] = time.monotonic, 
        sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep, 
        max_retries: int = 3
    ) -> None:
        self.client = client or httpx.AsyncClient()
        self.clock = clock
        self.sleeper = sleeper
        self.max_retries = max_retries

    async def get_json(
        self,
        *,
        provider: str,
        url: str,
        params: Mapping[str, str | int] | None = None,
        headers: Mapping[str, str] | None = None,
        trace_id: str,
        maximum_bytes: int,
    ) -> ProviderJsonResponse:
        attempt = 0
        # safe_headers omitted
        
        while attempt <= self.max_retries:
            start_time = self.clock()
            try:
                response = await self.client.get(
                    url,
                    params=params,
                    headers=headers,
                )
                latency_ms = int((self.clock() - start_time) * 1000)
                
                # Check JSON length
                content = await response.aread()
                if len(content) > maximum_bytes:
                    return ProviderJsonResponse(
                        status_code=response.status_code,
                        data=None,
                        headers=dict(response.headers),
                        latency_ms=latency_ms,
                        trace_id=trace_id,
                        response_sha256="",
                        error_code="response_too_large"
                    )

                response_sha256 = hashlib.sha256(content).hexdigest()
                
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self.max_retries:
                        retry_after = response.headers.get("retry-after")
                        sleep_time = float(retry_after) if retry_after else 1.0
                        await self.sleeper(sleep_time)
                        attempt += 1
                        continue
                    else:
                        return ProviderJsonResponse(
                            status_code=response.status_code,
                            data=None,
                            headers=dict(response.headers),
                            latency_ms=latency_ms,
                            trace_id=trace_id,
                            response_sha256=response_sha256,
                            error_code="provider_error"
                        )
                
                if 400 <= response.status_code < 500:
                    return ProviderJsonResponse(
                        status_code=response.status_code,
                        data=None,
                        headers=dict(response.headers),
                        latency_ms=latency_ms,
                        trace_id=trace_id,
                        response_sha256=response_sha256,
                        error_code="client_error" if response.status_code != 404 else "not_found"
                    )

                # Validate JSON
                try:
                    data = response.json()
                except ValueError:
                    return ProviderJsonResponse(
                        status_code=response.status_code,
                        data=None,
                        headers=dict(response.headers),
                        latency_ms=latency_ms,
                        trace_id=trace_id,
                        response_sha256=response_sha256,
                        error_code="invalid_json"
                    )
                    
                return ProviderJsonResponse(
                    status_code=response.status_code,
                    data=data,
                    headers=dict(response.headers),
                    latency_ms=latency_ms,
                    trace_id=trace_id,
                    response_sha256=response_sha256,
                    error_code=None
                )
                
            except httpx.TimeoutException:
                latency_ms = int((self.clock() - start_time) * 1000)
                if attempt < self.max_retries:
                    await self.sleeper(1.0)
                    attempt += 1
                    continue
                return ProviderJsonResponse(
                    status_code=0,
                    data=None,
                    headers={},
                    latency_ms=latency_ms,
                    trace_id=trace_id,
                    response_sha256="",
                    error_code="timeout"
                )
            except httpx.RequestError:
                latency_ms = int((self.clock() - start_time) * 1000)
                if attempt < self.max_retries:
                    await self.sleeper(1.0)
                    attempt += 1
                    continue
                return ProviderJsonResponse(
                    status_code=0,
                    data=None,
                    headers={},
                    latency_ms=latency_ms,
                    trace_id=trace_id,
                    response_sha256="",
                    error_code="request_error"
                )
        
        # fallback
        return ProviderJsonResponse(
            status_code=0,
            data=None,
            headers={},
            latency_ms=0,
            trace_id=trace_id,
            response_sha256="",
            error_code="unknown"
        )
