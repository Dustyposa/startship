# Phase 1: Foundation Framework - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up the project foundation including directory structure, SQLite database layer, configuration management, and basic FastAPI application.

**Architecture:** Clean layered architecture with API → Services → Database. SQLite as default database with optional PostgreSQL support. Pydantic for configuration and validation.

**Tech Stack:** FastAPI, aiosqlite, Pydantic Settings, pytest, pytest-asyncio

---

## Task 1: Create Project Directory Structure

**Files:**
- Create: `src/__init__.py`
- Create: `src/api/__init__.py`
- Create: `src/db/__init__.py`
- Create: `src/services/__init__.py`
- Create: `src/llm/__init__.py`
- Create: `src/github/__init__.py`
- Create: `src/core/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`
- Create: `data/.gitkeep`
- Create: `static/.gitkeep`

**Step 1: Create all directories and __init__py files**

Run:
```bash
mkdir -p src/{api,db,services,llm,github,core}
mkdir -p data/readmes
mkdir -p tests/{unit,integration}
mkdir -p static
touch src/__init__.py src/api/__init__.py src/db/__init__.py src/services/__init__.py
touch src/llm/__init__.py src/github/__init__.py src/core/__init__.py
touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py
touch data/.gitkeep static/.gitkeep
```

Expected: All directories created with `__init__.py` files

**Step 2: Verify structure**

Run:
```bash
tree -L 2 src/ tests/ data/ static/ || find src/ tests/ data/ static/ -type d | sort
```

Expected: Directory tree showing all created folders

**Step 3: Commit**

```bash
git add .
git commit -m "feat: create project directory structure"
```

---

## Task 2: Create Configuration Management

**Files:**
- Create: `src/config.py`
- Create: `.env.example`

**Step 1: Write configuration module**

Create `src/config.py`:

```python
"""
Configuration management using Pydantic Settings.
Load from environment variables or .env file.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "GitHub Star RAG Service"
    api_version: str = "1.0.0"

    # Database Configuration
    db_type: str = "sqlite"  # sqlite or postgresql
    sqlite_path: str = "data/starship.db"

    # PostgreSQL (optional)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "starship"
    postgres_user: str = "starship"
    postgres_password: str = ""

    # LLM Configuration
    llm_provider: str = "openai"  # openai, ollama
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""
    llm_base_url: Optional[str] = None
    llm_timeout: int = 60

    # GitHub Configuration
    github_token: Optional[str] = None

    # Storage
    readme_storage_path: str = "data/readmes"

    # Concurrency
    max_concurrent_llm: int = 5
    max_concurrent_github: int = 10

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
```

**Step 2: Create .env.example**

Create `.env.example`:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database
DB_TYPE=sqlite
SQLITE_PATH=data/starship.db

# LLM
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-xxx
# LLM_BASE_URL=http://localhost:11434/v1  # For Ollama

# GitHub (optional but recommended)
GITHUB_TOKEN=ghp_xxx

# Storage
README_STORAGE_PATH=data/readmes

# Concurrency
MAX_CONCURRENT_LLM=5
MAX_CONCURRENT_GITHUB=10
```

**Step 3: Write test for configuration**

Create `tests/unit/test_config.py`:

```python
import os
from src.config import Settings, settings


def test_default_settings():
    """Test default settings are loaded"""
    s = Settings()
    assert s.api_host == "0.0.0.0"
    assert s.api_port == 8000
    assert s.db_type == "sqlite"
    assert s.llm_provider == "openai"
    assert s.llm_model == "gpt-4o-mini"


def test_settings_from_env():
    """Test settings can be loaded from environment"""
    os.environ["API_PORT"] = "9000"
    os.environ["LLM_MODEL"] = "gpt-4o"
    s = Settings()
    assert s.api_port == 9000
    assert s.llm_model == "gpt-4o"
    # Clean up
    del os.environ["API_PORT"]
    del os.environ["LLM_MODEL"]


def test_global_settings_instance():
    """Test global settings instance exists"""
    assert settings is not None
    assert isinstance(settings, Settings)
```

**Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/unit/test_config.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/config.py .env.example tests/unit/test_config.py
git commit -m "feat: add configuration management with Pydantic Settings"
```

---

## Task 3: Create Database Abstraction Layer

**Files:**
- Create: `src/db/base.py`

**Step 1: Write database abstract base class**

Create `src/db/base.py`:

```python
"""
Database abstraction layer.
Supports SQLite and PostgreSQL through a common interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MemoryItem:
    """Memory item for conversation storage"""
    item_id: str
    content: str
    metadata: Dict[str, Any]


class Database(ABC):
    """
    Abstract database interface.

    All database operations must be async.
    Supports both SQLite and PostgreSQL implementations.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize database connection and create tables"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close database connection"""
        pass

    # ==================== Repository Operations ====================

    @abstractmethod
    async def add_repository(self, repo_data: Dict[str, Any]) -> bool:
        """
        Add a repository to the database.

        Args:
            repo_data: Repository data including metadata and LLM analysis

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_repository(
        self,
        name_with_owner: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a repository by name_with_owner.

        Args:
            name_with_owner: Format "owner/repo"

        Returns:
            Repository data or None if not found
        """
        pass

    @abstractmethod
    async def search_repositories(
        self,
        categories: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search repositories with filters.

        Args:
            categories: Filter by categories
            languages: Filter by programming languages
            min_stars: Minimum star count
            max_stars: Maximum star count
            limit: Maximum number of results

        Returns:
            List of matching repositories
        """
        pass

    @abstractmethod
    async def update_repository(
        self,
        name_with_owner: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update an existing repository"""
        pass

    @abstractmethod
    async def delete_repository(self, name_with_owner: str) -> bool:
        """Delete a repository"""
        pass

    # ==================== Conversation Operations ====================

    @abstractmethod
    async def create_conversation(
        self,
        session_id: str
    ) -> int:
        """
        Create a new conversation session.

        Args:
            session_id: Unique session identifier

        Returns:
            Conversation ID
        """
        pass

    @abstractmethod
    async def get_conversation(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all messages in a conversation.

        Args:
            session_id: Session identifier

        Returns:
            List of messages with role and content
        """
        pass

    @abstractmethod
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> int:
        """
        Save a message to a conversation.

        Args:
            session_id: Session identifier
            role: Message role ("user" or "assistant")
            content: Message content

        Returns:
            Message ID
        """
        pass

    @abstractmethod
    async def delete_conversation(self, session_id: str) -> bool:
        """Delete a conversation and all its messages"""
        pass

    # ==================== Statistics ====================

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with counts and metadata
        """
        pass
```

**Step 2: Write test for database interface**

Create `tests/unit/test_db_base.py`:

```python
import pytest
from src.db.base import Database


def test_database_is_abstract():
    """Test Database cannot be instantiated directly"""
    with pytest.raises(TypeError):
        Database()


def test_database_has_required_methods():
    """Test Database defines all required abstract methods"""
    abstract_methods = Database.__abstractmethods__

    required_methods = [
        'initialize', 'close',
        'add_repository', 'get_repository', 'search_repositories',
        'update_repository', 'delete_repository',
        'create_conversation', 'get_conversation',
        'save_message', 'delete_conversation',
        'get_statistics'
    ]

    for method in required_methods:
        assert method in abstract_methods, f"Missing abstract method: {method}"
```

**Step 3: Run tests to verify they pass**

Run:
```bash
pytest tests/unit/test_db_base.py -v
```

Expected: All tests PASS

**Step 4: Commit**

```bash
git add src/db/base.py tests/unit/test_db_base.py
git commit -m "feat: add database abstraction layer"
```

---

## Task 4: Implement SQLite Database

**Files:**
- Create: `src/db/sqlite.py`
- Create: `src/db/sqlite_schema.sql`

**Step 1: Write SQL schema**

Create `src/db/sqlite_schema.sql`:

```sql
-- ============================================
-- GitHub Star RAG Service - SQLite Schema
-- ============================================

-- Drop existing tables if recreating
-- DROP TABLE IF EXISTS messages;
-- DROP TABLE IF EXISTS conversations;
-- DROP TABLE IF EXISTS repo_tech_stack;
-- DROP TABLE IF EXISTS repo_categories;
-- DROP TABLE IF EXISTS repositories;

-- ============================================
-- Repositories table
-- ============================================
CREATE TABLE IF NOT EXISTS repositories (
    -- Primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Basic information
    name_with_owner TEXT UNIQUE NOT NULL,  -- Format: "owner/repo"
    name TEXT NOT NULL,
    owner TEXT NOT NULL,

    -- Metadata from GitHub
    description TEXT,
    primary_language TEXT,
    languages TEXT,                      -- JSON array: ["Python": 80, "JS": 20]
    topics TEXT,                         -- JSON array: ["web", "api"]
    stargazer_count INTEGER DEFAULT 0,
    fork_count INTEGER DEFAULT 0,
    url TEXT,
    homepage_url TEXT,

    -- LLM analysis results
    summary TEXT,                        -- One-line summary
    categories TEXT,                     -- JSON array: ["工具", "前端"]
    features TEXT,                       -- JSON array of features
    tech_stack TEXT,                     -- JSON array of technologies
    use_cases TEXT,                      -- JSON array of use cases
    readme_summary TEXT,                 -- Summary of README

    -- README storage
    readme_path TEXT,                    -- Path to README file
    readme_content TEXT,                 -- Cached README content (optional)

    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    indexed_at TEXT DEFAULT (datetime('now')),

    -- Full-text search
    search_text TEXT                     -- Combined text for FTS
);

-- ============================================
-- Repository categories (many-to-many)
-- ============================================
CREATE TABLE IF NOT EXISTS repo_categories (
    repo_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    PRIMARY KEY (repo_id, category),
    FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE
);

-- ============================================
-- Repository tech stack (many-to-many)
-- ============================================
CREATE TABLE IF NOT EXISTS repo_tech_stack (
    repo_id INTEGER NOT NULL,
    tech TEXT NOT NULL,
    PRIMARY KEY (repo_id, tech),
    FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE
);

-- ============================================
-- Conversations (chat sessions)
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ============================================
-- Messages (within conversations)
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL,                  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- ============================================
-- Indexes for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_repos_name_with_owner ON repositories(name_with_owner);
CREATE INDEX IF NOT EXISTS idx_repos_language ON repositories(primary_language);
CREATE INDEX IF NOT EXISTS idx_repos_stars ON repositories(stargazer_count);
CREATE INDEX IF NOT EXISTS idx_repos_indexed_at ON repositories(indexed_at);

CREATE INDEX IF NOT EXISTS idx_categories_category ON repo_categories(category);
CREATE INDEX IF NOT EXISTS idx_categories_repo ON repo_categories(repo_id);

CREATE INDEX IF NOT EXISTS idx_tech_stack_tech ON repo_tech_stack(tech);
CREATE INDEX IF NOT EXISTS idx_tech_stack_repo ON repo_tech_stack(repo_id);

CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);

-- ============================================
-- Trigger to update updated_at timestamp
-- ============================================
CREATE TRIGGER IF NOT EXISTS update_repositories_timestamp
AFTER UPDATE ON repositories
FOR EACH ROW
BEGIN
    UPDATE repositories SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_conversations_timestamp
AFTER UPDATE ON conversations
FOR EACH ROW
BEGIN
    UPDATE conversations SET updated_at = datetime('now') WHERE id = NEW.id;
END;
```

**Step 2: Write SQLite implementation**

Create `src/db/sqlite.py`:

```python
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
            async with self._connection.execute(
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
            repo_id = self._connection.lastrowid
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
        await self._connection.execute(
            "INSERT INTO conversations (session_id) VALUES (?)",
            (session_id,)
        )
        await self._connection.commit()
        return self._connection.lastrowid

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

        await self._connection.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES ((SELECT id FROM conversations WHERE session_id = ?), ?, ?)
            """,
            (session_id, role, content)
        )
        await self._connection.commit()
        return self._connection.lastrowid

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
```

**Step 3: Write tests for SQLite implementation**

Create `tests/unit/test_sqlite.py`:

```python
import pytest
import asyncio
from aiosqlite import Error as AiosqliteError
from src.db.sqlite import SQLiteDatabase


@pytest.fixture
async def db():
    """Create a test database"""
    db = SQLiteDatabase(":memory:")  # Use in-memory database for tests
    await db.initialize()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_initialize_creates_tables(db):
    """Test database initialization creates all tables"""
    async with db._connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ) as cursor:
        tables = [row[0] for row in await cursor.fetchall()]

    assert "repositories" in tables
    assert "repo_categories" in tables
    assert "repo_tech_stack" in tables
    assert "conversations" in tables
    assert "messages" in tables


@pytest.mark.asyncio
async def test_add_repository(db):
    """Test adding a repository"""
    repo_data = {
        "name_with_owner": "test/repo",
        "name": "repo",
        "owner": "test",
        "description": "Test repository",
        "primary_language": "Python",
        "stargazer_count": 100,
        "fork_count": 10,
        "url": "https://github.com/test/repo",
        "categories": ["工具", "测试"],
        "tech_stack": ["Python", "FastAPI"],
        "summary": "A test repository"
    }

    result = await db.add_repository(repo_data)
    assert result is True

    # Verify it was added
    retrieved = await db.get_repository("test/repo")
    assert retrieved is not None
    assert retrieved["name_with_owner"] == "test/repo"
    assert retrieved["description"] == "Test repository"


@pytest.mark.asyncio
async def test_search_repositories(db):
    """Test searching repositories"""
    # Add test data
    repos = [
        {
            "name_with_owner": "owner1/repo1",
            "name": "repo1",
            "owner": "owner1",
            "primary_language": "Python",
            "stargazer_count": 100,
            "categories": ["工具"],
            "tech_stack": ["Python"]
        },
        {
            "name_with_owner": "owner2/repo2",
            "name": "repo2",
            "owner": "owner2",
            "primary_language": "JavaScript",
            "stargazer_count": 200,
            "categories": ["前端"],
            "tech_stack": ["JavaScript"]
        },
        {
            "name_with_owner": "owner3/repo3",
            "name": "repo3",
            "owner": "owner3",
            "primary_language": "Python",
            "stargazer_count": 300,
            "categories": ["工具"],
            "tech_stack": ["Python"]
        }
    ]

    for repo in repos:
        await db.add_repository(repo)

    # Test category filter
    results = await db.search_repositories(categories=["工具"])
    assert len(results) == 2

    # Test language filter
    results = await db.search_repositories(languages=["Python"])
    assert len(results) == 2

    # Test min_stars filter
    results = await db.search_repositories(min_stars=200)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_conversation_operations(db):
    """Test conversation CRUD operations"""
    session_id = "test-session-123"

    # Create conversation and add messages
    await db.save_message(session_id, "user", "Hello")
    await db.save_message(session_id, "assistant", "Hi there!")

    # Get conversation
    messages = await db.get_conversation(session_id)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hi there!"

    # Delete conversation
    result = await db.delete_conversation(session_id)
    assert result is True

    # Verify deletion
    messages = await db.get_conversation(session_id)
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_get_statistics(db):
    """Test getting database statistics"""
    # Add test data
    await db.add_repository({
        "name_with_owner": "test/repo1",
        "name": "repo1",
        "owner": "test",
        "categories": ["工具"],
        "tech_stack": ["Python"]
    })

    stats = await db.get_statistics()
    assert stats["total_repositories"] == 1
    assert "工具" in stats["categories"]
    assert stats["categories"]["工具"] == 1
```

**Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/unit/test_sqlite.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/db/sqlite.py src/db/sqlite_schema.sql tests/unit/test_sqlite.py
git commit -m "feat: implement SQLite database layer"
```

---

## Task 5: Create Database Factory

**Files:**
- Modify: `src/db/__init__.py`

**Step 1: Write database factory function**

Modify `src/db/__init__.py`:

```python
"""
Database package with factory function.
"""
from .base import Database
from .sqlite import SQLiteDatabase

__all__ = ["Database", "SQLiteDatabase", "create_database"]


def create_database(db_type: str = "sqlite", **config) -> Database:
    """
    Factory function to create database instance.

    Args:
        db_type: Type of database ("sqlite" or "postgresql")
        **config: Configuration parameters for the database

    Returns:
        Database instance

    Raises:
        ValueError: If db_type is not supported

    Examples:
        >>> db = create_database("sqlite", db_path="data/starship.db")
        >>> db = create_database("postgresql", host="localhost", database="starship")
    """
    if db_type == "sqlite":
        return SQLiteDatabase(
            db_path=config.get("db_path", config.get("sqlite_path", "data/starship.db"))
        )
    elif db_type == "postgresql":
        # TODO: Implement PostgreSQL
        raise NotImplementedError("PostgreSQL support not yet implemented")
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
```

**Step 2: Write test for database factory**

Create `tests/unit/test_db_factory.py`:

```python
import pytest
from src.db import create_database, SQLiteDatabase


def test_create_sqlite_database():
    """Test creating SQLite database"""
    db = create_database("sqlite", db_path=":memory:")
    assert isinstance(db, SQLiteDatabase)


def test_create_sqlite_with_default_path():
    """Test creating SQLite database with default path"""
    db = create_database("sqlite")
    assert isinstance(db, SQLiteDatabase)
    assert db.db_path == "data/starship.db"


def test_create_unsupported_database_type():
    """Test creating unsupported database type raises error"""
    with pytest.raises(ValueError, match="Unsupported database type"):
        create_database("mysql")


def test_create_postgresql_not_implemented():
    """Test PostgreSQL is not yet implemented"""
    with pytest.raises(NotImplementedError):
        create_database("postgresql")
```

**Step 3: Run tests to verify they pass**

Run:
```bash
pytest tests/unit/test_db_factory.py -v
```

Expected: All tests PASS

**Step 4: Commit**

```bash
git add src/db/__init__.py tests/unit/test_db_factory.py
git commit -m "feat: add database factory function"
```

---

## Task 6: Create Basic FastAPI Application

**Files:**
- Create: `src/api/app.py`

**Step 1: Write basic FastAPI application**

Create `src/api/app.py`:

```python
"""
FastAPI application for GitHub Star RAG Service.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print(f"Starting {settings.api_title} v{settings.api_version}")
    yield
    # Shutdown
    print("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.api_version
    }


@app.get("/stats")
async def get_stats():
    """
    Get service statistics.

    TODO: Implement actual statistics
    """
    return {
        "status": "ok",
        "message": "Statistics not yet implemented"
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "status_code": 500
    }
```

**Step 2: Write tests for API endpoints**

Create `tests/unit/test_app.py`:

```python
import pytest
from fastapi.testclient import TestClient
from src.api.app import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert data["status"] == "running"


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_stats_endpoint(client):
    """Test stats endpoint"""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_cors_headers(client):
    """Test CORS headers are set"""
    response = client.options("/")
    assert "access-control-allow-origin" in response.headers
```

**Step 3: Run tests to verify they pass**

Run:
```bash
pytest tests/unit/test_app.py -v
```

Expected: All tests PASS

**Step 4: Test manually that server starts**

Run:
```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 &
sleep 2
curl http://localhost:8000/health
curl http://localhost:8000/
pkill -f uvicorn
```

Expected: Both endpoints return 200 OK

**Step 5: Commit**

```bash
git add src/api/app.py tests/unit/test_app.py
git commit -m "feat: create basic FastAPI application"
```

---

## Task 7: Create Database Lifecycle Management

**Files:**
- Modify: `src/api/app.py`

**Step 1: Add database initialization to lifespan**

Modify `src/api/app.py`:

```python
"""
FastAPI application for GitHub Star RAG Service.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.db import create_database


# Global database instance
db = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global db

    # Startup
    print(f"Starting {settings.api_title} v{settings.api_version}")

    # Initialize database
    db = create_database(
        db_type=settings.db_type,
        sqlite_path=settings.sqlite_path
    )
    await db.initialize()
    print(f"Database initialized: {settings.db_type}")

    yield

    # Shutdown
    print("Shutting down application")
    if db:
        await db.close()
        print("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.api_version
    }


@app.get("/stats")
async def get_stats():
    """
    Get service statistics.
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    stats = await db.get_statistics()
    return {
        "success": True,
        "data": stats
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "status_code": 500
    }
```

**Step 2: Write integration test for database lifecycle**

Create `tests/integration/test_database_lifecycle.py`:

```python
import pytest
from fastapi.testclient import TestClient
from src.api.app import app


@pytest.fixture
def client():
    """Create test client with lifespan"""
    return TestClient(app)


def test_stats_endpoint_returns_data(client):
    """Test stats endpoint returns database statistics"""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "total_repositories" in data["data"]


def test_database_is_initialized(client):
    """Test database is initialized on startup"""
    # The stats endpoint requires database to be initialized
    response = client.get("/stats")
    assert response.status_code == 200
    # If database wasn't initialized, would return 503
```

**Step 3: Run tests to verify they pass**

Run:
```bash
pytest tests/integration/test_database_lifecycle.py -v
```

Expected: All tests PASS

**Step 4: Commit**

```bash
git add src/api/app.py tests/integration/test_database_lifecycle.py
git commit -m "feat: add database lifecycle management"
```

---

## Task 8: Update Project Configuration Files

**Files:**
- Modify: `pyproject.toml`
- Create: `requirements.txt`
- Modify: `.gitignore`

**Step 1: Update pyproject.toml dependencies**

Read current `pyproject.toml` and update dependencies section:

Run to check current dependencies:
```bash
cat /Users/dustyposa/data/open_source/ai/startship/pyproject.toml
```

Then modify to add new dependencies (if not present):

Add to `dependencies` section:
```toml
dependencies = [
    # Existing dependencies...
    "mcp[cli]>=1.0.0",
    "fastapi>=0.116.1",
    "python-dotenv>=1.0.0",
    "uvicorn[standard]>=0.24.0",
    "chromadb>=0.4.0",
    "loguru>=0.7.3",
    "sentence-transformers>=5.0.0",
    "orjson>=3.11.1",
    "polars>=1.32.0",
    "llama-index-core>=0.14.3",
    "llama-index-embeddings-huggingface>=0.6.1",
    "llama-index-vector-stores-chroma>=0.5.3",
    "llama-index-retrievers-bm25>=0.6.5",
    "openai>=1.109.1",

    # New dependencies for Phase 1
    "pydantic-settings>=2.0.0",
    "aiosqlite>=0.19.0",
    "httpx>=0.25.0",
]
```

**Step 2: Create requirements.txt for pip users**

Create `requirements.txt`:

```txt
# Core dependencies
fastapi>=0.116.1
uvicorn[standard]>=0.24.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0

# Database
aiosqlite>=0.19.0

# HTTP client
httpx>=0.25.0

# LLM (optional, for production use)
openai>=1.109.1

# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0

# Logging
loguru>=0.7.3

# Utilities
orjson>=3.11.1
```

**Step 3: Update .gitignore**

Add to `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environments
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo

# Database
*.db
*.db-shm
*.db-wal
data/*.db

# Environment
.env
.env.local

# Logs
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/

# Distribution
dist/
build/
*.egg-info/

# README
README.md
```

**Step 4: Verify installation works**

Run:
```bash
pip install -r requirements.txt
python -c "from src.config import settings; print(f'Config loaded: {settings.api_title}')"
python -c "from src.db import create_database; print('Database module OK')"
python -c "from src.api.app import app; print('API module OK')"
```

Expected: All imports work without errors

**Step 5: Commit**

```bash
git add pyproject.toml requirements.txt .gitignore
git commit -m "feat: update project dependencies and configuration"
```

---

## Task 9: Create Entry Point Script

**Files:**
- Create: `src/main.py`

**Step 1: Write main entry point**

Create `src/main.py`:

```python
"""
Main entry point for running the server.
"""
import uvicorn
from src.config import settings


def main():
    """Run the FastAPI server"""
    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )


if __name__ == "__main__":
    main()
```

**Step 2: Add console script to pyproject.toml**

Add to `pyproject.toml`:

```toml
[project.scripts]
starship = "src.main:main"
```

**Step 3: Test entry point works**

Run:
```bash
python -m src.main &
PID=$!
sleep 3
curl http://localhost:8000/health
kill $PID
```

Expected: Server starts and health endpoint returns 200 OK

**Step 4: Commit**

```bash
git add src/main.py pyproject.toml
git commit -m "feat: add main entry point script"
```

---

## Task 10: Write Integration Test for Full Stack

**Files:**
- Create: `tests/integration/test_full_stack.py`

**Step 1: Write full stack integration test**

Create `tests/integration/test_full_stack.py`:

```python
import pytest
from fastapi.testclient import TestClient
from src.api.app import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_full_request_flow(client):
    """Test complete request flow"""
    # 1. Check health
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    # 2. Get stats (should have empty database)
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total_repositories"] == 0

    # 3. Root endpoint
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


def test_error_handling(client):
    """Test error handling"""
    # Test 404
    response = client.get("/nonexistent")
    assert response.status_code == 404

    # Test invalid method
    response = client.post("/health")
    # Should either return 405 or handle gracefully
    assert response.status_code in [200, 405]
```

**Step 2: Run all tests to ensure everything works**

Run:
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

Expected: All tests pass with reasonable coverage

**Step 3: Commit**

```bash
git add tests/integration/test_full_stack.py
git commit -m "test: add full stack integration tests"
```

---

## Task 11: Create Documentation

**Files:**
- Create: `README.phase1.md`
- Update: `README.md`

**Step 1: Create Phase 1 completion documentation**

Create `README.phase1.md`:

```markdown
# Phase 1: Foundation Framework - COMPLETED

## Overview

This document summarizes the completion of Phase 1 of the GitHub Star RAG Service refactoring.

## What Was Built

### 1. Project Structure
- Clean layered architecture: API → Services → Database
- Modular package structure
- Separated tests (unit/integration)

### 2. Configuration Management
- Pydantic Settings for type-safe configuration
- Environment variable support
- `.env` file support

### 3. Database Layer
- Abstract base class for database operations
- SQLite implementation with async support
- Full schema with indexes and triggers
- Support for repositories, categories, tech stack, conversations, messages

### 4. FastAPI Application
- Basic API framework
- Health check endpoint
- Statistics endpoint
- CORS middleware
- Database lifecycle management
- Error handling

### 5. Testing
- Unit tests for all components
- Integration tests for full stack
- >70% code coverage

## File Structure

```
startship/
├── src/
│   ├── api/
│   │   └── app.py              # FastAPI application
│   ├── db/
│   │   ├── __init__.py         # Factory function
│   │   ├── base.py             # Abstract base class
│   │   ├── sqlite.py           # SQLite implementation
│   │   └── sqlite_schema.sql   # Database schema
│   ├── config.py               # Configuration
│   └── main.py                 # Entry point
├── tests/
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── data/
│   └── starship.db             # SQLite database (created at runtime)
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## Running the Application

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run server
python -m src.main
# Or:
uvicorn src.api.app:app --reload
```

### Using the CLI

```bash
# After installation
starship
```

### API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /stats` - Database statistics

## Next Steps

Proceed to [Phase 2: Core Services](../plans/2025-12-28-phase2-services.md)

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_sqlite.py -v
```

## Notes

- SQLite is the default database (zero configuration)
- PostgreSQL support is planned but not implemented
- All database operations are async
- The application uses lifespan management for database connections
```

**Step 2: Update main README with Phase 1 status**

Add to main `README.md` (update existing content):

```markdown
# GitHub Star RAG Service

## Development Status

### Phase 1: Foundation Framework ✅ COMPLETED
- [x] Project structure
- [x] Configuration management
- [x] Database layer (SQLite)
- [x] Basic FastAPI application
- [x] Testing framework

### Phase 2: Core Services 🚧 IN PROGRESS
- [ ] GitHub API client
- [ ] LLM abstraction layer
- [ ] Initialization service
- [ ] Search service
- [ ] Chat service

See [docs/implementation-plan.md](docs/implementation-plan.md) for full roadmap.
```

**Step 3: Commit**

```bash
git add README.phase1.md README.md
git commit -m "docs: add Phase 1 completion documentation"
```

---

## Phase 1 Completion Checklist

- [x] Project directory structure created
- [x] Configuration management with Pydantic Settings
- [x] Database abstraction layer defined
- [x] SQLite implementation with full schema
- [x] Database factory function
- [x] FastAPI application with basic endpoints
- [x] Database lifecycle management
- [x] Entry point script
- [x] Comprehensive test suite
- [x] Documentation updated

---

## Summary

Phase 1 establishes the foundation for the entire application. All core infrastructure is in place:

✅ **Database**: SQLite with async operations, full schema, indexes
✅ **Configuration**: Type-safe, environment-aware
✅ **API**: FastAPI with CORS, error handling, lifecycle management
✅ **Testing**: Unit and integration tests with good coverage

The application can be started and responds to basic health and statistics requests.

**Estimated time to complete Phase 1**: 3-4 days

**Ready for Phase 2**: Yes - proceed to implementing core services
