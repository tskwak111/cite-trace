"""Live GROBID smoke test.

This test runs only when a GROBID endpoint is reachable at the URL
configured in `CITETRACE_GROBID_URL` (or the default
`http://localhost:8070`). It exercises the real `GrobidClient`
against a small fixture PDF and asserts the response is a valid
TEI-XML payload with the expected element.

In CI, a job spins up the GROBID container before running this
test; locally, you can run it with:

    docker run --rm -p 8070:8070 grobid/grobid:0.9.1-crf &
    CITETRACE_GROBID_URL=http://localhost:8070 pytest -q \\
        starter/services/api/tests/test_grobid_live_smoke.py
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import httpx
import pytest

from citetrace_api.parsing.grobid_client import GrobidClient

FIXTURE_PDF = Path(__file__).parent / "fixtures" / "grobid_fixture.pdf"
LIVE_GROBID_URL = os.environ.get(
    "CITETRACE_GROBID_URL", "http://localhost:8070"
)


def _grobid_alive() -> bool:
    try:
        response = httpx.get(f"{LIVE_GROBID_URL}/api/isalive", timeout=2.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


@pytest.fixture(scope="module")
def grobid_alive() -> bool:
    return _grobid_alive()


def test_fixture_pdf_exists() -> None:
    assert FIXTURE_PDF.exists(), (
        f"GROBID fixture PDF missing at {FIXTURE_PDF}. "
        "Generate it with the helper script in scripts/build_grobid_fixture.py"
    )


@pytest.mark.skipif(
    "_grobid_alive" not in globals() or not _grobid_alive(),
    reason=(
        f"GROBID not reachable at {LIVE_GROBID_URL}; start a GROBID 0.9.1 "
        "container (see starter/compose.yaml) and re-run with "
        "CITETRACE_GROBID_URL set."
    ),
)
def test_live_grobid_health() -> None:
    """The /api/isalive endpoint must respond before we trust the parser."""
    response = httpx.get(f"{LIVE_GROBID_URL}/api/isalive", timeout=2.0)
    assert response.status_code == 200
    assert response.text.strip().lower() == "true"


@pytest.mark.skipif(
    "_grobid_alive" not in globals() or not _grobid_alive(),
    reason=(
        f"GROBID not reachable at {LIVE_GROBID_URL}; start a GROBID 0.9.1 "
        "container (see starter/compose.yaml) and re-run with "
        "CITETRACE_GROBID_URL set."
    ),
)
@pytest.mark.anyio
async def test_live_grobid_parses_fixture_pdf() -> None:
    pdf_bytes = FIXTURE_PDF.read_bytes()
    assert len(pdf_bytes) > 100, "fixture PDF is suspiciously small"

    os.environ["CITETRACE_GROBID_URL"] = LIVE_GROBID_URL
    client = GrobidClient()
    result = await client.process_fulltext(pdf_bytes)

    assert result.status == "success"
    assert result.tei_xml, "GROBID returned an empty TEI payload"
    assert b"<TEI" in result.tei_xml, (
        f"GROBID did not return TEI-XML; got {result.tei_xml[:200]!r}"
    )
    assert b"<teiHeader" in result.tei_xml, (
        "GROBID TEI payload is missing teiHeader; the parser may be misconfigured"
    )
    assert result.timings_ms.get("grobid_ms", 0) > 0


@pytest.mark.skipif(
    "_grobid_alive" not in globals() or not _grobid_alive(),
    reason=(
        f"GROBID not reachable at {LIVE_GROBID_URL}; start a GROBID 0.9.1 "
        "container (see starter/compose.yaml) and re-run with "
        "CITETRACE_GROBID_URL set."
    ),
)
@pytest.mark.anyio
async def test_live_grobid_400_on_invalid_pdf() -> None:
    os.environ["CITETRACE_GROBID_URL"] = LIVE_GROBID_URL
    client = GrobidClient()
    with pytest.raises(Exception):
        await client.process_fulltext(b"not a pdf")
