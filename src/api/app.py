"""
FastAPI application for GitHub Star RAG Service.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from src.config import settings
from src.db import create_database
from src.api.routes import chat, search, init, recommendation


# Global database instance
db = None
search_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global db, search_service

    # Startup
    print(f"Starting {settings.api_title} v{settings.api_version}")

    # Initialize database
    db = create_database(
        db_type=settings.db_type,
        sqlite_path=settings.sqlite_path
    )
    await db.initialize()
    print(f"Database initialized: {settings.db_type}")

    # Initialize search service
    from src.services.search import SearchService
    search_service = SearchService(db)
    print("Search service initialized")

    yield

    # Shutdown
    print("Shutting down application")
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


@app.get("/stats")
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
