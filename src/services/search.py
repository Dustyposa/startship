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
        limit: int = 1000,
        offset: int = 0,
        # New filter dimensions
        is_active: Optional[bool] = None,  # Filter by active maintenance (pushed within 7 days)
        is_new: Optional[bool] = None,  # Filter by new projects (created within 6 months)
        owner_type: Optional[str] = None,  # Filter by owner type ("Organization" or "User")
        exclude_archived: bool = True,  # Exclude archived repos by default
        sort_by: str = "starred_at"  # Default sort by starred_at (newest stars first)
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
            offset: Number of results to skip
            is_active: Filter by active maintenance (pushed within 7 days)
            is_new: Filter by new projects (created within 6 months)
            owner_type: Filter by owner type ("Organization" or "User")
            exclude_archived: Exclude archived repos

        Returns:
            List of matching repositories
        """
        # Use full-text search if query is provided and non-empty
        if query and query.strip():
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
                offset=offset,
                is_active=is_active,
                is_new=is_new,
                owner_type=owner_type,
                exclude_archived=exclude_archived,
                sort_by=sort_by
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

    async def search_with_relations(
        self,
        query: Optional[str] = None,
        categories: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        limit: int = 1000,
        offset: int = 0,
        is_active: Optional[bool] = None,
        is_new: Optional[bool] = None,
        owner_type: Optional[str] = None,
        exclude_archived: bool = True,
        sort_by: str = "starred_at",
        include_related: bool = True
    ) -> Dict[str, Any]:
        """
        Search repositories with filters and include related recommendations.

        Args:
            query: Full-text search query
            categories: Filter by categories
            languages: Filter by programming languages
            min_stars: Minimum star count
            max_stars: Maximum star count
            limit: Maximum number of results
            offset: Number of results to skip
            is_active: Filter by active maintenance (pushed within 7 days)
            is_new: Filter by new projects (created within 6 months)
            owner_type: Filter by owner type ("Organization" or "User")
            exclude_archived: Exclude archived repos
            sort_by: Sort field
            include_related: Whether to include related repo recommendations

        Returns:
            Dictionary with "results" and "related" keys
        """
        # Get direct matches
        results = await self.search(
            query=query,
            categories=categories,
            languages=languages,
            min_stars=min_stars,
            max_stars=max_stars,
            limit=limit,
            offset=offset,
            is_active=is_active,
            is_new=is_new,
            owner_type=owner_type,
            exclude_archived=exclude_archived,
            sort_by=sort_by
        )

        related = []
        if include_related and results:
            # Get related repos for top results
            related_repos = set()
            for repo in results[:5]:  # Top 5 results
                edges = await self.db.get_graph_edges(
                    repo['name_with_owner'],
                    limit=3
                )
                for edge in edges:
                    related_repos.add(edge['target_repo'])

            # Remove already shown repos
            result_names = {r['name_with_owner'] for r in results}
            related_repos = related_repos - result_names

            # Fetch full repo data for related
            for repo_name in list(related_repos)[:5]:  # Top 5 related
                repo_data = await self.db.get_repository(repo_name)
                if repo_data:
                    related.append(repo_data)

        return {
            "results": results,
            "related": related
        }
