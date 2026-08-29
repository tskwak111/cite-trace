#!/usr/bin/env python3
"""Generate the small fixture PDF used by `test_grobid_live_smoke.py`.

The fixture is a one-page PDF with a single sentence of body text
and a short references list. GROBID parses it into a TEI payload
that has a `<teiHeader>` and a `<text>` element with at least one
paragraph. Keeping the fixture small keeps the smoke test fast
(<2s on a warm container).

Run:
    uv run --with pypdf python scripts/build_grobid_fixture.py

Output:
    starter/services/api/tests/fixtures/grobid_fixture.pdf
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = (
    REPO_ROOT
    / "starter"
    / "services"
    / "api"
    / "tests"
    / "fixtures"
    / "grobid_fixture.pdf"
)

PDF_BYTES = b"""%PDF-1.4
1 0 obj
<</Type /Catalog /Pages 2 0 R>>
endobj
2 0 obj
<</Type /Pages /Kids [3 0 R] /Count 1>>
endobj
3 0 obj
<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R
   /Resources <</Font <</F1 5 0 R>>>>>>
endobj
4 0 obj
<</Length 270>>
stream
BT
/F1 12 Tf
50 750 Td
(CiteTrace fixture paper for GROBID smoke testing.) Tj
0 -18 Td
(This PDF is intentionally tiny; it exists to exercise the) Tj
0 -18 Td
(GrobidClient against a real container.) Tj
0 -36 Td
(References) Tj
0 -18 Td
(Smith, J. (2024). A short reference.) Tj
ET
endstream
endobj
5 0 obj
<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000109 00000 n
0000000201 00000 n
0000000482 00000 n
trailer
<</Size 6 /Root 1 0 R>>
startxref
545
%%EOF
"""


def main() -> int:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_bytes(PDF_BYTES)
    print(f"wrote {len(PDF_BYTES)} bytes to {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
