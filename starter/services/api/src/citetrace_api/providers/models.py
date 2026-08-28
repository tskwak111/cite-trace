from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BibliographicQuery:
    reference_entry_id: UUID
    title: str | None
    authors: tuple[str, ...]
    year: int | None
    venue: str | None
    identifiers: Mapping[str, str]
    raw_reference: str

@dataclass(frozen=True, slots=True)
class ProviderCandidate:
    provider: str
    provider_record_id: str
    title: str
    normalized_title: str
    authors: tuple[str, ...]
    year: int | None
    venue: str | None
    identifiers: Mapping[str, str]
    version_hints: Mapping[str, str]
    access_hints: Mapping[str, object]
    raw_snapshot: Mapping[str, object]

    @classmethod
    def from_provider(
        cls,
        *,
        provider: str,
        provider_record_id: str,
        title: str,
        authors: tuple[str, ...],
        year: int | None,
        venue: str | None,
        identifiers: Mapping[str, str],
        version_hints: Mapping[str, str] | None = None,
        access_hints: Mapping[str, object] | None = None,
        raw_snapshot: Mapping[str, object]
    ) -> "ProviderCandidate":
        normalized_title = title.strip().lower()
        import re
        normalized_title = re.sub(r"\s+", " ", normalized_title)
        
        norm_authors = tuple(a.strip() for a in authors if a.strip())
        
        norm_identifiers = dict(identifiers)
        if "doi" in norm_identifiers:
            doi = norm_identifiers["doi"].strip().lower()
            if doi.startswith("https://doi.org/"):
                doi = doi[len("https://doi.org/"):]
            elif doi.startswith("http://doi.org/"):
                doi = doi[len("http://doi.org/"):]
            elif doi.startswith("doi:"):
                doi = doi[len("doi:"):]
            norm_identifiers["doi"] = doi

        return cls(
            provider=provider,
            provider_record_id=provider_record_id,
            title=title,
            normalized_title=normalized_title,
            authors=norm_authors,
            year=year,
            venue=venue,
            identifiers=norm_identifiers,
            version_hints=version_hints or {},
            access_hints=access_hints or {},
            raw_snapshot=raw_snapshot
        )

@dataclass(frozen=True, slots=True)
class ProviderJsonResponse:
    status_code: int
    data: dict[str, Any] | list[Any] | None
    headers: dict[str, str]
    latency_ms: int
    trace_id: str
    response_sha256: str
    error_code: str | None = None
