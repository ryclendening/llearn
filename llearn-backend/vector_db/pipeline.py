"""Compatibility facade and CLI for vector ingestion."""

from document_processing.pdf import extract_pdf_pages
from vector_db.chunking import CHUNK_OVERLAP, CHUNK_SIZE, chunk_text
from vector_db.ingestion import EMBED_MODEL, embed, ingest_pdf

extract_pages = extract_pdf_pages

__all__ = [
    "CHUNK_OVERLAP",
    "CHUNK_SIZE",
    "EMBED_MODEL",
    "chunk_text",
    "embed",
    "extract_pages",
    "ingest_pdf",
]


if __name__ == "__main__":
    import sys

    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "sample.pdf"
    ingest_pdf(pdf_path)
