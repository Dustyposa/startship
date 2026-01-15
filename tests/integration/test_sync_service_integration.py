"""
Integration tests for SyncService.

Tests the complete sync flow with mocked GitHub client.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock


# Helper function to create GitHubRepository
def create_test_repo(id, name, owner="user", stars=100, forks=20, language="Python", description="Test repo"):
    """Create a test GitHubRepository with correct field names."""
    from src.github.models import GitHubRepository
    return GitHubRepository(
        id=id,
        full_name=f"{owner}/{name}",
        name=name,
        owner={"login": owner, "type": "User"},
        description=description,
        language=language,
        topics=["test"],
        stargazers_count=stars,
        forks_count=forks,
        open_issues_count=5,
        html_url=f"https://github.com/{owner}/{name}",
        homepage=None,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
        pushed_at=datetime(2024, 1, 1),
        starred_at=datetime(2024, 1, 1),
        archived=False,
        visibility="public",
        owner_type="User",
        organization=None,
    )


# Helper to create a mocked GitHubClient class
def create_mock_github_client_class(repos):
    """Create a mock GitHubClient class that returns the given repos."""
    from src.github.client import GitHubClient

    class MockGitHubClient:
        def __init__(self, *args, **kwargs):
            self.repos = repos

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

    return MockGitHubClient


# ============================================================================
# Full Sync Integration Tests
# ============================================================================

class TestFullSyncIntegration:
    """Integration tests for full sync flow."""

    @pytest.mark.asyncio
    async def test_full_sync_adds_new_repositories(self, integration_db):
        """Test that full sync adds new repositories from GitHub."""
        from src.services.sync import SyncService

        # Create mock repos
        mock_repos = [
            create_test_repo(1, "test-repo-1", language="Python"),
            create_test_repo(2, "test-repo-2", language="JavaScript"),
        ]

        service = SyncService(integration_db)

        # Perform full sync with mocked client
        MockClient = create_mock_github_client_class(mock_repos)
        with patch('src.services.sync.GitHubClient', MockClient):
            stats = await service.full_sync(skip_llm=True)

        # Verify statistics
        assert stats['added'] == 2  # Two repos from mock
        assert stats['updated'] == 0
        assert stats['deleted'] == 0
        assert stats['failed'] == 0

        # Verify repositories were added to database
        repo1 = await integration_db.get_repository("user/test-repo-1")
        assert repo1 is not None
        assert repo1['name'] == "test-repo-1"
        assert repo1['stargazer_count'] == 100

        repo2 = await integration_db.get_repository("user/test-repo-2")
        assert repo2 is not None
        assert repo2['name'] == "test-repo-2"
        assert repo2['primary_language'] == "JavaScript"

    @pytest.mark.asyncio
    async def test_full_sync_updates_existing_repositories(self, integration_db):
        """Test that full sync updates existing repositories."""
        from src.services.sync import SyncService

        service = SyncService(integration_db)

        # Add an existing repository with different data
        await integration_db.add_repository({
            "name_with_owner": "user/test-repo-1",
            "name": "test-repo-1",
            "owner": "user",
            "description": "Old description",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 50,  # Different from mock (100)
            "fork_count": 10,  # Different from mock (20)
            "url": "https://github.com/user/test-repo-1",
            "homepage_url": None,
            "pushed_at": "2023-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2023-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Old summary",
            "categories": [],
            "features": [],
            "tech_stack": [],
            "use_cases": []
        })

        # Create mock repos
        mock_repos = [
            create_test_repo(1, "test-repo-1", stars=100, forks=20, language="Python"),
            create_test_repo(2, "test-repo-2", language="JavaScript"),
        ]

        # Perform full sync
        MockClient = create_mock_github_client_class(mock_repos)
        with patch('src.services.sync.GitHubClient', MockClient):
            stats = await service.full_sync(skip_llm=True)

        # Verify statistics
        assert stats['added'] == 1  # Only test-repo-2 is new
        assert stats['updated'] == 1  # test-repo-1 was updated
        assert stats['deleted'] == 0

        # Verify repository was updated
        repo1 = await integration_db.get_repository("user/test-repo-1")
        assert repo1['stargazer_count'] == 100  # Updated from mock
        assert repo1['fork_count'] == 20  # Updated from mock

    @pytest.mark.asyncio
    async def test_full_sync_soft_deletes_removed_repos(self, integration_db):
        """Test that full sync soft deletes repositories no longer starred."""
        from src.services.sync import SyncService

        service = SyncService(integration_db)

        # Add existing repositories
        await integration_db.add_repository({
            "name_with_owner": "user/old-repo",
            "name": "old-repo",
            "owner": "user",
            "description": "Old repository",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 10,
            "fork_count": 5,
            "url": "https://github.com/user/old-repo",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Old repo",
            "categories": [],
            "features": [],
            "tech_stack": [],
            "use_cases": []
        })

        # Mock GitHub client to return different repos (old-repo not included)
        mock_repos = [
            create_test_repo(1, "new-repo", description="New repository"),
        ]
        MockClient = create_mock_github_client_class(mock_repos)

        # Perform full sync
        with patch('src.services.sync.GitHubClient', MockClient):
            stats = await service.full_sync(skip_llm=True)

        # Verify statistics
        assert stats['added'] == 1  # new-repo added
        assert stats['deleted'] == 1  # old-repo soft deleted

        # Verify old repo was soft deleted
        old_repo = await integration_db.get_repository("user/old-repo")
        assert old_repo is not None
        assert old_repo['is_deleted'] == 1

    @pytest.mark.asyncio
    async def test_full_sync_records_history(self, integration_db):
        """Test that full sync records sync history."""
        from src.services.sync import SyncService

        service = SyncService(integration_db)

        # Create mock repos
        mock_repos = [
            create_test_repo(1, "test-repo-1", language="Python"),
            create_test_repo(2, "test-repo-2", language="JavaScript"),
        ]
        MockClient = create_mock_github_client_class(mock_repos)

        # Perform full sync
        with patch('src.services.sync.GitHubClient', MockClient):
            stats = await service.full_sync(skip_llm=True)

        # Verify sync history was recorded
        rows = []
        async with integration_db._connection.execute(
            "SELECT * FROM sync_history ORDER BY started_at DESC LIMIT 1"
        ) as cursor:
            async for row in cursor:
                rows.append(row)

        assert len(rows) == 1
        record = rows[0]
        assert record[1] == 'full'  # sync_type is at index 1
        # Find the correct indices
        assert record[4] == 2  # stats_added is at index 4
        assert record[5] == 0  # stats_updated is at index 5
        assert record[6] == 0  # stats_deleted is at index 6
        assert record[7] == 0  # stats_failed is at index 7


# ============================================================================
# Incremental Sync Integration Tests
# ============================================================================

class TestIncrementalSyncIntegration:
    """Integration tests for incremental sync flow."""

    @pytest.mark.asyncio
    async def test_incremental_sync_with_last_sync(self, integration_db):
        """Test incremental sync uses last_synced_at timestamp."""
        from src.services.sync import SyncService

        service = SyncService(integration_db)

        # Mock GitHub client
        mock_repos = [
            create_test_repo(1, "updated-repo", stars=150, forks=30, description="Updated repository"),
        ]
        MockClient = create_mock_github_client_class(mock_repos)

        # Perform incremental sync
        with patch('src.services.sync.GitHubClient', MockClient):
            stats = await service.incremental_sync(skip_llm=True)

        # Verify incremental sync was performed
        assert stats['added'] == 1

    @pytest.mark.asyncio
    async def test_incremental_sync_first_sync(self, integration_db):
        """Test incremental sync when there's no previous sync."""
        from src.services.sync import SyncService

        service = SyncService(integration_db)

        # First incremental sync (no last_synced_at in DB)
        mock_repos = [
            create_test_repo(1, "test-repo-1", language="Python"),
            create_test_repo(2, "test-repo-2", language="JavaScript"),
        ]
        MockClient = create_mock_github_client_class(mock_repos)

        with patch('src.services.sync.GitHubClient', MockClient):
            stats = await service.incremental_sync(skip_llm=True)

        # Should behave like full sync for first time
        assert stats['added'] == 2

        # Verify repositories were added
        repo1 = await integration_db.get_repository("user/test-repo-1")
        assert repo1 is not None


# ============================================================================
# Change Detection Integration Tests
# ============================================================================

class TestChangeDetectionIntegration:
    """Integration tests for change detection."""

    @pytest.mark.asyncio
    async def test_detects_stargazer_count_change(self, integration_db):
        """Test that changes in stargazer count are detected."""
        from src.services.sync import SyncService

        service = SyncService(integration_db)

        # Add repo with old star count
        await integration_db.add_repository({
            "name_with_owner": "user/popular-repo",
            "name": "popular-repo",
            "owner": "user",
            "description": "Popular repo",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 100,
            "fork_count": 20,
            "url": "https://github.com/user/popular-repo",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Popular repo",
            "categories": [],
            "features": [],
            "tech_stack": [],
            "use_cases": []
        })

        # Mock GitHub client with updated star count
        mock_repos = [
            create_test_repo(1, "popular-repo", stars=150, description="Popular repo"),
        ]
        MockClient = create_mock_github_client_class(mock_repos)

        # Sync should detect the change and update
        with patch('src.services.sync.GitHubClient', MockClient):
            stats = await service.full_sync(skip_llm=True)

        assert stats['updated'] >= 1  # At least the popular-repo was updated

        # Verify the star count was updated
        repo = await integration_db.get_repository("user/popular-repo")
        assert repo['stargazer_count'] == 150

    @pytest.mark.asyncio
    async def test_detects_description_change(self, integration_db):
        """Test that changes in description are detected."""
        from src.services.sync import SyncService

        service = SyncService(integration_db)

        # Add repo with old description
        await integration_db.add_repository({
            "name_with_owner": "user/changed-repo",
            "name": "changed-repo",
            "owner": "user",
            "description": "Old description",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 50,
            "fork_count": 10,
            "url": "https://github.com/user/changed-repo",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Changed repo",
            "categories": [],
            "features": [],
            "tech_stack": [],
            "use_cases": []
        })

        # Mock GitHub client with new description
        mock_repos = [
            create_test_repo(1, "changed-repo", stars=50, description="New and improved description"),
        ]
        MockClient = create_mock_github_client_class(mock_repos)

        # Sync should detect the change
        with patch('src.services.sync.GitHubClient', MockClient):
            stats = await service.full_sync(skip_llm=True)

        assert stats['updated'] >= 1

        # Verify description was updated
        repo = await integration_db.get_repository("user/changed-repo")
        assert repo['description'] == "New and improved description"


# ============================================================================
# Soft Delete and Restore Integration Tests
# ============================================================================

class TestSoftDeleteRestoreIntegration:
    """Integration tests for soft delete and restore functionality."""

    @pytest.mark.asyncio
    async def test_soft_delete_and_restore_flow(self, integration_db):
        """Test complete soft delete and restore flow."""
        from src.services.sync import SyncService

        service = SyncService(integration_db)

        # Add a repository
        await integration_db.add_repository({
            "name_with_owner": "user/temp-repo",
            "name": "temp-repo",
            "owner": "user",
            "description": "Temporary repo",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 10,
            "fork_count": 5,
            "url": "https://github.com/user/temp-repo",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Temp repo",
            "categories": [],
            "features": [],
            "tech_stack": [],
            "use_cases": []
        })

        # Verify repo is active
        repo = await integration_db.get_repository("user/temp-repo")
        assert repo['is_deleted'] == 0

        # Soft delete the repo
        await service.soft_delete_repo("user/temp-repo")

        # Verify repo is soft deleted
        repo = await integration_db.get_repository("user/temp-repo")
        assert repo['is_deleted'] == 1

        # Restore the repo
        await service.restore_repo("user/temp-repo")

        # Verify repo is restored
        repo = await integration_db.get_repository("user/temp-repo")
        assert repo['is_deleted'] == 0

    @pytest.mark.asyncio
    async def test_soft_deleted_repos_excluded_from_sync(self, integration_db):
        """Test that soft deleted repos are handled correctly in sync."""
        from src.services.sync import SyncService

        service = SyncService(integration_db)

        # Add a soft deleted repo
        await integration_db.add_repository({
            "name_with_owner": "user/deleted-repo",
            "name": "deleted-repo",
            "owner": "user",
            "description": "Deleted repo",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 10,
            "fork_count": 5,
            "url": "https://github.com/user/deleted-repo",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Deleted repo",
            "categories": [],
            "features": [],
            "tech_stack": [],
            "use_cases": []
        })
        await integration_db.update_repository("user/deleted-repo", {"is_deleted": 1})

        # Mock GitHub client that doesn't include the deleted repo
        mock_repos = [
            create_test_repo(1, "active-repo", description="Active repo"),
        ]
        MockClient = create_mock_github_client_class(mock_repos)

        # Sync should add the new repo but not re-delete the already deleted one
        with patch('src.services.sync.GitHubClient', MockClient):
            stats = await service.full_sync(skip_llm=True)

        assert stats['added'] == 1  # Only active-repo

        # Verify the deleted repo is still soft deleted
        deleted_repo = await integration_db.get_repository("user/deleted-repo")
        assert deleted_repo['is_deleted'] == 1
