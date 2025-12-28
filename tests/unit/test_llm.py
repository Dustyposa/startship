import pytest
from src.llm import create_llm, OpenAILLM, Message


def test_create_openai_llm():
    """Test creating OpenAI LLM"""
    llm = create_llm("openai", api_key="test_key", model="gpt-4")
    assert isinstance(llm, OpenAILLM)


def test_create_unsupported_llm():
    """Test creating unsupported LLM raises error"""
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_llm("unknown")


@pytest.mark.asyncio
async def test_openai_initialize(mocker):
    """Test OpenAI client initialization"""
    llm = OpenAILLM(api_key="test_key")

    # Mock AsyncOpenAI with async close method
    mock_client = mocker.AsyncMock()
    mocker.patch("src.llm.openai.AsyncOpenAI", return_value=mock_client)

    await llm.initialize()
    assert llm._client is not None

    # Test close
    await llm.close()
    mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_openai_initialize_requires_key(mocker):
    """Test OpenAI requires API key"""
    # Mock settings to have no api_key
    mocker.patch("src.llm.openai.settings.llm_api_key", None)
    mocker.patch("src.llm.openai.settings.llm_base_url", None)

    llm = OpenAILLM(api_key=None)

    with pytest.raises(ValueError, match="OpenAI API key is required"):
        await llm.initialize()

