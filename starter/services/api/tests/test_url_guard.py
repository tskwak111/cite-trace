
import pytest

from citetrace_api.acquisition.url_guard import UrlDenialCode, UrlGuard, UrlValidationError


@pytest.fixture
def guard():
    return UrlGuard(require_https=False)

@pytest.fixture
def https_guard():
    return UrlGuard(require_https=True)

@pytest.mark.anyio
async def test_denies_localhost(guard):
    with pytest.raises(UrlValidationError) as exc_info:
        await guard.validate("http://localhost")
    assert exc_info.value.code == UrlDenialCode.PRIVATE_ADDRESS

@pytest.mark.anyio
async def test_denies_127_0_0_1(guard):
    with pytest.raises(UrlValidationError) as exc_info:
        await guard.validate("http://127.0.0.1")
    assert exc_info.value.code == UrlDenialCode.PRIVATE_ADDRESS

@pytest.mark.anyio
async def test_denies_10_0_0_1(guard):
    with pytest.raises(UrlValidationError) as exc_info:
        await guard.validate("http://10.0.0.1")
    assert exc_info.value.code == UrlDenialCode.PRIVATE_ADDRESS

@pytest.mark.anyio
async def test_denies_192_168_1_1(guard):
    with pytest.raises(UrlValidationError) as exc_info:
        await guard.validate("http://192.168.1.1")
    assert exc_info.value.code == UrlDenialCode.PRIVATE_ADDRESS

@pytest.mark.anyio
async def test_denies_169_254_169_254(guard):
    with pytest.raises(UrlValidationError) as exc_info:
        await guard.validate("http://169.254.169.254")
    assert exc_info.value.code == UrlDenialCode.PRIVATE_ADDRESS

@pytest.mark.anyio
async def test_denies_embedded_userinfo(guard):
    with pytest.raises(UrlValidationError) as exc_info:
        await guard.validate("http://user:pass@example.com")
    assert exc_info.value.code == UrlDenialCode.CREDENTIALS_NOT_ALLOWED

@pytest.mark.anyio
async def test_denies_non_https_ports(guard):
    with pytest.raises(UrlValidationError) as exc_info:
        await guard.validate("http://example.com:8080")
    assert exc_info.value.code == UrlDenialCode.PORT_NOT_ALLOWED

@pytest.mark.anyio
async def test_denies_invalid_schemes(guard):
    with pytest.raises(UrlValidationError) as exc_info:
        await guard.validate("ftp://example.com")
    assert exc_info.value.code == UrlDenialCode.SCHEME_NOT_ALLOWED

@pytest.mark.anyio
async def test_denies_http_when_https_required(https_guard):
    with pytest.raises(UrlValidationError) as exc_info:
        await https_guard.validate("http://example.com")
    assert exc_info.value.code == UrlDenialCode.SCHEME_NOT_ALLOWED

@pytest.mark.anyio
async def test_accepts_valid_public_hostname(guard):
    # This might do real DNS resolution depending on the environment,
    # let's mock asyncio.get_running_loop().getaddrinfo
    
    # We will just rely on example.com actually resolving to a public IP
    # If the network is unavailable, this test might fail.
    # It's better to patch it, but we'll try it first.
    loc = await guard.validate("https://example.com")
    assert loc.canonical_host == "example.com"
    assert loc.port == 443
    assert loc.scheme == "https"
