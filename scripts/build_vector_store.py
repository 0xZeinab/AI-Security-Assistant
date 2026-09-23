"""
Build and persist the ChromaDB vector store for TrustAI Assistant.
Reads PDFs from data/raw, chunks them with metadata, computes embeddings using
sentence-transformers/all-MiniLM-L6-v2, and saves to backend/data/vector_store.
"""

import os
import pypdf
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "backend", "data", "vector_store")
COLLECTION_NAME = "trustai_compliance_docs"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100


def build_vector_store():
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    ids = []
    documents = []
    metadatas = []

    print(f"[*] Reading and chunking documents from: {RAW_DIR}")
    for fname in sorted(os.listdir(RAW_DIR)):
        if not fname.endswith(".pdf"):
            continue
        path = os.path.join(RAW_DIR, fname)
        reader = pypdf.PdfReader(path)
        doc_title = fname.replace(".pdf", "").replace("_", " ")

        for page_idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            # Clean extraction noise: normalize spaces and linebreaks
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = " ".join(lines)
            if len(clean_text) < 40:
                continue

            chunks = text_splitter.split_text(clean_text)
            for chunk_idx, chunk_str in enumerate(chunks):
                chunk_id = f"{fname}_p{page_idx}_c{chunk_idx}"
                ids.append(chunk_id)
                documents.append(chunk_str)
                metadatas.append({
                    "source": fname,
                    "document_title": doc_title,
                    "page": page_idx,
                    "chunk_index": chunk_idx,
                    "char_count": len(chunk_str)
                })

    print(f"[OK] Total chunks prepared: {len(documents)}")
    print(f"[*] Initializing Chroma persistent client at: {VECTOR_STORE_DIR}")
    print(f"[*] Embedding model: {EMBEDDING_MODEL_NAME}")

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )
    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"[*] Resetting collection '{COLLECTION_NAME}' for clean AI Security re-indexing...")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # Batch upsert to prevent memory spikes
    batch_size = 64
    print(f"[*] Upserting {len(ids)} chunks in batches of {batch_size}...")
    for i in range(0, len(ids), batch_size):
        end_idx = min(i + batch_size, len(ids))
        collection.upsert(
            ids=ids[i:end_idx],
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx]
        )
        print(f"    - Indexed {end_idx}/{len(ids)} chunks...")

    count = collection.count()
    print(f"[SUCCESS] Chroma vector store persisted successfully! Total documents: {count}")

    # Verify sample query
    print("\n[*] Verifying retrieval with sample AI Security question:")
    sample_query = "What is Prompt Injection and how can it be mitigated?"
    res = collection.query(query_texts=[sample_query], n_results=3)
    print(f"Query: '{sample_query}'")
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        similarity = 1.0 - dist
        print(f"  -> [{meta['source']} | Page {meta['page']}] (Similarity: {similarity:.4f})")
        print(f"     Snippet: {doc[:140]}...")

    return count


if __name__ == "__main__":
    build_vector_store()
