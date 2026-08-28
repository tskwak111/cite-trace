from uuid import uuid4

from citetrace_api.acquisition.policy import (
    AccessLevel,
    AcquisitionPolicyRequest,
    evaluate_acquisition_policy,
)


def test_user_upload():
    req = AcquisitionPolicyRequest(
        workspace_id=uuid4(),
        work_version_id=uuid4(),
        proposed_method="user_upload",
        provider_access_metadata={}
    )
    decision = evaluate_acquisition_policy(req)
    assert decision.allowed is True
    assert decision.access_level == AccessLevel.user_private_full_text

def test_publisher_oa():
    req = AcquisitionPolicyRequest(
        workspace_id=uuid4(),
        work_version_id=uuid4(),
        proposed_method="unpaywall",
        provider_access_metadata={"is_oa": True, "host_type": "publisher"}
    )
    decision = evaluate_acquisition_policy(req)
    assert decision.allowed is True
    assert decision.access_level == AccessLevel.publisher_open_full_text

def test_repository_oa():
    req = AcquisitionPolicyRequest(
        workspace_id=uuid4(),
        work_version_id=uuid4(),
        proposed_method="unpaywall",
        provider_access_metadata={"is_oa": True, "host_type": "repository"}
    )
    decision = evaluate_acquisition_policy(req)
    assert decision.allowed is True
    assert decision.access_level == AccessLevel.repository_manuscript

def test_abstract_only():
    req = AcquisitionPolicyRequest(
        workspace_id=uuid4(),
        work_version_id=uuid4(),
        proposed_method="unpaywall",
        provider_access_metadata={"is_oa": False, "has_abstract": True}
    )
    decision = evaluate_acquisition_policy(req)
    assert decision.allowed is True
    assert decision.access_level == AccessLevel.abstract_only

def test_metadata_only():
    req = AcquisitionPolicyRequest(
        workspace_id=uuid4(),
        work_version_id=uuid4(),
        proposed_method="unpaywall",
        provider_access_metadata={"is_oa": False, "has_abstract": False, "has_metadata": True}
    )
    decision = evaluate_acquisition_policy(req)
    assert decision.allowed is True
    assert decision.access_level == AccessLevel.metadata_only

def test_not_accessible():
    req = AcquisitionPolicyRequest(
        workspace_id=uuid4(),
        work_version_id=uuid4(),
        proposed_method="unpaywall",
        provider_access_metadata={"is_oa": False, "has_abstract": False, "has_metadata": False}
    )
    decision = evaluate_acquisition_policy(req)
    assert decision.allowed is False
    assert decision.access_level == AccessLevel.not_accessible
