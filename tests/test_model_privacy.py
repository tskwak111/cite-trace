
from src.models.privacy import PrivacyPolicy


def test_privacy_policy():
    policy = PrivacyPolicy()
    decision = policy.evaluate("test")
    assert decision.allowed
