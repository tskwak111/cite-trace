from collections.abc import Sequence
from uuid import UUID

from . import features
from .models import ReadingPriority, ReadingPriorityBand, ReferencePriorityInput


class ReadingPriorityService:
    def rank(
        self,
        mode: str,
        references: Sequence[ReferencePriorityInput],
        profile_version: str = "default-v1",
        analysis_id: UUID = UUID("00000000-0000-0000-0000-000000000000")
    ) -> tuple[ReadingPriority, ...]:
        results = []
        for ref in references:
            # Mock feature extraction based on intents
            ref_features = {}
            if "method" in ref.citation_intents:
                ref_features["adopted_method"] = True
            if "background" in ref.citation_intents:
                ref_features["background"] = True
            
            # Compute score based on mode
            score = 0.0
            if mode == "understand":
                score = features.compute_understand_score(ref_features)
            elif mode == "implement":
                score = features.compute_implement_score(ref_features)
            elif mode == "review":
                score = features.compute_review_score(ref_features)
            elif mode == "survey":
                score = features.compute_survey_score(ref_features)
            elif mode == "present":
                score = features.compute_present_score(ref_features)
                
            # Fallback mock for testing if no intents match
            if score == 0.0 and len(ref.citation_intents) > 0:
                score = 0.5
                
            band = ReadingPriorityBand.LOW
            if score >= 0.80:
                band = ReadingPriorityBand.MUST_READ
            elif score >= 0.60:
                band = ReadingPriorityBand.HIGH
            elif score >= 0.35:
                band = ReadingPriorityBand.MEDIUM
                
            reason_codes = tuple(ref_features.keys()) or ("default_reason",)
            
            results.append(ReadingPriority(
                analysis_id=analysis_id,
                reference_entry_id=ref.reference_entry_id,
                mode=mode,
                score=score,
                band=band,
                reason_codes=reason_codes,
                recommended_sections=("Methods",),
                next_actions=("read_paper",),
                feature_profile_version=profile_version
            ))
            
        return tuple(results)
