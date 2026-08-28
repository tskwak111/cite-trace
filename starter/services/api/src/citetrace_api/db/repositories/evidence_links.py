from typing import Any
from uuid import UUID


class EvidenceLinkRepository:
    def __init__(self, session: Any = None):
        self.session = session
        self._store: dict[UUID, dict[str, Any]] = {}

    async def save_evidence_link(self, evidence_link_id: UUID, data: dict[str, Any]) -> None:
        self._store[evidence_link_id] = data

    async def get_evidence_link(self, evidence_link_id: UUID) -> dict[str, Any] | None:
        return self._store.get(evidence_link_id)
