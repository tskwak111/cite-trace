
from src.models.contracts import ModelTask
from src.models.gateway import ModelGateway

from .models import ClaimExtractionOutcome, ExtractedClaim


class ClaimExtractor:
    def __init__(self, gateway: ModelGateway):
        self.gateway = gateway
        
    def extract(self, text: str) -> ClaimExtractionOutcome:
        task = ModelTask(task_id="extract", prompt=text)
        _res = self.gateway.execute(task)
        return ClaimExtractionOutcome(claims=[ExtractedClaim(text="test claim")])
