"""
Service for searching repositories.
"""
from typing import List, Dict, Any, Optional
from src.db import Database


class SearchService:
    """Service for searching and filtering repositories"""

    def __init__(self, db: Database):
        """
        Initialize search service.

        Args:
            db: Database instance
        """
        self.db = db

    async def search(
        self,
        query: Optional[str] = None,
        categories: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        limit: int = 20,
        # New filter dimensions
        is_active: Optional[bool] = None,  # Filter by active maintenance (pushed within 7 days)
        is_new: Optional[bool] = None,  # Filter by new projects (created within 6 months)
        owner_type: Optional[str] = None,  # Filter by owner type ("Organization" or "User")
        exclude_archived: bool = True  # Exclude archived repos by default
    ) -> List[Dict[str, Any]]:
        """
        Search repositories with filters.

        Args:
            query: Full-text search query
            categories: Filter by categories
            languages: Filter by programming languages
            min_stars: Minimum star count
            max_stars: Maximum star count
            limit: Maximum number of results
            is_active: Filter by active maintenance (pushed within 7 days)
            is_new: Filter by new projects (created within 6 months)
            owner_type: Filter by owner type ("Organization" or "User")
            exclude_archived: Exclude archived repos

        Returns:
            List of matching repositories
        """
        # Use full-text search if query is provided
        if query:
            results = await self.db.search_repositories_fulltext(
                query=query,
                limit=limit
            )
        else:
            # Use database search for filters only
            results = await self.db.search_repositories(
                categories=categories,
                languages=languages,
                min_stars=min_stars,
                max_stars=max_stars,
                limit=limit,
                is_active=is_active,
                is_new=is_new,
                owner_type=owner_type,
                exclude_archived=exclude_archived
            )

        return results

    async def search_fulltext(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Full-text search using FTS5

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching repositories
        """
        return await self.db.search_repositories_fulltext(
            query=query,
            limit=limit
        )

    async def get_categories(self) -> Dict[str, int]:
        """
        Get all available categories with counts.

        Returns:
            Dictionary mapping category to count
        """
        stats = await self.db.get_statistics()
        return stats.get("categories", {})

    async def get_languages(self) -> List[str]:
        """
        Get all available programming languages.

        Returns:
            List of languages
        """
        # This would require a new DB method
        # For now, return empty list
        return []

    async def get_repository(self, name_with_owner: str) -> Optional[Dict[str, Any]]:
        """
        Get a single repository by name.

        Args:
            name_with_owner: Repository name (owner/repo)

        Returns:
            Repository data or None
        """
        return await self.db.get_repository(name_with_owner)

    async def get_similar_repositories(
        self,
        name_with_owner: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find repositories similar to the given one.

        Args:
            name_with_owner: Repository name
            limit: Maximum number of results

        Returns:
            List of similar repositories
        """
        # Get the target repository
        repo = await self.db.get_repository(name_with_owner)
        if not repo:
            return []

        # Find repos with same categories or language
        results = await self.db.search_repositories(
            categories=repo.get("categories", [])[:2],  # Use first 2 categories
            languages=[repo.get("primary_language")] if repo.get("primary_language") else None,
            limit=limit + 1  # +1 to exclude the repo itself
        )

        # Exclude the original repository
        return [r for r in results if r["name_with_owner"] != name_with_owner][:limit]
