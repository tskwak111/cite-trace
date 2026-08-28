
from datetime import datetime
from typing import Optional, List
from .contracts import ModelTask, ModelExecutionRecord, ModelProvider, ModelOutputViolation
from .privacy import PrivacyPolicy
from .execution_repository import ModelExecutionRepository

class FakeModelProvider(ModelProvider):
    def __init__(self, response: str = "fake response"):
        self.response = response
        
    def call_model(self, task: ModelTask) -> str:
        return self.response

class ModelGateway:
    def __init__(self, provider: ModelProvider, repository: ModelExecutionRepository, privacy_policy: PrivacyPolicy):
        self.provider = provider
        self.repository = repository
        self.privacy_policy = privacy_policy

    def execute(self, task: ModelTask) -> str:
        decision = self.privacy_policy.evaluate(task.prompt)
        if not decision.allowed:
            raise ValueError(f"Privacy check failed: {decision.reason}")
            
        response = self.provider.call_model(task)
        
        record = ModelExecutionRecord(
            task_id=task.task_id,
            executed_at=datetime.utcnow(),
            prompt=task.prompt,
            response=response,
            success=True
        )
        self.repository.save(record)
        return response
