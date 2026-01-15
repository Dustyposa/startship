"""
SQLite database implementation.
"""
import json
import aiosqlite
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
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

        # Add FTS5 full-text search table
        await self.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS repositories_fts USING fts5(
                name_with_owner,
                name,
                description,
                summary,
                content='repositories',
                content_rowid='rowid'
            )
        """)

        # Add FTS5 triggers to keep FTS5 table in sync
        await self.execute("""
            CREATE TRIGGER IF NOT EXISTS repositories_ai AFTER INSERT ON repositories BEGIN
                INSERT INTO repositories_fts(rowid, name_with_owner, name, description, summary)
                VALUES (new.rowid, new.name_with_owner, new.name, new.description, new.summary);
            END
        """)

        await self.execute("""
            CREATE TRIGGER IF NOT EXISTS repositories_ad AFTER DELETE ON repositories BEGIN
                INSERT INTO repositories_fts(repositories_fts, rowid, name_with_owner, name, description, summary)
                VALUES ('delete', old.rowid, old.name_with_owner, old.name, old.description, old.summary);
            END
        """)

        await self.execute("""
            CREATE TRIGGER IF NOT EXISTS repositories_au AFTER UPDATE ON repositories BEGIN
                INSERT INTO repositories_fts(repositories_fts, rowid, name_with_owner, name, description, summary)
                VALUES ('delete', old.rowid, old.name_with_owner, old.name, old.description, old.summary);
                INSERT INTO repositories_fts(rowid, name_with_owner, name, description, summary)
                VALUES (new.rowid, new.name_with_owner, new.name, new.description, new.summary);
            END
        """)

        # Run database migrations
        await self._run_migrations()

    async def close(self) -> None:
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None

    # ==================== Generic Helper Methods ====================

    async def _update_entity(
        self,
        table: str,
        entity_id: str,
        **fields
    ) -> bool:
        """Generic method to update any entity by ID."""
        updates = []
        params = []
        for key, value in fields.items():
            if value is not None:
                updates.append(f"{key} = ?")
                params.append(value)

        if updates:
            params.append(entity_id)
            await self._connection.execute(
                f"UPDATE {table} SET {', '.join(updates)} WHERE id = ?",
                params
            )
            await self._connection.commit()
        return True

    async def _delete_entity(self, table: str, id_field: str, entity_id: str) -> bool:
        """Generic method to delete any entity by ID."""
        await self._connection.execute(
            f"DELETE FROM {table} WHERE {id_field} = ?",
            (entity_id,)
        )
        await self._connection.commit()
        return True

    async def _get_entity(
        self,
        table: str,
        id_field: str,
        entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """Generic method to get any entity by ID."""
        async with self._connection.execute(
            f"SELECT * FROM {table} WHERE {id_field} = ?",
            (entity_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def execute(self, sql: str) -> None:
        """Execute a SQL statement"""
        await self._connection.execute(sql)
        await self._connection.commit()

    async def _run_migrations(self) -> None:
        """Run pending database migrations.

        This method manages database schema migrations by:
        1. Creating a _migrations tracking table if it doesn't exist
        2. Scanning the migrations directory for .sql files
        3. Executing unapplied migrations in sorted order
        4. Recording applied migrations to prevent re-execution

        Raises:
            Exception: If a migration fails, rolls back the transaction
                and re-raises the exception to prevent partial migrations.
        """
        migration_dir = Path(__file__).parent / "migrations"
        if not migration_dir.exists():
            return

        # Track executed migrations
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Find and run unapplied migrations
        for migration_file in sorted(migration_dir.glob("*.sql")):
            migration_name = migration_file.name
            # Check if already applied
            result = await self._connection.execute(
                "SELECT 1 FROM _migrations WHERE name = ?",
                (migration_name,)
            )
            if not await result.fetchone():
                # Run migration with error handling and rollback
                try:
                    sql = migration_file.read_text()
                    await self._connection.executescript(sql)
                    await self._connection.execute(
                        "INSERT INTO _migrations (name) VALUES (?)",
                        (migration_name,)
                    )
                    await self._connection.commit()
                except Exception as e:
                    await self._connection.rollback()
                    raise

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
                    readme_content, search_text, starred_at,
                    pushed_at, archived, visibility, owner_type, organization
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    self._build_search_text(repo_data),
                    repo_data.get("starred_at"),
                    # New GitHub metadata fields
                    repo_data.get("pushed_at"),
                    repo_data.get("archived", 0),
                    repo_data.get("visibility", "public"),
                    repo_data.get("owner_type"),
                    repo_data.get("organization")
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

    async def execute_query(self, sql: str, params: Tuple = ()) -> None:
        """Execute a raw SQL query (for inserts, updates, etc.)."""
        await self._connection.execute(sql, params)
        await self._connection.commit()

    async def search_repositories(
        self,
        categories: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        limit: int = 10,
        # New filter dimensions
        is_active: Optional[bool] = None,
        is_new: Optional[bool] = None,
        owner_type: Optional[str] = None,
        exclude_archived: bool = True,
        is_deleted: Optional[bool] = False,
        # Sorting
        sort_by: Optional[str] = None,
        sort_order: str = "DESC"
    ) -> List[Dict[str, Any]]:
        """Search repositories with filters"""
        from datetime import datetime, timedelta

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

        # New filter dimensions
        if is_active:
            # Active: pushed within last 7 days
            seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            conditions.append("r.pushed_at >= ?")
            params.append(seven_days_ago)

        if is_new:
            # New: created within last 6 months
            six_months_ago = (datetime.utcnow() - timedelta(days=180)).isoformat()
            conditions.append("r.created_at >= ?")
            params.append(six_months_ago)

        if owner_type:
            conditions.append("r.owner_type = ?")
            params.append(owner_type)

        if exclude_archived:
            conditions.append("r.archived = 0")

        # Soft delete filter
        if is_deleted is not None:
            conditions.append("r.is_deleted = ?")
            params.append(1 if is_deleted else 0)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Sorting
        valid_sort_fields = {
            "stargazer_count": "r.stargazer_count",
            "last_synced_at": "r.last_synced_at",
            "pushed_at": "r.pushed_at",
            "created_at": "r.created_at",
            "name": "r.name"
        }
        sort_field = valid_sort_fields.get(sort_by, "r.stargazer_count")
        query += f" ORDER BY {sort_field} {sort_order if sort_order in ('ASC', 'DESC') else 'DESC'}"
        query += " LIMIT ?"
        params.append(limit)

        async with self._connection.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    async def search_repositories_fulltext(
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
        if not query:
            return []

        async with self._connection.execute(
            """SELECT r.* FROM repositories r
               INNER JOIN repositories_fts fts ON r.rowid = fts.rowid
               WHERE repositories_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (query, limit)
        ) as cursor:
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
        """Delete a repository."""
        return await self._delete_entity("repositories", "name_with_owner", name_with_owner)

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
        """Delete a conversation and all its messages."""
        return await self._delete_entity("conversations", "session_id", session_id)

    # ==================== Statistics ====================

    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        async with self._connection.execute(
            "SELECT COUNT(*) FROM repositories"
        ) as cursor:
            total_repos = (await cursor.fetchone())[0]

        # Get languages instead of topics categories
        async with self._connection.execute(
            """
            SELECT primary_language, COUNT(*) as count
            FROM repositories
            WHERE primary_language IS NOT NULL AND primary_language != ''
            GROUP BY primary_language
            ORDER BY count DESC
            """
        ) as cursor:
            languages = {row[0]: row[1] for row in await cursor.fetchall()}

        async with self._connection.execute(
            "SELECT COUNT(DISTINCT session_id) FROM conversations"
        ) as cursor:
            total_conversations = (await cursor.fetchone())[0]

        # Get top language
        async with self._connection.execute(
            """
            SELECT primary_language, COUNT(*) as count
            FROM repositories
            WHERE primary_language IS NOT NULL AND primary_language != ''
            GROUP BY primary_language
            ORDER BY count DESC
            LIMIT 1
            """
        ) as cursor:
            row = await cursor.fetchone()
            top_language = row[0] if row else None

        # Derived tag counts
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        six_months_ago = now - timedelta(days=180)

        async with self._connection.execute(
            """
            SELECT COUNT(*) FROM repositories
            WHERE stargazer_count >= 10000
            """
        ) as cursor:
            popular_count = (await cursor.fetchone())[0]

        async with self._connection.execute(
            f"""
            SELECT COUNT(*) FROM repositories
            WHERE indexed_at >= '{seven_days_ago.strftime('%Y-%m-%d')}'
            """
        ) as cursor:
            active_count = (await cursor.fetchone())[0]

        async with self._connection.execute(
            f"""
            SELECT COUNT(*) FROM repositories
            WHERE created_at >= '{six_months_ago.strftime('%Y-%m-%d')}'
            """
        ) as cursor:
            new_count = (await cursor.fetchone())[0]

        return {
            "total_repositories": total_repos,
            "total_conversations": total_conversations,
            "languages": languages,
            "top_language": top_language,
            "database_path": self.db_path,
            # Derived tags
            "derived_tags": {
                "popular": popular_count,
                "active": active_count,
                "new": new_count
            }
        }

    # ==================== Collections Operations ====================

    async def get_collections(self) -> List[Dict[str, Any]]:
        """Get all collections ordered by position"""
        async with self._connection.execute(
            "SELECT * FROM collections ORDER BY position ASC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_collection(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """Get a collection by id"""
        async with self._connection.execute(
            "SELECT * FROM collections WHERE id = ?",
            (collection_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def create_collection(
        self,
        collection_id: str,
        name: str,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        position: int = 0
    ) -> bool:
        """Create a new collection"""
        try:
            await self._connection.execute(
                """
                INSERT INTO collections (id, name, icon, color, position)
                VALUES (?, ?, ?, ?, ?)
                """,
                (collection_id, name, icon, color, position)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False

    async def update_collection(
        self,
        collection_id: str,
        name: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        position: Optional[int] = None
    ) -> bool:
        """Update a collection."""
        return await self._update_entity("collections", collection_id, name=name, icon=icon, color=color, position=position)

    async def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection (cascade will remove repo associations)."""
        return await self._delete_entity("collections", "id", collection_id)

    # ==================== Tags Operations ====================

    async def get_tags(self) -> List[Dict[str, Any]]:
        """Get all tags"""
        async with self._connection.execute(
            "SELECT * FROM tags ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_tag(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """Get a tag by id"""
        async with self._connection.execute(
            "SELECT * FROM tags WHERE id = ?",
            (tag_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def create_tag(
        self,
        tag_id: str,
        name: str,
        color: str = "#3B82F6"
    ) -> bool:
        """Create a new tag"""
        try:
            await self._connection.execute(
                """
                INSERT INTO tags (id, name, color)
                VALUES (?, ?, ?)
                """,
                (tag_id, name, color)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            print(f"Error creating tag: {e}")
            return False

    async def update_tag(
        self,
        tag_id: str,
        name: Optional[str] = None,
        color: Optional[str] = None
    ) -> bool:
        """Update a tag."""
        return await self._update_entity("tags", tag_id, name=name, color=color)

    async def delete_tag(self, tag_id: str) -> bool:
        """Delete a tag (cascade will remove repo associations)."""
        return await self._delete_entity("tags", "id", tag_id)

    # ==================== Repo-Collection Operations ====================

    async def add_repo_to_collection(
        self,
        repo_id: str,
        collection_id: str,
        position: int = 0
    ) -> bool:
        """Add a repository to a collection"""
        try:
            # First remove from any existing collection
            await self._connection.execute(
                "DELETE FROM repo_collections WHERE repo_id = ?",
                (repo_id,)
            )
            # Add to new collection
            await self._connection.execute(
                """
                INSERT INTO repo_collections (repo_id, collection_id, position)
                VALUES (?, ?, ?)
                """,
                (repo_id, collection_id, position)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            print(f"Error adding repo to collection: {e}")
            return False

    async def remove_repo_from_collection(
        self,
        repo_id: str,
        collection_id: Optional[str] = None
    ) -> bool:
        """Remove a repository from a collection (or all collections)"""
        try:
            if collection_id:
                await self._connection.execute(
                    "DELETE FROM repo_collections WHERE repo_id = ? AND collection_id = ?",
                    (repo_id, collection_id)
                )
            else:
                await self._connection.execute(
                    "DELETE FROM repo_collections WHERE repo_id = ?",
                    (repo_id,)
                )
            await self._connection.commit()
            return True
        except Exception as e:
            print(f"Error removing repo from collection: {e}")
            return False

    async def get_repos_in_collection(self, collection_id: str) -> List[str]:
        """Get all repo IDs in a collection"""
        async with self._connection.execute(
            """
            SELECT repo_id FROM repo_collections
            WHERE collection_id = ?
            ORDER BY position ASC
            """,
            (collection_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def get_collection_for_repo(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get the collection a repository belongs to"""
        async with self._connection.execute(
            """
            SELECT c.* FROM collections c
            INNER JOIN repo_collections rc ON c.id = rc.collection_id
            WHERE rc.repo_id = ?
            """,
            (repo_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    # ==================== Repo-Tag Operations ====================

    async def add_tag_to_repo(self, repo_id: str, tag_id: str) -> bool:
        """Add a tag to a repository"""
        try:
            await self._connection.execute(
                """
                INSERT INTO repo_tags (repo_id, tag_id)
                VALUES (?, ?)
                """,
                (repo_id, tag_id)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            print(f"Error adding tag to repo: {e}")
            return False

    async def remove_tag_from_repo(self, repo_id: str, tag_id: str) -> bool:
        """Remove a tag from a repository."""
        try:
            await self._connection.execute(
                "DELETE FROM repo_tags WHERE repo_id = ? AND tag_id = ?",
                (repo_id, tag_id)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            print(f"Error removing tag from repo: {e}")
            return False

    async def get_tags_for_repo(self, repo_id: str) -> List[Dict[str, Any]]:
        """Get all tags for a repository"""
        async with self._connection.execute(
            """
            SELECT t.* FROM tags t
            INNER JOIN repo_tags rt ON t.id = rt.tag_id
            WHERE rt.repo_id = ?
            ORDER BY t.name ASC
            """,
            (repo_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_repos_for_tag(self, tag_id: str) -> List[str]:
        """Get all repo IDs that have a tag"""
        async with self._connection.execute(
            "SELECT repo_id FROM repo_tags WHERE tag_id = ?",
            (tag_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    # ==================== Notes Operations ====================

    async def get_note(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get a note for a repository"""
        async with self._connection.execute(
            "SELECT * FROM notes WHERE repo_id = ?",
            (repo_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def upsert_note(
        self,
        repo_id: str,
        note: Optional[str] = None,
        rating: Optional[int] = None
    ) -> bool:
        """Create or update a note for a repository"""
        try:
            await self._connection.execute(
                """
                INSERT INTO notes (repo_id, note, rating)
                VALUES (?, ?, ?)
                ON CONFLICT(repo_id) DO UPDATE SET
                    note = excluded.note,
                    rating = excluded.rating,
                    updated_at = datetime('now')
                """,
                (repo_id, note, rating)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            print(f"Error upserting note: {e}")
            return False

    async def delete_note(self, repo_id: str) -> bool:
        """Delete a note for a repository."""
        return await self._delete_entity("notes", "repo_id", repo_id)

    async def get_all_notes(self) -> List[Dict[str, Any]]:
        """Get all notes"""
        async with self._connection.execute(
            "SELECT * FROM notes ORDER BY updated_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== User Settings Operations ====================

    async def get_setting(self, key: str) -> Optional[str]:
        """Get a user setting value"""
        async with self._connection.execute(
            "SELECT value FROM user_settings WHERE key = ?",
            (key,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def set_setting(self, key: str, value: str) -> bool:
        """Set a user setting value"""
        try:
            await self._connection.execute(
                """
                INSERT INTO user_settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = datetime('now')
                """,
                (key, value)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            print(f"Error setting user setting: {e}")
            return False

    async def get_all_settings(self) -> Dict[str, str]:
        """Get all user settings"""
        async with self._connection.execute(
            "SELECT key, value FROM user_settings"
        ) as cursor:
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}

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
