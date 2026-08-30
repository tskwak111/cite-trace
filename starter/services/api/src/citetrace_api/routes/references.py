from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from citetrace_api.security.auth import WorkspacePrincipal, current_principal

router = APIRouter(prefix="/v1/references", tags=["references"])


class ConfirmResolutionRequest(BaseModel):
    candidate_id: str
    reason: str | None = None


@router.post("/{reference_entry_id}:confirm-resolution")
async def confirm_resolution(
    reference_entry_id: UUID,
    request: ConfirmResolutionRequest,
    principal: WorkspacePrincipal = Depends(current_principal),
) -> dict[str, str]:
    return {"status": "user_confirmed"}


@router.get("/{reference_entry_id}/candidates")
async def get_candidates(
    reference_entry_id: UUID,
    principal: WorkspacePrincipal = Depends(current_principal),
) -> dict[str, list[Any]]:
    return {"candidates": []}
