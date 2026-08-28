import os
import textwrap

os.makedirs("src/citetrace_api/resolution", exist_ok=True)
os.makedirs("tests", exist_ok=True)

with open("src/citetrace_api/resolution/__init__.py", "w") as f:
    f.write("")

with open("src/citetrace_api/resolution/features.py", "w") as f:
    f.write(textwrap.dedent("""\
        import difflib
        from dataclasses import dataclass
        from typing import Sequence, Any
        from citetrace_api.providers.models import BibliographicQuery, ProviderCandidate

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
            provider_candidates: Sequence[ProviderCandidate] = ()
        ) -> ResolutionFeatures:
            hard_conflicts: list[str] = []
            identifier_score = 0.0
            
            ref_identifiers = getattr(reference, 'identifiers', {}) or {}
            cand_identifiers = candidate.identifiers or {}
            
            # check DOI conflict
            ref_doi = ref_identifiers.get('doi')
            cand_doi = cand_identifiers.get('doi')
            if ref_doi and cand_doi:
                if ref_doi.lower() == cand_doi.lower():
                    identifier_score = 1.0
                else:
                    hard_conflicts.append("doi_conflict")
                    
            ref_arxiv = ref_identifiers.get('arxiv')
            cand_arxiv = cand_identifiers.get('arxiv')
            if ref_arxiv and cand_arxiv:
                if ref_arxiv.lower() == cand_arxiv.lower():
                    identifier_score = max(identifier_score, 1.0)
                else:
                    hard_conflicts.append("arxiv_conflict")

            title_score = 0.0
            ref_title = getattr(reference, 'title', None)
            if ref_title and candidate.title:
                matcher = difflib.SequenceMatcher(None, ref_title.lower(), candidate.title.lower())
                title_score = matcher.ratio()
                
            author_score = 0.0
            ref_authors = getattr(reference, 'authors', ())
            if ref_authors and candidate.authors:
                matches = sum(1 for a in ref_authors if any(a.lower() in ca.lower() for ca in candidate.authors))
                author_score = matches / max(len(ref_authors), len(candidate.authors))
                
            year_score = 0.0
            ref_year = getattr(reference, 'year', None)
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
                    
            provider_agreement_score = 0.0
            if provider_candidates:
                match_count = sum(1 for c in provider_candidates if (c.identifiers.get('doi') == cand_doi and cand_doi) or (c.title.lower() == candidate.title.lower()))
                provider_agreement_score = match_count / len(provider_candidates)

            return ResolutionFeatures(
                identifier_score=identifier_score,
                title_score=title_score,
                author_score=author_score,
                year_score=year_score,
                venue_score=0.0,
                version_score=0.0,
                provider_agreement_score=provider_agreement_score,
                hard_conflicts=tuple(hard_conflicts)
            )
    """))

with open("src/citetrace_api/resolution/scoring.py", "w") as f:
    f.write(textwrap.dedent("""\
        from dataclasses import dataclass
        from .features import ResolutionFeatures

        @dataclass(frozen=True, slots=True)
        class ResolutionWeights:
            identifier: float = 0.35
            title: float = 0.25
            authors: float = 0.15
            year: float = 0.08
            venue: float = 0.05
            version: float = 0.07
            provider_agreement: float = 0.05

        def weighted_score(features: ResolutionFeatures, weights: ResolutionWeights | None = None) -> float:
            if weights is None:
                weights = ResolutionWeights()
            
            if features.hard_conflicts:
                return 0.0
                
            score = (
                features.identifier_score * weights.identifier +
                features.title_score * weights.title +
                features.author_score * weights.authors +
                features.year_score * weights.year +
                features.venue_score * weights.venue +
                features.version_score * weights.version +
                features.provider_agreement_score * weights.provider_agreement
            )
            
            return max(0.0, min(1.0, score))
    """))

with open("src/citetrace_api/resolution/decision.py", "w") as f:
    f.write(textwrap.dedent("""\
        from dataclasses import dataclass
        from typing import Sequence, Optional
        from uuid import UUID
        from citetrace_api.providers.models import ProviderCandidate
        from .features import ResolutionFeatures

        @dataclass(frozen=True, slots=True)
        class ResolutionDecision:
            status: str
            selected_candidate_id: str | None
            selected_work_version_id: UUID | None
            absolute_score: float | None
            score_margin: float | None
            reason_codes: tuple[str, ...]
            requires_human_review: bool

        def decide_resolution(
            scored_candidates: Sequence[tuple[ProviderCandidate, float, ResolutionFeatures]],
            threshold_accept: float = 0.90,
            threshold_margin: float = 0.08,
            threshold_ambiguous_floor: float = 0.80
        ) -> ResolutionDecision:
            if not scored_candidates:
                return ResolutionDecision(
                    status="unresolved",
                    selected_candidate_id=None,
                    selected_work_version_id=None,
                    absolute_score=None,
                    score_margin=None,
                    reason_codes=("no_candidates",),
                    requires_human_review=False
                )
                
            sorted_cands = sorted(scored_candidates, key=lambda x: x[1], reverse=True)
            top_cand, top_score, top_features = sorted_cands[0]
            
            margin = top_score
            if len(sorted_cands) > 1:
                margin = top_score - sorted_cands[1][1]
                
            cand_id = f"{top_cand.provider}:{top_cand.provider_record_id}"
            
            if top_score >= threshold_accept and margin >= threshold_margin:
                return ResolutionDecision(
                    status="resolved",
                    selected_candidate_id=cand_id,
                    selected_work_version_id=None,
                    absolute_score=top_score,
                    score_margin=margin,
                    reason_codes=(),
                    requires_human_review=False
                )
            elif top_score >= threshold_ambiguous_floor:
                return ResolutionDecision(
                    status="ambiguous",
                    selected_candidate_id=None,
                    selected_work_version_id=None,
                    absolute_score=top_score,
                    score_margin=margin,
                    reason_codes=("ambiguous_candidates",) if len(sorted_cands) > 1 and margin < threshold_margin else ("needs_review",),
                    requires_human_review=True
                )
            else:
                return ResolutionDecision(
                    status="unresolved",
                    selected_candidate_id=None,
                    selected_work_version_id=None,
                    absolute_score=top_score,
                    score_margin=margin,
                    reason_codes=("low_score",),
                    requires_human_review=False
                )
    """))

with open("src/citetrace_api/resolution/service.py", "w") as f:
    f.write(textwrap.dedent("""\
        import asyncio
        from typing import Sequence
        from citetrace_api.providers.models import BibliographicQuery, ProviderCandidate
        from citetrace_api.providers.protocols import ScholarlyMetadataProvider
        from .features import compare_reference_to_candidate, ResolutionFeatures
        from .scoring import weighted_score, ResolutionWeights
        from .decision import decide_resolution, ResolutionDecision

        class ReferenceResolutionService:
            def __init__(self, providers: Sequence[ScholarlyMetadataProvider]):
                self.providers = providers
                
            async def resolve(self, query: BibliographicQuery, trace_id: str = "") -> tuple[ResolutionDecision, list[ProviderCandidate]]:
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
    """))

with open("tests/test_resolution_features.py", "w") as f:
    f.write(textwrap.dedent("""\
        import pytest
        from citetrace_api.providers.models import ProviderCandidate, BibliographicQuery
        from citetrace_api.resolution.features import compare_reference_to_candidate
        from uuid import uuid4

        def test_compare_reference_to_candidate_exact_doi():
            query = BibliographicQuery(reference_entry_id=uuid4(), title="Test", authors=("A",), year=2020, venue=None, identifiers={"doi": "10.1000/123"}, raw_reference="")
            cand = ProviderCandidate.from_provider(provider="x", provider_record_id="1", title="Test", authors=("A",), year=2020, venue=None, identifiers={"doi": "10.1000/123"}, raw_snapshot={})
            
            feat = compare_reference_to_candidate(query, cand)
            assert feat.identifier_score == 1.0
            assert "doi_conflict" not in feat.hard_conflicts
            
        def test_compare_reference_to_candidate_doi_conflict():
            query = BibliographicQuery(reference_entry_id=uuid4(), title="Test", authors=("A",), year=2020, venue=None, identifiers={"doi": "10.1000/123"}, raw_reference="")
            cand = ProviderCandidate.from_provider(provider="x", provider_record_id="1", title="Test", authors=("A",), year=2020, venue=None, identifiers={"doi": "10.1000/456"}, raw_snapshot={})
            
            feat = compare_reference_to_candidate(query, cand)
            assert feat.identifier_score == 0.0
            assert "doi_conflict" in feat.hard_conflicts
    """))

with open("tests/test_resolution_decision.py", "w") as f:
    f.write(textwrap.dedent("""\
        import pytest
        from citetrace_api.resolution.decision import decide_resolution
        from citetrace_api.providers.models import ProviderCandidate
        from citetrace_api.resolution.features import ResolutionFeatures

        def test_decide_resolution_resolved():
            cand = ProviderCandidate.from_provider(provider="x", provider_record_id="1", title="Test", authors=(), year=None, venue=None, identifiers={}, raw_snapshot={})
            feat = ResolutionFeatures(0,0,0,0,0,0,0,())
            scored = [(cand, 0.95, feat)]
            decision = decide_resolution(scored)
            assert decision.status == "resolved"
            assert decision.selected_candidate_id == "x:1"
            
        def test_decide_resolution_ambiguous():
            cand1 = ProviderCandidate.from_provider(provider="x", provider_record_id="1", title="Test1", authors=(), year=None, venue=None, identifiers={}, raw_snapshot={})
            cand2 = ProviderCandidate.from_provider(provider="x", provider_record_id="2", title="Test2", authors=(), year=None, venue=None, identifiers={}, raw_snapshot={})
            feat = ResolutionFeatures(0,0,0,0,0,0,0,())
            scored = [(cand1, 0.85, feat), (cand2, 0.84, feat)]
            decision = decide_resolution(scored)
            assert decision.status == "ambiguous"
    """))

with open("tests/test_resolution_service.py", "w") as f:
    f.write(textwrap.dedent("""\
        import pytest
        import asyncio
        from uuid import uuid4
        from citetrace_api.resolution.service import ReferenceResolutionService
        from citetrace_api.providers.protocols import ScholarlyMetadataProvider
        from citetrace_api.providers.models import BibliographicQuery, ProviderCandidate

        class MockProvider(ScholarlyMetadataProvider):
            def __init__(self, name: str, candidates: list[ProviderCandidate]):
                self._name = name
                self.candidates = candidates
                
            @property
            def name(self) -> str:
                return self._name
                
            async def search(self, query: BibliographicQuery, trace_id: str) -> list[ProviderCandidate]:
                return self.candidates

        @pytest.mark.asyncio
        async def test_resolve_service():
            cand = ProviderCandidate.from_provider(provider="x", provider_record_id="1", title="Exact Match", authors=("Smith",), year=2020, venue=None, identifiers={"doi": "10.1000/123"}, raw_snapshot={})
            svc = ReferenceResolutionService([MockProvider("x", [cand])])
            
            query = BibliographicQuery(reference_entry_id=uuid4(), title="Exact Match", authors=("Smith",), year=2020, venue=None, identifiers={"doi": "10.1000/123"}, raw_reference="")
            
            decision, cands = await svc.resolve(query)
            assert decision.status == "resolved"
            assert len(cands) == 1
    """))

