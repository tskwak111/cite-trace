
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

class ModelTask(BaseModel):
    task_id: str
    prompt: str
    allowed_artifact_ids: List[str] = []

class ModelExecutionRecord(BaseModel):
    task_id: str
    executed_at: datetime
    prompt: str
    response: str
    success: bool
    violations: List['ModelOutputViolation'] = []

class ModelOutputViolation(BaseModel):
    rule: str
    message: str

ModelExecutionRecord.model_rebuild()

class ModelProvider:
    def call_model(self, task: ModelTask) -> str:
        raise NotImplementedError
