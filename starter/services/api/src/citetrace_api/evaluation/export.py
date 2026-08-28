from typing import Any

from pydantic import BaseModel


class ExportPolicy(BaseModel):
    include_private_quotes: bool = False
    anonymize_users: bool = True

class EvaluationCaseRecord(BaseModel):
    case_id: str
    citing_claim: dict[str, Any]
    cited_source: dict[str, Any]
    citation_intents: list[str]
    evidence_relation: str
    transformations: list[str]
    confidence_vector: dict[str, Any]
    audit_status: str
    limitations: list[str]

class EvaluationExporter:
    def __init__(self, policy: ExportPolicy):
        self.policy = policy

    def export(self, cases: list[dict[str, Any]]) -> list[EvaluationCaseRecord]:
        records = []
        for case in cases:
            # We would exclude secrets, db internals, private full-text here
            records.append(EvaluationCaseRecord(
                case_id=case["case_id"],
                citing_claim=case["citing_claim"],
                cited_source=case["cited_source"],
                citation_intents=case["citation_intents"],
                evidence_relation=case["evidence_relation"],
                transformations=case["transformations"],
                confidence_vector=case["confidence_vector"],
                audit_status=case["audit_status"],
                limitations=case["limitations"]
            ))
        return records
