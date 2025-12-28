import pytest
from src.services.chat import ChatService


@pytest.mark.asyncio
async def test_chat_service_creation(db):
    """Test creating chat service"""
    llm = None
    from src.services.search import SearchService
    search = SearchService(db)

    service = ChatService(db, llm, search)
    assert service.db is not None
    assert service.search_service is not None


@pytest.mark.asyncio
async def test_create_conversation(db):
    """Test creating a conversation"""
    llm = None
    from src.services.search import SearchService
    search = SearchService(db)

    service = ChatService(db, llm, search)

    conv_id = await service.create_conversation("test_session")
    assert conv_id > 0


@pytest.mark.asyncio
async def test_get_conversation_history(db):
    """Test getting conversation history"""
    llm = None
    from src.services.search import SearchService
    search = SearchService(db)

    service = ChatService(db, llm, search)

    # Create a conversation
    await service.create_conversation("test_session")

    # Get history
    history = await service.get_conversation_history("test_session")
    assert isinstance(history, list)


@pytest.mark.asyncio
async def test_delete_conversation(db):
    """Test deleting a conversation"""
    llm = None
    from src.services.search import SearchService
    search = SearchService(db)

    service = ChatService(db, llm, search)

    # Create a conversation
    await service.create_conversation("test_session")

    # Delete it
    result = await service.delete_conversation("test_session")
    assert result is True
