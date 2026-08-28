"""In-memory outbox for use during testing and when no DB session is injected."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class InMemoryOutbox:
    """Thread-unsafe, test-only in-memory outbox. Never use in production."""

    _events: list[dict[str, object]] = field(default_factory=list)

    def add_event(
        self, event_type: str, aggregate_id: UUID, workspace_id: UUID, payload: dict[str, object]
    ) -> UUID:
        event_id = uuid4()
        self._events.append(
            {
                "id": event_id,
                "event_type": event_type,
                "aggregate_id": aggregate_id,
                "workspace_id": workspace_id,
                "payload": payload,
            }
        )
        return event_id

    def events_for_aggregate(self, aggregate_id: UUID) -> list[dict[str, object]]:
        return [e for e in self._events if e["aggregate_id"] == aggregate_id]

    def clear(self) -> None:
        self._events.clear()
