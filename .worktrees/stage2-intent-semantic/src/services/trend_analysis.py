from datetime import datetime
from src.db import Database


class TrendAnalysisService:
    """Service for analyzing trends in repository data."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_star_timeline(
        self,
        username: str | None = None
    ) -> list[dict]:
        """
        Get star timeline by month.

        Args:
            username: Optional username filter (not used yet)

        Returns:
            List of {month, count} entries
        """
        cursor = await self.db._connection.execute(
            """
            SELECT
                strftime('%Y-%m', starred_at) as month,
                COUNT(*) as count
            FROM repositories
            WHERE starred_at IS NOT NULL
            GROUP BY month
            ORDER BY month ASC
            """
        )
        rows = await cursor.fetchall()

        return [
            {"month": month, "count": count}
            for month, count in rows
        ] if rows else []

    async def get_language_trend(self) -> list[dict]:
        """
        Get language distribution over time.

        Returns:
            List of {language, month, count} entries
        """
        cursor = await self.db._connection.execute(
            """
            SELECT
                primary_language,
                strftime('%Y-%m', starred_at) as month,
                COUNT(*) as count
            FROM repositories
            WHERE starred_at IS NOT NULL
            AND primary_language IS NOT NULL
            GROUP BY primary_language, month
            ORDER BY month ASC, count DESC
            """
        )
        rows = await cursor.fetchall()

        return [
            {"language": lang, "month": month, "count": count}
            for lang, month, count in rows
        ] if rows else []

    async def get_category_evolution(self) -> list[dict]:
        """
        Get category interest evolution over time.

        Returns:
            List of {category, month, count} entries
        """
        cursor = await self.db._connection.execute(
            """
            SELECT
                category.value,
                strftime('%Y-%m', starred_at) as month,
                COUNT(*) as count
            FROM repositories,
                json_each(categories) as category
            WHERE starred_at IS NOT NULL
            GROUP BY category.value, month
            ORDER BY month ASC, count DESC
            """
        )
        rows = await cursor.fetchall()

        return [
            {"category": cat, "month": month, "count": count}
            for cat, month, count in rows
        ] if rows else []
