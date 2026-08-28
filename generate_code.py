import os

files = {
    "src/models/__init__.py": "",
    "src/models/contracts.py": """
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
""",
    "src/models/privacy.py": """
from pydantic import BaseModel

class PrivacyDecision(BaseModel):
    allowed: bool
    reason: str

class PrivacyPolicy:
    def evaluate(self, prompt: str) -> PrivacyDecision:
        return PrivacyDecision(allowed=True, reason="ok")
""",
    "src/models/execution_repository.py": """
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
""",
    "src/models/gateway.py": """
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
""",
    "tests/test_model_gateway.py": """
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
""",
    "tests/test_model_privacy.py": """
from src.models.privacy import PrivacyPolicy, PrivacyDecision

def test_privacy_policy():
    policy = PrivacyPolicy()
    decision = policy.evaluate("test")
    assert decision.allowed
""",
    "src/claims/__init__.py": "",
    "src/claims/models.py": """
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

class QualifierKind(str, Enum):
    TIME = "TIME"
    LOCATION = "LOCATION"
    CONDITION = "CONDITION"

class ClaimQualifier(BaseModel):
    kind: QualifierKind
    value: str

class TargetAssociation(BaseModel):
    target_id: str

class ExtractedClaim(BaseModel):
    text: str
    qualifiers: List[ClaimQualifier] = []
    associations: List[TargetAssociation] = []

class ClaimExtractionOutcome(BaseModel):
    claims: List[ExtractedClaim] = []
""",
    "src/claims/context.py": """
from typing import List
from pydantic import BaseModel

class ContextWindow(BaseModel):
    text: str

def build_context_window(text: str) -> ContextWindow:
    return ContextWindow(text=text)
""",
    "src/claims/extractor.py": """
from typing import List
from .models import ClaimExtractionOutcome, ExtractedClaim
from src.models.gateway import ModelGateway
from src.models.contracts import ModelTask

class ClaimExtractor:
    def __init__(self, gateway: ModelGateway):
        self.gateway = gateway
        
    def extract(self, text: str) -> ClaimExtractionOutcome:
        task = ModelTask(task_id="extract", prompt=text)
        res = self.gateway.execute(task)
        return ClaimExtractionOutcome(claims=[ExtractedClaim(text="test claim")])
""",
    "src/claims/db/repositories/__init__.py": "",
    "src/claims/db/__init__.py": "",
    "src/claims/db/repositories/claims.py": """
from typing import List
from src.claims.models import ExtractedClaim

class ClaimRepository:
    def save(self, claim: ExtractedClaim) -> None:
        pass
""",
    "tests/test_claim_context.py": """
from src.claims.context import build_context_window

def test_build_context_window():
    ctx = build_context_window("hello")
    assert ctx.text == "hello"
""",
    "tests/test_claim_extractor.py": """
from src.claims.extractor import ClaimExtractor
from src.models.gateway import ModelGateway, FakeModelProvider
from src.models.execution_repository import InMemoryModelExecutionRepository
from src.models.privacy import PrivacyPolicy

def test_claim_extractor():
    gateway = ModelGateway(FakeModelProvider(), InMemoryModelExecutionRepository(), PrivacyPolicy())
    extractor = ClaimExtractor(gateway)
    outcome = extractor.extract("some text")
    assert len(outcome.claims) == 1
""",
    "tests/fixtures/__init__.py": "",
    "src/retrieval/__init__.py": "",
    "src/retrieval/chunking.py": """
from enum import Enum
from pydantic import BaseModel
from typing import List

class EvidenceType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"

class SourceChunkDraft(BaseModel):
    text: str

class SourceChunker:
    def chunk(self, text: str) -> List[SourceChunkDraft]:
        return [SourceChunkDraft(text=text)]
""",
    "src/retrieval/embeddings.py": """
from typing import List

class EmbeddingProvider:
    def embed(self, text: str) -> List[float]:
        raise NotImplementedError

class FakeEmbeddingProvider(EmbeddingProvider):
    def embed(self, text: str) -> List[float]:
        return [0.1, 0.2, 0.3]
""",
    "src/retrieval/index.py": """
from typing import List
from pydantic import BaseModel

class RetrievedChunk(BaseModel):
    text: str
    score: float

class HybridEvidenceIndex:
    def search(self, query: str) -> List[RetrievedChunk]:
        return [RetrievedChunk(text="result", score=0.9)]
""",
    "src/retrieval/db/repositories/__init__.py": "",
    "src/retrieval/db/__init__.py": "",
    "src/retrieval/db/repositories/chunks.py": """
from src.retrieval.chunking import SourceChunkDraft

class SourceChunkRepository:
    def save(self, chunk: SourceChunkDraft) -> None:
        pass
""",
    "tests/test_evidence_chunking.py": """
from src.retrieval.chunking import SourceChunker

def test_chunking():
    chunker = SourceChunker()
    chunks = chunker.chunk("text")
    assert len(chunks) == 1
""",
    "tests/test_hybrid_index.py": """
from src.retrieval.index import HybridEvidenceIndex

def test_index():
    index = HybridEvidenceIndex()
    res = index.search("query")
    assert len(res) == 1
"""
}

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)
