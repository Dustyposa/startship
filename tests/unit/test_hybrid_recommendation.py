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
    assert "name" in first_rec
    assert "final_score" in first_rec
    assert "sources" in first_rec
    assert isinstance(first_rec["final_score"], float)
    assert isinstance(first_rec["sources"], list)

    # Verify name is correctly extracted
    if "/" in first_rec["name_with_owner"]:
        expected_name = first_rec["name_with_owner"].split("/")[1]
        assert first_rec["name"] == expected_name


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

    # Score should be weighted: 0.65 * normalized_graph + 0.35 * semantic
    # graph_score = 1.0 (author edge weight 1.0)
    # normalized_graph = 1.0 / 2.0 = 0.5
    # semantic_score = 0.85
    # expected = 0.65 * 0.5 + 0.35 * 0.85 = 0.6225
    expected_score = 0.65 * 0.5 + 0.35 * 0.85
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
