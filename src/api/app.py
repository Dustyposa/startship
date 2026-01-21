"""
FastAPI application for GitHub Star RAG Service.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from src.config import settings
from src.db import create_database
from src.api.routes import chat, search, init, recommendation, trends, network, user_data, sync, graph, vector


logger = logging.getLogger(__name__)


# Global database instance
db = None
search_service = None
scheduler = None
hybrid_search = None
hybrid_recommendation_service = None
semantic_edge_discovery = None


def _init_semantic_search():
    """Initialize semantic search if dependencies are available.

    Returns:
        SemanticSearch instance if successful, None otherwise.
    """
    try:
        from src.vector.semantic import SemanticSearch
        from src.vector.embeddings import OllamaEmbeddings

        embeddings = OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
            timeout=settings.ollama_timeout
        )

        if not embeddings.check_health():
            logger.warning("Ollama not available, semantic search disabled")
            print("Ollama not available - semantic search disabled")
            return None

        return SemanticSearch(
            ollama_base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
            persist_path=settings.chromadb_path
        )

    except ImportError as e:
        logger.warning(f"ChromaDB not installed: {e}. Semantic search disabled.")
        print("ChromaDB not installed - semantic search disabled")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize semantic search: {e}")
        print(f"Failed to initialize semantic search: {e}")
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global db, search_service, scheduler, hybrid_search, hybrid_recommendation_service, semantic_edge_discovery

    # Startup
    print(f"Starting {settings.api_title} v{settings.api_version}")

    # Initialize database
    db = create_database(
        db_type=settings.db_type,
        sqlite_path=settings.sqlite_path
    )
    await db.initialize()
    print(f"Database initialized: {settings.db_type}")

    # Initialize semantic search (optional)
    semantic_search = _init_semantic_search()
    if semantic_search:
        from src.services.hybrid_search import HybridSearch
        hybrid_search = HybridSearch(
            db=db,
            semantic=semantic_search,
            fts_weight=0.3,
            semantic_weight=0.7
        )
        logger.info("Semantic search enabled in HybridSearch")
        print("Semantic search enabled")
    else:
        hybrid_search = None

    # Initialize semantic edge discovery if semantic search is available
    if semantic_search:
        from src.services.graph.semantic_edges import SemanticEdgeDiscovery
        semantic_edge_discovery = SemanticEdgeDiscovery(semantic_search, db)
        logger.info("Semantic edge discovery initialized")
        print("Semantic edge discovery initialized")

    # Initialize search service
    from src.services.search import SearchService
    search_service = SearchService(db, hybrid_search)
    print("Search service initialized")

    # Initialize hybrid recommendation service
    if semantic_search:
        from src.services.hybrid_recommendation import HybridRecommendationService
        hybrid_recommendation_service = HybridRecommendationService(db, semantic_search)
        print("Hybrid recommendation service initialized")
    else:
        hybrid_recommendation_service = None

    # Initialize scheduler if GitHub token is configured
    if settings.github_token:
        try:
            from src.services.scheduler import start_scheduler
            scheduler = start_scheduler(db, semantic_search, semantic_edge_discovery)
            print("Sync scheduler started")
        except Exception as e:
            print(f"Failed to start scheduler: {e}")
            scheduler = None
    else:
        print("GitHub Token not configured - sync scheduler disabled")

    yield

    # Shutdown
    print("Shutting down application")
    if scheduler:
        from src.services.scheduler import stop_scheduler
        stop_scheduler()
        print("Sync scheduler stopped")
    if db:
        await db.close()
        print("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(init.router)
app.include_router(recommendation.router)
app.include_router(trends.router)
app.include_router(network.router)
app.include_router(user_data.router)
app.include_router(sync.router)
app.include_router(graph.router)
app.include_router(vector.router)

# Mount static files for frontend
# TODO: Uncomment when frontend is built
# frontend_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
# if frontend_path.exists():
#     app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.api_version
    }


@app.get("/api/stats")
async def get_stats():
    """
    Get service statistics.
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    stats = await db.get_statistics()
    return {
        "success": True,
        "data": stats
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )
