from citetrace_api.verification.transformations import TransformationKind


def test_transformations():
    assert TransformationKind.adopted_unchanged.value == "adopted_unchanged"
