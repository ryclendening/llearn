from __future__ import annotations

from document_processing.models import DocumentPage


CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks


def build_page_chunks(pages: list[DocumentPage], *, doc_id: str) -> list[dict]:
    items = []
    for page in pages:
        for chunk in chunk_text(page["text"]):
            if chunk.strip():
                items.append({
                    "text": chunk,
                    "doc_id": doc_id,
                    "page": page["page"],
                })
    return items
