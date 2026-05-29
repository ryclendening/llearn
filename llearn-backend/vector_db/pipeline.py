import os
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from vector_db.vector_store import WeaviateVectorDB

EMBED_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500  # characters per chunk
CHUNK_OVERLAP = 50

def extract_pages(pdf_path: str) -> list[dict]:
    """Extract text from each page of a PDF."""
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page": i + 1, "text": text.strip()})
    return pages

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

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
    
    print(f"Loading model...")
    model = SentenceTransformer(EMBED_MODEL)
    
    db = WeaviateVectorDB(
        url=os.getenv("WEAVIATE_URL", "http://localhost:8080"),
        grpc_port=int(os.getenv("WEAVIATE_GRPC_PORT", "50051")),
    )
    db.ensure_schema()

    print(f"Extracting text from {pdf_path}...")
    pages = extract_pages(pdf_path)
    print(f"Found {len(pages)} pages.")

    # Build chunks across all pages
    items = []
    for page in pages:
        chunks = chunk_text(page["text"])
        for chunk in chunks:
            if chunk.strip():
                items.append({
                    "text": chunk,
                    "doc_id": doc_id,
                    "page": page["page"],
                })

    print(f"Embedding {len(items)} chunks...")
    texts = [i["text"] for i in items]
    vectors = embed(model, texts)

    batch = [
        (
            item["text"],
            vec,
            item["doc_id"],
            item["page"],
            {
                key: value
                for key, value in {
                    "class_id": class_id,
                    "material_id": material_id,
                }.items()
                if value is not None
            },
        )
        for item, vec in zip(items, vectors)
    ]

    uuids = db.add_many(items=batch)
    print(f"Inserted {len(uuids)} chunks for doc '{doc_id}'.")
    db.close()
    return uuids


if __name__ == "__main__":
    import sys
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "sample.pdf"
    ingest_pdf(pdf_path)
