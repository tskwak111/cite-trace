from typing import Any
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/v1/references", tags=["references"])


class ConfirmResolutionRequest(BaseModel):
    candidate_id: str
    reason: str | None = None


@router.post("/{reference_entry_id}:confirm-resolution")
async def confirm_resolution(
    reference_entry_id: UUID, request: ConfirmResolutionRequest
) -> dict[str, str]:
    return {"status": "user_confirmed"}


@router.get("/{reference_entry_id}/candidates")
async def get_candidates(reference_entry_id: UUID) -> dict[str, list[Any]]:
    return {"candidates": []}
