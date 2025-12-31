"""Statistics aggregation service."""
from src.db import Database


class StatsService:
    """Service for generating repository statistics."""

    async def get_stats(self, query: str, db: Database) -> str:
        """
        Generate statistics based on user query.

        Args:
            query: User query text
            db: Database instance

        Returns:
            Formatted statistics text
        """
        # Simple keyword detection
        query_lower = query.lower()

        if "语言" in query or "language" in query_lower:
            data = await self._stats_by_language(db)
            return self._format_language_stats(data)
        else:
            data = await self._overall_stats(db)
            return self._format_overall_stats(data)

    async def _stats_by_language(self, db: Database) -> dict:
        """Get statistics grouped by language."""
        async with db._connection.execute("""
            SELECT primary_language, COUNT(*) as count
            FROM repositories
            WHERE primary_language IS NOT NULL
            GROUP BY primary_language
            ORDER BY count DESC
            LIMIT 10
        """) as cursor:
            rows = await cursor.fetchall()
            return {lang: count for lang, count in rows}

    async def _overall_stats(self, db: Database) -> dict:
        """Get overall statistics."""
        stats = await db.get_statistics()
        return {
            "total": stats.get("total_repositories", 0),
            "with_language": stats.get("repositories_with_primary_language", 0)
        }

    def _format_language_stats(self, data: dict) -> str:
        """Format language statistics as text."""
        total = sum(data.values())
        lines = [f"总共 {total} 个项目按语言分布："]
        for lang, count in list(data.items())[:5]:
            lines.append(f"- {lang}: {count}")
        return "\n".join(lines)

    def _format_overall_stats(self, data: dict) -> str:
        """Format overall statistics as text."""
        return f"总共收藏了 {data['total']} 个项目，" \
               f"其中 {data.get('with_language', 0)} 个标记了主语言。"
