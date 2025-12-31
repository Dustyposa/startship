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
    # Use AsyncMock for the async context manager
    db._connection.execute = AsyncMock(return_value=mock_cursor)

    service = TrendAnalysisService(db)
    timeline = await service.get_star_timeline("testuser")

    assert len(timeline) == 2
    assert timeline[0]["month"] == "2024-01"
    assert timeline[0]["count"] == 5


@pytest.mark.asyncio
async def test_get_language_trend():
    db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall = AsyncMock(return_value=[
        ("Python", "2024-01", 10),
        ("JavaScript", "2024-01", 5)
    ])
    db._connection.execute = AsyncMock(return_value=mock_cursor)

    service = TrendAnalysisService(db)
    trends = await service.get_language_trend()

    assert len(trends) == 2
    assert trends[0]["language"] == "Python"
    assert trends[0]["month"] == "2024-01"
    assert trends[0]["count"] == 10


@pytest.mark.asyncio
async def test_get_category_evolution():
    db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall = AsyncMock(return_value=[
        ("ai", "2024-01", 8),
        ("web", "2024-01", 3)
    ])
    db._connection.execute = AsyncMock(return_value=mock_cursor)

    service = TrendAnalysisService(db)
    evolution = await service.get_category_evolution()

    assert len(evolution) == 2
    assert evolution[0]["category"] == "ai"
    assert evolution[0]["month"] == "2024-01"
    assert evolution[0]["count"] == 8
