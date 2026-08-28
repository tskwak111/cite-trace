
from datetime import datetime

from pydantic import BaseModel


class ModelTask(BaseModel):
    task_id: str
    prompt: str
    allowed_artifact_ids: list[str] = []

class ModelExecutionRecord(BaseModel):
    task_id: str
    executed_at: datetime
    prompt: str
    response: str
    success: bool
    violations: list['ModelOutputViolation'] = []

class ModelOutputViolation(BaseModel):
    rule: str
    message: str

ModelExecutionRecord.model_rebuild()

class ModelProvider:
    def call_model(self, task: ModelTask) -> str:
        raise NotImplementedError
