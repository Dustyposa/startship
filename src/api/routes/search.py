"""
Search API endpoints.
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional, List

from .utils import get_db, build_response

router = APIRouter(prefix="/api", tags=["search"])


async def get_search_service():
    """Dependency to get search service"""
    from src.api.app import search_service
    if search_service is None:
        raise HTTPException(status_code=503, detail="Search service not initialized")
    return search_service


def parse_list_param(value: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated string into list.

    Args:
        value: Comma-separated string or None

    Returns:
        List of strings or None
    """
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


@router.get("/search")
async def search_repositories(
    q: Optional[str] = None,
    categories: Optional[str] = None,
    languages: Optional[str] = None,
    min_stars: Optional[int] = None,
    max_stars: Optional[int] = None,
    limit: int = 1000,
    offset: int = 0,
    is_active: Optional[bool] = None,
    is_new: Optional[bool] = None,
    owner_type: Optional[str] = None,
    exclude_archived: bool = True,
    include_related: bool = True,
    search_service = Depends(get_search_service)
):
    """Search repositories with filters and optional related recommendations"""
    parsed_categories = parse_list_param(categories)
    parsed_languages = parse_list_param(languages)

    if include_related:
        result = await search_service.search_with_relations(
            query=q,
            categories=parsed_categories,
            languages=parsed_languages,
            min_stars=min_stars,
            max_stars=max_stars,
            limit=limit,
            offset=offset,
            is_active=is_active,
            is_new=is_new,
            owner_type=owner_type,
            exclude_archived=exclude_archived,
            include_related=True
        )
        return build_response(result["results"], count=result["total"], related=result["related"])

    # Regular search without related repos
    result = await search_service.search(
        query=q,
        categories=parsed_categories,
        languages=parsed_languages,
        min_stars=min_stars,
        max_stars=max_stars,
        limit=limit,
        offset=offset,
        is_active=is_active,
        is_new=is_new,
        owner_type=owner_type,
        exclude_archived=exclude_archived,
        return_count=True
    )
    return build_response(result["results"], count=result.get("total"))


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
    ensure_entity_exists(result, "Repository not found")
    return result


def ensure_entity_exists(entity: object | None, error_message: str = "Entity not found") -> None:
    """Raise HTTPException if entity doesn't exist."""
    if entity is None:
        raise HTTPException(status_code=404, detail=error_message)
