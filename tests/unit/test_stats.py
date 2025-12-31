"""Tests for stats service."""
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
