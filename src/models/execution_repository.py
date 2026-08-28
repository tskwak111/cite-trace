
from typing import List
from .contracts import ModelExecutionRecord

class ModelExecutionRepository:
    def save(self, record: ModelExecutionRecord) -> None:
        raise NotImplementedError
    def get_all(self) -> List[ModelExecutionRecord]:
        raise NotImplementedError

class InMemoryModelExecutionRepository(ModelExecutionRepository):
    def __init__(self) -> None:
        self.records: List[ModelExecutionRecord] = []
        
    def save(self, record: ModelExecutionRecord) -> None:
        self.records.append(record)
        
    def get_all(self) -> List[ModelExecutionRecord]:
        return self.records
