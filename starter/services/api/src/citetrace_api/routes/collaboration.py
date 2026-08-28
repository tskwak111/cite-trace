import typing

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..collaboration.models import CreateNote, Note
from ..collaboration.notes import NotesService
from ..exports.models import ExportRequest
from ..exports.service import AnalysisExportService
from ..sharing.service import ShareService

router = APIRouter(prefix="/v1")

notes_service = NotesService()
export_service = AnalysisExportService()
share_service = ShareService()

@router.post("/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
async def create_note(note: CreateNote) -> typing.Any:
    return await notes_service.create_note(note)

@router.get("/notes", response_model=list[Note])
async def get_notes() -> typing.Any:
    return await notes_service.get_notes()

@router.post("/analyses/{id}/export")
async def export_analysis(id: str, request: ExportRequest) -> typing.Any:
    return await export_service.export_analysis(id, request.format)

class ShareRequest(BaseModel):
    target_id: str
    permissions: list[str]

@router.post("/shares", status_code=status.HTTP_201_CREATED)
async def create_share(req: ShareRequest) -> typing.Any:
    return await share_service.create_share(req.target_id, req.permissions)

@router.get("/shares/{token}")
async def resolve_share(token: str) -> typing.Any:
    try:
        return await share_service.resolve_share(token)
    except ValueError:
        raise HTTPException(status_code=404, detail="Share not found") from None

@router.delete("/shares/{share_id}")
async def revoke_share(share_id: str) -> typing.Any:
    success = await share_service.revoke_share(share_id)
    if not success:
        raise HTTPException(status_code=404, detail="Share not found")
    return {"status": "revoked"}
