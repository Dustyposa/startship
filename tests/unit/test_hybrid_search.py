"""Tests for hybrid search weighted score fusion."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.hybrid_search import HybridSearch


@pytest.mark.asyncio
async def test_hybrid_search_merge():
    """Test hybrid search merges FTS and semantic results with weighted fusion."""
    # Mock database with FTS scores
    db = MagicMock()
    db.search_repositories = AsyncMock(return_value=[
        {"name_with_owner": "ft/repo1", "name": "repo1", "fts_score": -5.0}
    ])
    # Mock enrichment query (returns empty since data already has stargazer_count in real use)
    db.execute_query = AsyncMock(return_value=[])

    # Mock semantic search with similarity scores
    semantic = MagicMock()
    semantic.search = AsyncMock(return_value=[
        {"name_with_owner": "sem/repo2", "name": "repo2", "similarity_score": 0.85}
    ])

    hybrid = HybridSearch(db, semantic, fts_weight=0.3, semantic_weight=0.7)
    results = await hybrid.search("test query")

    assert len(results) == 2

    # Verify score fields exist
    for r in results:
        assert "fts_score" in r
        assert "semantic_score" in r
        assert "final_score" in r
        assert "match_type" in r

    # Verify match types
    ft_result = next(r for r in results if r["name_with_owner"] == "ft/repo1")
    sem_result = next(r for r in results if r["name_with_owner"] == "sem/repo2")

    assert ft_result["match_type"] == "fts"
    assert ft_result["semantic_score"] == 0  # Only FTS found it

    assert sem_result["match_type"] == "semantic"
    assert sem_result["fts_score"] == 0  # Only semantic found it


@pytest.mark.asyncio
async def test_hybrid_search_fts_fallback():
    """Test hybrid search when FTS fails but semantic works."""
    # FTS fails
    db = MagicMock()
    db.search_repositories = AsyncMock(side_effect=Exception("FTS error"))
    db.execute_query = AsyncMock(return_value=[])

    # Semantic works
    semantic = MagicMock()
    semantic.search = AsyncMock(return_value=[
        {"name_with_owner": "sem/repo1", "name": "repo1", "similarity_score": 0.9}
    ])

    hybrid = HybridSearch(db, semantic)
    results = await hybrid.search("test query")

    assert len(results) == 1
    assert results[0]["name_with_owner"] == "sem/repo1"
    assert results[0]["match_type"] == "semantic"
    assert results[0]["semantic_score"] > 0
    assert results[0]["fts_score"] == 0


@pytest.mark.asyncio
async def test_hybrid_search_no_semantic():
    """Test hybrid search with only FTS (no semantic)."""
    db = MagicMock()
    db.search_repositories = AsyncMock(return_value=[
        {"name_with_owner": "ft/repo1", "name": "repo1", "fts_score": -3.5}
    ])
    db.execute_query = AsyncMock(return_value=[])

    hybrid = HybridSearch(db, semantic=None)
    results = await hybrid.search("test query")

    assert len(results) == 1
    assert results[0]["name_with_owner"] == "ft/repo1"
    assert results[0]["match_type"] == "fts"
    assert results[0]["fts_score"] > 0  # Normalized from BM25
    assert results[0]["semantic_score"] == 0


@pytest.mark.asyncio
async def test_hybrid_search_both_fail():
    """Test hybrid search when both FTS and semantic fail."""
    db = MagicMock()
    db.search_repositories = AsyncMock(side_effect=Exception("DB error"))
    db.execute_query = AsyncMock(return_value=[])

    hybrid = HybridSearch(db, semantic=None)
    results = await hybrid.search("test query")

    assert len(results) == 0


@pytest.mark.asyncio
async def test_weighted_fusion_calculation():
    """Test that final_score = fts_weight * fts_score + semantic_weight * semantic_score."""
    # Mock both searches returning the same repo
    db = MagicMock()
    db.search_repositories = AsyncMock(return_value=[
        {"name_with_owner": "both/repo1", "name": "repo1", "fts_score": -10.0}
    ])
    db.execute_query = AsyncMock(return_value=[])

    semantic = MagicMock()
    semantic.search = AsyncMock(return_value=[
        {"name_with_owner": "both/repo1", "name": "repo1", "similarity_score": 0.8}
    ])

    fts_weight = 0.3
    semantic_weight = 0.7

    hybrid = HybridSearch(db, semantic, fts_weight=fts_weight, semantic_weight=semantic_weight)
    results = await hybrid.search("test query")

    assert len(results) == 1
    result = results[0]

    # Should be hybrid match (both found it)
    assert result["match_type"] == "hybrid"
    assert result["fts_score"] > 0
    assert result["semantic_score"] > 0

    # Verify weighted fusion calculation
    expected_final = fts_weight * result["fts_score"] + semantic_weight * result["semantic_score"]
    assert abs(result["final_score"] - expected_final) < 0.01, \
        f"Final score calculation incorrect: expected {expected_final:.3f}, got {result['final_score']:.3f}"


@pytest.mark.asyncio
async def test_results_sorted_by_final_score():
    """Test that results are sorted by final_score descending."""
    db = MagicMock()
    db.search_repositories = AsyncMock(return_value=[
        {"name_with_owner": "ft/repo1", "name": "repo1", "fts_score": -20.0},  # Lower BM25
        {"name_with_owner": "ft/repo2", "name": "repo2", "fts_score": -5.0},   # Higher BM25
    ])
    db.execute_query = AsyncMock(return_value=[])

    semantic = MagicMock()
    semantic.search = AsyncMock(return_value=[
        {"name_with_owner": "sem/repo3", "name": "repo3", "similarity_score": 0.95},
    ])

    hybrid = HybridSearch(db, semantic, fts_weight=0.5, semantic_weight=0.5)
    results = await hybrid.search("test query")

    # Extract final scores
    final_scores = [r["final_score"] for r in results]

    # Verify descending order
    for i in range(len(final_scores) - 1):
        assert final_scores[i] >= final_scores[i + 1], \
            f"Results not sorted: {final_scores[i]} < {final_scores[i + 1]}"


@pytest.mark.asyncio
async def test_bm25_score_normalization():
    """Test that BM25 scores are properly normalized to 0-1 range."""
    db = MagicMock()
    # BM25 scores are typically negative (e.g., -50 to 0)
    db.search_repositories = AsyncMock(return_value=[
        {"name_with_owner": "repo1", "name": "repo1", "fts_score": -1.0},   # Good match
        {"name_with_owner": "repo2", "name": "repo2", "fts_score": -50.0},  # Poor match
    ])
    db.execute_query = AsyncMock(return_value=[])

    hybrid = HybridSearch(db, semantic=None)
    results = await hybrid.search("test query")

    # After normalization, scores should be in 0-1 range
    for result in results:
        assert 0 <= result["fts_score"] <= 1, \
            f"FTS score not normalized: {result['fts_score']}"

    # Better BM25 score (less negative) should have higher normalized score
    repo1 = next(r for r in results if r["name_with_owner"] == "repo1")
    repo2 = next(r for r in results if r["name_with_owner"] == "repo2")
    assert repo1["fts_score"] > repo2["fts_score"], \
        "Better BM25 match should have higher normalized score"

