import asyncio
from hashlib import sha256
from uuid import UUID

from citetrace_api.domain.enums import AnalysisStatus
from citetrace_api.domain.models import Analysis, AnalysisCreateRequest
from citetrace_api.services.workflow import transition


class AnalysisNotFoundError(LookupError):
    pass


class IdempotencyConflictError(ValueError):
    pass


class InMemoryAnalysisStore:
    def __init__(self) -> None:
        self._analyses: dict[UUID, Analysis] = {}
        self._idempotency: dict[tuple[UUID, str], tuple[str, UUID]] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _fingerprint(request: AnalysisCreateRequest) -> str:
        canonical = request.model_dump_json(exclude_none=False)
        return sha256(canonical.encode("utf-8")).hexdigest()

    async def create(
        self,
        request: AnalysisCreateRequest,
        idempotency_key: str,
    ) -> tuple[Analysis, bool]:
        key = (request.workspace_id, idempotency_key)
        fingerprint = self._fingerprint(request)
        async with self._lock:
            existing = self._idempotency.get(key)
            if existing is not None:
                existing_fingerprint, analysis_id = existing
                if existing_fingerprint != fingerprint:
                    raise IdempotencyConflictError("idempotency_key_reused_with_different_body")
                return self._analyses[analysis_id], False

            analysis = Analysis.create(request)
            self._analyses[analysis.id] = analysis
            self._idempotency[key] = (fingerprint, analysis.id)
            return analysis, True

    async def get(self, analysis_id: UUID) -> Analysis:
        async with self._lock:
            analysis = self._analyses.get(analysis_id)
            if analysis is None:
                raise AnalysisNotFoundError(str(analysis_id))
            return analysis

    async def cancel(self, analysis_id: UUID) -> Analysis:
        async with self._lock:
            analysis = self._analyses.get(analysis_id)
            if analysis is None:
                raise AnalysisNotFoundError(str(analysis_id))
            if analysis.status.terminal:
                return analysis
            cancelled = transition(analysis, AnalysisStatus.CANCELLED)
            self._analyses[analysis_id] = cancelled
            return cancelled
