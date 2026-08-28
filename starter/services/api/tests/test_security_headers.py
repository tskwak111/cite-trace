from citetrace_api.security.headers import get_security_headers


def test_get_security_headers_development() -> None:
    headers = get_security_headers("development")
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "unsafe-inline" in headers["Content-Security-Policy"]

def test_get_security_headers_production() -> None:
    headers = get_security_headers("production")
    assert "unsafe-inline" not in headers["Content-Security-Policy"]
    assert "default-src 'self'" in headers["Content-Security-Policy"]
