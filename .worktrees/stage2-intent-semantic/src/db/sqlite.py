"""SQLite database implementation."""

import aiosqlite
from pathlib import Path
from .base import Database


class SQLiteDatabase(Database):
    """SQLite database implementation."""

    def __init__(self, db_path: str = "data/starship.db"):
        super().__init__()
        self.db_path = Path(db_path)

    async def initialize(self):
        """Initialize database connection."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)

    async def close(self):
        """Close database connection."""
        if self._connection:
            await self._connection.close()
