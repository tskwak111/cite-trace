import typing

from fastapi import APIRouter, Depends, status

from citetrace_api.security.auth import WorkspacePrincipal, current_principal

from ..db.repositories.feedback import FeedbackRepository
from ..feedback.models import AdjudicationItem, FeedbackRecord, FeedbackSubmission
from ..feedback.service import FeedbackService

router = APIRouter(prefix="/v1")

_repo = FeedbackRepository()

def get_feedback_service() -> FeedbackService:
    return FeedbackService(_repo)

@router.post("/feedback", response_model=FeedbackRecord, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    submission: FeedbackSubmission,
    service: FeedbackService = Depends(get_feedback_service),
    principal: WorkspacePrincipal = Depends(current_principal),
) -> typing.Any:
    return await service.submit_feedback(submission)

@router.get("/adjudication-queue", response_model=list[AdjudicationItem])
async def get_adjudication_queue(
    service: FeedbackService = Depends(get_feedback_service),
    principal: WorkspacePrincipal = Depends(current_principal),
) -> typing.Any:
    return await service.get_adjudication_queue()
