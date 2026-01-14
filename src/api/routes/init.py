"""Initialization API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/init", tags=["init"])


class InitRequest(BaseModel):
    """Initialization request model."""
    username: str
    max_repos: Optional[int] = None
    skip_llm: bool = False
    enable_semantic: bool = False


class InitStatusResponse(BaseModel):
    """Initialization status response."""
    has_data: bool
    username: Optional[str] = None
    repo_count: int = 0


def _handle_init_error(error_msg: str, username: str) -> HTTPException:
    """Convert initialization errors to appropriate HTTP exceptions."""
    error_lower = error_msg.lower()

    if any(x in error_lower or x in error_msg for x in ["rate limit", "403", "429"]):
        return HTTPException(
            status_code=429,
            detail={
                "error": "GitHub API 频率限制已超限",
                "message": "GitHub API 请求频率限制已用完。请稍后再试，或配置 GITHUB_TOKEN 来提高限制。",
                "suggestions": [
                    "等待约 1 小时后重试",
                    "或配置 GitHub Token（限制提升至 5000 次/小时）: 在 .env 文件中添加 GITHUB_TOKEN=your_token_here"
                ],
                "retry_after": 3600
            }
        )

    if any(x in error_lower or x in error_msg for x in ["401", "unauthorized"]):
        return HTTPException(
            status_code=401,
            detail={
                "error": "GitHub Token 无效",
                "message": "配置的 GitHub Token 无效或已过期，请检查配置。"
            }
        )

    if any(x in error_lower or x in error_msg for x in ["404", "not found"]):
        return HTTPException(
            status_code=404,
            detail={
                "error": "用户不存在",
                "message": f"GitHub 用户 '{username}' 不存在，请检查用户名是否正确。"
            }
        )

    return HTTPException(
        status_code=500,
        detail={
            "error": "初始化失败",
            "message": error_msg,
            "suggestions": [
                "检查用户名是否正确",
                "检查网络连接",
                "查看后端日志获取更多详情"
            ]
        }
    )


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
        try:
            from src.vector.semantic import SemanticSearch
            semantic = SemanticSearch()
        except ImportError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Semantic search requires chromadb to be installed: {str(e)}"
            )

    # Create initialization service
    init_service = InitializationService(db, llm, semantic)

    try:
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
        raise _handle_init_error(str(e), request.username)
    finally:
        if llm:
            await llm.close()
