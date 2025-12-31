import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.recommendation import RecommendationService

@pytest.mark.asyncio
async def test_get_similar_repos():
    db = MagicMock()

    # Mock repo categories - first call
    mock_result1 = AsyncMock()
    mock_result1.fetchone = AsyncMock(return_value=(["AI", "ML"],))

    # Mock similar repos - second call
    mock_result2 = AsyncMock()
    mock_result2.fetchall = AsyncMock(return_value=[
        ("owner/repo1", "test repo", 100, ["AI"]),
        ("owner/repo2", "test repo2", 50, ["ML", "AI"])
    ])

    # Setup execute to return different results on each call
    execute_results = [mock_result1, mock_result2]

    async def mock_execute(*args, **kwargs):
        return execute_results.pop(0)

    db._connection.execute = mock_execute

    service = RecommendationService(db)
    results = await service.get_similar_repos("owner/test_repo")

    assert len(results) == 2
    assert results[0]["name_with_owner"] == "owner/repo1"


@pytest.mark.asyncio
async def test_get_recommended_by_category():
    db = MagicMock()

    # Mock repos by category
    mock_result = AsyncMock()
    mock_result.fetchall = AsyncMock(return_value=[
        ("owner/repo1", "test repo", 100, ["AI", "ML"]),
        ("owner/repo2", "test repo2", 50, ["AI", "Data"])
    ])

    db._connection.execute = AsyncMock(return_value=mock_result)

    service = RecommendationService(db)
    results = await service.get_recommended_by_category("AI")

    assert len(results) == 2
    assert results[0]["name_with_owner"] == "owner/repo1"
    assert results[0]["stargazer_count"] == 100
