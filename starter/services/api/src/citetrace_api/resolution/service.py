import asyncio
from collections.abc import Sequence

from citetrace_api.providers.models import BibliographicQuery, ProviderCandidate
from citetrace_api.providers.protocols import ScholarlyMetadataProvider

from .decision import ResolutionDecision, decide_resolution
from .features import compare_reference_to_candidate
from .scoring import weighted_score


class ReferenceResolutionService:
    def __init__(self, providers: Sequence[ScholarlyMetadataProvider]):
        self.providers = providers

    async def resolve(
        self, query: BibliographicQuery, trace_id: str = ""
    ) -> tuple[ResolutionDecision, list[ProviderCandidate]]:
        if not self.providers:
            return decide_resolution([]), []

        coros = [p.search(query, trace_id) for p in self.providers]
        results = await asyncio.gather(*coros, return_exceptions=True)

        all_candidates: list[ProviderCandidate] = []
        for res in results:
            if isinstance(res, list):
                all_candidates.extend(res)

        # deduplicate
        seen = set()
        unique_cands: list[ProviderCandidate] = []
        for c in all_candidates:
            key = c.identifiers.get("doi") or c.title.lower()
            if key not in seen:
                seen.add(key)
                unique_cands.append(c)

        scored = []
        for c in unique_cands:
            feat = compare_reference_to_candidate(query, c, unique_cands)
            score = weighted_score(feat)
            scored.append((c, score, feat))

        decision = decide_resolution(scored)
        return decision, unique_cands
