"""
Test that InitializationService saves starred_at timestamp.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.init import InitializationService
from src.github.models import GitHubRepository


@pytest.mark.asyncio
async def test_initialization_saves_starred_at():
    """Test that starred_at timestamp is extracted and saved to database."""
    db = MagicMock()
    db.add_repository = AsyncMock()
    db.get_repository = AsyncMock(return_value=None)
    # Mock database connection for network building
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []  # No repos for network
    db._connection.execute = AsyncMock(return_value=mock_cursor)

    # Mock NetworkService to avoid network building issues
    with patch('src.services.network.NetworkService') as mock_network_class:
        mock_network = AsyncMock()
        mock_network.build_network.return_value = {"nodes": [], "edges": []}
        mock_network_class.return_value = mock_network

        service = InitializationService(db, None, None)

        # Mock GitHub GraphQL response with starred_at - return GitHubRepository objects
        # Note: Use aliases (original field names) for Pydantic model with alias priority
        from datetime import datetime
        mock_repo = GitHubRepository(
            id=1,
            full_name="owner/repo",  # alias for name_with_owner
            name="repo",
            owner="owner",
            description="Test",
            language="Python",  # alias for primary_language
            stargazers_count=100,  # alias for stargazer_count
            forks_count=10,  # alias for fork_count
            html_url="https://github.com/owner/repo",  # alias for url
            homepage=None,  # alias for homepage_url
            created_at=datetime.now(),
            updated_at=datetime.now(),
            pushed_at=datetime.now(),
            archived=False,
            visibility="public",
            owner_type="User"
        )
        # Set starred_at as an attribute (simulating GraphQL extension)
        mock_repo.starred_at = "2024-01-01T00:00:00Z"

        # Mock GitHubGraphQLClient context manager
        mock_github = AsyncMock()
        mock_github.get_starred_repositories = AsyncMock(return_value=[mock_repo])
        mock_github.get_readme_content = AsyncMock(return_value="# Test README")

        with patch('src.services.init.GitHubGraphQLClient') as mock_github_class:
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
    # Mock database connection for network building
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []  # No repos for network
    db._connection.execute = AsyncMock(return_value=mock_cursor)

    # Mock NetworkService to avoid network building issues
    with patch('src.services.network.NetworkService') as mock_network_class:
        mock_network = AsyncMock()
        mock_network.build_network.return_value = {"nodes": [], "edges": []}
        mock_network_class.return_value = mock_network

        service = InitializationService(db, None, None)

        # Mock GitHub GraphQL response without starred_at
        from datetime import datetime
        mock_repo = GitHubRepository(
            id=1,
            full_name="owner/repo",
            name="repo",
            owner="owner",
            description="Test",
            language="Python",
            stargazers_count=100,
            forks_count=10,
            html_url="https://github.com/owner/repo",
            homepage=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            pushed_at=datetime.now(),
            archived=False,
            visibility="public",
            owner_type="User"
        )
        # Don't set starred_at - simulate missing attribute

        # Mock GitHubGraphQLClient context manager
        mock_github = AsyncMock()
        mock_github.get_starred_repositories = AsyncMock(return_value=[mock_repo])
        mock_github.get_readme_content = AsyncMock(return_value="# Test README")

        with patch('src.services.init.GitHubGraphQLClient') as mock_github_class:
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
    # Mock database connection for network building
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []  # No repos for network
    db._connection.execute = AsyncMock(return_value=mock_cursor)

    # Mock NetworkService to avoid network building issues
    with patch('src.services.network.NetworkService') as mock_network_class:
        mock_network = AsyncMock()
        mock_network.build_network.return_value = {"nodes": [], "edges": []}
        mock_network_class.return_value = mock_network

        service = InitializationService(db, None, None)

        # Mock GitHub GraphQL response with starred_at set to None
        from datetime import datetime
        mock_repo = GitHubRepository(
            id=1,
            full_name="owner/repo",
            name="repo",
            owner="owner",
            description="Test",
            language="Python",
            stargazers_count=100,
            forks_count=10,
            html_url="https://github.com/owner/repo",
            homepage=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            pushed_at=datetime.now(),
            archived=False,
            visibility="public",
            owner_type="User"
        )
        mock_repo.starred_at = None

        # Mock GitHubGraphQLClient context manager
        mock_github = AsyncMock()
        mock_github.get_starred_repositories = AsyncMock(return_value=[mock_repo])
        mock_github.get_readme_content = AsyncMock(return_value="# Test README")

        with patch('src.services.init.GitHubGraphQLClient') as mock_github_class:
            mock_github_class.return_value.__aenter__.return_value = mock_github
            mock_github_class.return_value.__aexit__.return_value = None

            # Process repo
            await service.initialize_from_stars(username="test", skip_llm=True)

        # Verify starred_at is None
        call_args = db.add_repository.call_args
        assert call_args is not None
        repo_data = call_args[0][0]
        assert repo_data["starred_at"] is None

