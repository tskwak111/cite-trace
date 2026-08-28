from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Header, Request, Response, UploadFile, status
from pydantic import BaseModel

from citetrace_api.config import get_settings
from citetrace_api.documents.models import RegisterUpload
from citetrace_api.documents.pdf_validation import PdfValidationCode
from citetrace_api.documents.registry import DocumentRegistry
from citetrace_api.domain.errors import ProblemException
from citetrace_api.domain.models import ProblemDetails

router = APIRouter(prefix="/v1/documents", tags=["Documents"])


class SourceAssetResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    sha256: str
    media_type: str
    byte_size: int
    access_level: str
    security_scan_status: str
    created_at: datetime


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    response: Response,
    file: Annotated[UploadFile, File(...)],
    x_workspace_id: Annotated[UUID, Header()],
    idempotency_key: Annotated[str, Header()],
) -> SourceAssetResponse:
    if file.content_type != "application/pdf":
        raise ProblemException(
            ProblemDetails(
                title="Unsupported Media Type",
                status=415,
                detail="Only PDF files are supported.",
                code="unsupported_media_type",
            )
        )

    settings = get_settings()
    data = await file.read(settings.maximum_upload_bytes + 1)
    if len(data) > settings.maximum_upload_bytes:
        raise ProblemException(
            ProblemDetails(
                title="Payload Too Large",
                status=413,
                detail="The uploaded file exceeds the maximum allowed size.",
                code="upload_too_large",
            )
        )

    idem_key = (str(x_workspace_id), idempotency_key)
    if idem_key in request.app.state.upload_idempotency:
        cached_res = request.app.state.upload_idempotency[idem_key]
        response.status_code = status.HTTP_200_OK
        return SourceAssetResponse(**cached_res)

    registry = DocumentRegistry(store=request.app.state.fake_object_store)
    now = datetime.now(UTC)
    retention_expires_at = now + timedelta(days=30)
    upload_req = RegisterUpload(
        workspace_id=x_workspace_id,
        original_filename=file.filename or "unknown.pdf",
        media_type="application/pdf",
        data=data,
        retention_expires_at=retention_expires_at,
    )

    try:
        asset = await registry.register_upload(upload_req)
    except ValueError as e:
        error_msg = str(e)
        if PdfValidationCode.INVALID_MAGIC in error_msg or PdfValidationCode.MALFORMED in error_msg:
            code = "pdf_validation_failed"
        elif PdfValidationCode.ENCRYPTED in error_msg:
            code = "pdf_encrypted"
        elif PdfValidationCode.PAGE_LIMIT_EXCEEDED in error_msg:
            code = "pdf_page_limit_exceeded"
        elif PdfValidationCode.BYTE_LIMIT_EXCEEDED in error_msg:
            code = "upload_too_large"
        elif PdfValidationCode.IMAGE_ONLY_UNSUPPORTED in error_msg:
            raise ProblemException(
                ProblemDetails(
                    title="Unprocessable Entity",
                    status=422,
                    detail=error_msg,
                    code="pdf_image_only_unsupported",
                    recoverable_actions=["upload_born_digital_pdf"],
                )
            ) from e
        else:
            code = "pdf_validation_failed"

        status_code = 413 if code == "upload_too_large" else 422
        raise ProblemException(
            ProblemDetails(
                title="Validation Failed",
                status=status_code,
                detail=error_msg,
                code=code,
            )
        ) from e

    outbox = request.app.state.in_memory_outbox
    outbox.add_event(
        event_type="document.source.registered",
        aggregate_id=asset.id,
        workspace_id=x_workspace_id,
        payload={
            "source_asset_id": str(asset.id),
            "workspace_id": str(asset.workspace_id),
            "sha256": asset.sha256,
            "byte_size": asset.byte_size,
            "acquisition_method": asset.acquisition_method,
        },
    )

    resp = SourceAssetResponse(
        id=asset.id,
        workspace_id=asset.workspace_id,
        sha256=asset.sha256,
        media_type=asset.media_type,
        byte_size=asset.byte_size,
        access_level=asset.access_level,
        security_scan_status=asset.security_scan_status,
        created_at=asset.created_at,
    )

    request.app.state.upload_idempotency[idem_key] = resp.model_dump(mode="json")

    return resp


class DocumentStatusResponse(BaseModel):
    status: str
    latest_quality_grade: str | None = None
    limitations: list[str] | None = None
    access_level: str | None = None


@router.get("/{source_asset_id}")
async def get_document(
    request: Request,
    source_asset_id: UUID,
) -> DocumentStatusResponse:
    # We can query the Outbox and ParsedDocuments to infer state
    outbox = request.app.state.in_memory_outbox
    events = outbox.events_for_aggregate(source_asset_id)
    
    status = "registered"
    quality_grade = None
    limitations = None
    
    for e in events:
        t = e["event_type"]
        if t == "document.parsing.failed":
            status = "failed"
            limitations = [e["payload"]["failure_reason"]]
        elif t == "document.parsing.limited":
            status = "parsed_with_limits"
            quality_grade = e["payload"]["quality_grade"]
            limitations = [e["payload"]["limitation_reason"]]
        elif t == "document.parsed":
            status = "parsed"
            quality_grade = e["payload"]["quality_grade"]
            
    if status == "registered" and any(e["event_type"] == "document.source.registered" for e in events):
        # We can assume it's parsing if registered but not parsed/failed
        status = "parsing"
            
    return DocumentStatusResponse(
        status=status,
        latest_quality_grade=quality_grade,
        limitations=limitations,
        access_level="user_private_full_text"
    )
