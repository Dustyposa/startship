from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/trends", tags=["trends"])


class TimelinePoint(BaseModel):
    """Timeline data point."""
    month: str
    count: int


@router.get("/timeline", response_model=list[TimelinePoint])
async def get_star_timeline(username: str | None = None):
    """Get star timeline by month."""
    from src.api.app import db
    from src.services.trend_analysis import TrendAnalysisService

    service = TrendAnalysisService(db)
    return await service.get_star_timeline(username)


@router.get("/languages")
async def get_language_trend():
    """Get language trend over time."""
    from src.api.app import db
    from src.services.trend_analysis import TrendAnalysisService

    service = TrendAnalysisService(db)
    return await service.get_language_trend()


@router.get("/categories")
async def get_category_evolution():
    """Get category evolution over time."""
    from src.api.app import db
    from src.services.trend_analysis import TrendAnalysisService

    service = TrendAnalysisService(db)
    return await service.get_category_evolution()
