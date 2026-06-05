from __future__ import annotations

import os

from sentence_transformers import SentenceTransformer

from document_processing.pdf import extract_pdf_pages
from vector_db.chunking import build_page_chunks
from vector_db.vector_store import WeaviateVectorDB


EMBED_MODEL = "all-MiniLM-L6-v2"


def embed(model: SentenceTransformer, texts: list[str]) -> list[list[float]]:
    return model.encode(texts, show_progress_bar=False).tolist()


def ingest_pdf(
    pdf_path: str,
    doc_id: str | None = None,
    *,
    class_id: str | None = None,
    material_id: int | None = None,
):
    doc_id = doc_id or os.path.basename(pdf_path)

    model = SentenceTransformer(EMBED_MODEL)
    db = WeaviateVectorDB(
        url=os.getenv("WEAVIATE_URL", "http://localhost:8080"),
        grpc_port=int(os.getenv("WEAVIATE_GRPC_PORT", "50051")),
    )
    try:
        db.ensure_schema()
        pages = extract_pdf_pages(pdf_path)
        items = build_page_chunks(pages, doc_id=doc_id)
        vectors = embed(model, [item["text"] for item in items])
        metadata = {
            key: value
            for key, value in {
                "class_id": class_id,
                "material_id": material_id,
            }.items()
            if value is not None
        }
        batch = [
            (item["text"], vector, item["doc_id"], item["page"], metadata)
            for item, vector in zip(items, vectors)
        ]
        return db.add_many(items=batch)
    finally:
        db.close()
