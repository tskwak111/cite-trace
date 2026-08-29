"""GROBID robustness contract tests (Slice 11).

The Slice 4 smoke test only exercised a single happy-path
fixture. Production traffic is messy:

- PDFs are sometimes truncated, garbage, or empty.
- PDFs sometimes contain non-ASCII (CJK, Greek) characters
  that older PDF parsers mishandle.
- Multi-page PDFs are the default; a parser that only handles
  the first page is a quiet regression.

These tests assert that the `GrobidClient` behaves correctly
on each of those cases. They use `respx` for the unit tests
and the live container when reachable for the integration
tests; offline runs skip the integration tests honestly.
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest
import respx

from citetrace_api.config import get_settings
from citetrace_api.parsing.grobid_client import GrobidClient, GrobidClientError

FIXTURES_DIR = Path(__file__).parent / "fixtures"
LIVE_GROBID_URL = os.environ.get(
    "CITETRACE_GROBID_URL", "http://localhost:8070"
)


def _grobid_alive() -> bool:
    try:
        response = httpx.get(f"{LIVE_GROBID_URL}/api/isalive", timeout=2.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


@pytest.fixture
def grobid_url() -> str:
    return f"{get_settings().grobid_url}/api/processFulltextDocument"


@pytest.mark.anyio
@respx.mock
async def test_multi_page_te_payload_contains_two_pages(grobid_url: str) -> None:
    """A multi-page PDF must produce a TEI payload that mentions
    the body text from both pages. A regression that only
    parses page one would return the same teiHeader but only
    one <p> element with body text."""
    fixture = FIXTURES_DIR / "grobid_multi_page.pdf"
    assert fixture.exists(), f"{fixture.name} missing; run scripts/build_grobid_robustness_fixtures.py"
    tei = b"<TEI><teiHeader/><text><body><p>page one</p><p>page two with reference</p></body></text></TEI>"
    respx.post(grobid_url).respond(200, content=tei)
    client = GrobidClient()
    result = await client.process_fulltext(fixture.read_bytes())
    assert result.status == "success"
    assert b"<p>page one</p>" in result.tei_xml
    assert b"<p>page two" in result.tei_xml


@pytest.mark.anyio
@respx.mock
async def test_truncated_pdf_surfaces_400_or_500(grobid_url: str) -> None:
    """A truncated PDF must not silently succeed. GROBID returns
    400 (or 500 on a JVM crash); the client must raise."""
    fixture = FIXTURES_DIR / "grobid_truncated.pdf"
    assert fixture.exists()
    respx.post(grobid_url).respond(400, text="invalid xref")
    client = GrobidClient()
    with pytest.raises(GrobidClientError):
        await client.process_fulltext(fixture.read_bytes())


@pytest.mark.anyio
@respx.mock
async def test_garbage_pdf_surfaces_400(grobid_url: str) -> None:
    fixture = FIXTURES_DIR / "grobid_garbage.pdf"
    assert fixture.exists()
    respx.post(grobid_url).respond(400, text="malformed pdf")
    client = GrobidClient()
    with pytest.raises(GrobidClientError):
        await client.process_fulltext(fixture.read_bytes())


@pytest.mark.anyio
@respx.mock
async def test_empty_pdf_surfaces_400_from_grobid(grobid_url: str) -> None:
    """The empty-PDF case is a real production failure mode.
    GROBID returns 400 for an empty body; the client must
    surface the error rather than returning an empty TEI
    payload that downstream consumers would misread as
    'parsed successfully'."""
    fixture = FIXTURES_DIR / "grobid_empty.pdf"
    assert fixture.exists()
    respx.post(grobid_url).respond(400, text="empty input")
    client = GrobidClient()
    with pytest.raises(GrobidClientError):
        await client.process_fulltext(fixture.read_bytes())


@pytest.mark.anyio
@respx.mock
async def test_cjk_te_payload_preserves_codepoints(grobid_url: str) -> None:
    """GROBID returns UTF-8; the CJK codepoints must round-trip
    through the client without being mangled by the response
    reader."""
    fixture = FIXTURES_DIR / "grobid_cjk.pdf"
    assert fixture.exists()
    cjk = "標昌定義".encode()
    tei = b'<TEI><teiHeader/><text><body><p>' + cjk + b'</p></body></text></TEI>'
    respx.post(grobid_url).respond(200, content=tei)
    client = GrobidClient()
    result = await client.process_fulltext(fixture.read_bytes())
    assert result.status == "success"
    assert cjk in result.tei_xml, (
        f"CJK codepoints lost: expected {cjk!r} in {result.tei_xml!r}"
    )


@pytest.mark.anyio
@respx.mock
async def test_greek_te_payload_preserves_codepoints(grobid_url: str) -> None:
    fixture = FIXTURES_DIR / "grobid_greek.pdf"
    assert fixture.exists()
    greek = "αβγ".encode()
    tei = b'<TEI><teiHeader/><text><body><p>' + greek + b'</p></body></text></TEI>'
    respx.post(grobid_url).respond(200, content=tei)
    client = GrobidClient()
    result = await client.process_fulltext(fixture.read_bytes())
    assert result.status == "success"
    assert greek in result.tei_xml


@pytest.mark.anyio
@respx.mock
async def test_5xx_retry_with_eventual_success(grobid_url: str) -> None:
    """Two consecutive 503 responses followed by a 200 must
    surface a successful parse; the client already retries
    server errors and this test pins that contract for the
    robustness fixture set."""
    fixture = FIXTURES_DIR / "grobid_multi_page.pdf"
    assert fixture.exists()
    tei = b"<TEI><teiHeader/><text><body><p>ok</p></body></text></TEI>"
    route = respx.post(grobid_url)
    route.side_effect = [
        httpx.Response(503, headers={"Retry-After": "0"}),
        httpx.Response(503, headers={"Retry-After": "0"}),
        httpx.Response(200, content=tei),
    ]
    client = GrobidClient()
    result = await client.process_fulltext(fixture.read_bytes())
    assert result.status == "success"
    assert route.call_count == 3


@pytest.mark.skipif(
    not _grobid_alive(),
    reason=f"GROBID not reachable at {LIVE_GROBID_URL}",
)
@pytest.mark.anyio
async def test_live_grobid_parses_multi_page_pdf() -> None:
    """When a real GROBID container is reachable, the multi-page
    fixture must produce a TEI payload whose <facsimile> lists
    both pages (the `<surface n="1" .../>` and `<surface n="2"
    .../>` elements are GROBID's authoritative signal that
    both pages were recognised, even when the body text was
    not extracted). The minimal fixture PDFs generated by
    `scripts/build_grobid_robustness_fixtures.py` use
    Helvetica without proper font embedding, so GROBID
    often returns a body without text; the page count is
    the right assertion for this fixture set."""
    fixture = FIXTURES_DIR / "grobid_multi_page.pdf"
    assert fixture.exists()
    os.environ["CITETRACE_GROBID_URL"] = LIVE_GROBID_URL
    client = GrobidClient()
    result = await client.process_fulltext(fixture.read_bytes())
    assert result.status == "success"
    assert b'surface n="1"' in result.tei_xml, (
        f"GROBID did not register page 1; payload: {result.tei_xml[:200]!r}"
    )
    assert b'surface n="2"' in result.tei_xml, (
        f"GROBID did not register page 2; payload: {result.tei_xml[:200]!r}"
    )


@pytest.mark.skipif(
    not _grobid_alive(),
    reason=f"GROBID not reachable at {LIVE_GROBID_URL}",
)
@pytest.mark.anyio
async def test_live_grobid_rejects_truncated_pdf() -> None:
    fixture = FIXTURES_DIR / "grobid_truncated.pdf"
    assert fixture.exists()
    os.environ["CITETRACE_GROBID_URL"] = LIVE_GROBID_URL
    client = GrobidClient()
    with pytest.raises(GrobidClientError):
        await client.process_fulltext(fixture.read_bytes())


def test_all_robustness_fixtures_are_present() -> None:
    """A regression that drops a fixture is silent. This test
    fails when any of the expected fixtures is missing.
    `grobid_empty.pdf` is the documented zero-byte case."""
    expected = [
        ("grobid_multi_page.pdf", True),
        ("grobid_truncated.pdf", True),
        ("grobid_garbage.pdf", True),
        ("grobid_empty.pdf", False),
        ("grobid_cjk.pdf", True),
        ("grobid_greek.pdf", True),
    ]
    for name, must_be_nonempty in expected:
        path = FIXTURES_DIR / name
        assert path.exists(), f"missing fixture {name}; run scripts/build_grobid_robustness_fixtures.py"
        if must_be_nonempty:
            assert path.stat().st_size > 0, f"fixture {name} is empty"
        else:
            assert path.stat().st_size == 0, (
                f"fixture {name} must be zero bytes (the empty-PDF case)"
            )
