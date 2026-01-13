"""
Search API endpoints.
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional, List

router = APIRouter(prefix="/api", tags=["search"])


async def get_search_service():
    """Dependency to get search service"""
    from src.api.app import search_service
    if search_service is None:
        raise HTTPException(status_code=503, detail="Search service not initialized")
    return search_service


def parse_list_param(value: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated string into list"""
    return value.split(",") if value else None


def build_response(results: List) -> dict:
    """Build standard API response"""
    return {"results": results, "count": len(results)}


@router.get("/search")
async def search_repositories(
    q: Optional[str] = None,
    categories: Optional[str] = None,
    languages: Optional[str] = None,
    min_stars: Optional[int] = None,
    max_stars: Optional[int] = None,
    limit: int = 20,
    search_service = Depends(get_search_service)
):
    """Search repositories with filters"""
    results = await search_service.search(
        query=q,
        categories=parse_list_param(categories),
        languages=parse_list_param(languages),
        min_stars=min_stars,
        max_stars=max_stars,
        limit=limit
    )
    return build_response(results)


@router.get("/search/fulltext")
async def search_fulltext(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=20, ge=1, le=100),
    search_service = Depends(get_search_service)
):
    """Full-text search using FTS5"""
    results = await search_service.search_fulltext(query=query, limit=limit)
    return build_response(results)


@router.get("/categories")
async def get_categories(search_service = Depends(get_search_service)):
    """Get all categories with counts"""
    categories = await search_service.get_categories()
    return {"categories": categories}


@router.get("/repo/{name_with_owner:path}")
async def get_repository(name_with_owner: str, search_service = Depends(get_search_service)):
    """Get a single repository"""
    result = await search_service.get_repository(name_with_owner)
    if not result:
        raise HTTPException(status_code=404, detail="Repository not found")
    return result
