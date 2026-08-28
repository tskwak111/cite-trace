from enum import StrEnum


class AnalysisMode(StrEnum):
    UNDERSTAND = "understand"
    IMPLEMENT = "implement"
    REVIEW = "review"
    SURVEY = "survey"
    PRESENT = "present"


class Audience(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class AnalysisStatus(StrEnum):
    CREATED = "created"
    VALIDATING = "validating"
    PARSING = "parsing"
    RESOLVING_REFERENCES = "resolving_references"
    ACQUIRING_SOURCES = "acquiring_sources"
    RETRIEVING_EVIDENCE = "retrieving_evidence"
    VERIFYING_RELATIONS = "verifying_relations"
    GENERATING_EXPLANATIONS = "generating_explanations"
    AUDITING = "auditing"
    COMPLETED = "completed"
    COMPLETED_WITH_LIMITS = "completed_with_limits"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def terminal(self) -> bool:
        return self in {
            AnalysisStatus.COMPLETED,
            AnalysisStatus.COMPLETED_WITH_LIMITS,
            AnalysisStatus.FAILED,
            AnalysisStatus.CANCELLED,
        }


class EvidenceRelation(StrEnum):
    DIRECT_SUPPORT = "direct_support"
    PARTIAL_SUPPORT = "partial_support"
    INDIRECT_SUPPORT = "indirect_support"
    CONTRADICTS = "contradicts"
    OVERGENERALIZED = "overgeneralized"
    SCOPE_MISMATCH = "scope_mismatch"
    NO_RELEVANT_EVIDENCE = "no_relevant_evidence"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    INACCESSIBLE_SOURCE = "inaccessible_source"


class EvidenceLinkStatus(StrEnum):
    VERIFIED = "verified"
    LIMITED = "limited"
    REVIEW_REQUIRED = "review_required"
    BLOCKED = "blocked"
