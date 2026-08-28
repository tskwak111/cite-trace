from typing import Any


class EvidenceCandidateRepository:
    def __init__(self) -> None:
        self.storage: dict[str, dict[str, Any]] = {}

    def save(self, id: str, data: dict[str, Any]) -> None:
        self.storage[id] = data

    def get(self, id: str) -> dict[str, Any] | None:
        return self.storage.get(id)
