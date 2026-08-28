
from src.claims.context import build_context_window


def test_build_context_window():
    ctx = build_context_window("hello")
    assert ctx.text == "hello"
