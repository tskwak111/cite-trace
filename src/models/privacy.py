
from pydantic import BaseModel

class PrivacyDecision(BaseModel):
    allowed: bool
    reason: str

class PrivacyPolicy:
    def evaluate(self, prompt: str) -> PrivacyDecision:
        return PrivacyDecision(allowed=True, reason="ok")
