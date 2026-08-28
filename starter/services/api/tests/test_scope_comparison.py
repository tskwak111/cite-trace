from citetrace_api.verification.scope import compare_scope


def test_compare_scope():
    res = compare_scope({}, {})
    assert res.compatibility == "compatible"
