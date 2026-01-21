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

    await discovery._update_semantic_edges_for_single_repo("test/repo", top_k=10, min_similarity=0.6)

    # Only the high-score edge should be inserted
    edges = mock_db.batch_insert_graph_edges.call_args[0][0]
    assert len(edges) == 1
    assert edges[0]["target_repo"] == "repo1"


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

    # Verify all old semantic edges were deleted once (batch delete at start)
    assert mock_db.execute_query.call_count == 1  # 1 batch delete for all semantic edges
