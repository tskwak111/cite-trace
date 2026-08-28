from typing import Any

from citetrace_api.verification.relations import EvidenceRelation, RelationDecision


class RelationVerificationService:
    def verify(self, access_level: str, spans: list[Any]) -> RelationDecision:
        if access_level == "not_accessible":
            return RelationDecision(EvidenceRelation.inaccessible_source, 1.0, [], (), False)
        if not spans:
            return RelationDecision(EvidenceRelation.no_relevant_evidence, 1.0, [], (), False)
        return RelationDecision(EvidenceRelation.direct_support, 1.0, [], (), False)
