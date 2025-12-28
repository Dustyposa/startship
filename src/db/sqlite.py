"""
SQLite database implementation.
"""
import json
import aiosqlite
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base import Database


class SQLiteDatabase(Database):
    """
    SQLite implementation of Database interface.

    Uses aiosqlite for async operations.
    """

    def __init__(self, db_path: str = "data/starship.db"):
        """
        Initialize SQLite database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Initialize database connection and create tables"""
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row

        # Enable foreign keys
        await self._connection.execute("PRAGMA foreign_keys = ON")
        await self._connection.commit()

        # Read and execute schema
        schema_path = Path(__file__).parent / "sqlite_schema.sql"
        if schema_path.exists():
            schema_sql = schema_path.read_text()
            await self._connection.executescript(schema_sql)
            await self._connection.commit()
        else:
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

    async def close(self) -> None:
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None

    # ==================== Repository Operations ====================

    async def add_repository(self, repo_data: Dict[str, Any]) -> bool:
        """Add a repository to the database"""
        try:
            cursor = await self._connection.execute(
                """
                INSERT INTO repositories (
                    name_with_owner, name, owner, description,
                    primary_language, topics, stargazer_count, fork_count,
                    url, homepage_url, summary, categories, features,
                    tech_stack, use_cases, readme_summary, readme_path,
                    readme_content, search_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    repo_data.get("name_with_owner"),
                    repo_data.get("name"),
                    repo_data.get("owner"),
                    repo_data.get("description"),
                    repo_data.get("primary_language"),
                    json.dumps(repo_data.get("topics", []), ensure_ascii=False),
                    repo_data.get("stargazer_count", 0),
                    repo_data.get("fork_count", 0),
                    repo_data.get("url"),
                    repo_data.get("homepage_url"),
                    repo_data.get("summary"),
                    json.dumps(repo_data.get("categories", []), ensure_ascii=False),
                    json.dumps(repo_data.get("features", []), ensure_ascii=False),
                    json.dumps(repo_data.get("tech_stack", []), ensure_ascii=False),
                    json.dumps(repo_data.get("use_cases", []), ensure_ascii=False),
                    repo_data.get("readme_summary"),
                    repo_data.get("readme_path"),
                    repo_data.get("readme_content"),
                    self._build_search_text(repo_data)
                )
            )
            await self._connection.commit()

            # Insert categories
            repo_id = cursor.lastrowid
            await self._insert_categories(repo_id, repo_data.get("categories", []))
            await self._insert_tech_stack(repo_id, repo_data.get("tech_stack", []))

            return True
        except Exception as e:
            print(f"Error adding repository: {e}")
            return False

    async def get_repository(
        self,
        name_with_owner: str
    ) -> Optional[Dict[str, Any]]:
        """Get a repository by name_with_owner"""
        async with self._connection.execute(
            "SELECT * FROM repositories WHERE name_with_owner = ?",
            (name_with_owner,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_dict(row)
        return None

    async def search_repositories(
        self,
        categories: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search repositories with filters"""
        query = "SELECT DISTINCT r.* FROM repositories r"
        conditions = []
        params = []

        # Join with categories if filtering
        if categories:
            query += " JOIN repo_categories rc ON r.id = rc.repo_id"
            placeholders = ",".join(["?" for _ in categories])
            conditions.append(f"rc.category IN ({placeholders})")
            params.extend(categories)

        if languages:
            placeholders = ",".join(["?" for _ in languages])
            conditions.append(f"r.primary_language IN ({placeholders})")
            params.extend(languages)

        if min_stars is not None:
            conditions.append("r.stargazer_count >= ?")
            params.append(min_stars)

        if max_stars is not None:
            conditions.append("r.stargazer_count <= ?")
            params.append(max_stars)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY r.stargazer_count DESC LIMIT ?"
        params.append(limit)

        async with self._connection.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    async def update_repository(
        self,
        name_with_owner: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update an existing repository"""
        try:
            set_clauses = []
            params = []

            for key, value in updates.items():
                if key in ["categories", "features", "tech_stack", "use_cases", "topics", "languages"]:
                    set_clauses.append(f"{key} = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                else:
                    set_clauses.append(f"{key} = ?")
                    params.append(value)

            params.append(name_with_owner)

            await self._connection.execute(
                f"UPDATE repositories SET {', '.join(set_clauses)} WHERE name_with_owner = ?",
                params
            )
            await self._connection.commit()
            return True
        except Exception as e:
            print(f"Error updating repository: {e}")
            return False

    async def delete_repository(self, name_with_owner: str) -> bool:
        """Delete a repository"""
        try:
            await self._connection.execute(
                "DELETE FROM repositories WHERE name_with_owner = ?",
                (name_with_owner,)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            print(f"Error deleting repository: {e}")
            return False

    # ==================== Conversation Operations ====================

    async def create_conversation(self, session_id: str) -> int:
        """Create a new conversation session"""
        cursor = await self._connection.execute(
            "INSERT INTO conversations (session_id) VALUES (?)",
            (session_id,)
        )
        await self._connection.commit()
        return cursor.lastrowid

    async def get_conversation(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a conversation"""
        # First ensure conversation exists
        await self._connection.execute(
            "INSERT OR IGNORE INTO conversations (session_id) VALUES (?)",
            (session_id,)
        )
        await self._connection.commit()

        # Get messages
        async with self._connection.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE conversation_id = (SELECT id FROM conversations WHERE session_id = ?)
            ORDER BY created_at ASC
            """,
            (session_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> int:
        """Save a message to a conversation"""
        # Ensure conversation exists
        await self._connection.execute(
            "INSERT OR IGNORE INTO conversations (session_id) VALUES (?)",
            (session_id,)
        )

        cursor = await self._connection.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES ((SELECT id FROM conversations WHERE session_id = ?), ?, ?)
            """,
            (session_id, role, content)
        )
        await self._connection.commit()
        return cursor.lastrowid

    async def delete_conversation(self, session_id: str) -> bool:
        """Delete a conversation and all its messages"""
        try:
            await self._connection.execute(
                "DELETE FROM conversations WHERE session_id = ?",
                (session_id,)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False

    # ==================== Statistics ====================

    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        async with self._connection.execute(
            "SELECT COUNT(*) FROM repositories"
        ) as cursor:
            total_repos = (await cursor.fetchone())[0]

        async with self._connection.execute(
            """
            SELECT category, COUNT(*) as count
            FROM repo_categories
            GROUP BY category
            ORDER BY count DESC
            """
        ) as cursor:
            categories = {row[0]: row[1] for row in await cursor.fetchall()}

        async with self._connection.execute(
            "SELECT COUNT(DISTINCT session_id) FROM conversations"
        ) as cursor:
            total_conversations = (await cursor.fetchone())[0]

        return {
            "total_repositories": total_repos,
            "total_conversations": total_conversations,
            "categories": categories,
            "database_path": self.db_path
        }

    # ==================== Helper Methods ====================

    async def _insert_categories(self, repo_id: int, categories: List[str]):
        """Insert categories for a repository"""
        for category in categories:
            await self._connection.execute(
                "INSERT OR IGNORE INTO repo_categories (repo_id, category) VALUES (?, ?)",
                (repo_id, category)
            )
        await self._connection.commit()

    async def _insert_tech_stack(self, repo_id: int, tech_stack: List[str]):
        """Insert tech stack for a repository"""
        for tech in tech_stack:
            await self._connection.execute(
                "INSERT OR IGNORE INTO repo_tech_stack (repo_id, tech) VALUES (?, ?)",
                (repo_id, tech)
            )
        await self._connection.commit()

    def _build_search_text(self, repo_data: Dict[str, Any]) -> str:
        """Build combined search text from repository data"""
        parts = [
            repo_data.get("name_with_owner", ""),
            repo_data.get("description", ""),
            repo_data.get("summary", ""),
            repo_data.get("readme_summary", ""),
        ]
        return " ".join(p for p in parts if p)

    def _row_to_dict(self, row: aiosqlite.Row) -> Dict[str, Any]:
        """Convert database row to dictionary"""
        d = dict(row)
        # Parse JSON fields
        for key in ["categories", "features", "tech_stack", "use_cases", "topics", "languages"]:
            if key in d and d[key]:
                try:
                    d[key] = json.loads(d[key])
                except:
                    d[key] = []
        return d
