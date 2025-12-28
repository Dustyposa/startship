import pytest
from src.services.init import InitializationService


@pytest.mark.asyncio
async def test_initialization_service_creation(db):
    """Test creating initialization service"""
    service = InitializationService(db, llm=None)
    assert service.db is not None
    assert service.llm is None


@pytest.mark.asyncio
async def test_initialize_requires_llm(db):
    """Test initialization requires LLM unless skip_llm=True"""
    service = InitializationService(db, llm=None)

    with pytest.raises(ValueError, match="LLM is required"):
        await service.initialize_from_stars(skip_llm=False)


@pytest.mark.asyncio
async def test_initialize_skip_llm_no_error(db, mocker):
    """Test skip_llm=True bypasses LLM requirement"""
    service = InitializationService(db, llm=None)

    # Mock GitHubClient context manager
    class MockGitHubClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def get_all_starred(self, *args, **kwargs):
            return []

    mocker.patch("src.services.init.GitHubClient", return_value=MockGitHubClient())

    result = await service.initialize_from_stars(skip_llm=True)
    assert "fetched" in result
    assert result["fetched"] == 0


@pytest.mark.asyncio
async def test_initialize_with_data(db, mocker):
    """Test initialization processes repositories"""
    from src.github.models import GitHubRepository

    # Mock LLM
    class MockLLM:
        async def analyze_repository(self, *args, **kwargs):
            return {
                "name_with_owner": "test/repo",
                "summary": "Test summary",
                "categories": ["工具"],
                "features": [],
                "tech_stack": ["Python"],
                "use_cases": []
            }

    # Mock GitHubClient
    class MockGitHubClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass

        async def get_all_starred(self, *args, **kwargs):
            return [
                GitHubRepository(
                    id=1,
                    full_name="test/repo",
                    name="repo",
                    owner="test",
                    stargazers_count=100,
                    forks_count=10,
                    html_url="https://github.com/test/repo",
                    created_at="2024-01-01T00:00:00Z",
                    updated_at="2024-01-01T00:00:00Z"
                )
            ]

        async def get_readme_content(self, *args, **kwargs):
            return "Test README"

    mocker.patch("src.services.init.GitHubClient", return_value=MockGitHubClient())

    service = InitializationService(db, llm=MockLLM())
    result = await service.initialize_from_stars(skip_llm=True)

    assert result["fetched"] == 1
    assert result["added"] == 1
