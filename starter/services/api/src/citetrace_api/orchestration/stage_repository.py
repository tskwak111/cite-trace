import datetime
from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class StageAttempt:
    id: UUID
    analysis_run_id: UUID | None
    stage_name: str
    fingerprint: str
    status: str
    output_artifact_ids: list[UUID] | None = None
    error_code: str | None = None
    error_detail: str | None = None
    created_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None


class StageRepository:
    def __init__(self) -> None:
        self._attempts: dict[str, StageAttempt] = {}

    def begin(
        self, analysis_run_id: UUID | None, stage_name: str, fingerprint: str
    ) -> StageAttempt:
        key = f"{stage_name}:{fingerprint}"
        if key in self._attempts:
            return self._attempts[key]

        attempt = StageAttempt(
            id=uuid4(),
            analysis_run_id=analysis_run_id,
            stage_name=stage_name,
            fingerprint=fingerprint,
            status="running",
            created_at=datetime.datetime.now(datetime.UTC),
        )
        self._attempts[key] = attempt
        return attempt

    def succeed(self, attempt_id: UUID, output_artifact_ids: list[UUID]) -> None:
        for attempt in self._attempts.values():
            if attempt.id == attempt_id:
                attempt.status = "success"
                attempt.output_artifact_ids = output_artifact_ids
                attempt.completed_at = datetime.datetime.now(datetime.UTC)

    def limit(self, attempt_id: UUID, code: str, output_artifact_ids: list[UUID]) -> None:
        for attempt in self._attempts.values():
            if attempt.id == attempt_id:
                attempt.status = "limited"
                attempt.error_code = code
                attempt.output_artifact_ids = output_artifact_ids
                attempt.completed_at = datetime.datetime.now(datetime.UTC)

    def fail(self, attempt_id: UUID, code: str, safe_detail: str) -> None:
        for attempt in self._attempts.values():
            if attempt.id == attempt_id:
                attempt.status = "failed"
                attempt.error_code = code
                attempt.error_detail = safe_detail
                attempt.completed_at = datetime.datetime.now(datetime.UTC)
