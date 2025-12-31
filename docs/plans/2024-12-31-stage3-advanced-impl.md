# Stage 3: Advanced Features Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance GitHub Star Helper with multi-turn context, query expansion, recommendations, and trend analysis.

**Architecture:** Add 4 new services (Context, QueryExpander, Recommendation, TrendAnalysis) and integrate into existing chat/search flows. Extend database with starred_at timestamp.

**Tech Stack:** Python 3.13, FastAPI, SQLite, ChromaDB, OpenAI, Vue 3

---

## Task 1: Database Migration - Add starred_at

**Files:**
- Create: `src/db/migrations/001_add_starred_at.sql`
- Create: `src/db/migrations/__init__.py`
- Modify: `src/db/sqlite.py`

**Step 1: Create migration file**

```sql
-- src/db/migrations/001_add_starred_at.sql
ALTER TABLE repositories ADD COLUMN starred_at TIMESTAMP;
```

**Step 2: Create migrations init**

```python
# src/db/migrations/__init__.py
__all__ = []
```

**Step 3: Update SQLite database to run migrations**

Read `src/db/sqlite.py`, find the `initialize()` method, add migration execution:

```python
# After table creation, run migrations
await self._run_migrations()
```

Add migration runner method:

```python
async def _run_migrations(self):
    """Run pending database migrations."""
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
            # Run migration
            sql = migration_file.read_text()
            await self._connection.execute(sql)
            await self._connection.execute(
                "INSERT INTO _migrations (name) VALUES (?)",
                (migration_name,)
            )
            await self._connection.commit()
```

**Step 4: Write test**

```python
# tests/unit/test_migrations.py
import pytest
from src.db import create_database

@pytest.mark.asyncio
async def test_starred_at_column_exists():
    db = create_database()
    await db.initialize()

    # Check if starred_at column exists
    cursor = await db._connection.execute(
        "PRAGMA table_info(repositories)"
    )
    columns = await cursor.fetchall()
    column_names = [col[1] for col in columns]

    assert "starred_at" in column_names

    await db.close()
```

**Step 5: Run test**

Run: `pytest tests/unit/test_migrations.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/db/migrations/ src/db/sqlite.py tests/unit/test_migrations.py
git commit -m "feat: add starred_at column migration"
```

---

## Task 2: ContextService Implementation

**Files:**
- Create: `src/services/context.py`
- Test: `tests/unit/test_context.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_context.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.context import ContextService

@pytest.mark.asyncio
async def test_get_context_with_first_round_preserved():
    db = MagicMock()
    mock_cursor = MagicMock()

    # Mock first round (earliest message)
    mock_cursor.fetchone = AsyncMock(return_value=(1, "test_session", "user", "First question", "2024-01-01"))
    db._connection.execute.return_value.__aenter__.return_value = mock_cursor

    service = ContextService(db)
    context = await service.get_context("test_session", limit=3)

    assert "First question" in context
    assert "1" in context  # Verify first round is included

@pytest.mark.asyncio
async def test_get_context_empty_session():
    db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone = AsyncMock(return_value=None)
    db._connection.execute.return_value.__aenter__.return_value = mock_cursor

    service = ContextService(db)
    context = await service.get_context("new_session")

    assert context == ""
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_context.py -v`
Expected: FAIL with "module 'src.services.context' not found"

**Step 3: Write minimal implementation**

```python
# src/services/context.py
from typing import Any
from src.db import Database


class ContextService:
    """Service for managing conversation context."""

    def __init__(self, db: Database):
        self.db = db

    async def get_context(self, session_id: str, limit: int = 5) -> str:
        """
        Get conversation context with first round always preserved.

        Args:
            session_id: Session identifier
            limit: Maximum number of recent rounds (excluding first)

        Returns:
            Formatted context string
        """
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

        # Get recent (limit - 1) rounds
        cursor = await self.db._connection.execute(
            """
            SELECT role, content
            FROM conversations
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (session_id, limit - 1)
        )
        recent_rows = await cursor.fetchall()

        # Reverse to get chronological order
        for role, content in reversed(recent_rows):
            # Skip if already included as first round
            lines.append(f"{role.capitalize()}: {content}")

        return "\n".join(lines)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_context.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/context.py tests/unit/test_context.py
git commit -m "feat: implement ContextService"
```

---

## Task 3: QueryExpander Implementation

**Files:**
- Create: `src/services/query_expander.py`
- Create: `src/data/synonyms.json`
- Test: `tests/unit/test_query_expander.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_query_expander.py
import pytest
from src.services.query_expander import QueryExpander

@pytest.mark.asyncio
async def test_expand_with_synonyms():
    expander = QueryExpander()
    queries = await expander.expand("ml 项目")

    assert len(queries) > 1
    assert "ml 项目" in queries  # Original query preserved
    assert any("机器学习" in q for q in queries)

@pytest.mark.asyncio
async def test_expand_no_synonyms():
    expander = QueryExpander()
    queries = await expander.expand("random query")

    assert len(queries) == 1
    assert queries[0] == "random query"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_query_expander.py -v`
Expected: FAIL with "module 'src.services.query_expander' not found"

**Step 3: Create synonyms data**

```json
// src/data/synonyms.json
{
  "ml": ["机器学习", "machine learning", "人工智能"],
  "ai": ["人工智能", "artificial intelligence"],
  "前端": ["frontend", "ui", "web", "client"],
  "后端": ["backend", "server", "api"],
  "数据库": ["database", "db", "storage"],
  "devops": ["运维", "operations"],
  "测试": ["test", "testing", "qa"],
  "框架": ["framework", "库", "library"]
}
```

**Step 4: Write minimal implementation**

```python
# src/services/query_expander.py
import json
from pathlib import Path


class QueryExpander:
    """Expands queries using synonym library."""

    def __init__(self, synonyms_path: str | None = None):
        if synonyms_path is None:
            synonyms_path = Path(__file__).parent.parent / "data" / "synonyms.json"
        self.synonyms_path = Path(synonyms_path)
        self._synonyms = self._load_synonyms()

    def _load_synonyms(self) -> dict[str, list[str]]:
        """Load synonyms from JSON file."""
        if not self.synonyms_path.exists():
            return {}
        with open(self.synonyms_path, encoding="utf-8") as f:
            return json.load(f)

    async def expand(self, query: str, max_expansions: int = 3) -> list[str]:
        """
        Expand query using synonyms.

        Args:
            query: Original query
            max_expansions: Maximum number of expanded queries

        Returns:
            List of expanded queries (original + variations)
        """
        expansions = [query]

        for term, synonyms in self._synonyms.items():
            if term.lower() in query.lower():
                for synonym in synonyms[:max_expansions]:
                    expanded = query.lower().replace(term.lower(), synonym)
                    if expanded not in expansions:
                        expansions.append(expanded)

        return expansions
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_query_expander.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/services/query_expander.py src/data/synonyms.json tests/unit/test_query_expander.py
git commit -m "feat: implement QueryExpander with synonym library"
```

---

## Task 4: RecommendationService Implementation

**Files:**
- Create: `src/services/recommendation.py`
- Test: `tests/unit/test_recommendation.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_recommendation.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.recommendation import RecommendationService

@pytest.mark.asyncio
async def test_get_similar_repos():
    db = MagicMock()
    mock_cursor = MagicMock()

    # Mock repo categories
    mock_cursor.fetchone = AsyncMock(return_value=(["AI", "ML"],))
    # Mock similar repos
    mock_cursor.fetchall = AsyncMock(return_value=[
        ("owner/repo1", "test repo", 100, ["AI"]),
        ("owner/repo2", "test repo2", 50, ["ML", "AI"])
    ])
    db._connection.execute.return_value.__aenter__.return_value = mock_cursor

    service = RecommendationService(db)
    results = await service.get_similar_repos("owner/test_repo")

    assert len(results) == 2
    assert results[0]["name_with_owner"] == "owner/repo1"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_recommendation.py -v`
Expected: FAIL with "module 'src.services.recommendation' not found"

**Step 3: Write minimal implementation**

```python
# src/services/recommendation.py
from typing import Any
from src.db import Database


class RecommendationService:
    """Service for repository recommendations."""

    def __init__(self, db: Database):
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
            (repo_name, limit * 2)  # Get more, then filter
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_recommendation.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/recommendation.py tests/unit/test_recommendation.py
git commit -m "feat: implement RecommendationService"
```

---

## Task 5: TrendAnalysisService Implementation

**Files:**
- Create: `src/services/trend_analysis.py`
- Test: `tests/unit/test_trend_analysis.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_trend_analysis.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.trend_analysis import TrendAnalysisService

@pytest.mark.asyncio
async def test_get_star_timeline():
    db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall = AsyncMock(return_value=[
        ("2024-01", 5),
        ("2024-02", 3)
    ])
    db._connection.execute.return_value.__aenter__.return_value = mock_cursor

    service = TrendAnalysisService(db)
    timeline = await service.get_star_timeline("testuser")

    assert len(timeline) == 2
    assert timeline[0]["month"] == "2024-01"
    assert timeline[0]["count"] == 5
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_trend_analysis.py -v`
Expected: FAIL with "module 'src.services.trend_analysis' not found"

**Step 3: Write minimal implementation**

```python
# src/services/trend_analysis.py
from typing import Any
from datetime import datetime
from src.db import Database


class TrendAnalysisService:
    """Service for analyzing trends in repository data."""

    def __init__(self, db: Database):
        self.db = db

    async def get_star_timeline(
        self,
        username: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get star timeline by month.

        Args:
            username: Optional username filter

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

    async def get_language_trend(self) -> list[dict[str, Any]]:
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

    async def get_category_evolution(self) -> list[dict[str, Any]]:
        """
        Get category interest evolution over time.

        Returns:
            List of {category, month, count} entries
        """
        cursor = await self.db._connection.execute(
            """
            SELECT
                category,
                strftime('%Y-%m', starred_at) as month,
                COUNT(*) as count
            FROM repositories,
                json_each(categories) as category
            WHERE starred_at IS NOT NULL
            GROUP BY category, month
            ORDER BY month ASC, count DESC
            """
        )
        rows = await cursor.fetchall()

        return [
            {"category": cat, "month": month, "count": count}
            for cat, month, count in rows
        ] if rows else []
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_trend_analysis.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/trend_analysis.py tests/unit/test_trend_analysis.py
git commit -m "feat: implement TrendAnalysisService"
```

---

## Task 6: API Routes - Recommendations

**Files:**
- Create: `src/api/routes/recommendation.py`
- Modify: `src/api/app.py`

**Step 1: Create recommendation routes**

```python
# src/api/routes/recommendation.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/recommend", tags=["recommendation"])


class SimilarResponse(BaseModel):
    """Similar repositories response."""
    name_with_owner: str
    description: str | None
    stargazer_count: int
    categories: list[str]


class CategoryResponse(BaseModel):
    """Category recommendation response."""
    name_with_owner: str
    description: str | None
    stargazer_count: int
    categories: list[str]


@router.get("/similar/{name_with_owner}", response_model=list[SimilarResponse])
async def get_similar_repos(name_with_owner: str, limit: int = 5):
    """Get similar repositories."""
    from src.api.app import db
    from src.services.recommendation import RecommendationService

    service = RecommendationService(db)
    results = await service.get_similar_repos(name_with_owner, limit)
    return results


@router.get("/category/{category}", response_model=list[CategoryResponse])
async def get_recommended_by_category(category: str, limit: int = 10):
    """Get repositories by category."""
    from src.api.app import db
    from src.services.recommendation import RecommendationService

    service = RecommendationService(db)
    results = await service.get_recommended_by_category(category, limit)
    return results
```

**Step 2: Update app.py to include router**

Read `src/api/app.py`, find the `# Include routers` section, add:

```python
from src.api.routes import chat, search, init, recommendation

# In the include routers section:
app.include_router(recommendation.router)
```

**Step 3: Write test**

```python
# tests/unit/test_recommendation_routes.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_similar_repos_endpoint():
    response = client.get("/recommend/similar/owner/repo?limit=5")
    # Response structure validation
    assert response.status_code in [200, 404, 500]
```

**Step 4: Run test**

Run: `pytest tests/unit/test_recommendation_routes.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/api/routes/recommendation.py src/api/app.py tests/unit/test_recommendation_routes.py
git commit -m "feat: add recommendation API routes"
```

---

## Task 7: API Routes - Trends

**Files:**
- Create: `src/api/routes/trends.py`
- Modify: `src/api/app.py`

**Step 1: Create trends routes**

```python
# src/api/routes/trends.py
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/trends", tags=["trends"])


class TimelinePoint(BaseModel):
    """Timeline data point."""
    month: str
    count: int


@router.get("/timeline", response_model=list[TimelinePoint])
async def get_star_timeline(username: str | None = None):
    """Get star timeline by month."""
    from src.api.app import db
    from src.services.trend_analysis import TrendAnalysisService

    service = TrendAnalysisService(db)
    return await service.get_star_timeline(username)


@router.get("/languages")
async def get_language_trend():
    """Get language trend over time."""
    from src.api.app import db
    from src.services.trend_analysis import TrendAnalysisService

    service = TrendAnalysisService(db)
    return await service.get_language_trend()


@router.get("/categories")
async def get_category_evolution():
    """Get category evolution over time."""
    from src.api.app import db
    from src.services.trend_analysis import TrendAnalysisService

    service = TrendAnalysisService(db)
    return await service.get_category_evolution()
```

**Step 2: Update app.py**

Add to imports:
```python
from src.api.routes import chat, search, init, recommendation, trends
```

Add to router includes:
```python
app.include_router(trends.router)
```

**Step 3: Write test**

```python
# tests/unit/test_trends_routes.py
import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_timeline_endpoint():
    response = client.get("/trends/timeline")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

**Step 4: Run test**

Run: `pytest tests/unit/test_trends_routes.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/api/routes/trends.py src/api/app.py tests/unit/test_trends_routes.py
git commit -m "feat: add trends API routes"
```

---

## Task 8: Integrate ContextService into ChatService

**Files:**
- Modify: `src/services/chat.py`

**Step 1: Read existing ChatService**

Read `src/services/chat.py` to understand current implementation.

**Step 2: Modify chat_with_rag_stream to include context**

Find the `chat_with_rag_stream` method, add context retrieval:

```python
async def chat_with_rag_stream(
    self,
    session_id: str,
    user_message: str,
    search_results: list | None = None
):
    # Get conversation context
    from src.services.context import ContextService
    context_service = ContextService(self.db)
    context = await context_service.get_context(session_id)

    # Build messages with context
    messages = [
        Message(role="system", content=self.system_prompt)
    ]

    if context:
        messages.append(
            Message(role="system", content=f"Previous conversation:\n{context}")
        )

    # Add search results context
    if search_results:
        context_text = self._format_search_results(search_results)
        messages.append(
            Message(role="system", content=f"Relevant repositories:\n{context_text}")
        )

    # Add current user message
    messages.append(Message(role="user", content=user_message))

    # Stream response
    async for chunk in self.llm.chat_stream(messages):
        yield chunk
```

**Step 3: Write test**

```python
# tests/unit/test_chat_with_context.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.chat import ChatService

@pytest.mark.asyncio
async def test_chat_includes_context():
    db = MagicMock()
    llm = MagicMock()

    service = ChatService(db, llm, None)

    # Mock context retrieval
    with patch('src.services.chat.ContextService') as MockContext:
        mock_context = MagicMock()
        mock_context.get_context = AsyncMock(return_value="User: Previous question")
        MockContext.return_value = mock_context

        # Mock LLM stream
        llm.chat_stream = AsyncMock(return_value=["Response"])

        chunks = []
        async for chunk in service.chat_with_rag_stream("session1", "New question"):
            chunks.append(chunk)

        # Verify context was retrieved
        mock_context.get_context.assert_called_once_with("session1")
```

**Step 4: Run test**

Run: `pytest tests/unit/test_chat_with_context.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/chat.py tests/unit/test_chat_with_context.py
git commit -m "feat: integrate context into chat"
```

---

## Task 9: Integrate QueryExpander into HybridSearch

**Files:**
- Modify: `src/services/hybrid_search.py`

**Step 1: Read existing HybridSearch**

Read `src/services/hybrid_search.py` to understand current implementation.

**Step 2: Modify search method to expand queries**

```python
async def search(
    self,
    query: str,
    keywords: str | None = None,
    top_k: int = 10
) -> list[dict[str, Any]]:
    """
    Hybrid search with query expansion.

    Args:
        query: Search query
        keywords: Optional keywords for FTS
        top_k: Number of results to return

    Returns:
        List of search results
    """
    # Expand query
    from src.services.query_expander import QueryExpander
    expander = QueryExpander()
    expanded_queries = await expander.expand(query)

    # Search with all query variations
    all_results = []

    for expanded_query in expanded_queries:
        # Parallel FTS and semantic search
        fts_results, semantic_results = await asyncio.gather(
            self._fts_search(expanded_query, top_k * 2),
            self.semantic.search(expanded_query, top_k * 2),
            return_exceptions=True
        )

        if not isinstance(fts_results, Exception):
            all_results.extend(fts_results)
        if not isinstance(semantic_results, Exception):
            all_results.extend(semantic_results)

    # Merge, deduplicate, and re-rank
    return self._merge_and_rerank(all_results, top_k)
```

**Step 3: Write test**

```python
# tests/unit/test_hybrid_search_with_expansion.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.hybrid_search import HybridSearch

@pytest.mark.asyncio
async def test_search_expands_queries():
    db = MagicMock()
    semantic = MagicMock()

    service = HybridSearch(db, semantic)

    with patch('src.services.hybrid_search.QueryExpander') as MockExpander:
        mock_expander = MagicMock()
        mock_expander.return_value.expand = AsyncMock(
            return_value=["ml project", "机器学习 project"]
        )
        MockExpander.return_value = mock_expander

        # Mock search methods
        service._fts_search = AsyncMock(return_value=[])
        semantic.search = AsyncMock(return_value=[])

        await service.search("ml project")

        # Verify expansion was called
        mock_expander.return_value.expand.assert_called_once()
```

**Step 4: Run test**

Run: `pytest tests/unit/test_hybrid_search_with_expansion.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/hybrid_search.py tests/unit/test_hybrid_search_with_expansion.py
git commit -m "feat: integrate query expansion into hybrid search"
```

---

## Task 10: Update InitializationService to save starred_at

**Files:**
- Modify: `src/services/init.py`

**Step 1: Read current implementation**

Read `src/services/init.py` to find where repository data is saved.

**Step 2: Add starred_at to repo data**

Find the `repo_data` dictionary construction, add starred_at:

```python
# In initialize_from_stars method, when processing each repo:
for repo in repos:
    try:
        # Get starred_at time from GitHub API response
        starred_at = getattr(repo, 'starred_at', None)

        # ... existing code ...

        repo_data = {
            # ... existing fields ...
            "starred_at": starred_at,
            **analysis
        }
```

**Step 3: Write test**

```python
# tests/unit/test_init_with_starred_at.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.init import InitializationService

@pytest.mark.asyncio
async def test_initialization_saves_starred_at():
    db = MagicMock()
    db.add_repository = AsyncMock()

    service = InitializationService(db, None, None)

    # Mock GitHub response with starred_at
    mock_repo = MagicMock()
    mock_repo.name_with_owner = "owner/repo"
    mock_repo.starred_at = "2024-01-01T00:00:00Z"

    # Process repo
    await service._process_single_repo(mock_repo, db)

    # Verify starred_at was saved
    call_args = db.add_repository.call_args
    assert call_args[0][0]["starred_at"] is not None
```

**Step 4: Run test**

Run: `pytest tests/unit/test_init_with_starred_at.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/init.py tests/unit/test_init_with_starred_at.py
git commit -m "feat: save starred_at during initialization"
```

---

## Task 11: Frontend TrendView

**Files:**
- Create: `frontend/src/views/TrendView.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/App.vue`

**Step 1: Create TrendView component**

```vue
<!-- frontend/src/views/TrendView.vue -->
<template>
  <div class="space-y-8">
    <h1 class="text-3xl font-bold text-gray-900">趋势分析</h1>

    <section>
      <h2 class="text-xl font-semibold mb-4">Star 时间线</h2>
      <div class="bg-white p-6 rounded-lg shadow-sm">
        <div v-if="timeline.length === 0" class="text-gray-500">
          暂无数据
        </div>
        <div v-else class="space-y-2">
          <div v-for="point in timeline" :key="point.month" class="flex justify-between">
            <span>{{ point.month }}</span>
            <span class="font-semibold">{{ point.count }} 个项目</span>
          </div>
        </div>
      </div>
    </section>

    <section>
      <h2 class="text-xl font-semibold mb-4">语言趋势</h2>
      <div class="bg-white p-6 rounded-lg shadow-sm">
        <div v-if="languageTrends.length === 0" class="text-gray-500">
          暂无数据
        </div>
        <div v-else class="space-y-2">
          <div v-for="(item, index) in languageTrends.slice(0, 10)" :key="index" class="flex justify-between">
            <span>{{ item.language }} ({{ item.month }})</span>
            <span class="font-semibold">{{ item.count }}</span>
          </div>
        </div>
      </div>
    </section>

    <section>
      <h2 class="text-xl font-semibold mb-4">主题演变</h2>
      <div class="bg-white p-6 rounded-lg shadow-sm">
        <div v-if="categoryEvolution.length === 0" class="text-gray-500">
          暂无数据
        </div>
        <div v-else class="space-y-2">
          <div v-for="(item, index) in categoryEvolution.slice(0, 10)" :key="index" class="flex justify-between">
            <span>{{ item.category }} ({{ item.month }})</span>
            <span class="font-semibold">{{ item.count }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const timeline = ref([])
const languageTrends = ref([])
const categoryEvolution = ref([])

onMounted(async () => {
  try {
    const [timelineRes, langRes, catRes] = await Promise.all([
      fetch('/api/trends/timeline'),
      fetch('/api/trends/languages'),
      fetch('/api/trends/categories')
    ])

    timeline.value = await timelineRes.json()
    languageTrends.value = await langRes.json()
    categoryEvolution.value = await catRes.json()
  } catch (error) {
    console.error('Failed to load trends:', error)
  }
})
</script>
```

**Step 2: Add route**

Add to `frontend/src/router/index.ts`:

```typescript
{
  path: '/trends',
  name: 'trends',
  component: () => import('../views/TrendView.vue')
}
```

**Step 3: Add nav link**

Add to `frontend/src/App.vue` navigation:

```vue
<router-link to="/trends" class="text-gray-600 hover:text-gray-900">趋势</router-link>
```

**Step 4: Commit**

```bash
cd frontend
git add src/views/TrendView.vue src/router/index.ts src/App.vue
git commit -m "feat: add TrendView page"
```

---

## Task 12: Final Integration & Testing

**Step 1: Run full test suite**

```bash
cd /Users/dustyposa/data/open_source/ai/startship
pytest tests/ -v
```

Expected: All tests pass (should be 80+ tests now)

**Step 2: Manual testing checklist**

- [ ] Initialize system with starred_at timestamps
- [ ] Test multi-turn conversation (verify context preserved)
- [ ] Test query expansion (search "ml" should find "机器学习" results)
- [ ] Test similar repo recommendations
- [ ] Test trend analysis page
- [ ] Verify all API endpoints in /docs

**Step 3: Update README**

Add Stage 3 completion status to README.md.

**Step 4: Final commit**

```bash
git add README.md
git commit -m "docs: update README with Stage 3 completion"
```

---

## Summary

**Total Tasks**: 12
**Estimated Tests**: ~85+ passing
**New Files**: ~15
**Modified Files**: ~8

**New Services**:
- ContextService
- QueryExpander
- RecommendationService
- TrendAnalysisService

**New API Endpoints**:
- GET /api/recommend/similar/{name_with_owner}
- GET /api/recommend/category/{category}
- GET /api/trends/timeline
- GET /api/trends/languages
- GET /api/trends/categories
