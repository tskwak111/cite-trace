import httpx
import pytest
import respx

from citetrace_api.providers.http import ProviderHttpClient


@pytest.fixture
def mock_clock():
    times = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]

    def clock():
        return times.pop(0) if times else 0.7

    return clock


@pytest.fixture
def mock_sleeper():
    sleeps = []

    async def sleeper(seconds):
        sleeps.append(seconds)

    sleeper.sleeps = sleeps
    return sleeper


@pytest.mark.anyio
@respx.mock
async def test_provider_http_success(mock_clock, mock_sleeper) -> None:
    respx.get("https://api.example.com/test").respond(status_code=200, json={"result": "ok"})

    async with httpx.AsyncClient() as client:
        http_client = ProviderHttpClient(
            client=client, clock=mock_clock, sleeper=mock_sleeper, max_retries=1
        )
        response = await http_client.get_json(
            provider="example",
            url="https://api.example.com/test",
            trace_id="test-trace",
            maximum_bytes=1000,
        )
        assert response.status_code == 200
        assert response.data == {"result": "ok"}
        assert response.error_code is None
        assert response.latency_ms == 100


@pytest.mark.anyio
@respx.mock
async def test_provider_http_retry_429(mock_clock, mock_sleeper) -> None:
    route = respx.get("https://api.example.com/test")
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "2.5"}),
        httpx.Response(200, json={"result": "ok"}),
    ]

    async with httpx.AsyncClient() as client:
        http_client = ProviderHttpClient(
            client=client, clock=mock_clock, sleeper=mock_sleeper, max_retries=1
        )
        response = await http_client.get_json(
            provider="example",
            url="https://api.example.com/test",
            trace_id="test-trace",
            maximum_bytes=1000,
        )
        assert response.status_code == 200
        assert response.data == {"result": "ok"}
        assert mock_sleeper.sleeps == [2.5]
        assert route.call_count == 2


@pytest.mark.anyio
@respx.mock
async def test_provider_http_no_retry_400(mock_clock, mock_sleeper) -> None:
    route = respx.get("https://api.example.com/test")
    route.side_effect = [httpx.Response(400, json={"error": "bad request"})]

    async with httpx.AsyncClient() as client:
        http_client = ProviderHttpClient(
            client=client, clock=mock_clock, sleeper=mock_sleeper, max_retries=1
        )
        response = await http_client.get_json(
            provider="example",
            url="https://api.example.com/test",
            trace_id="test-trace",
            maximum_bytes=1000,
        )
        assert response.status_code == 400
        assert response.error_code == "client_error"
        assert len(mock_sleeper.sleeps) == 0
        assert route.call_count == 1
