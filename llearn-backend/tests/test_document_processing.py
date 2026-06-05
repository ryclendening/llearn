from __future__ import annotations

import unittest
from unittest.mock import patch

from document_processing.pdf import extract_pdf_pages
from document_processing.text import clean_extracted_text


class DocumentProcessingTests(unittest.TestCase):
    def test_pdf_page_extractor_is_injectable_and_skips_empty_pages(self):
        reader = type("Reader", (), {"pages": ["first", "empty", "third"]})()

        with patch("document_processing.pdf._pdf_reader", return_value=reader):
            pages = extract_pdf_pages(
                "material.pdf",
                page_text_extractor=lambda page: "" if page == "empty" else f"text from {page}",
            )

        self.assertEqual(
            pages,
            [
                {"page": 1, "text": "text from first"},
                {"page": 3, "text": "text from third"},
            ],
        )

    def test_clean_extracted_text_normalizes_common_artifacts(self):
        self.assertEqual(clean_extracted_text("w h e n  ﬁve\u2212two\x00"), "when five-two-")

    def test_pdf_page_extractor_uses_fallback_for_empty_native_text(self):
        reader = type("Reader", (), {"pages": ["native", "scanned"]})()

        with patch("document_processing.pdf._pdf_reader", return_value=reader):
            pages = extract_pdf_pages(
                "material.pdf",
                page_text_extractor=lambda page: "native text" if page == "native" else "",
                fallback_page_text_extractor=lambda page: f"ocr text from {page}",
            )

        self.assertEqual(pages[1], {"page": 2, "text": "ocr text from scanned"})


if __name__ == "__main__":
    unittest.main()
