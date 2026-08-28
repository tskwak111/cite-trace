from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from citetrace_api import __version__
from citetrace_api.documents.storage import FakeObjectStore
from citetrace_api.domain.errors import ProblemException
from citetrace_api.orchestration.outbox import InMemoryOutbox
from citetrace_api.routes.analyses import router as analyses_router
from citetrace_api.routes.documents import router as documents_router
from citetrace_api.routes.health import router as health_router
from citetrace_api.services.job_store import InMemoryAnalysisStore


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.analysis_store = InMemoryAnalysisStore()
    app.state.fake_object_store = FakeObjectStore()
    app.state.in_memory_outbox = InMemoryOutbox()
    app.state.upload_idempotency = {}
    yield


app = FastAPI(
    title="CiteTrace API",
    version=__version__,
    summary="Evidence-first citation tracing foundation",
    lifespan=lifespan,
)
app.include_router(health_router)
app.include_router(analyses_router)
app.include_router(documents_router)


@app.exception_handler(ProblemException)
async def problem_exception_handler(
    request: Request,
    exc: ProblemException,
) -> JSONResponse:
    problem = exc.problem.model_copy(update={"instance": str(request.url.path)})
    return JSONResponse(
        status_code=problem.status,
        media_type="application/problem+json",
        content=problem.model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        media_type="application/problem+json",
        content={
            "type": "about:blank",
            "title": "Request validation failed",
            "status": 422,
            "detail": "One or more request fields are invalid.",
            "code": "request_validation_failed",
            "instance": str(request.url.path),
            "trace_id": request.headers.get("traceparent", "validation-" + str(id(request))),
            "retryable": False,
            "errors": exc.errors(),
        },
    )
