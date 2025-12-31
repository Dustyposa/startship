from src.db import Database


class ContextService:
    """Service for managing conversation context."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_context(self, session_id: str, limit: int = 5) -> str:
        """
        Get conversation context with first round always preserved.

        Args:
            session_id: Session identifier
            limit: Maximum number of recent rounds (excluding first)

        Returns:
            Formatted context string

        Raises:
            ValueError: If limit < 1
        """
        if limit < 1:
            raise ValueError(f"limit must be >= 1, got {limit}")

        try:
            # Get first round (earliest message)
            cursor = await self.db._connection.execute(
                """
                SELECT role, content
                FROM conversations
                WHERE session_id = ?
                ORDER BY timestamp ASC
                LIMIT 1
                """,
                (session_id,)
            )
            first_row = await cursor.fetchone()

            if not first_row:
                return ""

            lines = []
            role, content = first_row
            lines.append(f"{role.capitalize()}: {content}")

            # Get recent (limit - 1) rounds, excluding the first round
            if limit > 1:
                cursor = await self.db._connection.execute(
                    """
                    SELECT role, content
                    FROM conversations
                    WHERE session_id = ? AND rowid NOT IN (
                        SELECT rowid FROM conversations
                        WHERE session_id = ?
                        ORDER BY timestamp ASC
                        LIMIT 1
                    )
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (session_id, session_id, limit - 1)
                )
                recent_rows = await cursor.fetchall()

                # Reverse to get chronological order
                for role, content in reversed(recent_rows):
                    lines.append(f"{role.capitalize()}: {content}")

            return "\n".join(lines)

        except Exception as e:
            # Re-raise with additional context
            raise RuntimeError(f"Failed to get context for session {session_id}: {e}") from e
