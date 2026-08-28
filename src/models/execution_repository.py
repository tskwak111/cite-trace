

from .contracts import ModelExecutionRecord


class ModelExecutionRepository:
    def save(self, record: ModelExecutionRecord) -> None:
        raise NotImplementedError
    def get_all(self) -> list[ModelExecutionRecord]:
        raise NotImplementedError

class InMemoryModelExecutionRepository(ModelExecutionRepository):
    def __init__(self) -> None:
        self.records: list[ModelExecutionRecord] = []
        
    def save(self, record: ModelExecutionRecord) -> None:
        self.records.append(record)
        
    def get_all(self) -> list[ModelExecutionRecord]:
        return self.records
