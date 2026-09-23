"""
API Routes for Health Check and Question Answering Query.
"""

import time
import logging
from fastapi import APIRouter, Request, HTTPException, status
from backend.app.schemas.query import QueryRequest, QueryResponse, HealthResponse
from backend.app.core.config import settings

logger = logging.getLogger("trustai.routes")

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="System Health & Vector Store Diagnostics")
async def health_check(request: Request):
    """
    Returns system status, persistent vector store connection state,
    collection count, and active model configurations.
    """
    retrieval_service = getattr(request.app.state, "retrieval_service", None)
    if not retrieval_service:
        return HealthResponse(
            status="degraded",
            vector_store="uninitialized",
            collection_name=settings.COLLECTION_NAME,
            collection_count=0,
            embedding_model=settings.EMBEDDING_MODEL_NAME,
            ollama_model=settings.OLLAMA_MODEL,
            version=settings.VERSION
        )

    stats = retrieval_service.get_stats()
    return HealthResponse(
        status="healthy" if stats["status"] == "connected" else "degraded",
        vector_store=stats["status"],
        collection_name=stats["collection_name"],
        collection_count=stats["collection_count"],
        embedding_model=stats["embedding_model"],
        ollama_model=settings.OLLAMA_MODEL,
        version=settings.VERSION
    )


@router.post("/query", response_model=QueryResponse, summary="Query Compliance Documents")
async def execute_query(request: Request, payload: QueryRequest):
    """
    Performs full RAG cycle:
    1. Validates query string
    2. Retrieves top-k semantically relevant chunks from persistent ChromaDB
    3. Formats grounded prompt
    4. Calls local Ollama LLM (with fallback if Ollama offline)
    5. Returns grounded answer with verifiable citations and provenance metadata.
    """
    start_time = time.perf_counter()

    retrieval_service = getattr(request.app.state, "retrieval_service", None)
    generation_service = getattr(request.app.state, "generation_service", None)

    if not retrieval_service or not generation_service:
        logger.error("Core services not initialized in application state.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG services are still initializing or unavailable."
        )

    clean_question = payload.question.strip()
    if len(clean_question) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question must be at least 2 characters long."
        )

    try:
        # Step 1: Retrieval
        sources = retrieval_service.retrieve(
            query=clean_question,
            top_k=payload.top_k
        )

        # Step 2: Generation
        answer = generation_service.generate(
            query=clean_question,
            sources=sources
        )

        # Do not return sources when query is out-of-domain or information is insufficient
        if "sufficient information in the provided" in answer.lower():
            sources = []

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return QueryResponse(
            answer=answer,
            sources=sources,
            retrieval_count=len(sources),
            latency_ms=elapsed_ms
        )

    except Exception as e:
        logger.error(f"Error processing query '{clean_question}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the RAG query: {str(e)}"
        )
