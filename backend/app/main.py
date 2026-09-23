"""
FastAPI Main Application Entry Point.
Manages application lifespan, CORS middleware, and endpoint registration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from backend.app.core.config import settings
from backend.app.utils.logging_config import setup_logging
from backend.app.services.retrieval import RetrievalService
from backend.app.services.generation import GenerationService
from backend.app.api.routes.query import router as query_router

logger = setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Event:
    Loads persistent ChromaDB vector store and establishes LLM configuration
    ONCE at startup. Embeddings are never rebuilt on incoming requests.
    """
    logger.info("=" * 60)
    logger.info(f"Starting {settings.PROJECT_NAME} (v{settings.VERSION})...")
    logger.info(f"Persistent Vector Store Path: {settings.VECTOR_STORE_PATH}")
    logger.info(f"Collection Name: {settings.COLLECTION_NAME}")
    logger.info(f"Configured Ollama Endpoint: {settings.OLLAMA_BASE_URL} ({settings.OLLAMA_MODEL})")

    # Initialize Core Services once
    retrieval_service = RetrievalService()
    generation_service = GenerationService()

    app.state.retrieval_service = retrieval_service
    app.state.generation_service = generation_service

    logger.info("TrustAI Core Services successfully initialized and loaded into app state.")
    logger.info("=" * 60)

    yield

    logger.info("Shutting down TrustAI Application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade RAG Document Assistant for AI Governance, Safety & Regulation Standards.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes at root level (for GET /health and POST /query)
app.include_router(query_router, tags=["RAG Document Assistant"])

# Also register at API prefix (e.g. /api/v1/query)
app.include_router(query_router, prefix=settings.API_PREFIX, tags=["API v1"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
