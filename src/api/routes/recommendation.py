from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/recommendations", tags=["recommendation"])


# ==================== Response Models ====================

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


class RecommendationResponse(BaseModel):
    """Hybrid recommendation response."""
    name_with_owner: str
    name: str
    owner: str
    description: Optional[str]
    final_score: float
    sources: list[str]
    graph_score: Optional[float]
    semantic_score: Optional[float]


# ==================== Legacy Endpoints ====================

@router.get("/similar/{name_with_owner}", response_model=list[SimilarResponse])
async def get_similar_repos(name_with_owner: str, limit: int = 5):
    """Get similar repositories."""
    from src.api.app import db
    from src.services.recommendation import RecommendationService

    try:
        service = RecommendationService(db)
        return await service.get_similar_repos(name_with_owner, limit)
    except Exception:
        raise HTTPException(status_code=500, detail="Database not available")


@router.get("/category/{category}", response_model=list[CategoryResponse])
async def get_recommended_by_category(category: str, limit: int = 10):
    """Get repositories by category."""
    from src.api.app import db
    from src.services.recommendation import RecommendationService

    try:
        service = RecommendationService(db)
        return await service.get_recommended_by_category(category, limit)
    except Exception:
        raise HTTPException(status_code=500, detail="Database not available")


# ==================== Hybrid Recommendation Endpoints ====================

async def get_hybrid_recommendation_service():
    """Dependency to get hybrid recommendation service."""
    from src.api.app import hybrid_recommendation_service
    if hybrid_recommendation_service is None:
        raise HTTPException(
            status_code=503,
            detail="Hybrid recommendation service not initialized. Semantic search may be disabled."
        )
    return hybrid_recommendation_service


def parse_exclude_repos(value: Optional[str]) -> Optional[set[str]]:
    """Parse comma-separated string into set."""
    if not value:
        return None
    return {item.strip() for item in value.split(",") if item.strip()}


async def enrich_recommendations(recommendations: List[dict], db) -> List[RecommendationResponse]:
    """Enrich recommendations with repository details."""
    enriched_results = []
    for rec in recommendations:
        repo = await db.get_repository(rec["name_with_owner"])
        enriched_results.append(RecommendationResponse(
            name_with_owner=rec["name_with_owner"],
            name=rec["name"],
            owner=rec["owner"],
            description=repo.get("description") if repo else None,
            final_score=rec["final_score"],
            sources=rec["sources"],
            graph_score=rec.get("graph_score"),
            semantic_score=rec.get("semantic_score")
        ))
    return enriched_results


@router.get("/{repo_name:path}", response_model=List[RecommendationResponse])
async def get_recommendations(
    repo_name: str,
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of recommendations"),
    include_semantic: bool = Query(default=True, description="Include semantic similarity"),
    exclude_repos: Optional[str] = Query(default=None, description="Comma-separated repos to exclude"),
    hybrid_recommendation_service = Depends(get_hybrid_recommendation_service)
):
    """Get hybrid recommendations for a repository.

    Combines graph-based relationships (edges) and semantic similarity
    to provide personalized repository recommendations.
    """
    from src.api.app import db

    excluded = parse_exclude_repos(exclude_repos)
    recommendations = await hybrid_recommendation_service.get_recommendations(
        repo_name=repo_name,
        limit=limit,
        include_semantic=include_semantic,
        exclude_repos=excluded
    )

    return await enrich_recommendations(recommendations, db)
