from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class WorkIdentity:
    id: UUID
    title: str

@dataclass
class WorkVersionIdentity:
    id: UUID
    work_id: UUID

@dataclass
class CandidateRecord:
    id: str
    reference_entry_id: UUID

@dataclass
class ResolutionRecord:
    reference_entry_id: UUID
    decision: Any

class ReferenceRepository:
    def __init__(self, session: Any = None) -> None:
        self.session = session
        # In-memory storage for testing fallback
        self._candidates: list[CandidateRecord] = []
        self._work_identities: dict[UUID, WorkIdentity] = {}
        self._resolutions: list[Any] = []

    async def add_candidates(self, reference_entry_id: UUID, candidates: Sequence[Any]) -> None:
        for c in candidates:
            self._candidates.append(CandidateRecord(id=c.provider_record_id, reference_entry_id=reference_entry_id))

    async def upsert_work_identity(self, identity: WorkIdentity) -> None:
        self._work_identities[identity.id] = identity

    async def append_resolution(self, decision: Any) -> None:
        self._resolutions.append(decision)

    async def current_resolution(self, reference_entry_id: UUID) -> Any:
        for res in reversed(self._resolutions):
            if hasattr(res, 'reference_entry_id') and res.reference_entry_id == reference_entry_id:
                return res
        return None
