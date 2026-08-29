import math

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


def test_balanced_score_uses_geometric_mean_per_blueprint() -> None:
    """Per docs/00_MASTER_BLUEPRINT.md §13, balanced_score must be
    the geometric mean of the stage scores, not the arithmetic mean.
    The geometric mean punishes any single weak stage, which is the
    whole point of the weakest-link publish gate; the arithmetic
    mean would let a 0.0 stage hide behind several 1.0 stages.
    """
    scores = {
        "parse": 1.0,
        "reference_resolution": 1.0,
        "source_access": 1.0,
        "evidence_retrieval": 1.0,
        "relation_verification": 0.5,
        "explanation_grounding": 1.0,
    }
    vector = calculate_confidence(scores)
    expected = math.pow(0.5, 1 / 6)
    assert math.isclose(vector.balanced_score, expected, rel_tol=1e-9), (
        f"balanced_score must be geometric mean; got {vector.balanced_score}, "
        f"expected {expected} (arithmetic would have been 0.917)"
    )
    assert vector.balanced_score < 0.92, (
        f"geometric mean of these scores should be ~0.891; got {vector.balanced_score}"
    )


def test_weakest_link_dominates_publish_status() -> None:
    """The publish gate is decided by the weakest link, so a 0.2
    relation_verification must keep the analysis out of the
    'verified' state even when the other five stages are perfect."""
    scores = {
        "parse": 1.0,
        "reference_resolution": 1.0,
        "source_access": 1.0,
        "evidence_retrieval": 1.0,
        "relation_verification": 0.2,
        "explanation_grounding": 1.0,
    }
    vector = calculate_confidence(scores)
    assert vector.weakest_link == 0.2
    status = determine_publish_status(vector.weakest_link, vector.balanced_score)
    assert status != "verified", (
        f"weakest link 0.2 must not produce 'verified'; got {status}"
    )
