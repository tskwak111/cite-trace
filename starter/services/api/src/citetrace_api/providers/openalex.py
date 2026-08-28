from typing import Any

from citetrace_api.providers.http import ProviderHttpClient
from citetrace_api.providers.models import BibliographicQuery, ProviderCandidate
from citetrace_api.providers.protocols import ScholarlyMetadataProvider


class OpenAlexProvider(ScholarlyMetadataProvider):
    def __init__(
        self,
        http_client: ProviderHttpClient,
        base_url: str = "https://api.openalex.org",
        contact_email: str | None = None,
    ) -> None:
        self.http_client = http_client
        self.base_url = base_url.rstrip("/")
        self.contact_email = contact_email

    @property
    def name(self) -> str:
        return "openalex"

    async def search(self, query: BibliographicQuery, trace_id: str) -> list[ProviderCandidate]:
        headers: dict[str, str] = {}
        params: dict[str, str | int] = {}
        if self.contact_email:
            params["mailto"] = self.contact_email

        # 1. Try exact IDs
        exact_id = None
        if "openalex" in query.identifiers:
            exact_id = query.identifiers["openalex"]
        elif "doi" in query.identifiers:
            doi = query.identifiers["doi"]
            if doi.startswith("https://doi.org/"):
                doi = doi[len("https://doi.org/") :]
            elif doi.startswith("http://doi.org/"):
                doi = doi[len("http://doi.org/") :]
            elif doi.startswith("doi:"):
                doi = doi[len("doi:") :]
            exact_id = f"doi:{doi}"
        elif "arxiv" in query.identifiers:
            exact_id = f"arxiv:{query.identifiers['arxiv']}"

        if exact_id:
            url = f"{self.base_url}/works/{exact_id}"
            response = await self.http_client.get_json(
                provider=self.name,
                url=url,
                params=params,
                headers=headers,
                trace_id=trace_id,
                maximum_bytes=10485760,
            )
            if response.status_code == 200 and response.data and isinstance(response.data, dict):
                return [self._parse_item(response.data)]

        # 2. Try title search
        if query.title:
            search_params = dict(params)
            search_params["filter"] = f"title.search:{query.title}"
            search_params["per-page"] = 5

            url = f"{self.base_url}/works"
            response = await self.http_client.get_json(
                provider=self.name,
                url=url,
                params=search_params,
                headers=headers,
                trace_id=trace_id,
                maximum_bytes=10485760,
            )

            if response.status_code == 200 and response.data and isinstance(response.data, dict):
                items = response.data.get("results", [])
                candidates = []
                for item in items:
                    candidates.append(self._parse_item(item))
                return candidates

        return []

    def _parse_item(self, item: dict[str, Any]) -> ProviderCandidate:
        title = item.get("title") or "Unknown Title"

        authors = []
        for authorship in item.get("authorships", []):
            author = authorship.get("author", {})
            name = author.get("display_name")
            if name:
                authors.append(name)

        year = item.get("publication_year")

        venue = None
        primary_location = item.get("primary_location", {})
        if primary_location:
            source = primary_location.get("source", {})
            if source:
                venue = source.get("display_name")

        raw_id = item.get("id")
        openalex_id = raw_id.replace("https://openalex.org/", "") if isinstance(raw_id, str) else ""

        identifiers = {"openalex": openalex_id} if openalex_id else {}

        raw_doi = item.get("doi")
        if isinstance(raw_doi, str):
            identifiers["doi"] = raw_doi.replace("https://doi.org/", "")

        return ProviderCandidate.from_provider(
            provider=self.name,
            provider_record_id=openalex_id,
            title=title,
            authors=tuple(authors),
            year=year,
            venue=venue,
            identifiers=identifiers,
            raw_snapshot=item,
        )
