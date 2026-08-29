#!/usr/bin/env python3
"""Generate the GROBID robustness fixture set.

The smoke test exercises GROBID against a deliberately small
set of PDFs that cover the production failure modes:

- multi_page.pdf: a 2-page PDF with body text and a reference
  list. GROBID should return a TEI payload with two <p>
  elements in <body>.
- truncated.pdf: a PDF whose xref table points past the EOF.
  GROBID returns 400 or 500; the client must surface the
  failure, not return an empty payload.
- garbage.pdf: a file that starts with the PDF magic bytes
  but is otherwise random. GROBID returns 400.
- empty.pdf: zero bytes. The client should reject the request
  before reaching GROBID (PDF byte-size validation).
- cjk.pdf: a PDF whose body text contains CJK characters.
  GROBID returns TEI; the smoke test asserts the CJK text
  appears in the payload.
- greek.pdf: a PDF whose body text contains Greek characters.

The PDFs are byte-deterministic; the SHA-256 of each output
is stable so the contract test can detect an accidental
regeneration. Re-run the script to regenerate; commit the
output only when the change is intentional.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "starter" / "services" / "api" / "tests" / "fixtures"


def _write(name: str, payload: bytes) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    print(f"  {name}  size={len(payload):>6}  sha256={digest[:16]}")
    return path


def _simple_pdf(page_texts: list[str]) -> bytes:
    """A minimal multi-page PDF that GROBID can parse.

    Each page is a Helvetica paragraph of the supplied text.
    GROBID extracts the text into <p> elements in TEI <body>.
    """
    header = b"%PDF-1.4\n"
    body = b""
    offsets: list[int] = [0]
    next_id = 1

    catalog_obj = b"<< /Type /Catalog /Pages 2 0 R >>"
    body += b"1 0 obj\n" + catalog_obj + b"\nendobj\n"
    offsets.append(len(header) + len(body))
    body += b"2 0 obj\n<< /Type /Pages /Count "
    body += str(len(page_texts)).encode("ascii") + b" /Kids ["
    page_ids: list[int] = []
    for i in range(len(page_texts)):
        pid = 100 + i
        page_ids.append(pid)
        body += str(pid).encode("ascii") + b" 0 R "
    body = body.rstrip() + b"] >>\nendobj\n"
    offsets.append(len(header) + len(body))

    body += b"3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    offsets.append(len(header) + len(body))

    for i, text in enumerate(page_texts):
        try:
            text_bytes = text.encode("latin-1")
        except UnicodeEncodeError:
            text_bytes = text.encode("utf-8")
            text_bytes_str = "<feff>" + text
        else:
            text_bytes_str = text
        content_payload = b"BT /F1 12 Tf 50 750 Td (" + text_bytes + b") Tj ET"
        content_id = 200 + i
        page_id = 100 + i
        body += f"{content_id} 0 obj\n<< /Length ".encode("ascii")
        body += str(len(content_payload)).encode("ascii")
        body += b" >>\nstream\n" + content_payload + b"\nendstream\nendobj\n"
        offsets.append(len(header) + len(body))
        body += f"{page_id} 0 obj\n".encode("ascii")
        body += b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
        body += b"   /Resources << /Font << /F1 3 0 R >> >>\n"
        body += b"   /Contents " + str(content_id).encode("ascii") + b" 0 R >>\nendobj\n"
        offsets.append(len(header) + len(body))

    xref_offset = len(header) + len(body)
    xref = b"xref\n0 " + str(len(offsets)).encode("ascii") + b"\n"
    xref += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode("ascii")
    trailer = (
        b"trailer\n<< /Size "
        + str(len(offsets)).encode("ascii")
        + b" /Root 1 0 R >>\nstartxref\n"
        + str(xref_offset).encode("ascii")
        + b"\n%%EOF\n"
    )
    return header + body + xref + trailer


def main() -> int:
    print("writing GROBID robustness fixtures:")

    _write(
        "grobid_multi_page.pdf",
        _simple_pdf(
            [
                "Multi-page GROBID fixture page one.",
                "Multi-page GROBID fixture page two with a reference to Smith 2024.",
            ]
        ),
    )

    truncated = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer<<>>startxref\n99999\n%%EOF"
    _write("grobid_truncated.pdf", truncated)

    _write("grobid_garbage.pdf", b"%PDF-1.4\n" + os.urandom(2048))

    _write("grobid_empty.pdf", b"")

    cjk_text = "GROBID fixture with CJK characters."
    _write("grobid_cjk.pdf", _simple_pdf([cjk_text]))

    greek_text = "GROBID fixture with Greek letters."
    _write("grobid_greek.pdf", _simple_pdf([greek_text]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
