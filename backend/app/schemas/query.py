"""
Pydantic Schemas for API Requests, Responses, Citations, and Health Status.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SourceItem(BaseModel):
    """Represents a single retrieved chunk with provenance metadata and similarity score."""
    document: str = Field(..., description="Filename of source PDF")
    title: Optional[str] = Field(None, description="Clean document title")
    page: Optional[int] = Field(None, description="Page number where chunk originates")
    chunk_index: Optional[int] = Field(None, description="Sequential index of chunk on page")
    similarity: float = Field(..., description="Normalized cosine similarity score (0.0 to 1.0)")
    snippet: str = Field(..., description="Verbatim extracted text excerpt")


class QueryRequest(BaseModel):
    """User question payload."""
    question: str = Field(
        ...,
        min_length=2,
        max_length=1500,
        description="User compliance question"
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Optional override for number of retrieved chunks"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "What AI practices are prohibited under the EU AI Act?",
                "top_k": 3
            }
        }
    }


class QueryResponse(BaseModel):
    """Grounded answer with verifiable citations."""
    answer: str = Field(..., description="Grounded answer generated from retrieved context")
    sources: List[SourceItem] = Field(..., description="List of cited source chunks")
    retrieval_count: int = Field(..., description="Number of sources retrieved")
    latency_ms: float = Field(..., description="Total processing time in milliseconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": "Under Article 5 of the EU AI Act, prohibited AI practices include cognitive behavioral manipulation, social scoring by public authorities, vulnerability exploitation, individual predictive policing, untargeted facial recognition scraping, and emotion recognition in workplaces and educational institutions [EU_AI_Act_Key_Obligations.pdf, Page 1].",
                "sources": [
                    {
                        "document": "EU_AI_Act_Key_Obligations.pdf",
                        "title": "EU AI Act Key Obligations",
                        "page": 1,
                        "chunk_index": 0,
                        "similarity": 0.803,
                        "snippet": "Article 5 explicitly prohibits AI practices deemed unacceptable..."
                    }
                ],
                "retrieval_count": 1,
                "latency_ms": 124.5
            }
        }
    }


class HealthResponse(BaseModel):
    """System health and vector database readiness status."""
    status: str = Field(...)
    vector_store: str = Field(...)
    collection_name: str
    collection_count: int
    embedding_model: str
    ollama_model: str
    version: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "vector_store": "connected",
                "collection_name": "trustai_compliance_docs",
                "collection_count": 272,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "ollama_model": "llama3.2:3b",
                "version": "1.0.0"
            }
        }
    }
