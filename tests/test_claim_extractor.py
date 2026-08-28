
from src.claims.extractor import ClaimExtractor
from src.models.execution_repository import InMemoryModelExecutionRepository
from src.models.gateway import FakeModelProvider, ModelGateway
from src.models.privacy import PrivacyPolicy


def test_claim_extractor():
    gateway = ModelGateway(FakeModelProvider(), InMemoryModelExecutionRepository(), PrivacyPolicy())
    extractor = ClaimExtractor(gateway)
    outcome = extractor.extract("some text")
    assert len(outcome.claims) == 1
