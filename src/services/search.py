"""
Service for searching repositories.
"""
from typing import List, Dict, Any, Optional
from src.db import Database


class SearchService:
    """Service for searching and filtering repositories"""

    def __init__(self, db: Database, hybrid_search=None):
        """
        Initialize search service.

        Args:
            db: Database instance
            hybrid_search: Optional HybridSearch instance for semantic search
        """
        self.db = db
        self.hybrid_search = hybrid_search

    async def search(
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
        return_count: bool = False
    ) -> List[Dict[str, Any]] | Dict[str, Any]:
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
            sort_by: Sort field
            return_count: Whether to return total count with results

        Returns:
            If return_count is True: {"results": [...], "total": int}
            Otherwise: List of matching repositories
        """
        # Use hybrid search if query is provided and hybrid_search is available
        if query and query.strip() and self.hybrid_search:
            results = await self.hybrid_search.search(query, top_k=limit)

            # Apply filters if specified
            if any([categories, languages, min_stars, max_stars, is_active is not None,
                    is_new is not None, owner_type, exclude_archived]):
                results = self._apply_filters(
                    results,
                    categories=categories,
                    languages=languages,
                    min_stars=min_stars,
                    max_stars=max_stars,
                    is_active=is_active,
                    is_new=is_new,
                    owner_type=owner_type,
                    exclude_archived=exclude_archived
                )

            # Apply offset
            if offset > 0:
                results = results[offset:]

            if return_count:
                return {"results": results[:limit], "total": len(results)}
            return results[:limit]

        # Fall back to FTS5 or regular search
        if query and query.strip():
            return await self.db.search_repositories_fulltext(
                query=query,
                limit=limit,
                offset=offset,
                return_count=return_count
            )

        return await self.db.search_repositories(
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
            sort_by=sort_by,
            return_count=return_count
        )

    def _apply_filters(
        self,
        results: List[Dict[str, Any]],
        categories: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_new: Optional[bool] = None,
        owner_type: Optional[str] = None,
        exclude_archived: bool = True
    ) -> List[Dict[str, Any]]:
        """Apply filters to search results.

        Args:
            results: Search results to filter
            categories: Filter by categories
            languages: Filter by programming languages
            min_stars: Minimum star count
            max_stars: Maximum star count
            is_active: Filter by active maintenance
            is_new: Filter by new projects
            owner_type: Filter by owner type
            exclude_archived: Exclude archived repos

        Returns:
            Filtered results
        """
        from datetime import datetime, timedelta

        filtered = []
        for repo in results:
            # Exclude archived
            if exclude_archived and repo.get("archived"):
                continue

            # Filter by owner type
            if owner_type and repo.get("owner_type") != owner_type:
                continue

            # Filter by language
            if languages and repo.get("primary_language") not in languages:
                continue

            # Filter by stars
            stars = repo.get("stargazer_count", 0)
            if min_stars is not None and stars < min_stars:
                continue
            if max_stars is not None and stars > max_stars:
                continue

            # Filter by active status
            if is_active is not None:
                pushed_at = repo.get("pushed_at")
                if is_active and not pushed_at:
                    continue
                if is_active:
                    try:
                        pushed_date = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                        if pushed_date < datetime.now() - timedelta(days=7):
                            continue
                    except (ValueError, AttributeError):
                        continue

            # Filter by new status
            if is_new is not None:
                created_at = repo.get("created_at")
                if is_new and not created_at:
                    continue
                if is_new:
                    try:
                        created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        if created_date < datetime.now() - timedelta(days=180):
                            continue
                    except (ValueError, AttributeError):
                        continue

            filtered.append(repo)

        return filtered

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
            Dictionary with "results", "related", and "total" keys
        """
        search_result = await self.search(
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
            sort_by=sort_by,
            return_count=True
        )

        results = search_result.get("results", [])
        total = search_result.get("total", len(results))

        related = []
        if include_related and results:
            related = await self._get_related_repositories(results)

        return {
            "results": results,
            "related": related,
            "total": total
        }

    async def _get_related_repositories(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get related repositories based on graph edges.

        Args:
            results: Search results to find related repos for

        Returns:
            List of related repository data
        """
        related_repos = set()

        # Collect related repos from top 5 results
        for repo in results[:5]:
            edges = await self.db.get_graph_edges(
                repo['name_with_owner'],
                limit=3
            )
            for edge in edges:
                related_repos.add(edge['target_repo'])

        # Remove already shown repos
        result_names = {r['name_with_owner'] for r in results}
        related_repos = related_repos - result_names

        # Fetch full repo data for top 5 related
        related = []
        for repo_name in list(related_repos)[:5]:
            repo_data = await self.db.get_repository(repo_name)
            if repo_data:
                related.append(repo_data)

        return related
