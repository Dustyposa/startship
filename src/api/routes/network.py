"""
Network graph API routes.
"""
from fastapi import APIRouter, HTTPException, Depends

from .utils import get_db

router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("/graph")
async def get_network_graph(db = Depends(get_db)):
    """Get repository network graph data"""
    from src.services.network import NetworkService

    service = NetworkService(db)

    network = await service.get_cached_network()

    ensure_entity_exists(
        network,
        "Network data not found. Please complete initialization first."
    )

    return network


def ensure_entity_exists(entity: object | None, error_message: str = "Entity not found") -> None:
    """Raise HTTPException if entity doesn't exist."""
    if entity is None:
        raise HTTPException(status_code=404, detail=error_message)
