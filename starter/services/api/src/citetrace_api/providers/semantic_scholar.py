from typing import Any

from pydantic import SecretStr

from citetrace_api.providers.http import ProviderHttpClient
from citetrace_api.providers.models import BibliographicQuery, ProviderCandidate
from citetrace_api.providers.protocols import ScholarlyMetadataProvider


class SemanticScholarProvider(ScholarlyMetadataProvider):
    def __init__(
        self,
        http_client: ProviderHttpClient,
        base_url: str = "https://api.semanticscholar.org",
        api_key: SecretStr | None = None,
    ):
        self.http_client = http_client
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "semantic_scholar"

    async def search(self, query: BibliographicQuery, trace_id: str) -> list[ProviderCandidate]:
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key.get_secret_value()

        fields = "paperId,externalIds,title,authors,year,venue,publicationTypes,openAccessPdf"

        # 1. Try exact IDs
        exact_id = None
        if "semanticscholar" in query.identifiers:
            exact_id = query.identifiers["semanticscholar"]
        elif "doi" in query.identifiers:
            doi = query.identifiers["doi"]
            if doi.startswith("https://doi.org/"):
                doi = doi[len("https://doi.org/") :]
            elif doi.startswith("http://doi.org/"):
                doi = doi[len("http://doi.org/") :]
            elif doi.startswith("doi:"):
                doi = doi[len("doi:") :]
            exact_id = f"DOI:{doi}"
        elif "arxiv" in query.identifiers:
            exact_id = f"ARXIV:{query.identifiers['arxiv']}"

        if exact_id:
            url = f"{self.base_url}/graph/v1/paper/{exact_id}"
            response = await self.http_client.get_json(
                provider=self.name,
                url=url,
                params={"fields": fields},
                headers=headers,
                trace_id=trace_id,
                maximum_bytes=10485760,
            )
            if response.status_code == 200 and response.data and isinstance(response.data, dict):
                return [self._parse_item(response.data)]

        # 2. Try title search
        if query.title:
            url = f"{self.base_url}/graph/v1/paper/search"
            response = await self.http_client.get_json(
                provider=self.name,
                url=url,
                params={"query": query.title, "fields": fields, "limit": 5},
                headers=headers,
                trace_id=trace_id,
                maximum_bytes=10485760,
            )

            if response.status_code == 200 and response.data and isinstance(response.data, dict):
                items = response.data.get("data", [])
                candidates = []
                for item in items:
                    candidates.append(self._parse_item(item))
                return candidates

        return []

    def _parse_item(self, item: dict[str, Any]) -> ProviderCandidate:
        title = item.get("title") or "Unknown Title"

        authors = []
        for author in item.get("authors", []):
            name = author.get("name")
            if name:
                authors.append(name)

        year = item.get("year")
        venue = item.get("venue")

        paper_id = item.get("paperId", "")

        identifiers = {"semanticscholar": paper_id} if paper_id else {}
        ext_ids = item.get("externalIds", {})
        if "DOI" in ext_ids:
            identifiers["doi"] = ext_ids["DOI"]
        if "ArXiv" in ext_ids:
            identifiers["arxiv"] = ext_ids["ArXiv"]

        return ProviderCandidate.from_provider(
            provider=self.name,
            provider_record_id=paper_id,
            title=title,
            authors=tuple(authors),
            year=year,
            venue=venue,
            identifiers=identifiers,
            raw_snapshot=item,
        )
