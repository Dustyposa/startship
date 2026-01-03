"""
Network graph API routes.
"""
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter(prefix="/api/network", tags=["network"])


async def get_db():
    """Dependency to get database connection"""
    from src.api.app import db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return db


@router.get("/graph")
async def get_network_graph(db = Depends(get_db)):
    """获取关系网络图数据"""
    from src.services.network import NetworkService

    service = NetworkService(db)

    try:
        network = await service.get_cached_network()

        if not network:
            raise HTTPException(
                status_code=404,
                detail="Network data not found. Please complete initialization first."
            )

        return network

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch network data: {e}"
        )
