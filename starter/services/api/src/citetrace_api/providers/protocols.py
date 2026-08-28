from typing import Protocol

from citetrace_api.providers.models import BibliographicQuery, ProviderCandidate


class ScholarlyMetadataProvider(Protocol):
    @property
    def name(self) -> str: ...

    async def search(self, query: BibliographicQuery, trace_id: str) -> list[ProviderCandidate]: ...
