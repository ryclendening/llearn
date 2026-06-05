from __future__ import annotations

from collections.abc import Callable

from document_processing.models import DocumentPage


PageTextExtractor = Callable[[object], str]


def extract_pdf_pages(
    pdf_path: str,
    *,
    page_text_extractor: PageTextExtractor | None = None,
    fallback_page_text_extractor: PageTextExtractor | None = None,
) -> list[DocumentPage]:
    """
    Extract page text from a PDF.

    The page extractors are injectable so OCR fallback belongs here instead of
    being coupled to vector ingestion or example parsing.
    """
    reader = _pdf_reader(pdf_path)
    extract_text = page_text_extractor or _extract_native_page_text
    pages: list[DocumentPage] = []
    for index, page in enumerate(reader.pages):
        text = extract_text(page).strip()
        if not text and fallback_page_text_extractor is not None:
            text = fallback_page_text_extractor(page).strip()
        if text:
            pages.append({"page": index + 1, "text": text})
    return pages


def _extract_native_page_text(page: object) -> str:
    extract_text = getattr(page, "extract_text")
    return extract_text() or ""


def _pdf_reader(pdf_path: str):
    from pypdf import PdfReader

    return PdfReader(pdf_path)
