
import httpx
from pydantic import BaseModel, Field


class UnpaywallLocation(BaseModel):
    url: str
    url_for_pdf: str | None = None
    url_for_landing_page: str | None = None
    is_best: bool
    license: str | None = None
    version: str | None = None
    host_type: str | None = None

class UnpaywallResult(BaseModel):
    doi: str
    is_oa: bool
    oa_status: str | None = None
    best_oa_location: UnpaywallLocation | None = None
    oa_locations: list[UnpaywallLocation] = Field(default_factory=list)
    title: str | None = None

class UnpaywallProvider:
    def __init__(self, contact_email: str, client: httpx.AsyncClient | None = None):
        self.contact_email = contact_email
        self.client = client

    async def get_oa_locations(self, doi: str) -> UnpaywallResult:
        async with httpx.AsyncClient() if self.client is None else _AsyncClientContextManager(self.client) as client:
            url = f"https://api.unpaywall.org/v2/{doi}?email={self.contact_email}"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return UnpaywallResult(**data)

class _AsyncClientContextManager:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        
    async def __aenter__(self) -> httpx.AsyncClient:
        return self.client
        
    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass
