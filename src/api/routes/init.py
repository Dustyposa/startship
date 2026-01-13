"""Initialization API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/init", tags=["init"])


class InitRequest(BaseModel):
    """Initialization request model"""
    username: str
    max_repos: Optional[int] = None
    skip_llm: bool = False
    enable_semantic: bool = False


class InitStatusResponse(BaseModel):
    """Initialization status response"""
    has_data: bool
    username: Optional[str] = None
    repo_count: int = 0


@router.get("/status", response_model=InitStatusResponse)
async def get_init_status():
    """
    Check if the system has been initialized with data.

    Returns whether there is any repository data in the database.
    """
    from src.api.app import db

    # Get repo count
    stats = await db.get_statistics()
    repo_count = stats.get("total_repositories", 0)

    return InitStatusResponse(
        has_data=repo_count > 0,
        username=None,
        repo_count=repo_count
    )


@router.post("/start")
async def start_initialization(request: InitRequest):
    """
    Start initialization from GitHub stars.

    - **username**: GitHub username
    - **max_repos**: Maximum number of repos to fetch (optional)
    - **skip_llm**: Skip LLM analysis for faster initialization
    - **enable_semantic**: Enable semantic search with vector embeddings
    """
    from src.api.app import db
    from src.llm import create_llm
    from src.services.init import InitializationService

    # Debug logging
    print(f"DEBUG: request.skip_llm = {request.skip_llm}")
    print(f"DEBUG: request model = {request.model_dump()}")

    # Create LLM if needed
    llm = None if request.skip_llm else create_llm("openai")
    print(f"DEBUG: llm = {llm}")
    if llm:
        await llm.initialize()

    # Create semantic search if enabled
    semantic = None
    if request.enable_semantic:
        from src.vector.semantic import SemanticSearch
        semantic = SemanticSearch()

    # Create initialization service
    init_service = InitializationService(db, llm, semantic)

    try:
        # Run initialization
        stats = await init_service.initialize_from_stars(
            username=request.username,
            max_repos=request.max_repos,
            skip_llm=request.skip_llm
        )

        return {
            "success": True,
            "message": f"Successfully initialized with {stats['fetched']} repositories",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if llm:
            await llm.close()
