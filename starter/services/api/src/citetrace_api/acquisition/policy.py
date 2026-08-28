from collections.abc import Mapping
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class AccessLevel(StrEnum):
    user_private_full_text = "user_private_full_text"
    open_access_full_text = "open_access_full_text"
    repository_manuscript = "repository_manuscript"
    publisher_open_full_text = "publisher_open_full_text"
    abstract_only = "abstract_only"
    metadata_only = "metadata_only"
    not_accessible = "not_accessible"

class AcquisitionPolicyRequest(BaseModel):
    workspace_id: UUID
    work_version_id: UUID
    proposed_method: str
    proposed_url: str | None = None
    provider_access_metadata: Mapping[str, object]
    intended_storage_days: int = 30

class AcquisitionPolicyDecision(BaseModel):
    allowed: bool
    access_level: AccessLevel
    reason_codes: tuple[str, ...]
    display_rule: str
    retention_days: int

def evaluate_acquisition_policy(request: AcquisitionPolicyRequest) -> AcquisitionPolicyDecision:
    if request.proposed_method == "user_upload":
        return AcquisitionPolicyDecision(
            allowed=True,
            access_level=AccessLevel.user_private_full_text,
            reason_codes=("USER_PROVIDED",),
            display_rule="Private to user",
            retention_days=request.intended_storage_days
        )
        
    meta = request.provider_access_metadata
    
    if meta.get("is_oa"):
        host_type = meta.get("host_type", "")
        if host_type == "publisher":
            return AcquisitionPolicyDecision(
                allowed=True,
                access_level=AccessLevel.publisher_open_full_text,
                reason_codes=("PUBLISHER_OA",),
                display_rule="Open Access (Publisher)",
                retention_days=request.intended_storage_days
            )
        elif host_type == "repository":
            return AcquisitionPolicyDecision(
                allowed=True,
                access_level=AccessLevel.repository_manuscript,
                reason_codes=("REPOSITORY_OA",),
                display_rule="Open Access (Repository)",
                retention_days=request.intended_storage_days
            )
        else:
            return AcquisitionPolicyDecision(
                allowed=True,
                access_level=AccessLevel.open_access_full_text,
                reason_codes=("OA_UNKNOWN_HOST",),
                display_rule="Open Access",
                retention_days=request.intended_storage_days
            )
            
    if meta.get("has_abstract"):
        return AcquisitionPolicyDecision(
            allowed=True,
            access_level=AccessLevel.abstract_only,
            reason_codes=("ABSTRACT_AVAILABLE",),
            display_rule="Abstract only",
            retention_days=request.intended_storage_days
        )
        
    if meta.get("has_metadata"):
        return AcquisitionPolicyDecision(
            allowed=True,
            access_level=AccessLevel.metadata_only,
            reason_codes=("METADATA_AVAILABLE",),
            display_rule="Metadata only",
            retention_days=request.intended_storage_days
        )
        
    return AcquisitionPolicyDecision(
        allowed=False,
        access_level=AccessLevel.not_accessible,
        reason_codes=("PAYWALLED",),
        display_rule="Not accessible",
        retention_days=0
    )
