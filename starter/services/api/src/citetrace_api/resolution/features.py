import difflib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from citetrace_api.providers.models import ProviderCandidate


@dataclass(frozen=True, slots=True)
class ResolutionFeatures:
    identifier_score: float
    title_score: float
    author_score: float
    year_score: float
    venue_score: float
    version_score: float
    provider_agreement_score: float
    hard_conflicts: tuple[str, ...]


def compare_reference_to_candidate(
    reference: Any,
    candidate: ProviderCandidate,
    provider_candidates: Sequence[ProviderCandidate] = (),
) -> ResolutionFeatures:
    hard_conflicts: list[str] = []
    identifier_score = 0.0

    ref_identifiers = getattr(reference, "identifiers", {}) or {}
    cand_identifiers = candidate.identifiers or {}

    # check DOI conflict
    ref_doi = ref_identifiers.get("doi")
    cand_doi = cand_identifiers.get("doi")
    if ref_doi and cand_doi:
        if ref_doi.lower() == cand_doi.lower():
            identifier_score = 1.0
        else:
            hard_conflicts.append("doi_conflict")

    ref_arxiv = ref_identifiers.get("arxiv")
    cand_arxiv = cand_identifiers.get("arxiv")
    if ref_arxiv and cand_arxiv:
        if ref_arxiv.lower() == cand_arxiv.lower():
            identifier_score = max(identifier_score, 1.0)
        else:
            hard_conflicts.append("arxiv_conflict")

    title_score = 0.0
    ref_title = getattr(reference, "title", None)
    if ref_title and candidate.title:
        matcher = difflib.SequenceMatcher(None, ref_title.lower(), candidate.title.lower())
        title_score = matcher.ratio()

    author_score = 0.0
    ref_authors = getattr(reference, "authors", ())
    if ref_authors and candidate.authors:
        matches = sum(
            1 for a in ref_authors if any(a.lower() in ca.lower() for ca in candidate.authors)
        )
        author_score = matches / max(len(ref_authors), len(candidate.authors))

    year_score = 0.0
    ref_year = getattr(reference, "year", None)
    if ref_year and candidate.year:
        diff = abs(int(ref_year) - int(candidate.year))
        if diff == 0:
            year_score = 1.0
        elif diff == 1:
            year_score = 0.8
        elif diff == 2:
            year_score = 0.5
        else:
            year_score = 0.0

    venue_score = 0.0
    ref_venue = getattr(reference, "venue", None)
    if ref_venue and candidate.venue:
        if (
            ref_venue.lower() in candidate.venue.lower()
            or candidate.venue.lower() in ref_venue.lower()
        ):
            venue_score = 1.0
        else:
            matcher = difflib.SequenceMatcher(None, ref_venue.lower(), candidate.venue.lower())
            venue_score = matcher.ratio()

    version_score = 1.0  # default if not specified

    provider_agreement_score = 0.0
    if provider_candidates:
        match_count = sum(
            1
            for c in provider_candidates
            if (c.identifiers.get("doi") == cand_doi and cand_doi)
            or (c.title.lower() == candidate.title.lower())
        )
        provider_agreement_score = match_count / len(provider_candidates)

    return ResolutionFeatures(
        identifier_score=identifier_score,
        title_score=title_score,
        author_score=author_score,
        year_score=year_score,
        venue_score=venue_score,
        version_score=version_score,
        provider_agreement_score=provider_agreement_score,
        hard_conflicts=tuple(hard_conflicts),
    )
