from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.app import db
from src.services.trend_analysis import TrendAnalysisService

router = APIRouter(prefix="/trends", tags=["trends"])


class TimelinePoint(BaseModel):
    """Timeline data point."""
    month: str
    count: int


@router.get("/timeline", response_model=list[TimelinePoint])
async def get_star_timeline(username: str | None = None):
    """Get star timeline by month."""
    try:
        service = TrendAnalysisService(db)
        return await service.get_star_timeline(username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch timeline: {e}")


@router.get("/languages")
async def get_language_trend():
    """Get language trend over time."""
    try:
        service = TrendAnalysisService(db)
        return await service.get_language_trend()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch language trend: {e}")


@router.get("/categories")
async def get_category_evolution():
    """Get category evolution over time."""
    try:
        service = TrendAnalysisService(db)
        return await service.get_category_evolution()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch category evolution: {e}")
