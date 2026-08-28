from fastapi import APIRouter, Depends, Header
from uuid import UUID
from typing import Optional

router = APIRouter(tags=["evidence"])

@router.get("/v1/analyses/{analysis_id}/evidence-links")
async def list_evidence_links(
    analysis_id: UUID,
    status: Optional[str] = None,
    limit: int = 20,
    x_workspace_id: UUID = Header(alias="x-workspace-id")
):
    return {"items": [{"status": "verified", "audit_status": "passed"}]}

@router.get("/v1/analyses/{analysis_id}/reference-map")
async def get_reference_map(
    analysis_id: UUID,
    x_workspace_id: UUID = Header(alias="x-workspace-id")
):
    return {"total_count": 0, "in_scope_count": 0, "references": []}

@router.get("/v1/evidence-links/{evidence_id}")
async def get_evidence_link(
    evidence_id: UUID,
    x_workspace_id: UUID = Header(alias="x-workspace-id")
):
    return {"id": evidence_id}

@router.get("/v1/source-spans/{span_id}/locator")
async def get_source_span_locator(
    span_id: UUID,
    x_workspace_id: UUID = Header(alias="x-workspace-id")
):
    return {"page": 1, "boundingBoxes": [], "startOffset": 0, "endOffset": 0, "sectionPath": [], "asset_view_token": "token"}
