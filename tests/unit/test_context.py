import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from src.services.context import ContextService

@pytest.mark.asyncio
async def test_get_context_with_first_round_preserved():
    db = Mock()
    mock_cursor = MagicMock()

    # Mock first round (earliest message)
    mock_cursor.fetchone = AsyncMock(return_value=("user", "First question"))
    mock_cursor.fetchall = AsyncMock(return_value=[("assistant", "First answer"), ("user", "Second question")])

    # Make execute return an async context manager
    async def mock_execute(*args, **kwargs):
        return mock_cursor

    db._connection.execute = mock_execute

    service = ContextService(db)
    context = await service.get_context("test_session", limit=3)

    assert "First question" in context
    assert "User" in context  # Capitalized by the service
    # Should have first message + (limit - 1) recent messages
    assert "First answer" in context
    assert "Second question" in context

@pytest.mark.asyncio
async def test_get_context_empty_session():
    db = Mock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone = AsyncMock(return_value=None)

    # Make execute return an async context manager
    async def mock_execute(*args, **kwargs):
        return mock_cursor

    db._connection.execute = mock_execute

    service = ContextService(db)
    context = await service.get_context("new_session")

    assert context == ""

@pytest.mark.asyncio
async def test_get_context_invalid_limit():
    """Test that limit < 1 raises ValueError."""
    db = Mock()
    service = ContextService(db)

    with pytest.raises(ValueError, match="limit must be >= 1"):
        await service.get_context("test_session", limit=0)

    with pytest.raises(ValueError, match="limit must be >= 1"):
        await service.get_context("test_session", limit=-1)

@pytest.mark.asyncio
async def test_get_context_limit_equals_one():
    """Test that limit=1 returns only the first round."""
    db = Mock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone = AsyncMock(return_value=("user", "Only message"))

    async def mock_execute(*args, **kwargs):
        return mock_cursor

    db._connection.execute = mock_execute

    service = ContextService(db)
    context = await service.get_context("test_session", limit=1)

    # Should only have the first message, no recent ones
    assert "User: Only message" in context
    mock_cursor.fetchall.assert_not_called()

@pytest.mark.asyncio
async def test_get_context_database_error():
    """Test that database errors are wrapped in RuntimeError."""
    db = Mock()

    async def mock_execute(*args, **kwargs):
        raise RuntimeError("Database connection lost")

    db._connection.execute = mock_execute

    service = ContextService(db)

    with pytest.raises(RuntimeError, match="Failed to get context"):
        await service.get_context("test_session")
