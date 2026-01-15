import pytest
from src.github.client import GitHubClient


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initializes correctly"""
    async with GitHubClient(token="test_token") as client:
        assert client.token == "test_token"
        assert client._client is not None


@pytest.mark.asyncio
async def test_client_without_token(mocker):
    """Test client uses settings token when not provided"""
    # Mock settings to have no token
    mocker.patch("src.github.base.settings.github_token", None)

    async with GitHubClient(token=None) as client:
        assert client.token is None
        assert client._client is not None


@pytest.mark.asyncio
async def test_get_user(mocker):
    """Test getting user data"""
    mock_response = {
        "id": 1,
        "login": "testuser",
        "name": "Test User",
        "avatar_url": "https://example.com/avatar.png",
        "followers": 10,
        "following": 5,
        "public_repos": 20
    }

    async def mock_get(*args, **kwargs):
        class Response:
            def raise_for_status(self):
                pass
        response = Response()
        response.json = lambda: mock_response
        return response

    mocker.patch("httpx.AsyncClient.get", mock_get)

    async with GitHubClient() as client:
        user = await client.get_user("testuser")
        assert user.login == "testuser"
        assert user.name == "Test User"


@pytest.mark.asyncio
async def test_context_manager():
    """Test client works as context manager"""
    async with GitHubClient() as client:
        assert client._client is not None
    # Client should be closed after context
