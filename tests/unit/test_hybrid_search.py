"""Tests for hybrid search."""
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


@pytest.mark.asyncio
async def test_hybrid_search_no_semantic():
    # Only FTS, no semantic
    db = MagicMock()
    db.search_repositories = AsyncMock(return_value=[
        {"name_with_owner": "ft/repo1", "name": "repo1"}
    ])

    hybrid = HybridSearch(db, semantic=None)
    results = await hybrid.search("test query")

    assert len(results) == 1
    assert results[0]["name_with_owner"] == "ft/repo1"
    assert results[0]["match_type"] == "fts"


@pytest.mark.asyncio
async def test_hybrid_search_both_fail():
    # Both fail
    db = MagicMock()
    db.search_repositories = AsyncMock(side_effect=Exception("DB error"))

    hybrid = HybridSearch(db, semantic=None)
    results = await hybrid.search("test query")

    assert len(results) == 0
