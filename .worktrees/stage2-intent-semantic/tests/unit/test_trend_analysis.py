import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.trend_analysis import TrendAnalysisService

@pytest.mark.asyncio
async def test_get_star_timeline():
    # Create mock cursor with fetchall
    mock_cursor = MagicMock()
    mock_cursor.fetchall = AsyncMock(return_value=[
        ("2024-01", 5),
        ("2024-02", 3)
    ])

    db = MagicMock()
    # execute returns cursor directly when awaited (aiosqlite behavior)
    db._connection.execute = AsyncMock(return_value=mock_cursor)

    service = TrendAnalysisService(db)
    timeline = await service.get_star_timeline("testuser")

    assert len(timeline) == 2
    assert timeline[0]["month"] == "2024-01"
    assert timeline[0]["count"] == 5
