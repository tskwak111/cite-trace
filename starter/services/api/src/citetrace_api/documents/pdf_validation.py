from __future__ import annotations

import io
from dataclasses import dataclass
from enum import StrEnum

PDF_MAGIC = b'%PDF-'
MAX_PAGE_COUNT = 60
MAX_BYTE_COUNT = 104_857_600  # 100 MiB
IMAGE_ONLY_CHAR_THRESHOLD = 40


class PdfValidationCode(StrEnum):
    ACCEPTED = "accepted"
    INVALID_MAGIC = "invalid_magic"
    MALFORMED = "malformed_pdf"
    ENCRYPTED = "encrypted_pdf"
    PAGE_LIMIT_EXCEEDED = "page_limit_exceeded"
    BYTE_LIMIT_EXCEEDED = "byte_limit_exceeded"
    IMAGE_ONLY_UNSUPPORTED = "image_only_unsupported"


@dataclass(frozen=True, slots=True)
class PdfValidationReport:
    accepted: bool
    code: PdfValidationCode
    page_count: int | None
    extracted_character_count: int


def validate_pdf(data: bytes) -> PdfValidationReport:
    # Check byte limit first
    if len(data) > MAX_BYTE_COUNT:
        return PdfValidationReport(accepted=False, code=PdfValidationCode.BYTE_LIMIT_EXCEEDED, page_count=None, extracted_character_count=0)
    # Check magic bytes
    if not data.startswith(PDF_MAGIC):
        return PdfValidationReport(accepted=False, code=PdfValidationCode.INVALID_MAGIC, page_count=None, extracted_character_count=0)
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            return PdfValidationReport(accepted=False, code=PdfValidationCode.ENCRYPTED, page_count=None, extracted_character_count=0)
        page_count = len(reader.pages)
        if page_count > MAX_PAGE_COUNT:
            return PdfValidationReport(accepted=False, code=PdfValidationCode.PAGE_LIMIT_EXCEEDED, page_count=page_count, extracted_character_count=0)
        total_chars = sum(len(reader.pages[i].extract_text() or '') for i in range(page_count))
        if total_chars < IMAGE_ONLY_CHAR_THRESHOLD:
            return PdfValidationReport(accepted=False, code=PdfValidationCode.IMAGE_ONLY_UNSUPPORTED, page_count=page_count, extracted_character_count=total_chars)
        return PdfValidationReport(accepted=True, code=PdfValidationCode.ACCEPTED, page_count=page_count, extracted_character_count=total_chars)
    except pypdf.errors.PdfReadError:
        return PdfValidationReport(accepted=False, code=PdfValidationCode.MALFORMED, page_count=None, extracted_character_count=0)
    except Exception:
        return PdfValidationReport(accepted=False, code=PdfValidationCode.MALFORMED, page_count=None, extracted_character_count=0)
