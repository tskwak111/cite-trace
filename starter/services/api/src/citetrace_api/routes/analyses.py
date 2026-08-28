import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, Response, status
from fastapi.responses import StreamingResponse

from citetrace_api.domain.enums import EvidenceLinkStatus, EvidenceRelation
from citetrace_api.domain.errors import ProblemException
from citetrace_api.domain.models import (
    Analysis,
    AnalysisCreateRequest,
    EvidenceLinkPage,
    ProblemDetails,
)
from citetrace_api.services.job_store import (
    AnalysisNotFoundError,
    IdempotencyConflictError,
    InMemoryAnalysisStore,
)

router = APIRouter(prefix="/v1/analyses", tags=["Analyses"])


def _store(request: Request) -> InMemoryAnalysisStore:
    from typing import cast

    return cast(InMemoryAnalysisStore, request.app.state.analysis_store)


def _problem(status_code: int, title: str, code: str, detail: str) -> ProblemException:
    return ProblemException(
        ProblemDetails(title=title, status=status_code, code=code, detail=detail)
    )


@router.post("", response_model=Analysis, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(
    command: AnalysisCreateRequest,
    request: Request,
    response: Response,
    idempotency_key: str = Header(min_length=8, max_length=255, alias="Idempotency-Key"),
) -> Analysis:
    try:
        analysis, created = await _store(request).create(command, idempotency_key)
    except IdempotencyConflictError as exc:
        raise _problem(
            status.HTTP_409_CONFLICT,
            "Idempotency conflict",
            "idempotency_conflict",
            str(exc),
        ) from exc
    response.headers["Idempotent-Replay"] = "false" if created else "true"
    return analysis


@router.get("/{analysis_id}", response_model=Analysis)
async def get_analysis(analysis_id: UUID, request: Request) -> Analysis:
    try:
        return await _store(request).get(analysis_id)
    except AnalysisNotFoundError as exc:
        raise _problem(
            status.HTTP_404_NOT_FOUND,
            "Analysis not found",
            "analysis_not_found",
            "The analysis does not exist or is not visible to this actor.",
        ) from exc


@router.post("/{analysis_id}:cancel", response_model=Analysis)
async def cancel_analysis(
    analysis_id: UUID,
    request: Request,
    idempotency_key: str = Header(min_length=8, max_length=255, alias="Idempotency-Key"),
) -> Analysis:
    del idempotency_key
    try:
        return await _store(request).cancel(analysis_id)
    except AnalysisNotFoundError as exc:
        raise _problem(
            status.HTTP_404_NOT_FOUND,
            "Analysis not found",
            "analysis_not_found",
            "The analysis does not exist or is not visible to this actor.",
        ) from exc




@router.get("/{analysis_id}/stream")
async def stream_analysis(analysis_id: UUID, request: Request) -> StreamingResponse:
    try:
        analysis = await _store(request).get(analysis_id)
    except AnalysisNotFoundError as exc:
        raise _problem(
            status.HTTP_404_NOT_FOUND,
            "Analysis not found",
            "analysis_not_found",
            "The analysis does not exist or is not visible to this actor.",
        ) from exc

    async def event_stream() -> AsyncIterator[str]:
        payload = {
            "event_id": f"analysis-{analysis.id}-{analysis.updated_at.timestamp()}",
            "event_type": "analysis.state.changed",
            "schema_version": "1.0.0",
            "aggregate_id": str(analysis.id),
            "payload": analysis.model_dump(mode="json"),
        }
        yield f"event: analysis.state.changed\ndata: {json.dumps(payload)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
