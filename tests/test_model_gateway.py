
import pytest
from src.models.contracts import ModelTask
from src.models.gateway import ModelGateway, FakeModelProvider
from src.models.execution_repository import InMemoryModelExecutionRepository
from src.models.privacy import PrivacyPolicy

def test_gateway_execution():
    provider = FakeModelProvider("hello")
    repo = InMemoryModelExecutionRepository()
    policy = PrivacyPolicy()
    gateway = ModelGateway(provider, repo, policy)
    
    task = ModelTask(task_id="1", prompt="test")
    res = gateway.execute(task)
    assert res == "hello"
    assert len(repo.get_all()) == 1
