from citetrace_api.verification.relations import EvidenceRelation
from citetrace_api.verification.service import RelationVerificationService


def test_verifier_no_access():
    service = RelationVerificationService()
    res = service.verify("not_accessible", [])
    assert res.relation == EvidenceRelation.inaccessible_source
