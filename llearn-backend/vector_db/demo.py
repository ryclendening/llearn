"""
Weaviate full demo — insert docs + similarity search.
 
Requirements:
    pip install weaviate-client sentence-transformers
 
Run Weaviate first:
    docker compose up -d
 
Then:
    python demo.py
"""
import os
from vector_store import WeaviateVectorDB   # <-- the module you shared
from sentence_transformers import SentenceTransformer
 
# ── Config ──────────────────────────────────────────────────────────────────
WEAVIATE_URL  = os.getenv("WEAVIATE_URL",  "http://localhost:8080")
GRPC_PORT     = int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))
COLLECTION    = os.getenv("WEAVIATE_COLLECTION", "Document")
EMBED_MODEL   = "all-MiniLM-L6-v2"   # fast, 384-dim, downloads automatically
 
# ── Sample documents ─────────────────────────────────────────────────────────
DOCUMENTS = [
    {"doc_id": "doc-1", "page": 1,
     "text": "The Eiffel Tower is a wrought-iron lattice tower in Paris, France."},
    {"doc_id": "doc-1", "page": 2,
     "text": "It was constructed between 1887 and 1889 as the entrance arch for the 1889 World's Fair."},
    {"doc_id": "doc-2", "page": 1,
     "text": "Python is a high-level, general-purpose programming language."},
    {"doc_id": "doc-2", "page": 2,
     "text": "Python emphasises code readability and supports multiple programming paradigms."},
    {"doc_id": "doc-3", "page": 1,
     "text": "The Amazon rainforest is the world's largest tropical rainforest."},
    {"doc_id": "doc-3", "page": 2,
     "text": "It covers over 5.5 million km² and is home to extraordinary biodiversity."},
]
 
QUERIES = [
    "Tell me about famous landmarks in Europe",
    "What programming languages are easy to read?",
    "Where is the largest rainforest on Earth?",
]
 
 
def embed(model: SentenceTransformer, texts: list[str]) -> list[list[float]]:
    return model.encode(texts, show_progress_bar=False).tolist()
 
 
def main() -> None:
    print(f"Loading embedding model '{EMBED_MODEL}' …")
    model = SentenceTransformer(EMBED_MODEL)
    print("Model loaded.\n")
 
    db = WeaviateVectorDB(
        url=WEAVIATE_URL,
        grpc_port=GRPC_PORT,
        collection=COLLECTION,
    )
 
    # ── 1. Ensure schema ─────────────────────────────────────────────────────
    print(f"Ensuring collection '{COLLECTION}' exists …")
    db.ensure_schema()
    print("Schema ready.\n")
 
    # ── 2. Embed + insert ────────────────────────────────────────────────────
    print(f"Inserting {len(DOCUMENTS)} document chunks …")
    texts   = [d["text"]   for d in DOCUMENTS]
    vectors = embed(model, texts)
 
    items = [
        (doc["text"], vec, doc["doc_id"], doc["page"], None)
        for doc, vec in zip(DOCUMENTS, vectors)
    ]
    uuids = db.add_many(items=items)
    print(f"Inserted {len(uuids)} chunks.")
    for uid, doc in zip(uuids, DOCUMENTS):
        print(f"  [{doc['doc_id']} p{doc['page']}]  uuid={uid}  — {doc['text'][:55]}…")
    print()
 
    # ── 3. Similarity search ─────────────────────────────────────────────────
    print("=" * 60)
    print("SIMILARITY SEARCH DEMO")
    print("=" * 60)
    for query in QUERIES:
        print(f"\nQuery: \"{query}\"")
        print("-" * 50)
        [q_vec] = embed(model, [query])
        results = db.similarity_search(query_vector=q_vec, k=3)
        for rank, r in enumerate(results, 1):
            dist   = f"{r.score:.4f}" if r.score is not None else "n/a"
            doc_id = r.properties.get("document_id", "?")
            page   = r.properties.get("page", "?")
            text   = r.properties.get("text", "")
            print(f"  #{rank}  dist={dist}  [{doc_id} p{page}]  {text[:70]}")
 
    # ── Clean up ─────────────────────────────────────────────────────────────
    db.close()
    print("\nDone. Connection closed.")
 
 
if __name__ == "__main__":
    main()
