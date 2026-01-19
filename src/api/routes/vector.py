from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from src.config import settings

router = APIRouter(prefix="/api/vector", tags=["vector"])


class VectorStatusResponse(BaseModel):
    """向量搜索状态响应"""
    enabled: bool
    ollama_running: bool
    model: Optional[str] = None
    indexed_count: int
    total_count: int
    last_indexed_at: Optional[str] = None


@router.get("/status", response_model=VectorStatusResponse)
async def get_vector_status():
    """获取向量搜索状态"""
    from src.api.app import db

    # Check if semantic search is available
    enabled, ollama_running, model = _check_semantic_search_status()

    # Get indexed count
    indexed_count = _get_indexed_count()

    # Get total repository count
    total_count = await _get_total_repository_count(db)

    return VectorStatusResponse(
        enabled=enabled,
        ollama_running=ollama_running,
        model=model,
        indexed_count=indexed_count,
        total_count=total_count
    )


def _check_semantic_search_status() -> tuple[bool, bool, Optional[str]]:
    """Check if semantic search components are available.

    Returns:
        Tuple of (enabled, ollama_running, model_name)
    """
    try:
        from src.vector.embeddings import OllamaEmbeddings
        embeddings = OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model
        )
        if embeddings.check_health():
            return True, True, embeddings.model
        return True, False, None
    except Exception:
        return False, False, None


def _get_indexed_count() -> int:
    """Get the number of indexed repositories in ChromaDB."""
    try:
        from src.vector.chroma_store import ChromaDBStore
        store = ChromaDBStore()
        return store.get_count()
    except Exception:
        return 0


async def _get_total_repository_count(db) -> int:
    """Get the total number of non-deleted repositories."""
    try:
        cursor = await db._connection.execute(
            "SELECT COUNT(*) FROM repositories WHERE is_deleted = 0"
        )
        result = await cursor.fetchone()
        return result[0] if result else 0
    except Exception:
        return 0
