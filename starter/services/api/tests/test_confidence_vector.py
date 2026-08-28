from citetrace_api.calibration.confidence import calculate_confidence
from citetrace_api.calibration.profiles import determine_publish_status


def test_confidence():
    scores = {
        "parse": 0.9,
        "reference_resolution": 0.9,
        "source_access": 0.9,
        "evidence_retrieval": 0.9,
        "relation_verification": 0.9,
        "explanation_grounding": 0.9,
    }
    vector = calculate_confidence(scores)
    assert vector.weakest_link == 0.9
    status = determine_publish_status(vector.weakest_link, vector.balanced_score)
    assert status == "verified"
