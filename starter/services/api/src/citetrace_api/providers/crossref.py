from typing import Any

from citetrace_api.providers.http import ProviderHttpClient
from citetrace_api.providers.models import BibliographicQuery, ProviderCandidate
from citetrace_api.providers.protocols import ScholarlyMetadataProvider


class CrossrefProvider(ScholarlyMetadataProvider):
    def __init__(
        self,
        http_client: ProviderHttpClient,
        base_url: str = "https://api.crossref.org",
        contact_email: str | None = None,
    ):
        self.http_client = http_client
        self.base_url = base_url.rstrip("/")
        self.contact_email = contact_email

    @property
    def name(self) -> str:
        return "crossref"

    async def search(self, query: BibliographicQuery, trace_id: str) -> list[ProviderCandidate]:
        headers = {}
        if self.contact_email:
            headers["User-Agent"] = f"CiteTrace/1.0 (mailto:{self.contact_email})"

        # 1. Try exact DOI
        if "doi" in query.identifiers:
            doi = query.identifiers["doi"]
            if doi.startswith("https://doi.org/"):
                doi = doi[len("https://doi.org/") :]
            elif doi.startswith("http://doi.org/"):
                doi = doi[len("http://doi.org/") :]
            elif doi.startswith("doi:"):
                doi = doi[len("doi:") :]

            url = f"{self.base_url}/works/{doi}"
            response = await self.http_client.get_json(
                provider=self.name,
                url=url,
                headers=headers,
                trace_id=trace_id,
                maximum_bytes=10485760,
            )

            if (
                response.status_code == 200
                and response.data
                and isinstance(response.data, dict)
                and response.data.get("status") == "ok"
            ):
                item = response.data.get("message", {})
                return [self._parse_item(item)]

        # 2. Try title search
        if query.title:
            params: dict[str, str | int] = {"query.bibliographic": query.title, "rows": 5}
            if query.authors:
                params["query.author"] = query.authors[0]

            url = f"{self.base_url}/works"
            response = await self.http_client.get_json(
                provider=self.name,
                url=url,
                params=params,
                headers=headers,
                trace_id=trace_id,
                maximum_bytes=10485760,
            )

            if (
                response.status_code == 200
                and response.data
                and isinstance(response.data, dict)
                and response.data.get("status") == "ok"
            ):
                items = response.data.get("message", {}).get("items", [])
                candidates = []
                for item in items:
                    candidates.append(self._parse_item(item))
                return candidates

        return []

    def _parse_item(self, item: dict[str, Any]) -> ProviderCandidate:
        titles = item.get("title", [])
        title = titles[0] if titles else "Unknown Title"

        authors = []
        for author in item.get("author", []):
            family = author.get("family", "")
            given = author.get("given", "")
            if family and given:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)

        year = None
        issued = item.get("issued", {}).get("date-parts", [])
        if issued and issued[0]:
            year = issued[0][0]

        containers = item.get("container-title", [])
        venue = containers[0] if containers else None

        doi = item.get("DOI", "")
        identifiers = {}
        if doi:
            identifiers["doi"] = doi

        return ProviderCandidate.from_provider(
            provider=self.name,
            provider_record_id=doi,
            title=title,
            authors=tuple(authors),
            year=year,
            venue=venue,
            identifiers=identifiers,
            raw_snapshot=item,
        )
