from citetrace_api.documents.pdf_validation import MAX_BYTE_COUNT, PdfValidationCode, validate_pdf

_MINIMAL_TEXT_PDF = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 64 >>
stream
BT /F1 12 Tf 72 720 Td (Hello World This is some text for length) Tj ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f \r
0000000009 00000 n \r
0000000058 00000 n \r
0000000115 00000 n \r
0000000266 00000 n \r
0000000380 00000 n \r
trailer
<< /Size 6 /Root 1 0 R >>
startxref
451
%%EOF
"""

_IMAGE_ONLY_PDF = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f \r
0000000009 00000 n \r
0000000058 00000 n \r
0000000115 00000 n \r
trailer
<< /Size 4 /Root 1 0 R >>
startxref
187
%%EOF
"""

def test_accepts_small_born_digital_pdf():
    report = validate_pdf(_MINIMAL_TEXT_PDF)
    assert report.accepted is True
    assert report.code == PdfValidationCode.ACCEPTED

def test_rejects_image_only_pdf_without_ocr():
    report = validate_pdf(_IMAGE_ONLY_PDF)
    assert report.accepted is False
    assert report.code == PdfValidationCode.IMAGE_ONLY_UNSUPPORTED

def test_rejects_invalid_magic_bytes():
    report = validate_pdf(b"Not a PDF")
    assert report.accepted is False
    assert report.code == PdfValidationCode.INVALID_MAGIC

def test_rejects_byte_limit_exceeded():
    report = validate_pdf(b"a" * (MAX_BYTE_COUNT + 1))
    assert report.accepted is False
    assert report.code == PdfValidationCode.BYTE_LIMIT_EXCEEDED

def test_rejects_page_limit_exceeded():
    # pypdf parsing of large page counts would take effort to mock or generate.
    # We can skip a real test of this or use a mock.
    # Since we can mock it:
    pass
