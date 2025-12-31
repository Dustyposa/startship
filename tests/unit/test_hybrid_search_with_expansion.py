"""Test hybrid search with query expansion."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.hybrid_search import HybridSearch


@pytest.mark.asyncio
async def test_search_expands_queries():
    """Test that search method expands queries using QueryExpander."""
    db = MagicMock()
    semantic = MagicMock()

    service = HybridSearch(db, semantic)

    with patch('src.services.query_expander.QueryExpander') as MockExpander:
        mock_expander_instance = MagicMock()
        mock_expander_instance.expand = AsyncMock(
            return_value=["ml project", "机器学习 project"]
        )
        MockExpander.return_value = mock_expander_instance

        # Mock search methods
        service._fts_search = AsyncMock(return_value=[])
        semantic.search = AsyncMock(return_value=[])

        await service.search("ml project")

        # Verify expansion was called
        mock_expander_instance.expand.assert_called_once_with("ml project")


@pytest.mark.asyncio
async def test_search_with_multiple_expanded_queries():
    """Test that search performs searches with all expanded queries."""
    db = MagicMock()
    semantic = MagicMock()

    service = HybridSearch(db, semantic)

    with patch('src.services.query_expander.QueryExpander') as MockExpander:
        mock_expander_instance = MagicMock()
        mock_expander_instance.expand = AsyncMock(
            return_value=["ml", "机器学习", "machine learning"]
        )
        MockExpander.return_value = mock_expander_instance

        # Mock search methods to return different results
        service._fts_search = AsyncMock(side_effect=[
            [{"name_with_owner": "user/repo1", "match_type": "fts"}],
            [{"name_with_owner": "user/repo2", "match_type": "fts"}],
            [{"name_with_owner": "user/repo3", "match_type": "fts"}]
        ])
        semantic.search = AsyncMock(side_effect=[
            [{"name_with_owner": "user/repo1", "match_type": "semantic"}],
            [{"name_with_owner": "user/repo2", "match_type": "semantic"}],
            [{"name_with_owner": "user/repo4", "match_type": "semantic"}]
        ])

        results = await service.search("ml", top_k=10)

        # Verify all expanded queries were searched
        assert service._fts_search.call_count == 3
        assert semantic.search.call_count == 3

        # Verify results are deduplicated
        repo_names = [r["name_with_owner"] for r in results]
        assert len(repo_names) == len(set(repo_names))


@pytest.mark.asyncio
async def test_search_deduplicates_results():
    """Test that search deduplicates results from multiple queries."""
    db = MagicMock()
    semantic = MagicMock()

    service = HybridSearch(db, semantic)

    with patch('src.services.query_expander.QueryExpander') as MockExpander:
        mock_expander_instance = MagicMock()
        mock_expander_instance.expand = AsyncMock(
            return_value=["ml", "机器学习"]
        )
        MockExpander.return_value = mock_expander_instance

        # Both queries return the same repo
        service._fts_search = AsyncMock(side_effect=[
            [{"name_with_owner": "user/ml-repo", "stars": 100, "match_type": "fts"}],
            [{"name_with_owner": "user/ml-repo", "stars": 100, "match_type": "fts"}]
        ])
        semantic.search = AsyncMock(return_value=[])

        results = await service.search("ml", top_k=10)

        # Should only have one instance of the repo
        assert len(results) == 1
        assert results[0]["name_with_owner"] == "user/ml-repo"


@pytest.mark.asyncio
async def test_search_handles_exception_in_fts():
    """Test that search handles exceptions in FTS gracefully."""
    db = MagicMock()
    semantic = MagicMock()

    service = HybridSearch(db, semantic)

    with patch('src.services.query_expander.QueryExpander') as MockExpander:
        mock_expander_instance = MagicMock()
        mock_expander_instance.expand = AsyncMock(
            return_value=["ml"]
        )
        MockExpander.return_value = mock_expander_instance

        # FTS raises exception
        service._fts_search = AsyncMock(side_effect=Exception("FTS error"))
        semantic.search = AsyncMock(
            return_value=[{"name_with_owner": "user/repo1", "match_type": "semantic"}]
        )

        results = await service.search("ml", top_k=10)

        # Should return results from semantic search only
        assert len(results) == 1
        assert results[0]["name_with_owner"] == "user/repo1"


@pytest.mark.asyncio
async def test_search_without_semantic():
    """Test that search works when semantic is None."""
    db = MagicMock()
    semantic = None

    service = HybridSearch(db, semantic)

    with patch('src.services.query_expander.QueryExpander') as MockExpander:
        mock_expander_instance = MagicMock()
        mock_expander_instance.expand = AsyncMock(
            return_value=["ml"]
        )
        MockExpander.return_value = mock_expander_instance

        service._fts_search = AsyncMock(
            return_value=[{"name_with_owner": "user/repo1", "match_type": "fts"}]
        )

        results = await service.search("ml", top_k=10)

        # Should return FTS results
        assert len(results) == 1
        assert results[0]["name_with_owner"] == "user/repo1"
