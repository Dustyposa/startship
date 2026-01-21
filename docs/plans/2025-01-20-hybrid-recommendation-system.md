# Hybrid Recommendation System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建融合图谱关系和语义相似度的混合推荐系统，为搜索页和详情页提供高质量项目推荐。

**Architecture:** 三阶段推荐流程：多源召回（图谱边 65% + 语义相似度 35%）→ 加权融合 → 多样性优化。语义边采用增量更新策略（同步时更新变化仓库，全量同步时重建）。

**Tech Stack:** FastAPI, ChromaDB, SQLite, Vue 3, TypeScript

---

## Task 1: Semantic Edge Discovery Service

**Files:**
- Create: `src/services/graph/semantic_edges.py`
- Test: `tests/unit/test_semantic_edges.py`

**Step 1: Write the failing test**

Create file `tests/unit/test_semantic_edges.py`:

```python
"""Tests for semantic edge discovery service."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.graph.semantic_edges import SemanticEdgeDiscovery


@pytest.fixture
def mock_semantic_search():
    """Mock semantic search service."""
    mock = Mock()
    mock.get_similar_repos = AsyncMock(return_value=[
        {"name_with_owner": "anthropic/claude-cookbook", "score": 0.85},
        {"name_with_owner": "openai/openai-cookbook", "score": 0.72},
    ])
    return mock


@pytest.fixture
def mock_db():
    """Mock database."""
    db = Mock()
    db.execute_query = AsyncMock()
    db.batch_insert_graph_edges = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_update_semantic_edges_for_single_repo(mock_semantic_search, mock_db):
    """Test updating semantic edges for a single repository."""
    discovery = SemanticEdgeDiscovery(mock_semantic_search, mock_db)

    await discovery._update_semantic_edges_for_single_repo("anthropic/claude-docs", top_k=10)

    # Verify old edges were deleted
    mock_db.execute_query.assert_called_once()
    call_args = mock_db.execute_query.call_args
    assert "DELETE FROM graph_edges" in call_args[0][0]
    assert "anthropic/claude-docs" in call_args[0][1]

    # Verify semantic search was called
    mock_semantic_search.get_similar_repos.assert_called_once_with(
        "anthropic/claude-docs", top_k=10
    )

    # Verify new edges were inserted
    assert mock_db.batch_insert_graph_edges.call_count == 1
    edges = mock_db.batch_insert_graph_edges.call_args[0][0]
    assert len(edges) == 2
    assert edges[0]["edge_type"] == "semantic"
    assert edges[0]["weight"] == 0.85


@pytest.mark.asyncio
async def test_update_semantic_edges_filters_by_min_score(mock_semantic_search, mock_db):
    """Test that edges below minimum similarity are filtered out."""
    # Mock returns one result below threshold
    mock_semantic_search.get_similar_repos = AsyncMock(return_value=[
        {"name_with_owner": "repo1", "score": 0.85},  # Above threshold
        {"name_with_owner": "repo2", "score": 0.45},  # Below threshold
    ])

    discovery = SemanticEdgeDiscovery(mock_semantic_search, mock_db)

    await discovery._update_semantic_edges_for_single_repo("test/repo", top_k=10, min_score=0.6)

    # Only the high-score edge should be inserted
    edges = mock_db.batch_insert_graph_edges.call_args[0][0]
    assert len(edges) == 1
    assert edges[0]["name_with_owner"] == "repo1"


@pytest.mark.asyncio
async def test_update_semantic_edges_handles_gracefully_on_error(mock_semantic_search, mock_db):
    """Test that errors don't crash the service."""
    # Make semantic search fail
    mock_semantic_search.get_similar_repos = AsyncMock(side_effect=Exception("ChromaDB error"))

    discovery = SemanticEdgeDiscovery(mock_semantic_search, mock_db)

    # Should not raise exception
    await discovery._update_semantic_edges_for_single_repo("test/repo")

    # Should log warning but not crash
    # (in real implementation, would check logs)


@pytest.mark.asyncio
async def test_discover_and_store_edges_full_rebuild(mock_semantic_search, mock_db):
    """Test full semantic edge rebuild for all repositories."""
    # Mock database to return list of repos
    mock_db.get_all_repositories = AsyncMock(return_value=[
        {"name_with_owner": "anthropic/claude-docs"},
        {"name_with_owner": "anthropic/claude-cookbook"},
    ])

    discovery = SemanticEdgeDiscovery(mock_semantic_search, mock_db)

    result = await discovery.discover_and_store_edges(top_k=10, min_similarity=0.6)

    assert result["repos_processed"] == 2
    assert result["edges_created"] == 4  # 2 repos * 2 edges each

    # Verify all old semantic edges were deleted
    assert mock_db.execute_query.call_count == 3  # 1 delete + 2 individual deletes
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_semantic_edges.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'src.services.graph.semantic_edges'"

**Step 3: Write minimal implementation**

Create file `src/services/graph/semantic_edges.py`:

```python
"""Semantic edge discovery service for knowledge graph."""
from typing import List, Dict, Any
from loguru import logger


class SemanticEdgeDiscovery:
    """Discover and store semantic similarity edges between repositories."""

    def __init__(self, semantic_search, db):
        """Initialize semantic edge discovery service.

        Args:
            semantic_search: SemanticSearch instance for vector similarity
            db: Database instance for storing edges
        """
        self.semantic_search = semantic_search
        self.db = db

    async def discover_and_store_edges(
        self,
        top_k: int = 10,
        min_similarity: float = 0.6
    ) -> Dict[str, int]:
        """Discover and store semantic edges for all repositories.

        Performs a full rebuild of all semantic edges.

        Args:
            top_k: Number of similar repos to find for each repo
            min_similarity: Minimum similarity score to create an edge

        Returns:
            Dict with stats: {"repos_processed": int, "edges_created": int}
        """
        # Clear all existing semantic edges
        await self.db.execute_query(
            "DELETE FROM graph_edges WHERE edge_type = 'semantic'"
        )

        # Get all repositories
        repos = await self.db.get_all_repositories()

        edges_created = 0
        repos_processed = 0

        # Process each repository
        for repo in repos:
            repo_name = repo.get("name_with_owner")
            if not repo_name:
                continue

            try:
                edges = await self._find_and_prepare_edges(
                    repo_name, top_k, min_similarity
                )
                await self.db.batch_insert_graph_edges(edges)
                edges_created += len(edges)
                repos_processed += 1
            except Exception as e:
                logger.warning(f"Failed to process {repo_name}: {e}")

        logger.info(f"Semantic edge discovery complete: {repos_processed} repos, {edges_created} edges")

        return {
            "repos_processed": repos_processed,
            "edges_created": edges_created
        }

    async def _update_semantic_edges_for_single_repo(
        self,
        repo_name: str,
        top_k: int = 10,
        min_score: float = 0.6
    ) -> None:
        """Update semantic edges for a single repository.

        Deletes old edges and creates new ones. Used for incremental updates.

        Args:
            repo_name: Repository identifier (e.g., "anthropic/claude-docs")
            top_k: Number of similar repos to find
            min_score: Minimum similarity score
        """
        try:
            # Delete old semantic edges for this repo (both as source and target)
            await self.db.execute_query(
                "DELETE FROM graph_edges WHERE edge_type = 'semantic' AND (source_repo = ? OR target_repo = ?)",
                (repo_name, repo_name)
            )

            # Find and create new edges
            edges = await self._find_and_prepare_edges(repo_name, top_k, min_score)
            await self.db.batch_insert_graph_edges(edges)

            logger.info(f"Updated semantic edges for {repo_name}: {len(edges)} edges created")

        except Exception as e:
            logger.warning(f"Failed to update semantic edges for {repo_name}: {e}")
            # Don't raise - allow sync to continue

    async def _find_and_prepare_edges(
        self,
        repo_name: str,
        top_k: int,
        min_score: float
    ) -> List[Dict[str, Any]]:
        """Find similar repos and prepare edge documents.

        Args:
            repo_name: Source repository
            top_k: Number of similar repos to find
            min_score: Minimum similarity threshold

        Returns:
            List of edge dictionaries ready for database insertion
        """
        # Query similar repositories
        similar_repos = await self.semantic_search.get_similar_repos(
            repo_name, top_k=top_k
        )

        # Filter by minimum score and prepare edges
        edges = []
        for similar in similar_repos:
            score = similar.get("score", 0)
            if score >= min_score:
                edges.append({
                    "source_repo": repo_name,
                    "target_repo": similar["name_with_owner"],
                    "edge_type": "semantic",
                    "weight": score,
                    "metadata": f'{{"similarity": {score}}}'
                })

        return edges
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_semantic_edges.py -v`

Expected: PASS (may need to adjust mock setup for get_all_repositories)

**Step 5: Commit**

```bash
git add tests/unit/test_semantic_edges.py src/services/graph/semantic_edges.py
git commit -m "feat: add semantic edge discovery service"
```

---

## Task 2: Add batch_insert_graph_edges to Database

**Files:**
- Modify: `src/db/sqlite.py`
- Test: `tests/unit/test_sqlite.py` (extend existing)

**Step 1: Write the failing test**

Add to `tests/unit/test_sqlite.py`:

```python
@pytest.mark.asyncio
async def test_batch_insert_graph_edges(db):
    """Test batch insertion of graph edges."""
    edges = [
        {
            "source_repo": "repo1",
            "target_repo": "repo2",
            "edge_type": "semantic",
            "weight": 0.85,
            "metadata": '{"similarity": 0.85}'
        },
        {
            "source_repo": "repo1",
            "target_repo": "repo3",
            "edge_type": "author",
            "weight": 1.0,
            "metadata": '{"author": "test"}'
        }
    ]

    await db.batch_insert_graph_edges(edges)

    # Verify edges were inserted
    result = await db.execute_query(
        "SELECT * FROM graph_edges WHERE source_repo = 'repo1'"
    )
    assert len(result) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_sqlite.py::test_batch_insert_graph_edges -v`

Expected: FAIL with "AttributeError: 'Database' object has no attribute 'batch_insert_graph_edges'"

**Step 3: Write minimal implementation**

Add to `src/db/sqlite.py` in the Database class:

```python
async def batch_insert_graph_edges(self, edges: List[Dict[str, Any]]) -> None:
    """Batch insert graph edges into the database.

    Args:
        edges: List of edge dictionaries with keys:
            - source_repo: str
            - target_repo: str
            - edge_type: str
            - weight: float
            - metadata: str (JSON)
    """
    if not edges:
        return

    query = """
        INSERT INTO graph_edges (source_repo, target_repo, edge_type, weight, metadata)
        VALUES (?, ?, ?, ?, ?)
    """

    # Prepare batch data
    data = [
        (
            edge["source_repo"],
            edge["target_repo"],
            edge["edge_type"],
            edge["weight"],
            edge.get("metadata", "{}")
        )
        for edge in edges
    ]

    # Execute batch insert using executemany
    await self.execute_query(query, data, many=True)
```

Also update `execute_query` to support batch operations:

```python
async def execute_query(self, query: str, params=(), many=False):
    """Execute a database query.

    Args:
        query: SQL query string
        params: Query parameters (tuple or list of tuples for many=True)
        many: If True, execute with executemany for batch operations

    Returns:
        Query results for SELECT, None for other queries
    """
    async with aiosqlite.connect(self.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.cursor()

        if many:
            await cursor.executemany(query, params)
            await db.commit()
            return None
        else:
            await cursor.execute(query, params)
            await db.commit()

            if query.strip().upper().startswith("SELECT"):
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
            return None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_sqlite.py::test_batch_insert_graph_edges -v`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/test_sqlite.py src/db/sqlite.py
git commit -m "feat: add batch_insert_graph_edges method to database"
```

---

## Task 3: Hybrid Recommendation Service

**Files:**
- Create: `src/services/hybrid_recommendation.py`
- Test: `tests/unit/test_hybrid_recommendation.py`

**Step 1: Write the failing test**

Create `tests/unit/test_hybrid_recommendation.py`:

```python
"""Tests for hybrid recommendation service."""
import pytest
from unittest.mock import Mock, AsyncMock
from src.services.hybrid_recommendation import HybridRecommendationService


@pytest.fixture
def mock_db():
    """Mock database."""
    db = Mock()
    db.get_graph_edges = AsyncMock(return_value=[
        {
            "source_repo": "anthropic/claude-docs",
            "target_repo": "anthropic/claude-cookbook",
            "edge_type": "author",
            "weight": 1.0
        },
        {
            "source_repo": "anthropic/claude-docs",
            "target_repo": "openai/openai-cookbook",
            "edge_type": "ecosystem",
            "weight": 0.5
        }
    ])
    db.get_repository = AsyncMock(return_value={
        "name_with_owner": "anthropic/claude-cookbook",
        "name": "claude-cookbook",
        "owner": "anthropic",
        "description": "Cookbook"
    })
    return db


@pytest.fixture
def mock_semantic_search():
    """Mock semantic search."""
    semantic = Mock()
    semantic.get_similar_repos = AsyncMock(return_value=[
        {"name_with_owner": "anthropic/claude-cookbook", "score": 0.85},
        {"name_with_owner": "google/ai-toolkit", "score": 0.78},
    ])
    return semantic


@pytest.mark.asyncio
async def test_get_recommendations_with_semantic(mock_db, mock_semantic_search):
    """Test getting hybrid recommendations with semantic search."""
    service = HybridRecommendationService(mock_db, mock_semantic_search)

    recommendations = await service.get_recommendations(
        "anthropic/claude-docs",
        limit=10,
        include_semantic=True
    )

    assert len(recommendations) > 0

    # Check first recommendation
    first_rec = recommendations[0]
    assert "name_with_owner" in first_rec
    assert "final_score" in first_rec
    assert "sources" in first_rec
    assert isinstance(first_rec["final_score"], float)
    assert isinstance(first_rec["sources"], list)


@pytest.mark.asyncio
async def test_recommendation_fusion_weights(mock_db, mock_semantic_search):
    """Test that graph and semantic scores are properly weighted."""
    service = HybridRecommendationService(mock_db, mock_semantic_search)

    recommendations = await service.get_recommendations(
        "anthropic/claude-docs",
        limit=10,
        include_semantic=True
    )

    # Find a repo that appears in both graph and semantic
    anthropic_cookbook = next(
        (r for r in recommendations if r["name_with_owner"] == "anthropic/claude-cookbook"),
        None
    )

    assert anthropic_cookbook is not None
    assert "author" in anthropic_cookbook["sources"]  # From graph
    assert "semantic" in anthropic_cookbook["sources"]  # From semantic

    # Score should be weighted: 0.65 * graph + 0.35 * semantic
    # graph_score = 1.0 (author edge weight 1.0)
    # semantic_score = 0.85
    # expected = 0.65 * 1.0 + 0.35 * 0.85 = 0.9475
    expected_score = 0.65 * 1.0 + 0.35 * 0.85
    assert abs(anthropic_cookbook["final_score"] - expected_score) < 0.01


@pytest.mark.asyncio
async def test_recommendations_without_semantic_fallback(mock_db):
    """Test fallback to graph-only when semantic search is None."""
    service = HybridRecommendationService(mock_db, semantic_search=None)

    recommendations = await service.get_recommendations(
        "anthropic/claude-docs",
        limit=10,
        include_semantic=True
    )

    # Should still return recommendations
    assert len(recommendations) > 0

    # None should have semantic source
    for rec in recommendations:
        assert "semantic" not in rec["sources"]


@pytest.mark.asyncio
async def test_recommendations_exclude_repos(mock_db, mock_semantic_search):
    """Test that specified repos are excluded from recommendations."""
    service = HybridRecommendationService(mock_db, mock_semantic_search)

    recommendations = await service.get_recommendations(
        "anthropic/claude-docs",
        limit=10,
        include_semantic=True,
        exclude_repos={"anthropic/claude-cookbook"}
    )

    # claude-cookbook should not be in results
    assert not any(r["name_with_owner"] == "anthropic/claude-cookbook" for r in recommendations)


@pytest.mark.asyncio
async def test_recommendations_diversity_limit_same_author(mock_db, mock_semantic_search):
    """Test that recommendations limit repos from same author."""
    # Setup mock to return many repos from same author
    mock_db.get_graph_edges = AsyncMock(return_value=[
        {"target_repo": f"anthropic/repo{i}", "edge_type": "author", "weight": 1.0}
        for i in range(10)
    ])

    service = HybridRecommendationService(mock_db, mock_semantic_search)

    recommendations = await service.get_recommendations(
        "anthropic/claude-docs",
        limit=10
    )

    # Count repos by author
    from collections import Counter
    authors = [r.get("owner") for r in recommendations]
    author_counts = Counter(authors)

    # No author should appear more than 2 times
    for author, count in author_counts.items():
        assert count <= 2, f"Author {author} appears {count} times, max 2 allowed"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_hybrid_recommendation.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'src.services.hybrid_recommendation'"

**Step 3: Write minimal implementation**

Create `src/services/hybrid_recommendation.py`:

```python
"""Hybrid recommendation service combining graph and semantic similarity."""
from typing import List, Dict, Any, Set, Optional
from loguru import logger


class HybridRecommendationService:
    """Hybrid recommendation service fusing graph edges and semantic similarity."""

    # Weight configuration
    WEIGHT_GRAPH = 0.65
    WEIGHT_SEMANTIC = 0.35

    # Edge type weights for normalization
    EDGE_TYPE_WEIGHTS = {
        "author": 1.0,
        "ecosystem": 0.5,
        "collection": 0.5,
    }

    def __init__(self, db, semantic_search=None):
        """Initialize hybrid recommendation service.

        Args:
            db: Database instance
            semantic_search: Optional SemanticSearch instance
        """
        self.db = db
        self.semantic_search = semantic_search

    async def get_recommendations(
        self,
        repo_name: str,
        limit: int = 10,
        include_semantic: bool = True,
        exclude_repos: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get hybrid recommendations for a repository.

        Args:
            repo_name: Repository identifier (e.g., "anthropic/claude-docs")
            limit: Maximum number of recommendations to return
            include_semantic: Whether to include semantic similarity
            exclude_repos: Set of repo names to exclude from results

        Returns:
            List of recommendation dicts with keys:
                - name_with_owner: str
                - name: str
                - owner: str
                - final_score: float
                - sources: List[str]
                - graph_score: Optional[float]
                - semantic_score: Optional[float]
        """
        exclude_repos = exclude_repos or set()

        # Stage 1: Multi-source recall
        graph_candidates = await self._recall_from_graph(repo_name)
        semantic_candidates = await self._recall_from_semantic(
            repo_name if include_semantic else None
        )

        # Stage 2: Weighted fusion
        fused = self._fuse_scores(graph_candidates, semantic_candidates)

        # Stage 3: Diversity optimization
        optimized = self._optimize_diversity(fused, exclude_repos, limit)

        return optimized

    async def _recall_from_graph(self, repo_name: str) -> Dict[str, Dict]:
        """Recall candidates from graph edges.

        Returns:
            Dict mapping repo_name to {score, sources}
        """
        edges = await self.db.get_graph_edges(
            source_repo=repo_name,
            edge_types=["author", "ecosystem", "collection"]
        )

        candidates = {}
        for edge in edges:
            target = edge["target_repo"]
            edge_type = edge["edge_type"]
            weight = edge["weight"]

            if target not in candidates:
                candidates[target] = {"score": 0.0, "sources": []}

            # Add weighted score
            type_weight = self.EDGE_TYPE_WEIGHTS.get(edge_type, 0.5)
            candidates[target]["score"] += weight * type_weight
            candidates[target]["sources"].append(edge_type)

        return candidates

    async def _recall_from_semantic(self, repo_name: Optional[str]) -> Dict[str, Dict]:
        """Recall candidates from semantic similarity.

        Returns:
            Dict mapping repo_name to {score, sources}
        """
        if not repo_name or not self.semantic_search:
            return {}

        try:
            similar = await self.semantic_search.get_similar_repos(
                repo_name, top_k=20
            )

            return {
                s["name_with_owner"]: {
                    "score": s["score"],
                    "sources": ["semantic"]
                }
                for s in similar
            }
        except Exception as e:
            logger.warning(f"Semantic recall failed for {repo_name}: {e}")
            return {}

    def _fuse_scores(
        self,
        graph: Dict[str, Dict],
        semantic: Dict[str, Dict]
    ) -> List[Dict]:
        """Fuse graph and semantic scores with weighted combination.

        Returns:
            List of candidate dicts with fused scores
        """
        # Get all unique repos
        all_repos = set(graph.keys()) | set(semantic.keys())

        fused = []
        for repo_name in all_repos:
            graph_data = graph.get(repo_name, {"score": 0.0, "sources": []})
            semantic_data = semantic.get(repo_name, {"score": 0.0, "sources": []})

            # Calculate weighted fusion
            graph_score = graph_data["score"]
            semantic_score = semantic_data["score"]

            # Normalize graph score to 0-1 (assuming max graph score is 2.0)
            normalized_graph = min(graph_score / 2.0, 1.0)

            # Weighted fusion
            final_score = (
                self.WEIGHT_GRAPH * normalized_graph +
                self.WEIGHT_SEMANTIC * semantic_score
            )

            # Combine sources
            sources = graph_data["sources"] + semantic_data["sources"]

            fused.append({
                "name_with_owner": repo_name,
                "graph_score": normalized_graph if graph_score > 0 else None,
                "semantic_score": semantic_score if semantic_score > 0 else None,
                "final_score": final_score,
                "sources": sources
            })

        return fused

    def _optimize_diversity(
        self,
        candidates: List[Dict],
        exclude_repos: Set[str],
        limit: int
    ) -> List[Dict]:
        """Optimize diversity: deduplicate, exclude, limit per author.

        Args:
            candidates: List of candidate dicts
            exclude_repos: Repos to exclude
            limit: Max results to return

        Returns:
            Optimized and sorted list of recommendations
        """
        # Filter out excluded repos
        filtered = [
            c for c in candidates
            if c["name_with_owner"] not in exclude_repos
        ]

        # Sort by final score
        filtered.sort(key=lambda x: x["final_score"], reverse=True)

        # Limit same author to 2 repos
        seen_authors = {}
        diverse = []
        for candidate in filtered:
            repo_name = candidate["name_with_owner"]
            owner = repo_name.split("/")[0] if "/" in repo_name else repo_name

            count = seen_authors.get(owner, 0)
            if count < 2:
                diverse.append(candidate)
                seen_authors[owner] = count + 1

            if len(diverse) >= limit:
                break

        return diverse
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_hybrid_recommendation.py -v`

Expected: PASS (may need to adjust mock setup for get_repository)

**Step 5: Commit**

```bash
git add tests/unit/test_hybrid_recommendation.py src/services/hybrid_recommendation.py
git commit -m "feat: add hybrid recommendation service"
```

---

## Task 4: Recommendation API Routes

**Files:**
- Create: `src/api/routes/recommendation.py`
- Modify: `src/api/app.py`

**Step 1: Write the API route**

Create `src/api/routes/recommendation.py`:

```python
"""Recommendation API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Set
from pydantic import BaseModel

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


class RecommendationResponse(BaseModel):
    """Recommendation response model."""
    name_with_owner: str
    name: str
    owner: str
    description: Optional[str] = None
    final_score: float
    sources: list[str]
    graph_score: Optional[float] = None
    semantic_score: Optional[float] = None


@router.get("/{repo_name}", response_model=list[RecommendationResponse])
async def get_recommendations(
    repo_name: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of recommendations"),
    include_semantic: bool = Query(True, description="Include semantic similarity"),
    exclude_repos: str = Query(None, description="Comma-separated list of repos to exclude")
):
    """Get hybrid recommendations for a repository.

    Combines graph edges (author, ecosystem, collection) with semantic similarity
    to provide high-quality project recommendations.

    - **repo_name**: Repository identifier (e.g., "anthropic/claude-docs")
    - **limit**: Maximum recommendations to return (default: 10, max: 50)
    - **include_semantic**: Whether to include semantic similarity (default: true)
    - **exclude_repos**: Repos to exclude (e.g., "repo1,repo2")
    """
    from src.api.app import hybrid_recommendation_service

    if not hybrid_recommendation_service:
        raise HTTPException(
            status_code=503,
            detail="Recommendation service not available"
        )

    # Parse exclude list
    exclude_set = set()
    if exclude_repos:
        exclude_set = set(r.strip() for r in exclude_repos.split(","))

    try:
        recommendations = await hybrid_recommendation_service.get_recommendations(
            repo_name=repo_name,
            limit=limit,
            include_semantic=include_semantic,
            exclude_repos=exclude_set
        )

        # Enrich with repository details
        enriched = []
        for rec in recommendations:
            repo_data = await hybrid_recommendation_service.db.get_repository(
                rec["name_with_owner"]
            )
            if repo_data:
                enriched.append({
                    **rec,
                    "name": repo_data.get("name", ""),
                    "owner": repo_data.get("owner", ""),
                    "description": repo_data.get("description")
                })

        return enriched

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendations: {str(e)}"
        )
```

**Step 2: Register router in app.py**

Add to `src/api/app.py`:

```python
from src.api.routes import recommendation

# Add to app initialization
app.include_router(recommendation.router)
```

Also initialize hybrid_recommendation_service:

```python
# After semantic_search initialization
hybrid_recommendation_service = None
if semantic_search:
    from src.services.hybrid_recommendation import HybridRecommendationService
    hybrid_recommendation_service = HybridRecommendationService(db, semantic_search)
```

**Step 3: Test API endpoint**

Run: `curl http://localhost:8889/api/recommendations/anthropic/claude-docs?limit=5`

Expected: JSON array with recommendations

**Step 4: Commit**

```bash
git add src/api/routes/recommendation.py src/api/app.py
git commit -m "feat: add recommendation API endpoints"
```

---

## Task 5: Semantic Edge Rebuild API

**Files:**
- Modify: `src/api/routes/graph.py`

**Step 1: Add rebuild endpoint**

Add to `src/api/routes/graph.py`:

```python
from fastapi import BackgroundTasks

@router.post("/semantic-edges/rebuild")
async def rebuild_semantic_edges(
    background_tasks: BackgroundTasks,
    top_k: int = Query(10, ge=1, le=50, description="Number of similar repos per repo"),
    min_similarity: float = Query(0.6, ge=0.0, le=1.0, description="Minimum similarity score")
):
    """Trigger full rebuild of semantic edges.

    Runs in background to avoid timeout. Check /api/graph/status for progress.

    - **top_k**: Number of similar repos to find for each repository
    - **min_similarity**: Minimum similarity score to create an edge
    """
    from src.api.app import semantic_edge_discovery

    if not semantic_edge_discovery:
        raise HTTPException(
            status_code=503,
            detail="Semantic edge discovery not available (semantic search not configured)"
        )

    def rebuild_task():
        import asyncio
        result = asyncio.run(
            semantic_edge_discovery.discover_and_store_edges(
                top_k=top_k,
                min_similarity=min_similarity
            )
        )
        logger.info(f"Semantic edge rebuild complete: {result}")

    background_tasks.add_task(rebuild_task)

    return {
        "status": "background_task_started",
        "message": "Semantic edge rebuild has been started in the background",
        "parameters": {
            "top_k": top_k,
            "min_similarity": min_similarity
        }
    }
```

**Step 2: Initialize semantic_edge_discovery in app.py**

Add to `src/api/app.py`:

```python
# Initialize semantic edge discovery if semantic search is available
semantic_edge_discovery = None
if semantic_search:
    from src.services.graph.semantic_edges import SemanticEdgeDiscovery
    semantic_edge_discovery = SemanticEdgeDiscovery(semantic_search, db)
```

**Step 3: Test endpoint**

Run: `curl -X POST http://localhost:8889/api/graph/semantic-edges/rebuild?top_k=10`

Expected: `{"status": "background_task_started", ...}`

**Step 4: Commit**

```bash
git add src/api/routes/graph.py src/api/app.py
git commit -m "feat: add semantic edge rebuild API endpoint"
```

---

## Task 6: Integrate Semantic Edge Updates into Sync

**Files:**
- Modify: `src/services/sync.py`

**Step 1: Add semantic_edge_discovery parameter**

Modify `SyncService.__init__`:

```python
def __init__(self, db: Database, llm=None, semantic_search=None, semantic_edge_discovery=None):
    """Initialize sync service.

    Args:
        db: Database instance
        llm: Optional LLM for analysis
        semantic_search: Optional semantic search for vector updates
        semantic_edge_discovery: Optional semantic edge discovery for graph updates
    """
    self.db = db
    self.llm = llm
    self.semantic_search = semantic_search
    self.semantic_edge_discovery = semantic_edge_discovery
```

**Step 2: Trigger semantic edge update in _update_repository**

Add after vector update:

```python
# In _update_repository method, after semantic_search.update_repository
if self.semantic_edge_discovery and self._needs_vector_update(changes):
    # Trigger semantic edge update asynchronously (don't block sync)
    asyncio.create_task(
        self.semantic_edge_discovery._update_semantic_edges_for_single_repo(
            name_with_owner
        )
    )
```

**Step 3: Add full rebuild in sync method**

Add in `sync` method when full_sync=True:

```python
# In sync method, after sync loop
if full_sync and self.semantic_edge_discovery:
    logger.info("Full sync: rebuilding semantic edges...")
    await self.semantic_edge_discovery.discover_and_store_edges(
        top_k=10, min_similarity=0.6
    )
```

**Step 4: Update app.py to pass semantic_edge_discovery**

Modify sync service initialization:

```python
from src.services.sync import SyncService

sync_service = SyncService(
    db,
    llm,
    semantic_search,
    semantic_edge_discovery
)
```

**Step 5: Update sync route**

Modify `src/api/routes/sync.py` to pass semantic_edge_discovery:

```python
from src.api.app import sync_service, semantic_edge_discovery

# In manual_sync endpoint
sync = SyncService(
    db,
    llm=llm,
    semantic_search=semantic_search,
    semantic_edge_discovery=semantic_edge_discovery
)
```

**Step 6: Test with manual sync**

Run: `curl -X POST http://localhost:8889/api/sync/manual?full_sync=true`

Expected: Sync completes and semantic edges are rebuilt

**Step 7: Commit**

```bash
git add src/services/sync.py src/api/routes/sync.py src/api/app.py
git commit -m "feat: integrate semantic edge updates into sync service"
```

---

## Task 7: Frontend Search View Integration

**Files:**
- Modify: `frontend/src/views/SearchView.vue`
- Create: `frontend/src/types/recommendation.ts`

**Step 1: Create TypeScript types**

Create `frontend/src/types/recommendation.ts`:

```typescript
/** Recommendation source types */
export type RecommendationSource = 'author' | 'ecosystem' | 'collection' | 'semantic'

/** Recommendation response */
export interface Recommendation {
  name_with_owner: string
  name: string
  owner: string
  description?: string
  final_score: number
  sources: RecommendationSource[]
  graph_score?: number
  semantic_score?: number
}

/** Source display labels */
export const SOURCE_LABELS: Record<RecommendationSource, string> = {
  author: '同一作者',
  ecosystem: '技术栈',
  collection: '收藏夹',
  semantic: '语义相似'
}
```

**Step 2: Add recommendation API call to SearchView.vue**

Add to script setup:

```typescript
import { ref } from 'vue'
import type { Recommendation } from '@/types/recommendation'

const recommendations = ref<Recommendation[]>([])

const fetchRecommendations = async (repoName: string) => {
  try {
    const response = await fetch(
      `/api/recommendations/${encodeURIComponent(repoName)}?limit=5&include_semantic=true`
    )
    if (response.ok) {
      recommendations.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to fetch recommendations:', error)
  }
}
```

**Step 3: Update template to show hybrid recommendations**

Replace existing recommendation section (lines 190-218):

```vue
<div class="related-recommendations" v-if="recommendations.length > 0">
  <h3>关联推荐</h3>
  <div class="repo-list">
    <div
      v-for="repo in recommendations"
      :key="repo.name_with_owner"
      class="repo-card"
      @click="navigateToRepo(repo.name_with_owner)"
    >
      <div class="repo-info">
        <h4>{{ repo.name }}</h4>
        <p class="repo-owner">{{ repo.owner }}</p>
        <p class="repo-description" v-if="repo.description">
          {{ repo.description.substring(0, 100) }}...
        </p>
        <div class="repo-sources">
          <span
            v-for="source in repo.sources"
            :key="source"
            :class="['source-tag', `source-${source}`]"
          >
            {{ SOURCE_LABELS[source] }}
          </span>
        </div>
        <div class="repo-score">
          匹配度: {{ (repo.final_score * 100).toFixed(0) }}%
        </div>
      </div>
    </div>
  </div>
</div>
```

**Step 4: Add CSS styles**

Add to style section:

```css
.source-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 4px;
  margin-bottom: 4px;
}

.source-semantic {
  background: #e3f2fd;
  color: #1976d2;
}

.source-author {
  background: #f3e5f5;
  color: #7b1fa2;
}

.source-ecosystem {
  background: #e8f5e9;
  color: #388e3c;
}

.source-collection {
  background: #fff3e0;
  color: #f57c00;
}

.repo-score {
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}
```

**Step 5: Test in browser**

Navigate to search page, observe recommendations showing mixed sources

**Step 6: Commit**

```bash
git add frontend/src/types/recommendation.ts frontend/src/views/SearchView.vue
git commit -m "feat: integrate hybrid recommendations into search view"
```

---

## Task 8: Frontend RepoDetailView Integration

**Files:**
- Modify: `frontend/src/views/RepoDetailView.vue`

**Step 1: Add recommendation section**

Add to template:

```vue
<div class="recommendations-sidebar" v-if="recommendations.length > 0">
  <h3>相似项目</h3>
  <div class="recommendation-list">
    <div
      v-for="repo in recommendations.slice(0, 5)"
      :key="repo.name_with_owner"
      class="recommendation-item"
      @click="navigateToRepo(repo.name_with_owner)"
    >
      <div class="rec-name">{{ repo.name }}</div>
      <div class="rec-owner">{{ repo.owner }}</div>
      <div class="rec-sources">
        <span
          v-for="source in repo.sources"
          :key="source"
          :class="['source-tag', `source-${source}`]"
        >
          {{ SOURCE_LABELS[source] }}
        </span>
      </div>
    </div>
  </div>
</div>
```

**Step 2: Add script logic**

Add to script setup:

```typescript
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import type { Recommendation } from '@/types/recommendation'
import { SOURCE_LABELS } from '@/types/recommendation'

const route = useRoute()
const recommendations = ref<Recommendation[]>([])

onMounted(async () => {
  const repoName = route.params.name as string
  await fetchRecommendations(repoName)
})

const fetchRecommendations = async (repoName: string) => {
  try {
    const response = await fetch(
      `/api/recommendations/${encodeURIComponent(repoName)}?limit=10&include_semantic=true`
    )
    if (response.ok) {
      recommendations.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to fetch recommendations:', error)
  }
}
```

**Step 3: Test in browser**

Navigate to repo detail page, observe sidebar recommendations

**Step 4: Commit**

```bash
git add frontend/src/views/RepoDetailView.vue
git commit -m "feat: add recommendations sidebar to repo detail view"
```

---

## Task 9: Integration Testing

**Files:**
- Create: `tests/integration/test_hybrid_recommendation_e2e.py`

**Step 1: Write integration test**

Create `tests/integration/test_hybrid_recommendation_e2e.py`:

```python
"""End-to-end integration tests for hybrid recommendation system."""
import pytest


@pytest.mark.asyncio
async def test_hybrid_recommendation_flow(db, semantic_search):
    """Test complete recommendation flow with real data."""
    from src.services.graph.semantic_edges import SemanticEdgeDiscovery
    from src.services.hybrid_recommendation import HybridRecommendationService

    # Setup: Create test repositories
    test_repos = [
        {
            "name_with_owner": "test/repo1",
            "name": "repo1",
            "owner": "test",
            "description": "Python web framework",
            "primary_language": "Python"
        },
        {
            "name_with_owner": "test/repo2",
            "name": "repo2",
            "owner": "test",
            "description": "Python async framework",
            "primary_language": "Python"
        },
    ]

    for repo in test_repos:
        await db.insert_repository(repo)

    # Add to semantic search
    await semantic_search.add_repositories(test_repos)

    # Create semantic edges
    edge_discovery = SemanticEdgeDiscovery(semantic_search, db)
    await edge_discovery.discover_and_store_edges(top_k=5, min_similarity=0.5)

    # Test recommendation service
    recommendation_service = HybridRecommendationService(db, semantic_search)
    recommendations = await recommendation_service.get_recommendations(
        "test/repo1",
        limit=5
    )

    # Verify results
    assert len(recommendations) > 0
    assert all("name_with_owner" in r for r in recommendations)
    assert all("final_score" in r for r in recommendations)
    assert all("sources" in r for r in recommendations)


@pytest.mark.asyncio
async def test_recommendation_api_integration(db, semantic_search):
    """Test recommendation API endpoint."""
    from fastapi.testclient import TestClient
    from src.api.app import app

    client = TestClient(app)

    # Setup test data
    await db.insert_repository({
        "name_with_owner": "test/api-repo",
        "name": "api-repo",
        "owner": "test"
    })
    await semantic_search.add_repositories([{
        "name_with_owner": "test/api-repo",
        "description": "Test repository"
    }])

    # Test API
    response = client.get("/api/recommendations/test/api-repo?limit=5")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_semantic_edge_rebuild_api(db, semantic_search):
    """Test semantic edge rebuild API."""
    from fastapi.testclient import TestClient
    from src.api.app import app

    client = TestClient(app)

    # Trigger rebuild
    response = client.post("/api/graph/semantic-edges/rebuild?top_k=5")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "background_task_started"
```

**Step 2: Run integration tests**

Run: `pytest tests/integration/test_hybrid_recommendation_e2e.py -v`

Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_hybrid_recommendation_e2e.py
git commit -m "test: add hybrid recommendation integration tests"
```

---

## Task 10: Documentation Updates

**Files:**
- Modify: `docs/business-logic.md`
- Modify: `CHANGELOG.md`

**Step 1: Update business-logic.md**

Add section 2.9 "混合推荐系统":

```markdown
### 2.9 混合推荐系统 (Hybrid Recommendation)

**功能定位**: 融合图谱关系和语义相似度，提供高质量项目推荐

**推荐流程**:
```
1. 多源召回:
   - 图谱边召回 (权重 65%): author (1.0), ecosystem (0.5), collection (0.5)
   - 语义相似召回 (权重 35%): ChromaDB 向量余弦相似度

2. 加权融合:
   final_score = 0.65 * graph_score + 0.35 * semantic_score

3. 多样性优化:
   - 去重
   - 排除已搜索/已查看仓库
   - 同一作者最多 2 个
```

**语义边更新策略**:
- **增量更新**: 同步时只更新变化仓库的语义边（异步，不阻塞）
- **全量重建**: 手动全量同步时重建所有语义边
- **定时任务**: 每周全量同步时重建

**API 端点**:
- `GET /api/recommendations/{repo}` - 获取混合推荐
- `POST /api/graph/semantic-edges/rebuild` - 重建语义边

**引用**:
- 服务: `src/services/hybrid_recommendation.py` → `HybridRecommendationService`
- 语义边: `src/services/graph/semantic_edges.py` → `SemanticEdgeDiscovery`
- API: `src/api/routes/recommendation.py`
```

**Step 2: Update CHANGELOG.md**

Add v1.2.0 entry:

```markdown
## [1.2.0] - 2025-01-20

### Added
- 混合推荐系统：融合图谱关系和语义相似度
- 语义边发现服务：自动计算仓库间语义相似度
- 推荐API端点：`/api/recommendations/{repo}`
- 语义边重建API：`/api/graph/semantic-edges/rebuild`
- 增量语义边更新：同步时只更新变化仓库
- 推荐来源标注：显示推荐来源（同一作者、技术栈、语义相似等）
- 推荐侧边栏：仓库详情页添加相似项目推荐

### Changed
- 搜索页推荐区域：使用混合推荐替代纯图谱推荐
- 同步服务：集成语义边增量更新
- 全量同步：自动重建所有语义边
```

**Step 3: Commit**

```bash
git add docs/business-logic.md CHANGELOG.md
git commit -m "docs: update documentation for hybrid recommendation system"
```

---

## Task 11: Final Testing and Validation

**Step 1: Run full test suite**

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Full suite with coverage
pytest --cov=src tests/ -v
```

Expected: All tests pass, coverage > 80%

**Step 2: Manual testing checklist**

- [ ] Start backend: `uvicorn src.api.app:app --reload`
- [ ] Start frontend: `cd frontend && npm run dev`
- [ ] Navigate to search page
- [ ] Perform search, verify recommendations show
- [ ] Check recommendation sources are labeled correctly
- [ ] Navigate to repo detail page
- [ ] Verify sidebar recommendations appear
- [ ] Test manual sync: `curl -X POST http://localhost:8889/api/sync/manual?full_sync=true`
- [ ] Test semantic edge rebuild: `curl -X POST http://localhost:8889/api/graph/semantic-edges/rebuild`
- [ ] Test recommendation API: `curl http://localhost:8889/api/recommendations/anthropic/claude-docs`

**Step 3: Performance validation**

- [ ] Semantic edge update for single repo: < 100ms
- [ ] Hybrid recommendation query: < 500ms
- [ ] Full semantic edge rebuild (500 repos): < 60s

**Step 4: Final commit**

```bash
git add .
git commit -m "chore: finalize hybrid recommendation system implementation"
```

---

## Summary

This plan implements a complete hybrid recommendation system that:

✅ Combines graph edges (65%) and semantic similarity (35%)
✅ Uses incremental updates for changed repos during sync
✅ Rebuilds all semantic edges during full sync
✅ Provides diversity optimization (max 2 repos per author)
✅ Falls back to graph-only when semantic search unavailable
✅ Labels recommendation sources in UI
✅ Exposes recommendation and rebuild APIs

**Total estimated implementation time**: 4-6 hours following TDD approach with frequent commits.
