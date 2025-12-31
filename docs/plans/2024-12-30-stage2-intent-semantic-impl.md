# Stage 2: Intent Recognition & Semantic Search Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add intent classification and semantic search to enable intelligent query routing and vector-based similarity search.

**Architecture:** Add three layers: (1) Intent Classifier using LLM to categorize queries, (2) Semantic Search using ChromaDB + Ollama embeddings, (3) Hybrid Search that merges FTS and semantic results with weighted scoring.

**Tech Stack:** ChromaDB, Ollama nomic-embed-text, OpenAI LLM for intent classification.

---

## Task 1: Add ChromaDB Dependency

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add chromadb to dependencies**

```bash
# Add chromadb to project dependencies
uv add chromadb
```

**Step 2: Verify installation**

Run: `uv run python -c "import chromadb; print(chromadb.__version__)"`
Expected: Version printed (e.g., 0.4.0 or later)

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "deps: add chromadb for vector storage"
```

---

## Task 2: Create Intent Result Model

**Files:**
- Create: `src/services/intent.py`

**Step 1: Write the model**

```python
"""Intent classification service."""
from pydantic import BaseModel
from typing import Literal


class IntentResult(BaseModel):
    """Result of intent classification."""
    intent: Literal["chat", "stats", "search"]
    keywords: str | None = None
    confidence: float = 1.0
```

**Step 2: Write failing test**

```python
# tests/unit/test_intent.py
from src.services.intent import IntentResult

def test_intent_result_model():
    result = IntentResult(intent="search", keywords="API framework")
    assert result.intent == "search"
    assert result.keywords == "API framework"
    assert result.confidence == 1.0
```

**Step 3: Run test to verify it passes**

Run: `pytest tests/unit/test_intent.py::test_intent_result_model -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/services/intent.py tests/unit/test_intent.py
git commit -m "feat: add IntentResult model"
```

---

## Task 3: Implement Intent Classifier

**Files:**
- Modify: `src/services/intent.py`
- Modify: `tests/unit/test_intent.py`

**Step 1: Write the IntentClassifier class**

```python
# src/services/intent.py
"""Intent classification service."""
from pydantic import BaseModel
from typing import Literal
from src.llm import Message, LLM


class IntentResult(BaseModel):
    """Result of intent classification."""
    intent: Literal["chat", "stats", "search"]
    keywords: str | None = None
    confidence: float = 1.0


class IntentClassifier:
    """Classify user intent using LLM."""

    def __init__(self, llm: LLM):
        self.llm = llm
        self._system_prompt = """分类用户意图，只返回 JSON：
{
  "intent": "chat|stats|search",
  "keywords": "提取的核心搜索词（仅 search 需要，否则 null）"
}

规则：
- "你好、在吗、谢谢" → chat
- "多少、分布、统计" → stats
- "找、推荐、有哪些、怎么、如何" → search"""

    async def classify(self, query: str) -> IntentResult:
        """
        Classify user intent.

        Args:
            query: User query text

        Returns:
            IntentResult with classified intent and extracted keywords
        """
        messages = [
            Message(role="system", content=self._system_prompt),
            Message(role="user", content=query)
        ]

        try:
            response = await self.llm.chat(messages, temperature=0.0)
            import json
            data = json.loads(response)
            return IntentResult(**data)
        except Exception:
            # Fallback to search on error
            return IntentResult(intent="search", keywords=query)
```

**Step 2: Write failing test**

```python
# tests/unit/test_intent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.intent import IntentClassifier, IntentResult


@pytest.mark.asyncio
async def test_intent_classifier_search():
    llm = MagicMock()
    llm.chat = AsyncMock(return_value='{"intent": "search", "keywords": "Python web"}')

    classifier = IntentClassifier(llm)
    result = await classifier.classify("有哪些 Python web 框架")

    assert result.intent == "search"
    assert result.keywords == "Python web"


@pytest.mark.asyncio
async def test_intent_classifier_stats():
    llm = MagicMock()
    llm.chat = AsyncMock(return_value='{"intent": "stats", "keywords": null}')

    classifier = IntentClassifier(llm)
    result = await classifier.classify("我收藏了多少个项目")

    assert result.intent == "stats"
    assert result.keywords is None


@pytest.mark.asyncio
async def test_intent_classifier_fallback():
    llm = MagicMock()
    llm.chat = AsyncMock(side_effect=Exception("LLM error"))

    classifier = IntentClassifier(llm)
    result = await classifier.classify("随便说点啥")

    assert result.intent == "search"  # Fallback
    assert result.keywords == "随便说点啥"
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/unit/test_intent.py -v`
Expected: FAIL - "cannot import 'Message' from 'src.llm'"

**Step 4: Check what needs to be exported from llm module**

Run: `cat src/llm/__init__.py`
Expected: See if Message is exported

**Step 5: Export Message if needed**

```python
# src/llm/__init__.py
from .base import LLM, Message
from .openai import OpenAILLM

__all__ = ["LLM", "Message", "OpenAILLM", "create_llm"]
```

**Step 6: Run tests again**

Run: `pytest tests/unit/test_intent.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add src/services/intent.py tests/unit/test_intent.py src/llm/__init__.py
git commit -m "feat: implement IntentClassifier with LLM"
```

---

## Task 4: Create Ollama Embedder

**Files:**
- Create: `src/vector/embeddings.py`
- Create: `tests/unit/test_embeddings.py`

**Step 1: Create vector package**

```bash
mkdir -p src/vector
touch src/vector/__init__.py
```

**Step 2: Write OllamaEmbedder class**

```python
# src/vector/embeddings.py
"""Ollama embedding service."""
import httpx
from typing import list


class OllamaEmbedder:
    """Generate embeddings using Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.base_url = base_url
        self.model = model

    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Vector embedding as list of floats
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of vector embeddings
        """
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings
```

**Step 3: Write test (requires Ollama running)**

```python
# tests/unit/test_embeddings.py
import pytest
from src.vector.embeddings import OllamaEmbedder


@pytest.mark.asyncio
async def test_ollama_embedder():
    embedder = OllamaEmbedder()

    result = await embedder.embed("test text")

    assert isinstance(result, list)
    assert all(isinstance(x, float) for x in result)
    assert len(result) > 0  # Embedding dimension


@pytest.mark.asyncio
async def test_ollama_embedder_batch():
    embedder = OllamaEmbedder()

    results = await embedder.embed_batch(["text 1", "text 2"])

    assert len(results) == 2
    assert all(isinstance(r, list) for r in results)
```

**Step 4: Run test (will fail if Ollama not running)**

Run: `pytest tests/unit/test_embeddings.py -v`
Expected: May FAIL if Ollama not running - that's okay for now

**Step 5: Commit**

```bash
git add src/vector/ tests/unit/test_embeddings.py
git commit -m "feat: add OllamaEmbedder for vector generation"
```

---

## Task 5: Implement Semantic Search with ChromaDB

**Files:**
- Create: `src/vector/semantic.py`
- Create: `tests/unit/test_semantic.py`

**Step 1: Write SemanticSearch class**

```python
# src/vector/semantic.py
"""Semantic search using ChromaDB."""
import chromadb
from chromadb.config import Settings
from src.vector.embeddings import OllamaEmbedder
from typing import list


class SemanticSearch:
    """Semantic search using vector embeddings."""

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        persist_path: str = "data/chromadb"
    ):
        """
        Initialize semantic search.

        Args:
            ollama_base_url: Ollama API URL
            model: Embedding model name
            persist_path: ChromaDB persistence path
        """
        self.embedder = OllamaEmbedder(ollama_base_url, model)
        self.client = chromadb.PersistentClient(
            path=persist_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="github_repos",
            metadata={"hnsw:space": "cosine"}
        )

    async def add_repositories(self, repos: list[dict]) -> None:
        """
        Add repositories to vector store.

        Args:
            repos: List of repository data dicts
        """
        if not repos:
            return

        # Generate texts for embedding
        texts = [self._repo_to_text(repo) for repo in repos]
        embeddings = await self.embedder.embed_batch(texts)

        # Prepare data
        ids = [repo["name_with_owner"] for repo in repos]
        metadatas = []
        for repo in repos:
            metadata = {
                "name": repo.get("name", ""),
                "description": repo.get("description", "") or "",
                "primary_language": repo.get("primary_language", "") or "",
                "url": repo.get("url", "")
            }
            metadatas.append(metadata)

        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )

    async def search(self, query: str, top_k: int = 10) -> list[dict]:
        """
        Search for similar repositories.

        Args:
            query: Search query text
            top_k: Number of results to return

        Returns:
            List of repository dicts with similarity scores
        """
        query_embedding = await self.embedder.embed(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # Format results
        repos = []
        if results["ids"] and results["ids"][0]:
            for i, repo_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i] if "distances" in results else 0
                repos.append({
                    "name_with_owner": repo_id,
                    "name": metadata.get("name", ""),
                    "description": metadata.get("description", ""),
                    "primary_language": metadata.get("primary_language", ""),
                    "url": metadata.get("url", ""),
                    "similarity_score": 1 - distance  # Convert to similarity
                })

        return repos

    def _repo_to_text(self, repo: dict) -> str:
        """Convert repository dict to text for embedding."""
        parts = [
            repo.get("name", ""),
            repo.get("description", "") or "",
            " ".join(repo.get("topics", []))
        ]
        return " ".join(p for p in parts if p)
```

**Step 2: Write test**

```python
# tests/unit/test_semantic.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.vector.semantic import SemanticSearch


@pytest.mark.asyncio
async def test_semantic_search_add_repos():
    with patch('src.vector.semantic.chromadb.PersistentClient'):
        semantic = SemanticSearch()
        # Mock collection
        semantic.collection = MagicMock()
        semantic.collection.add = MagicMock()

        repos = [
            {
                "name_with_owner": "test/repo1",
                "name": "repo1",
                "description": "A test repo",
                "primary_language": "Python",
                "url": "https://github.com/test/repo1",
                "topics": ["test"]
            }
        ]

        with patch.object(semantic, 'embedder') as mock_embedder:
            mock_embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

            await semantic.add_repositories(repos)

            assert semantic.collection.add.called


@pytest.mark.asyncio
async def test_repo_to_text():
    semantic = SemanticSearch()
    repo = {
        "name": "test-repo",
        "description": "A test repository",
        "topics": ["python", "api"]
    }

    text = semantic._repo_to_text(repo)

    assert "test-repo" in text
    assert "A test repository" in text
    assert "python" in text
```

**Step 3: Run tests**

Run: `pytest tests/unit/test_semantic.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/vector/semantic.py tests/unit/test_semantic.py
git commit -m "feat: implement SemanticSearch with ChromaDB"
```

---

## Task 6: Implement Hybrid Search

**Files:**
- Create: `src/services/hybrid_search.py`
- Create: `tests/unit/test_hybrid_search.py`

**Step 1: Write HybridSearch class**

```python
# src/services/hybrid_search.py
"""Hybrid search combining FTS and semantic search."""
import asyncio
from src.db import Database
from src.vector.semantic import SemanticSearch
from typing import list


class HybridSearch:
    """Hybrid search merging FTS and semantic results."""

    def __init__(
        self,
        db: Database,
        semantic: SemanticSearch,
        fts_weight: float = 0.3,
        semantic_weight: float = 0.7
    ):
        """
        Initialize hybrid search.

        Args:
            db: Database instance
            semantic: SemanticSearch instance
            fts_weight: Weight for FTS scores
            semantic_weight: Weight for semantic scores
        """
        self.db = db
        self.semantic = semantic
        self.fts_weight = fts_weight
        self.semantic_weight = semantic_weight

    async def search(
        self,
        query: str,
        keywords: str | None = None,
        top_k: int = 10
    ) -> list[dict]:
        """
        Perform hybrid search.

        Args:
            query: Original query for semantic search
            keywords: Extracted keywords for FTS (optional)
            top_k: Number of results to return

        Returns:
            List of merged and reranked repositories
        """
        search_term = keywords or query

        # Parallel search
        fts_task = self._fts_search(search_term, top_k * 2)
        semantic_task = self.semantic.search(query, top_k * 2)

        fts_results, semantic_results = await asyncio.gather(
            fts_task,
            semantic_task,
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(fts_results, Exception):
            fts_results = []
        if isinstance(semantic_results, Exception):
            semantic_results = []

        # Merge and rerank
        return self._merge_and_rerank(
            fts_results,
            semantic_results,
            top_k
        )

    async def _fts_search(self, query: str, limit: int) -> list[dict]:
        """Perform FTS search."""
        try:
            results = await self.db.search_repositories(query, limit=limit)
            return results
        except Exception:
            return []

    def _merge_and_rerank(
        self,
        fts_results: list[dict],
        semantic_results: list[dict],
        top_k: int
    ) -> list[dict]:
        """
        Merge and rerank results from both searches.

        Args:
            fts_results: Results from FTS search
            semantic_results: Results from semantic search
            top_k: Number of final results

        Returns:
            Merged and reranked results
        """
        scores = {}

        # Score FTS results
        for i, repo in enumerate(fts_results):
            name = repo["name_with_owner"]
            fts_score = (1 - i / len(fts_results)) if fts_results else 0
            scores[name] = {
                "repo": repo,
                "score": self.fts_weight * fts_score,
                "match_type": "fts"
            }

        # Add semantic scores
        for i, repo in enumerate(semantic_results):
            name = repo["name_with_owner"]
            semantic_score = (1 - i / len(semantic_results)) if semantic_results else 0

            if name in scores:
                scores[name]["score"] += self.semantic_weight * semantic_score
                scores[name]["match_type"] = "hybrid"
            else:
                scores[name] = {
                    "repo": repo,
                    "score": self.semantic_weight * semantic_score,
                    "match_type": "semantic"
                }

        # Sort by score and return top-k
        sorted_items = sorted(
            scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )[:top_k]

        return [
            {**item["repo"], "match_type": item["match_type"]}
            for _, item in sorted_items
        ]
```

**Step 2: Write tests**

```python
# tests/unit/test_hybrid_search.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.hybrid_search import HybridSearch


@pytest.mark.asyncio
async def test_hybrid_search_merge():
    # Mock database
    db = MagicMock()
    db.search_repositories = AsyncMock(return_value=[
        {"name_with_owner": "ft/repo1", "name": "repo1"}
    ])

    # Mock semantic search
    semantic = MagicMock()
    semantic.search = AsyncMock(return_value=[
        {"name_with_owner": "sem/repo2", "name": "repo2"}
    ])

    hybrid = HybridSearch(db, semantic)
    results = await hybrid.search("test query")

    assert len(results) == 2
    assert results[0]["name_with_owner"] in ["ft/repo1", "sem/repo2"]


@pytest.mark.asyncio
async def test_hybrid_search_fts_fallback():
    # FTS fails, semantic works
    db = MagicMock()
    db.search_repositories = AsyncMock(side_effect=Exception("FTS error"))

    semantic = MagicMock()
    semantic.search = AsyncMock(return_value=[
        {"name_with_owner": "sem/repo1", "name": "repo1"}
    ])

    hybrid = HybridSearch(db, semantic)
    results = await hybrid.search("test query")

    assert len(results) == 1
    assert results[0]["name_with_owner"] == "sem/repo1"
```

**Step 3: Run tests**

Run: `pytest tests/unit/test_hybrid_search.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/services/hybrid_search.py tests/unit/test_hybrid_search.py
git commit -m "feat: implement HybridSearch with weighted merging"
```

---

## Task 7: Implement Stats Service

**Files:**
- Create: `src/services/stats.py`
- Create: `tests/unit/test_stats.py`

**Step 1: Write StatsService class**

```python
# src/services/stats.py
"""Statistics aggregation service."""
from src.db import Database
from typing import dict


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
        # Simple keyword detection (can be enhanced with LLM)
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
```

**Step 2: Write tests**

```python
# tests/unit/test_stats.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.stats import StatsService


@pytest.mark.asyncio
async def test_stats_by_language():
    db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall = AsyncMock(return_value=[
        ("Python", 10),
        ("JavaScript", 5)
    ])
    db._connection.execute.return_value.__aenter__.return_value = mock_cursor

    service = StatsService()
    result = await service.get_stats("按语言统计", db)

    assert "Python" in result
    assert "10" in result


@pytest.mark.asyncio
async def test_stats_overall():
    db = MagicMock()
    db.get_statistics = AsyncMock(return_value={
        "total_repositories": 30,
        "repositories_with_primary_language": 25
    })

    service = StatsService()
    result = await service.get_stats("有多少项目", db)

    assert "30" in result
```

**Step 3: Run tests**

Run: `pytest tests/unit/test_stats.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/services/stats.py tests/unit/test_stats.py
git commit -m "feat: implement StatsService for aggregation queries"
```

---

## Task 8: Modify Initialization Service

**Files:**
- Modify: `src/services/init.py`
- Modify: `tests/unit/test_init_service.py`

**Step 1: Add semantic parameter to InitializationService**

```python
# src/services/init.py

class InitializationService:
    """
    Service for initializing the database with GitHub star data.

    Fetches repositories, analyzes with LLM, and stores in database.
    """

    def __init__(
        self,
        db: Database,
        llm: LLM | None = None,
        semantic: object | None = None  # SemanticSearch instance
    ):
        """
        Initialize service.

        Args:
            db: Database instance
            llm: LLM instance (optional)
            semantic: SemanticSearch instance (optional)
        """
        self.db = db
        self.llm = llm
        self.semantic = semantic

    async def initialize_from_stars(
        self,
        username: str | None = None,
        max_repos: int | None = None,
        skip_llm: bool = False
    ) -> dict[str, any]:
        """
        Initialize database from user's starred repositories using GraphQL API.

        Args:
            username: GitHub username
            max_repos: Maximum number of repositories to fetch
            skip_llm: Skip LLM analysis (faster)

        Returns:
            Statistics about initialization
        """
        # ... existing code ...

        # After fetching repos, generate embeddings if semantic search enabled
        if self.semantic and repos:
            print("Generating vector embeddings...")
            await self.semantic.add_repositories([
                {
                    "name_with_owner": r.get("name_with_owner"),
                    "name": r.get("name"),
                    "description": r.get("description", "") or "",
                    "primary_language": r.get("primary_language", ""),
                    "url": r.get("url", ""),
                    "topics": r.get("topics", [])
                }
                for r in repos
            ])

        # ... rest of existing code ...
```

**Step 2: Update init API route**

```python
# src/api/routes/init.py

class InitRequest(BaseModel):
    """Initialization request model"""
    username: str
    max_repos: int | None = None
    skip_llm: bool = False
    enable_semantic: bool = False  # New parameter

@router.post("/start")
async def start_initialization(request: InitRequest):
    """Start initialization from GitHub stars."""
    from src.api.app import db
    from src.llm import create_llm
    from src.services.init import InitializationService
    from src.config import settings

    # Create LLM if needed
    llm = None if request.skip_llm else create_llm("openai")
    if llm:
        await llm.initialize()

    # Create semantic search if enabled
    semantic = None
    if request.enable_semantic:
        from src.vector.semantic import SemanticSearch
        semantic = SemanticSearch()

    # Create initialization service
    init_service = InitializationService(db, llm, semantic)

    try:
        stats = await init_service.initialize_from_stars(
            username=request.username,
            max_repos=request.max_repos,
            skip_llm=request.skip_llm
        )

        return {
            "success": True,
            "message": f"Successfully initialized with {stats['fetched']} repositories",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if llm:
            await llm.close()
```

**Step 3: Update tests**

```python
# tests/unit/test_init_service.py

@pytest.mark.asyncio
async def test_initialize_with_semantic(db, mocker):
    """Test initialization with semantic search enabled."""
    # Mock semantic search
    class MockSemantic:
        async def add_repositories(self, repos):
            pass

    mocker.patch("src.services.init.GitHubClient", return_value=MockGitHubClient())

    service = InitializationService(
        db,
        llm=None,
        semantic=MockSemantic()
    )
    result = await service.initialize_from_stars(
        username="test",
        skip_llm=True
    )

    assert result["fetched"] >= 0
```

**Step 4: Run tests**

Run: `pytest tests/unit/test_init_service.py -v`
Expected: PASS (may need to adjust existing tests)

**Step 5: Commit**

```bash
git add src/services/init.py src/api/routes/init.py tests/unit/test_init_service.py
git commit -m "feat: add semantic search to initialization flow"
```

---

## Task 9: Modify Chat API for Intent Routing

**Files:**
- Modify: `src/api/routes/chat.py`

**Step 1: Update chat stream endpoint**

```python
# src/api/routes/chat.py

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response with intent-based routing.

    Routes to:
    - chat: Simple conversation
    - stats: Statistics aggregation
    - search: Hybrid search + RAG
    """
    from src.api.app import db, search_service
    from src.llm import create_llm
    from src.services.intent import IntentClassifier
    from src.services.stats import StatsService
    from src.services.hybrid_search import HybridSearch
    from src.vector.semantic import SemanticSearch

    # Create LLM
    llm_kwargs = {}
    if request.llm_config and request.llm_config.get("api_key"):
        llm_kwargs["api_key"] = request.llm_config["api_key"]
    if request.llm_config and request.llm_config.get("base_url"):
        llm_kwargs["base_url"] = request.llm_config["base_url"]

    llm = create_llm("openai", **llm_kwargs)
    await llm.initialize()

    # Classify intent
    classifier = IntentClassifier(llm)
    intent = await classifier.classify(request.message)

    async def event_generator():
        yield {"type": "intent", "data": intent.intent}

        try:
            if intent.intent == "chat":
                # Simple chat
                async for chunk in _simple_chat_stream(llm, request.message):
                    yield chunk

            elif intent.intent == "stats":
                # Statistics
                stats_service = StatsService()
                stats_text = await stats_service.get_stats(request.message, db)
                yield {"type": "content", "content": stats_text}
                yield {"type": "done"}

            else:  # search
                # Hybrid search + RAG
                semantic = SemanticSearch() if search_service.vector_memory else None
                hybrid = HybridSearch(db, semantic) if semantic else search_service

                search_results = await hybrid.search(
                    request.message,
                    intent.keywords
                )

                yield {"type": "search_results", "data": search_results}

                # RAG generation
                from src.services.chat import ChatService
                chat_service = ChatService(db, llm)
                async for chunk in chat_service.chat_with_rag_stream(
                    session_id=request.session_id,
                    user_message=request.message,
                    search_results=search_results
                ):
                    yield chunk
        finally:
            await llm.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


async def _simple_chat_stream(llm, message: str):
    """Simple chat without RAG."""
    system_prompt = "You are a helpful assistant for GitHub Star Helper."
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=message)
    ]

    async for chunk in llm.chat_stream(messages):
        yield {"type": "content", "content": chunk}

    yield {"type": "done"}
```

**Step 2: Add integration test**

```python
# tests/integration/test_intent_flow.py

import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_chat_intent_flow():
    """Test complete intent routing flow."""
    from src.api.app import app

    with TestClient(app) as client:
        # Test stats intent
        response = client.post("/chat/stream", json={
            "session_id": "test",
            "message": "我收藏了多少个项目",
            "use_rag": False
        })

        assert response.status_code == 200

        events = list(response.streaming())
        intent_events = [e for e in events if e.get("type") == "intent"]
        assert len(intent_events) > 0
```

**Step 3: Run tests**

Run: `pytest tests/integration/test_intent_flow.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/api/routes/chat.py tests/integration/test_intent_flow.py
git commit -m "feat: add intent-based routing to chat API"
```

---

## Task 10: Update Frontend Init View

**Files:**
- Modify: `frontend/src/views/InitView.vue`

**Step 1: Add semantic search checkbox**

```vue
<!-- frontend/src/views/InitView.vue -->

<template>
  <!-- ... existing code ... -->

  <div>
    <label class="flex items-center gap-2 text-sm text-gray-600">
      <input
        v-model="enableSemantic"
        type="checkbox"
        id="enable-semantic"
        :disabled="isInitializing"
        class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
      >
      <span class="cursor-pointer" @click="enableSemantic = !enableSemantic">
        启用语义搜索（更智能，但初始化更慢）
      </span>
    </label>
    <p class="text-xs text-gray-500 mt-1 ml-6">
      首次需要为所有仓库生成向量嵌入，大约需要额外 1-2 分钟
    </p>
  </div>

  <!-- ... rest of template ... -->
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const username = ref('')
const skipLlm = ref(false)
const enableSemantic = ref(false)  // New
const isInitializing = ref(false)
const error = ref('')
const progress = ref<any>(null)
const progressMessage = ref('连接 GitHub...')

async function startInit() {
  if (!username.value) return

  isInitializing.value = true
  error.value = ''
  progress.value = null

  try {
    const response = await fetch('/init/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        skip_llm: skipLlm.value,
        enable_semantic: enableSemantic.value  // New
      })
    })

    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || '初始化失败')
    }

    const result = await response.json()

    if (result.success) {
      progressMessage.value = '初始化完成！'
      setTimeout(() => {
        router.push('/')
      }, 1000)
    }
  } catch (e: any) {
    error.value = e.message || '初始化失败，请检查用户名是否正确'
    isInitializing.value = false
  }
}

checkInitStatus()
</script>
```

**Step 2: Build frontend to verify**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/views/InitView.vue
git commit -m "feat(frontend): add semantic search option to init page"
```

---

## Task 11: Run Full Test Suite

**Files:**
- All test files

**Step 1: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 2: Fix any failing tests**

If tests fail, debug and fix them.

**Step 3: Final commit if needed**

```bash
git add tests/
git commit -m "test: fix failing tests after Stage 2 implementation"
```

---

## Task 12: Update Documentation

**Files:**
- Modify: `README.md`

**Step 1: Update README with Stage 2 features**

```markdown
## Features

- **Intent Classification**: Automatically understand if you want to chat, get stats, or search
- **Semantic Search**: Find repositories by meaning, not just keywords
- **Hybrid Search**: Combined full-text and semantic search for best results
- **Statistics**: Get quick stats on your starred repositories
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with Stage 2 features"
```

---

## Summary

This plan implements Stage 2: Intent Recognition & Semantic Search in 12 tasks:

1. ✅ Add ChromaDB dependency
2. ✅ Intent Result model
3. ✅ Intent Classifier with LLM
4. ✅ Ollama Embedder
5. ✅ Semantic Search with ChromaDB
6. ✅ Hybrid Search with weighted merging
7. ✅ Stats Service for aggregations
8. ✅ Initialization Service modification
9. ✅ Chat API intent routing
10. ✅ Frontend Init View update
11. ✅ Full test suite
12. ✅ Documentation update

**Total estimated time:** 2-3 hours for implementation

**Dependencies:**
- Ollama service running on localhost:11434
- OpenAI API key for LLM intent classification
