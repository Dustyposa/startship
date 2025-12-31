from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.app import db
from src.services.recommendation import RecommendationService

router = APIRouter(prefix="/recommend", tags=["recommendation"])


class SimilarResponse(BaseModel):
    """Similar repositories response."""
    name_with_owner: str
    description: str | None
    stargazer_count: int
    categories: list[str]


class CategoryResponse(BaseModel):
    """Category recommendation response."""
    name_with_owner: str
    description: str | None
    stargazer_count: int
    categories: list[str]


@router.get("/similar/{name_with_owner}", response_model=list[SimilarResponse])
async def get_similar_repos(name_with_owner: str, limit: int = 5):
    """Get similar repositories."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    try:
        service = RecommendationService(db)
        results = await service.get_similar_repos(name_with_owner, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch recommendations")


@router.get("/category/{category}", response_model=list[CategoryResponse])
async def get_recommended_by_category(category: str, limit: int = 10):
    """Get repositories by category."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    try:
        service = RecommendationService(db)
        results = await service.get_recommended_by_category(category, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch recommendations")
