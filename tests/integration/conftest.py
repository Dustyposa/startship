"""
Integration tests for the sync system.

These tests use real GitHub API calls and require GITHUB_TOKEN to be set.
"""
import pytest
import pytest_asyncio
import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator


# ============================================================================
# Configuration
# ============================================================================

def get_github_token() -> str:
    """Get GitHub token from environment."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        pytest.skip("GITHUB_TOKEN environment variable not set - skipping integration tests")
    return token


def get_github_username() -> str:
    """Get GitHub username from environment or use default."""
    return os.getenv("GITHUB_USERNAME", "testuser")


# ============================================================================
# Fixtures
# ============================================================================

@pytest_asyncio.fixture(scope="function")
async def integration_db() -> AsyncGenerator:
    """
    Create a fresh database for each integration test.

    Uses in-memory database for test isolation.
    """
    from src.db import create_database

    # Create in-memory database for test isolation
    db = create_database("sqlite", db_path=":memory:")

    # Initialize database schema
    await db.initialize()

    yield db

    # Cleanup
    await db.close()


@pytest.fixture(scope="session")
def github_token() -> str:
    """Get GitHub token for integration tests."""
    return get_github_token()


@pytest.fixture(scope="session")
def github_username() -> str:
    """Get GitHub username for integration tests."""
    return get_github_username()


@pytest_asyncio.fixture(scope="function")
async def sync_service(integration_db, github_token):
    """
    Create SyncService instance with real GitHub token.

    Note: This fixture enables real GitHub API calls.
    """
    from src.services.sync import SyncService
    from unittest.mock import patch

    # Mock the settings to use real token
    with patch('src.services.sync.get_github_token', return_value=github_token):
        service = SyncService(integration_db)
        yield service


@pytest.fixture(scope="function")
def mock_github_client():
    """
    Create a mock GitHub client for controlled testing.

    This allows testing without real API calls while still
    exercising the full sync flow.
    """
    from unittest.mock import Mock, AsyncMock, patch, MagicMock
    from src.github.models import GitHubRepository
    from datetime import datetime
    from src.github.client import GitHubClient

    # Create mock repositories
    mock_repos = [
        GitHubRepository(
            id=1,
            full_name="user/test-repo-1",
            name="test-repo-1",
            owner={"login": "user", "type": "User"},
            description="Test repository 1",
            language="Python",
            topics=["test", "python"],
            stargazers_count=100,
            forks_count=20,
            open_issues_count=5,
            html_url="https://github.com/user/test-repo-1",
            homepage=None,
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            pushed_at=datetime(2024, 1, 1),
            starred_at=datetime(2024, 1, 1),
            archived=False,
            visibility="public",
            owner_type="User",
            organization=None,
        ),
        GitHubRepository(
            id=2,
            full_name="user/test-repo-2",
            name="test-repo-2",
            owner={"login": "user", "type": "User"},
            description="Test repository 2",
            language="JavaScript",
            topics=["test", "javascript"],
            stargazers_count=50,
            forks_count=10,
            open_issues_count=3,
            html_url="https://github.com/user/test-repo-2",
            homepage=None,
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            pushed_at=datetime(2024, 1, 1),
            starred_at=datetime(2024, 1, 1),
            archived=False,
            visibility="public",
            owner_type="User",
            organization=None,
        ),
    ]

    # Create a mock class that returns instances with proper async context manager support
    class MockGitHubClient:
        def __init__(self, *args, **kwargs):
            self.repos = mock_repos

        async def get_all_starred(self, *args, **kwargs):
            """Mock get_all_starred method."""
            return self.repos

        async def get_starred_repositories(self, *args, **kwargs):
            """Mock get_starred_repositories method."""
            return self.repos

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args, **kwargs):
            pass

    with patch('src.services.sync.GitHubClient', MockGitHubClient):
        # Return the mock class so tests can use it in patches
        yield MockGitHubClient


@pytest_asyncio.fixture(scope="function")
async def integration_client(integration_db) -> AsyncGenerator:
    """
    Create async HTTP client for integration tests.

    Uses the test database and allows testing FastAPI endpoints.
    """
    from httpx import AsyncClient, ASGITransport
    from src.api.app import app
    import src.api.routes.sync as sync_routes
    import src.api.routes.user_data as user_data_routes
    import src.api.routes.search as search_routes

    # Override the get_db dependency to use test database
    for routes_module in [sync_routes, user_data_routes, search_routes]:
        if hasattr(routes_module, 'get_db'):
            app.dependency_overrides[routes_module.get_db] = lambda: integration_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Test Helpers
# ============================================================================

async def add_test_repos(db, count: int = 3) -> list:
    """
    Add test repositories to database.

    Returns list of repo names that were added.
    """
    from datetime import datetime

    repo_names = []
    for i in range(count):
        name = f"owner/test-repo-{i}"
        repo_names.append(name)

        await db.add_repository({
            "name_with_owner": name,
            "name": f"test-repo-{i}",
            "owner": "owner",
            "description": f"Test repo {i}",
            "primary_language": "Python",
            "topics": ["test"],
            "stargazer_count": 100 + i,
            "fork_count": 20,
            "url": f"https://github.com/owner/test-repo-{i}",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": f"Test repo {i}",
            "categories": [],
            "features": [],
            "tech_stack": ["Python"],
            "use_cases": []
        })

    return repo_names


async def count_active_repos(db) -> int:
    """Count active (non-deleted) repositories in database."""
    cursor = await db._connection.execute(
        "SELECT COUNT(*) FROM repositories WHERE is_deleted = 0"
    )
    return (await cursor.fetchone())[0]


async def get_sync_history_count(db) -> int:
    """Get count of sync history records."""
    cursor = await db._connection.execute(
        "SELECT COUNT(*) FROM sync_history"
    )
    return (await cursor.fetchone())[0]
