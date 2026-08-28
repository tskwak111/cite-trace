from typing import Any
from uuid import UUID


class ReferencePriorityRepository:
    def __init__(self, session: Any = None):
        self.session = session
        self._store: dict[tuple[UUID, UUID, str], dict[str, Any]] = {}

    async def save_priority(self, analysis_id: UUID, reference_entry_id: UUID, mode: str, data: dict[str, Any]) -> None:
        self._store[(analysis_id, reference_entry_id, mode)] = data

    async def get_priority(self, analysis_id: UUID, reference_entry_id: UUID, mode: str) -> dict[str, Any] | None:
        return self._store.get((analysis_id, reference_entry_id, mode))
