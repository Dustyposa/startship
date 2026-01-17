"""
Unit tests for SyncService.

Tests the core synchronization logic including:
- Change detection (_needs_update)
- Soft delete and restore operations
- Full and incremental sync
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.services.sync import SyncService
from src.github.models import GitHubRepository


@pytest.fixture
def sync_service(db):
    """Create a SyncService instance for testing."""
    return SyncService(db)


@pytest.fixture
def sample_github_repo():
    """Create a sample GitHub repository."""
    return GitHubRepository(
        id=123,
        full_name="owner/test-repo",
        name="test-repo",
        owner="owner",
        description="A test repository",
        language="Python",
        topics=["test", "python"],
        stargazers_count=100,
        forks_count=20,
        open_issues_count=5,
        html_url="https://github.com/owner/test-repo",
        homepage=None,
        created_at=datetime(2023, 1, 1),
        updated_at=datetime(2023, 12, 1),
        pushed_at=datetime(2023, 12, 1),
        starred_at=datetime(2023, 6, 1),
        archived=False,
        visibility="public",
        owner_type="User"
    )


@pytest.fixture
def sample_local_repo():
    """Create a sample local repository dict."""
    return {
        "name_with_owner": "owner/test-repo",
        "name": "test-repo",
        "owner": "owner",
        "description": "A test repository",
        "primary_language": "Python",
        "topics": ["test", "python"],
        "stargazer_count": 100,
        "fork_count": 20,
        "url": "https://github.com/owner/test-repo",
        "homepage_url": None,
        "pushed_at": "2023-12-01T00:00:00",
        
        "archived": 0,
        "visibility": "public",
        "owner_type": "User",
        "organization": None,
        "is_deleted": 0
    }


# ============================================================================
# _needs_update() tests
# ============================================================================

class TestNeedsUpdate:
    """Tests for _needs_update method."""

    def test_no_changes_needed(self, sync_service, sample_local_repo, sample_github_repo):
        """Test that identical repos don't need update."""
        result = sync_service._needs_update(sample_local_repo, sample_github_repo)
        assert result is False

    def test_pushed_at_change_triggers_update(self, sync_service, sample_local_repo):
        """Test that pushed_at changes trigger update."""
        github_repo = GitHubRepository(
            id=123,
            full_name="owner/test-repo",
            name="test-repo",
            owner="owner",
            description="A test repository",
            language="Python",
            topics=[],
            stargazers_count=100,
            forks_count=20,
            html_url="https://github.com/owner/test-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 2),  # Different pushed_at
            archived=False,
            visibility="public",
            owner_type="User"
        )
        result = sync_service._needs_update(sample_local_repo, github_repo)
        assert result is True

    def test_stargazer_count_change_triggers_update(self, sync_service, sample_local_repo):
        """Test that stargazer_count changes trigger update."""
        github_repo = GitHubRepository(
            id=123,
            full_name="owner/test-repo",
            name="test-repo",
            owner="owner",
            description="A test repository",
            language="Python",
            topics=[],
            stargazers_count=101,  # Different count
            forks_count=20,
            html_url="https://github.com/owner/test-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 1),
            archived=False,
            visibility="public",
            owner_type="User"
        )
        result = sync_service._needs_update(sample_local_repo, github_repo)
        assert result is True

    def test_fork_count_change_triggers_update(self, sync_service, sample_local_repo):
        """Test that fork_count changes trigger update."""
        github_repo = GitHubRepository(
            id=123,
            full_name="owner/test-repo",
            name="test-repo",
            owner="owner",
            description="A test repository",
            language="Python",
            topics=[],
            stargazers_count=100,
            forks_count=21,  # Different count
            html_url="https://github.com/owner/test-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 1),
            archived=False,
            visibility="public",
            owner_type="User"
        )
        result = sync_service._needs_update(sample_local_repo, github_repo)
        assert result is True

    def test_language_change_triggers_update(self, sync_service, sample_local_repo):
        """Test that primary_language changes trigger update."""
        github_repo = GitHubRepository(
            id=123,
            full_name="owner/test-repo",
            name="test-repo",
            owner="owner",
            description="A test repository",
            language="TypeScript",  # Different language
            topics=[],
            stargazers_count=100,
            forks_count=20,
            html_url="https://github.com/owner/test-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 1),
            archived=False,
            visibility="public",
            owner_type="User"
        )
        result = sync_service._needs_update(sample_local_repo, github_repo)
        assert result is True

    def test_description_change_triggers_update(self, sync_service, sample_local_repo):
        """Test that description changes trigger update."""
        github_repo = GitHubRepository(
            id=123,
            full_name="owner/test-repo",
            name="test-repo",
            owner="owner",
            description="Updated description",  # Different description
            language="Python",
            topics=[],
            stargazers_count=100,
            forks_count=20,
            html_url="https://github.com/owner/test-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 1),
            archived=False,
            visibility="public",
            owner_type="User"
        )
        result = sync_service._needs_update(sample_local_repo, github_repo)
        assert result is True

    def test_archived_change_triggers_update(self, sync_service, sample_local_repo):
        """Test that archived status changes trigger update."""
        github_repo = GitHubRepository(
            id=123,
            full_name="owner/test-repo",
            name="test-repo",
            owner="owner",
            description="A test repository",
            language="Python",
            topics=[],
            stargazers_count=100,
            forks_count=20,
            html_url="https://github.com/owner/test-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 1),
            archived=True,  # Now archived
            visibility="public",
            owner_type="User"
        )
        result = sync_service._needs_update(sample_local_repo, github_repo)
        assert result is True

    def test_visibility_change_triggers_update(self, sync_service, sample_local_repo):
        """Test that visibility changes trigger update."""
        github_repo = GitHubRepository(
            id=123,
            full_name="owner/test-repo",
            name="test-repo",
            owner="owner",
            description="A test repository",
            language="Python",
            topics=[],
            stargazers_count=100,
            forks_count=20,
            html_url="https://github.com/owner/test-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 1),
            archived=False,
            visibility="private",  # Different visibility
            owner_type="User"
        )
        result = sync_service._needs_update(sample_local_repo, github_repo)
        assert result is True

    def test_owner_type_change_triggers_update(self, sync_service, sample_local_repo):
        """Test that owner_type changes trigger update."""
        github_repo = GitHubRepository(
            id=123,
            full_name="owner/test-repo",
            name="test-repo",
            owner="owner",
            description="A test repository",
            language="Python",
            topics=[],
            stargazers_count=100,
            forks_count=20,
            html_url="https://github.com/owner/test-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 1),
            archived=False,
            visibility="public",
            owner_type="Organization"  # Different owner type
        )
        result = sync_service._needs_update(sample_local_repo, github_repo)
        assert result is True

    def test_handles_null_pushed_at_in_github_repo(self, sync_service, sample_local_repo):
        """Test handling of null pushed_at in GitHub repo."""
        github_repo = GitHubRepository(
            id=123,
            full_name="owner/test-repo",
            name="test-repo",
            owner="owner",
            description="A test repository",
            language="Python",
            topics=[],
            stargazers_count=100,
            forks_count=20,
            html_url="https://github.com/owner/test-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=None,  # Null pushed_at
            archived=False,
            visibility="public",
            owner_type="User"
        )
        result = sync_service._needs_update(sample_local_repo, github_repo)
        assert result is True  # Should trigger update due to null

    def test_handles_null_pushed_at_in_local_repo(self, sync_service, sample_github_repo):
        """Test handling of null pushed_at in local repo."""
        local_repo = {
            **sample_github_repo.model_dump(),
            "pushed_at": None
        }
        result = sync_service._needs_update(local_repo, sample_github_repo)
        assert result is True  # Should trigger update due to null

    def test_handles_null_language(self, sync_service):
        """Test handling of null primary_language."""
        local_repo = {
            "name_with_owner": "owner/test-repo",
            "primary_language": None,
            "stargazer_count": 100,
            "fork_count": 20,
            "pushed_at": "2023-12-01T00:00:00",
            "description": "A test repository",
            "archived": 0,
            "visibility": "public",
            "owner_type": "User"
        }
        github_repo = GitHubRepository(
            id=123,
            full_name="owner/test-repo",
            name="test-repo",
            owner="owner",
            description="A test repository",
            language=None,
            topics=[],
            stargazers_count=100,
            forks_count=20,
            html_url="https://github.com/owner/test-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 1),
            archived=False,
            visibility="public",
            owner_type="User"
        )
        result = sync_service._needs_update(local_repo, github_repo)
        assert result is False  # No change when both are null


# ============================================================================
# soft_delete_repo() tests
# ============================================================================

class TestSoftDeleteRepo:
    """Tests for soft_delete_repo method."""

    @pytest.mark.asyncio
    async def test_soft_delete_repo_success(self, sync_service, db):
        """Test successful soft delete of a repository."""
        # First add a repo
        await db.add_repository({
            "name_with_owner": "owner/test-repo",
            "name": "test-repo",
            "owner": "owner",
            "description": "Test",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 100,
            "fork_count": 20,
            "url": "https://github.com/owner/test-repo",
            "homepage_url": None,
            "pushed_at": "2023-12-01T00:00:00",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2023-06-01T00:00:00",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Test",
            "categories": [],
            "features": [],
            "use_cases": []
        })

        # Soft delete it
        await sync_service.soft_delete_repo("owner/test-repo")

        # Verify it's soft deleted
        result = await db.get_repository("owner/test-repo")
        assert result is not None
        assert result["is_deleted"] == 1

    @pytest.mark.asyncio
    async def test_soft_delete_nonexistent_repo(self, sync_service):
        """Test soft deleting a non-existent repository."""
        # Should not raise an error
        await sync_service.soft_delete_repo("owner/nonexistent-repo")


# ============================================================================
# restore_repo() tests
# ============================================================================

class TestRestoreRepo:
    """Tests for restore_repo method."""

    @pytest.mark.asyncio
    async def test_restore_repo_success(self, sync_service, db):
        """Test successful restore of a soft-deleted repository."""
        # Add a repo
        await db.add_repository({
            "name_with_owner": "owner/test-repo",
            "name": "test-repo",
            "owner": "owner",
            "description": "Test",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 100,
            "fork_count": 20,
            "url": "https://github.com/owner/test-repo",
            "homepage_url": None,
            "pushed_at": "2023-12-01T00:00:00",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2023-06-01T00:00:00",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Test",
            "categories": [],
            "features": [],
            "use_cases": []
        })
        # Soft delete it first
        await sync_service.soft_delete_repo("owner/test-repo")

        # Restore it
        await sync_service.restore_repo("owner/test-repo")

        # Verify it's restored
        result = await db.get_repository("owner/test-repo")
        assert result is not None
        assert result["is_deleted"] == 0

    @pytest.mark.asyncio
    async def test_restore_nonexistent_repo(self, sync_service):
        """Test restoring a non-existent repository."""
        # Should not raise an error
        await sync_service.restore_repo("owner/nonexistent-repo")

    @pytest.mark.asyncio
    async def test_restore_already_active_repo(self, sync_service, db):
        """Test restoring a repository that is already active."""
        # Add an active repo
        await db.add_repository({
            "name_with_owner": "owner/test-repo",
            "name": "test-repo",
            "owner": "owner",
            "description": "Test",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 100,
            "fork_count": 20,
            "url": "https://github.com/owner/test-repo",
            "homepage_url": None,
            "pushed_at": "2023-12-01T00:00:00",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2023-06-01T00:00:00",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Test",
            "categories": [],
            "features": [],
            "use_cases": []
        })

        # Restore it (should be idempotent)
        await sync_service.restore_repo("owner/test-repo")

        # Verify it's still active
        result = await db.get_repository("owner/test-repo")
        assert result is not None
        assert result["is_deleted"] == 0


# ============================================================================
# full_sync() tests
# ============================================================================

class TestFullSync:
    """Tests for full_sync method."""

    @pytest.mark.asyncio
    async def test_full_sync_adds_new_repos(self, sync_service, db, mocker):
        """Test that full_sync adds new repositories from GitHub."""
        # Create mock GitHub repos
        github_repo = GitHubRepository(
            id=123,
            full_name="owner/new-repo",
            name="new-repo",
            owner="owner",
            description="A new repository",
            language="Python",
            topics=["test"],
            stargazers_count=50,
            forks_count=10,
            html_url="https://github.com/owner/new-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 1),
            starred_at=datetime(2023, 6, 1),
            archived=False,
            visibility="public",
            owner_type="User"
        )

        # Mock GitHubClient
        mock_github = AsyncMock()
        mock_github.__aenter__ = AsyncMock(return_value=mock_github)
        mock_github.__aexit__ = AsyncMock()
        mock_github.get_all_starred = AsyncMock(return_value=[github_repo])

        mocker.patch("src.services.sync.GitHubClient", return_value=mock_github)

        # Run full sync
        result = await sync_service.full_sync(skip_llm=True)

        # Verify results
        assert result["sync_type"] == "full"
        assert result["added"] == 1
        assert result["updated"] == 0
        assert result["deleted"] == 0
        assert result["failed"] == 0

        # Verify repo was added
        added_repo = await db.get_repository("owner/new-repo")
        assert added_repo is not None
        assert added_repo["name"] == "new-repo"
        assert added_repo["is_deleted"] == 0

    @pytest.mark.asyncio
    async def test_full_sync_updates_existing_repos(self, sync_service, db, mocker):
        """Test that full_sync updates existing repositories."""
        # Add an existing repo
        await db.add_repository({
            "name_with_owner": "owner/existing-repo",
            "name": "existing-repo",
            "owner": "owner",
            "description": "Old description",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 50,
            "fork_count": 10,
            "url": "https://github.com/owner/existing-repo",
            "homepage_url": None,
            "pushed_at": "2023-11-01T00:00:00",  # Older pushed_at
            
            "archived": 0,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            
            "last_synced_at": datetime(2023, 11, 1).isoformat(),
            "summary": "Old summary",
            "categories": [],
            "features": [],
            "use_cases": []
        })

        # Create updated GitHub repo
        github_repo = GitHubRepository(
            id=123,
            full_name="owner/existing-repo",
            name="existing-repo",
            owner="owner",
            description="New description",  # Updated
            language="Python",
            topics=[],
            stargazers_count=60,  # Updated
            forks_count=15,  # Updated
            html_url="https://github.com/owner/existing-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 1),  # Updated
            archived=False,
            visibility="public",
            owner_type="User"
        )

        # Mock GitHubClient
        mock_github = AsyncMock()
        mock_github.__aenter__ = AsyncMock(return_value=mock_github)
        mock_github.__aexit__ = AsyncMock()
        mock_github.get_all_starred = AsyncMock(return_value=[github_repo])

        mocker.patch("src.services.sync.GitHubClient", return_value=mock_github)

        # Run full sync
        result = await sync_service.full_sync(skip_llm=True)

        # Verify results
        assert result["sync_type"] == "full"
        assert result["added"] == 0
        assert result["updated"] == 1
        assert result["deleted"] == 0

        # Verify repo was updated
        updated_repo = await db.get_repository("owner/existing-repo")
        assert updated_repo is not None
        assert updated_repo["description"] == "New description"
        assert updated_repo["stargazer_count"] == 60
        assert updated_repo["fork_count"] == 15

    @pytest.mark.asyncio
    async def test_full_sync_soft_deletes_removed_repos(self, sync_service, db, mocker):
        """Test that full_sync soft-deletes repos no longer starred."""
        # Add an existing repo that will be "unstarred"
        await db.add_repository({
            "name_with_owner": "owner/unstarred-repo",
            "name": "unstarred-repo",
            "owner": "owner",
            "description": "Unstarred repo",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 50,
            "fork_count": 10,
            "url": "https://github.com/owner/unstarred-repo",
            "homepage_url": None,
            "pushed_at": "2023-12-01T00:00:00",
            
            "archived": 0,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            
            "last_synced_at": datetime(2023, 11, 1).isoformat(),
            "summary": "Test",
            "categories": [],
            "features": [],
            "use_cases": []
        })

        # Mock GitHubClient returning empty list (all repos unstarred)
        mock_github = AsyncMock()
        mock_github.__aenter__ = AsyncMock(return_value=mock_github)
        mock_github.__aexit__ = AsyncMock()
        mock_github.get_all_starred = AsyncMock(return_value=[])

        mocker.patch("src.services.sync.GitHubClient", return_value=mock_github)

        # Run full sync
        result = await sync_service.full_sync(skip_llm=True)

        # Verify results
        assert result["sync_type"] == "full"
        assert result["added"] == 0
        assert result["updated"] == 0
        assert result["deleted"] == 1

        # Verify repo was soft deleted
        deleted_repo = await db.get_repository("owner/unstarred-repo")
        assert deleted_repo is not None
        assert deleted_repo["is_deleted"] == 1

    @pytest.mark.asyncio
    async def test_full_sync_records_history(self, sync_service, db, mocker):
        """Test that full_sync records sync history."""
        # Mock GitHubClient
        mock_github = AsyncMock()
        mock_github.__aenter__ = AsyncMock(return_value=mock_github)
        mock_github.__aexit__ = AsyncMock()
        mock_github.get_all_starred = AsyncMock(return_value=[])

        mocker.patch("src.services.sync.GitHubClient", return_value=mock_github)

        # Run full sync
        await sync_service.full_sync(skip_llm=True)

        # Verify sync history was recorded
        cursor = await db._connection.execute(
            "SELECT * FROM sync_history ORDER BY started_at DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        assert row is not None
        history = dict(row)
        assert history["sync_type"] == "full"
        assert history["stats_added"] == 0
        assert history["stats_updated"] == 0
        assert history["stats_deleted"] == 0
        assert history["stats_failed"] == 0


# ============================================================================
# incremental_sync() tests
# ============================================================================

class TestIncrementalSync:
    """Tests for incremental_sync method."""

    @pytest.mark.asyncio
    async def test_incremental_sync_with_no_last_sync(self, sync_service, db, mocker):
        """Test incremental_sync when there's no previous sync (first sync)."""
        # Create mock GitHub repos
        github_repo = GitHubRepository(
            id=123,
            full_name="owner/new-repo",
            name="new-repo",
            owner="owner",
            description="A new repository",
            language="Python",
            topics=[],
            stargazers_count=50,
            forks_count=10,
            html_url="https://github.com/owner/new-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 1),
            archived=False,
            visibility="public",
            owner_type="User"
        )

        # Mock GitHubClient
        mock_github = AsyncMock()
        mock_github.__aenter__ = AsyncMock(return_value=mock_github)
        mock_github.__aexit__ = AsyncMock()
        mock_github.get_all_starred = AsyncMock(return_value=[github_repo])

        mocker.patch("src.services.sync.GitHubClient", return_value=mock_github)

        # Run incremental sync (no previous sync)
        result = await sync_service.incremental_sync(skip_llm=True)

        # Verify results - should add new repo even without last_sync
        assert result["sync_type"] == "incremental"
        assert result["added"] == 1

    @pytest.mark.asyncio
    async def test_incremental_sync_adds_updates_deletes(self, sync_service, db, mocker):
        """Test incremental_sync handles adds, updates, and deletes."""
        # Add an existing repo (will be updated)
        await db.add_repository({
            "name_with_owner": "owner/existing-repo",
            "name": "existing-repo",
            "owner": "owner",
            "description": "Old description",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 50,
            "fork_count": 10,
            "url": "https://github.com/owner/existing-repo",
            "homepage_url": None,
            "pushed_at": "2023-11-01T00:00:00",
            
            "archived": 0,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            
            "last_synced_at": datetime(2023, 11, 1).isoformat(),
            "summary": "Old summary",
            "categories": [],
            "features": [],
            "use_cases": []
        })

        # Add a repo that will be deleted
        await db.add_repository({
            "name_with_owner": "owner/to-delete-repo",
            "name": "to-delete-repo",
            "owner": "owner",
            "description": "To be deleted",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 30,
            "fork_count": 5,
            "url": "https://github.com/owner/to-delete-repo",
            "homepage_url": None,
            "pushed_at": "2023-12-01T00:00:00",
            
            "archived": 0,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            
            "last_synced_at": datetime(2023, 11, 1).isoformat(),
            "summary": "Test",
            "categories": [],
            "features": [],
            "use_cases": []
        })

        # Create GitHub repos (existing updated, new added, to-delete missing)
        updated_repo = GitHubRepository(
            id=123,
            full_name="owner/existing-repo",
            name="existing-repo",
            owner="owner",
            description="New description",  # Changed
            language="Python",
            topics=[],
            stargazers_count=60,  # Changed
            forks_count=15,  # Changed
            html_url="https://github.com/owner/existing-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 1),
            archived=False,
            visibility="public",
            owner_type="User"
        )

        new_repo = GitHubRepository(
            id=456,
            full_name="owner/new-repo",
            name="new-repo",
            owner="owner",
            description="A new repository",
            language="TypeScript",
            topics=[],
            stargazers_count=100,
            forks_count=20,
            html_url="https://github.com/owner/new-repo",
            homepage=None,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            pushed_at=datetime(2023, 12, 1),
            archived=False,
            visibility="public",
            owner_type="User"
        )

        # Mock GitHubClient
        mock_github = AsyncMock()
        mock_github.__aenter__ = AsyncMock(return_value=mock_github)
        mock_github.__aexit__ = AsyncMock()
        mock_github.get_all_starred = AsyncMock(return_value=[updated_repo, new_repo])

        mocker.patch("src.services.sync.GitHubClient", return_value=mock_github)

        # Run incremental sync
        result = await sync_service.incremental_sync(skip_llm=True)

        # Verify results
        assert result["sync_type"] == "incremental"
        assert result["added"] == 1  # new-repo
        assert result["updated"] == 1  # existing-repo
        assert result["deleted"] == 1  # to-delete-repo
