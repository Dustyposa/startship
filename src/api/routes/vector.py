from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

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

    # 检查是否启用
    enabled = False
    ollama_running = False
    model = None

    try:
        from src.vector.embeddings import OllamaEmbeddings
        embeddings = OllamaEmbeddings()
        ollama_running = embeddings.check_health()
        model = embeddings.model if ollama_running else None
        enabled = True
    except Exception:
        pass

    # 获取索引数量
    indexed_count = 0
    try:
        from src.vector.chroma_store import ChromaDBStore
        store = ChromaDBStore()
        indexed_count = store.get_count()
    except Exception:
        pass

    # 获取总仓库数
    total_count = 0
    try:
        cursor = await db._connection.execute(
            "SELECT COUNT(*) FROM repositories WHERE is_deleted = 0"
        )
        result = await cursor.fetchone()
        total_count = result[0] if result else 0
    except Exception:
        pass

    return VectorStatusResponse(
        enabled=enabled,
        ollama_running=ollama_running,
        model=model,
        indexed_count=indexed_count,
        total_count=total_count
    )
