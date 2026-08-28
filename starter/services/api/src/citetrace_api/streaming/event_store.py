from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class StreamEvent:
    id: UUID
    aggregate_id: UUID
    event_type: str
    schema_version: str
    sequence: int
    occurred_at: datetime
    payload: Mapping[str, object]

class EventStore:
    async def after(self, analysis_id: UUID, last_event_id: UUID | None, limit: int) -> list[StreamEvent]:
        return []
        
    async def wait_for_new(self, analysis_id: UUID, after_sequence: int, timeout_seconds: float) -> None:
        pass
