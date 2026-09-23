"""
Retrieval Service managing persistent ChromaDB connection and similarity search.
Loaded once at FastAPI lifespan startup.
"""

import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import logging
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions

from backend.app.core.config import settings
from backend.app.schemas.query import SourceItem

logger = logging.getLogger("trustai.retrieval")


class RetrievalService:
    def __init__(self, vector_store_path: str = None, collection_name: str = None):
        self.vector_store_path = vector_store_path or settings.VECTOR_STORE_PATH
        self.collection_name = collection_name or settings.COLLECTION_NAME
        self.embedding_model_name = settings.EMBEDDING_MODEL_NAME
        self.client = None
        self.collection = None
        self.is_ready = False

        self._initialize()

    def _initialize(self):
        logger.info(f"Initializing ChromaDB PersistentClient at: {self.vector_store_path}")
        if not os.path.exists(self.vector_store_path):
            logger.warning(f"Vector store directory does not exist yet: {self.vector_store_path}")

        try:
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model_name
            )
            self.client = chromadb.PersistentClient(path=self.vector_store_path)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            count = self.collection.count()
            self.is_ready = True
            logger.info(f"Connected to ChromaDB collection '{self.collection_name}' ({count} chunks indexed).")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB collection: {e}", exc_info=True)
            self.is_ready = False

    def retrieve(self, query: str, top_k: int = None) -> List[SourceItem]:
        """
        Executes semantic similarity search against the persistent ChromaDB collection.
        Returns a sorted list of SourceItem models with cosine similarity scores.
        """
        if not self.is_ready or self.collection is None:
            raise RuntimeError("Retrieval service is not initialized or vector store is missing.")

        k = top_k or settings.TOP_K
        logger.debug(f"Querying vector store for: '{query}' (top_k={k})")

        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )

        sources: List[SourceItem] = []
        if not results or not results.get("documents") or not results["documents"][0]:
            return sources

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        for doc, meta, dist in zip(docs, metas, distances):
            # Chroma returns cosine distance in [0, 2]; similarity = 1.0 - distance
            similarity = max(0.0, min(1.0, 1.0 - float(dist)))
            source_item = SourceItem(
                document=meta.get("source", "unknown"),
                title=meta.get("document_title", meta.get("source", "Document")),
                page=meta.get("page"),
                chunk_index=meta.get("chunk_index"),
                similarity=round(similarity, 4),
                snippet=doc
            )
            sources.append(source_item)

        logger.info(f"Retrieved {len(sources)} chunks (top similarity: {sources[0].similarity if sources else 0.0})")
        return sources

    def get_stats(self) -> Dict[str, Any]:
        """Returns health diagnostics for /health endpoint."""
        count = self.collection.count() if (self.collection and self.is_ready) else 0
        return {
            "status": "connected" if self.is_ready else "error",
            "collection_name": self.collection_name,
            "collection_count": count,
            "embedding_model": self.embedding_model_name
        }
