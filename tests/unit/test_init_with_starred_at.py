"""
Test that InitializationService saves starred_at timestamp.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.init import InitializationService


@pytest.mark.asyncio
async def test_initialization_saves_starred_at():
    """Test that starred_at timestamp is extracted and saved to database."""
    db = MagicMock()
    db.add_repository = AsyncMock()
    db.get_repository = AsyncMock(return_value=None)

    service = InitializationService(db, None, None)

    # Mock GitHub response with starred_at
    mock_repo = MagicMock()
    mock_repo.name_with_owner = "owner/repo"
    mock_repo.starred_at = "2024-01-01T00:00:00Z"

    # Mock other required attributes
    mock_repo.name = "repo"
    mock_repo.owner_login = "owner"
    mock_repo.description = "Test"
    mock_repo.primary_language = "Python"
    mock_repo.topics = []
    mock_repo.stargazer_count = 100
    mock_repo.fork_count = 10
    mock_repo.url = "https://github.com/owner/repo"
    mock_repo.homepage_url = None

    # Mock GitHubClient context manager
    mock_github = AsyncMock()
    mock_github.get_all_starred = AsyncMock(return_value=[mock_repo])
    mock_github.get_readme_content = AsyncMock(return_value="# Test README")

    with patch('src.services.init.GitHubClient') as mock_github_class:
        mock_github_class.return_value.__aenter__.return_value = mock_github
        mock_github_class.return_value.__aexit__.return_value = None

        # Process repo (call the internal processing logic)
        await service.initialize_from_stars(username="test", skip_llm=True)

    # Verify starred_at was saved
    call_args = db.add_repository.call_args
    assert call_args is not None
    repo_data = call_args[0][0]
    assert repo_data["starred_at"] == "2024-01-01T00:00:00Z"


@pytest.mark.asyncio
async def test_initialization_handles_missing_starred_at():
    """Test that missing starred_at is handled gracefully (defaults to None)."""
    db = MagicMock()
    db.add_repository = AsyncMock()
    db.get_repository = AsyncMock(return_value=None)

    service = InitializationService(db, None, None)

    # Mock GitHub response without starred_at
    mock_repo = MagicMock()
    mock_repo.name_with_owner = "owner/repo"
    # Don't set starred_at - simulate missing attribute
    del mock_repo.starred_at

    # Mock other required attributes
    mock_repo.name = "repo"
    mock_repo.owner_login = "owner"
    mock_repo.description = "Test"
    mock_repo.primary_language = "Python"
    mock_repo.topics = []
    mock_repo.stargazer_count = 100
    mock_repo.fork_count = 10
    mock_repo.url = "https://github.com/owner/repo"
    mock_repo.homepage_url = None

    # Mock GitHubClient context manager
    mock_github = AsyncMock()
    mock_github.get_all_starred = AsyncMock(return_value=[mock_repo])
    mock_github.get_readme_content = AsyncMock(return_value="# Test README")

    with patch('src.services.init.GitHubClient') as mock_github_class:
        mock_github_class.return_value.__aenter__.return_value = mock_github
        mock_github_class.return_value.__aexit__.return_value = None

        # Process repo
        await service.initialize_from_stars(username="test", skip_llm=True)

    # Verify starred_at defaults to None when missing
    call_args = db.add_repository.call_args
    assert call_args is not None
    repo_data = call_args[0][0]
    assert repo_data["starred_at"] is None


@pytest.mark.asyncio
async def test_initialization_with_none_starred_at():
    """Test that None starred_at value is preserved."""
    db = MagicMock()
    db.add_repository = AsyncMock()
    db.get_repository = AsyncMock(return_value=None)

    service = InitializationService(db, None, None)

    # Mock GitHub response with starred_at set to None
    mock_repo = MagicMock()
    mock_repo.name_with_owner = "owner/repo"
    mock_repo.starred_at = None

    # Mock other required attributes
    mock_repo.name = "repo"
    mock_repo.owner_login = "owner"
    mock_repo.description = "Test"
    mock_repo.primary_language = "Python"
    mock_repo.topics = []
    mock_repo.stargazer_count = 100
    mock_repo.fork_count = 10
    mock_repo.url = "https://github.com/owner/repo"
    mock_repo.homepage_url = None

    # Mock GitHubClient context manager
    mock_github = AsyncMock()
    mock_github.get_all_starred = AsyncMock(return_value=[mock_repo])
    mock_github.get_readme_content = AsyncMock(return_value="# Test README")

    with patch('src.services.init.GitHubClient') as mock_github_class:
        mock_github_class.return_value.__aenter__.return_value = mock_github
        mock_github_class.return_value.__aexit__.return_value = None

        # Process repo
        await service.initialize_from_stars(username="test", skip_llm=True)

    # Verify starred_at is None
    call_args = db.add_repository.call_args
    assert call_args is not None
    repo_data = call_args[0][0]
    assert repo_data["starred_at"] is None
