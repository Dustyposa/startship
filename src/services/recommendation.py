from typing import Any
from src.db import Database


class RecommendationService:
    """Service for repository recommendations."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_similar_repos(
        self,
        repo_name: str,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get similar repositories based on shared categories.

        Args:
            repo_name: Repository name_with_owner
            limit: Maximum number of recommendations

        Returns:
            List of similar repositories
        """
        # Get target repo categories
        cursor = await self.db._connection.execute(
            "SELECT categories FROM repositories WHERE name_with_owner = ?",
            (repo_name,)
        )
        row = await cursor.fetchone()

        if not row or not row[0]:
            return []

        categories = row[0]

        # Find repos with shared categories
        cursor = await self.db._connection.execute(
            """
            SELECT name_with_owner, description, stargazer_count, categories
            FROM repositories
            WHERE name_with_owner != ?
            AND categories IS NOT NULL
            ORDER BY stargazer_count DESC
            LIMIT ?
            """,
            (repo_name, limit * 2)
        )
        rows = await cursor.fetchall()

        # Filter by category overlap and sort
        results = []
        for name_with_owner, description, stars, cats in rows:
            if cats and any(c in categories for c in cats):
                results.append({
                    "name_with_owner": name_with_owner,
                    "description": description,
                    "stargazer_count": stars,
                    "categories": cats
                })

        return results[:limit]

    async def get_recommended_by_category(
        self,
        category: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get repositories by category.

        Args:
            category: Category name
            limit: Maximum number of results

        Returns:
            List of repositories in the category
        """
        cursor = await self.db._connection.execute(
            """
            SELECT name_with_owner, description, stargazer_count, categories
            FROM repositories
            WHERE categories IS NOT NULL
            AND ? IN categories
            ORDER BY stargazer_count DESC
            LIMIT ?
            """,
            (category, limit)
        )
        rows = await cursor.fetchall()

        return [
            {
                "name_with_owner": name,
                "description": desc,
                "stargazer_count": stars,
                "categories": cats
            }
            for name, desc, stars, cats in rows
        ]
