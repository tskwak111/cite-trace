from fastapi import APIRouter

from citetrace_api import __version__
from citetrace_api.domain.models import HealthResponse

router = APIRouter(tags=["System"])


@router.get("/healthz", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(version=__version__)
