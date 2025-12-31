import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from src.services.chat import ChatService


@pytest.mark.asyncio
async def test_chat_includes_context():
    """Test that chat_with_rag_stream includes conversation context."""
    db = Mock()
    llm = MagicMock()

    service = ChatService(db, llm, None)

    # Mock the database's execute method to return context
    mock_cursor = MagicMock()
    mock_cursor.fetchone = AsyncMock(return_value=("user", "Previous question"))
    mock_cursor.fetchall = AsyncMock(return_value=[])

    async def mock_execute(*args, **kwargs):
        return mock_cursor

    db._connection = Mock()
    db._connection.execute = mock_execute

    # Mock LLM stream
    async def mock_stream(messages):
        yield "Response"

    llm.chat_stream = mock_stream

    chunks = []
    async for chunk in service.chat_with_rag_stream("session1", "New question"):
        chunks.append(chunk)

    # Verify we got a response
    assert chunks == ["Response"]


@pytest.mark.asyncio
async def test_chat_with_empty_context():
    """Test that chat_with_rag_stream handles empty context gracefully."""
    db = Mock()
    llm = MagicMock()

    service = ChatService(db, llm, None)

    # Mock the database to return None (empty session)
    mock_cursor = MagicMock()
    mock_cursor.fetchone = AsyncMock(return_value=None)

    async def mock_execute(*args, **kwargs):
        return mock_cursor

    db._connection = Mock()
    db._connection.execute = mock_execute

    # Mock LLM stream
    async def mock_stream(messages):
        yield "Response"

    llm.chat_stream = mock_stream

    chunks = []
    async for chunk in service.chat_with_rag_stream("session1", "New question"):
        chunks.append(chunk)

    # Verify we got a response even with empty context
    assert chunks == ["Response"]


@pytest.mark.asyncio
async def test_chat_with_search_results():
    """Test that chat_with_rag_stream includes search results."""
    db = Mock()
    llm = MagicMock()

    service = ChatService(db, llm, None)

    # Mock the database to return None (empty session)
    mock_cursor = MagicMock()
    mock_cursor.fetchone = AsyncMock(return_value=None)

    async def mock_execute(*args, **kwargs):
        return mock_cursor

    db._connection = Mock()
    db._connection.execute = mock_execute

    # Track messages passed to LLM
    captured_messages = []

    # Mock LLM stream
    async def mock_stream(messages):
        captured_messages.extend(messages)
        yield "Response"

    llm.chat_stream = mock_stream

    search_results = [
        {"name_with_owner": "owner/repo1", "description": "Test repo 1"},
        {"name_with_owner": "owner/repo2", "summary": "Test repo 2"}
    ]

    chunks = []
    async for chunk in service.chat_with_rag_stream(
        "session1",
        "Find repos",
        search_results=search_results
    ):
        chunks.append(chunk)

    # Verify LLM was called with search results in messages
    message_contents = [m.content for m in captured_messages]
    assert any("Relevant repositories" in content for content in message_contents)
    assert any("owner/repo1" in content for content in message_contents)
    assert any("owner/repo2" in content for content in message_contents)


@pytest.mark.asyncio
async def test_format_search_results():
    """Test the _format_search_results helper method."""
    db = Mock()
    llm = MagicMock()

    service = ChatService(db, llm, None)

    search_results = [
        {"name_with_owner": "owner/repo1", "description": "Test repo 1"},
        {"name_with_owner": "owner/repo2", "summary": "Test repo 2"},
        {"name": "repo3", "description": "Test repo 3"}
    ]

    formatted = service._format_search_results(search_results)

    assert "owner/repo1" in formatted
    assert "Test repo 1" in formatted
    assert "owner/repo2" in formatted
    assert "Test repo 2" in formatted
    assert "repo3" in formatted
    assert "Test repo 3" in formatted
