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

    # Mock GitHubGraphQLClient context manager
    class MockGraphQLClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def get_starred_repositories(self, *args, **kwargs):
            return []

    mocker.patch("src.services.init.GitHubGraphQLClient", return_value=MockGraphQLClient())

    result = await service.initialize_from_stars(skip_llm=True)
    assert "fetched" in result
    assert result["fetched"] == 0


@pytest.mark.asyncio
async def test_initialize_with_data(db, mocker):
    """Test initialization processes repositories"""
    from src.github.models import GitHubRepository
    from datetime import datetime

    # Mock LLM
    class MockLLM:
        async def analyze_repository(self, *args, **kwargs):
            return {
                "name_with_owner": "test/repo",
                "summary": "Test summary",
                "categories": ["工具"],
                "features": [],
                "use_cases": []
            }

    # Mock GitHubGraphQLClient - return GitHubRepository objects with all required fields
    # Note: Use aliases (original field names) for Pydantic model with alias priority
    mock_repo = GitHubRepository(
        id=1,
        name_with_owner="test/repo",  # alias for name_with_owner
        name="repo",
        owner="test",
        description="Test repo",
        language="Python",  # alias for primary_language
        stargazer_count=100,  # alias for stargazer_count
        fork_count=10,  # alias for fork_count
        url="https://github.com/test/repo",  # alias for url
        homepage=None,  # alias for homepage_url
        created_at=datetime.now(),
        updated_at=datetime.now(),
        pushed_at=datetime.now(),
        archived=False,
        visibility="public",
        owner_type="User"
    )

    class MockGraphQLClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass

        async def get_starred_repositories(self, *args, **kwargs):
            return [mock_repo]

        async def get_readme_content(self, *args, **kwargs):
            return "Test README"

    mocker.patch("src.services.init.GitHubGraphQLClient", return_value=MockGraphQLClient())

    service = InitializationService(db, llm=MockLLM())
    result = await service.initialize_from_stars(skip_llm=True)

    assert result["fetched"] == 1
    assert result["added"] == 1
