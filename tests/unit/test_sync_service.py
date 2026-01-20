"""
Unit tests for SyncService.

Tests the core synchronization logic including:
- Change detection (_should_update_repo)
- Soft delete and restore operations
- Full and incremental sync
- Vector index updates with semantic_search
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
def sync_service_with_semantic(db):
    """Create a SyncService instance with semantic search for testing."""
    mock_semantic = Mock()
    mock_semantic.add_repositories = AsyncMock()
    mock_semantic.update_repository = AsyncMock()
    mock_semantic.delete_repository = AsyncMock()
    return SyncService(db, mock_semantic)


@pytest.fixture
def github_repo_factory():
    """Factory for creating GitHubRepository objects with default values."""
    _sentinel = object()

    def create(
        name_with_owner: str = "owner/test-repo",
        name: str = "test-repo",
        owner: str = "owner",
        description: str = "A test repository",
        primary_language: str = "Python",
        topics: list = None,
        stargazer_count: int = 100,
        fork_count: int = 20,
        open_issues_count: int = 5,
        url: str = "https://github.com/owner/test-repo",
        homepage_url: str = None,
        created_at: object = _sentinel,
        updated_at: object = _sentinel,
        pushed_at: object = _sentinel,
        starred_at: object = _sentinel,
        archived: bool = False,
        visibility: str = "public",
        owner_type: str = "User",
        languages: list = None,
        readme_content: str = None,
        **kwargs
    ) -> GitHubRepository:
        return GitHubRepository(
            id=123,
            name_with_owner=name_with_owner,
            name=name,
            owner=owner,
            description=description,
            primary_language=primary_language,
            topics=topics or [],
            stargazer_count=stargazer_count,
            fork_count=fork_count,
            open_issues_count=open_issues_count,
            url=url,
            homepage_url=homepage_url,
            created_at=created_at if created_at is not _sentinel else datetime(2023, 1, 1),
            updated_at=updated_at if updated_at is not _sentinel else datetime(2023, 12, 1),
            pushed_at=pushed_at if pushed_at is not _sentinel else datetime(2023, 12, 1),
            starred_at=starred_at if starred_at is not _sentinel else datetime(2023, 6, 1),
            archived=archived,
            visibility=visibility,
            owner_type=owner_type,
            languages=languages or [],
            readme_content=readme_content,
            **kwargs
        )
    return create


@pytest.fixture
def sample_github_repo(github_repo_factory):
    """Create a sample GitHub repository."""
    return github_repo_factory()


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
        "is_deleted": 0,
        "languages": [{"name": "Python", "size": 1000, "percent": 100.0}]
    }


# ============================================================================
# _should_update_repo() tests
# ============================================================================

class TestNeedsUpdate:
    """Tests for _should_update_repo method."""

    @pytest.mark.asyncio
    async def test_no_changes_needed(self, sync_service, sample_local_repo, sample_github_repo):
        """Test that identical repos don't need update."""
        result = await sync_service._should_update_repo(
            name="owner/test-repo",
            github_repo_map={"owner/test-repo": sample_github_repo},
            local_repo_map={"owner/test-repo": sample_local_repo},
            stats={"failed": 0, "errors": []},
            skip_llm=True
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_pushed_at_change_triggers_update(self, sync_service, sample_local_repo, github_repo_factory):
        """Test that pushed_at changes trigger update."""
        github_repo = github_repo_factory(pushed_at=datetime(2023, 12, 2))
        result = await sync_service._should_update_repo(
            name="owner/test-repo",
            github_repo_map={"owner/test-repo": github_repo},
            local_repo_map={"owner/test-repo": sample_local_repo},
            stats={"failed": 0, "errors": []},
            skip_llm=True
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_stargazer_count_change_triggers_update(self, sync_service, sample_local_repo, github_repo_factory):
        """Test that stargazer_count changes trigger update."""
        github_repo = github_repo_factory(stargazer_count=101)
        result = await sync_service._should_update_repo(
            name="owner/test-repo",
            github_repo_map={"owner/test-repo": github_repo},
            local_repo_map={"owner/test-repo": sample_local_repo},
            stats={"failed": 0, "errors": []},
            skip_llm=True
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_fork_count_change_triggers_update(self, sync_service, sample_local_repo, github_repo_factory):
        """Test that fork_count changes trigger update."""
        github_repo = github_repo_factory(fork_count=21)
        result = await sync_service._should_update_repo(
            name="owner/test-repo",
            github_repo_map={"owner/test-repo": github_repo},
            local_repo_map={"owner/test-repo": sample_local_repo},
            stats={"failed": 0, "errors": []},
            skip_llm=True
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_language_change_triggers_update(self, sync_service, sample_local_repo, github_repo_factory):
        """Test that primary_language changes trigger update."""
        github_repo = github_repo_factory(primary_language="TypeScript")
        result = await sync_service._should_update_repo(
            name="owner/test-repo",
            github_repo_map={"owner/test-repo": github_repo},
            local_repo_map={"owner/test-repo": sample_local_repo},
            stats={"failed": 0, "errors": []},
            skip_llm=True
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_description_change_triggers_update(self, sync_service, sample_local_repo, github_repo_factory):
        """Test that description changes trigger update."""
        github_repo = github_repo_factory(description="Updated description")
        result = await sync_service._should_update_repo(
            name="owner/test-repo",
            github_repo_map={"owner/test-repo": github_repo},
            local_repo_map={"owner/test-repo": sample_local_repo},
            stats={"failed": 0, "errors": []},
            skip_llm=True
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_archived_change_triggers_update(self, sync_service, sample_local_repo, github_repo_factory):
        """Test that archived status changes trigger update."""
        github_repo = github_repo_factory(archived=True)
        result = await sync_service._should_update_repo(
            name="owner/test-repo",
            github_repo_map={"owner/test-repo": github_repo},
            local_repo_map={"owner/test-repo": sample_local_repo},
            stats={"failed": 0, "errors": []},
            skip_llm=True
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_visibility_change_triggers_update(self, sync_service, sample_local_repo, github_repo_factory):
        """Test that visibility changes trigger update."""
        github_repo = github_repo_factory(visibility="private")
        result = await sync_service._should_update_repo(
            name="owner/test-repo",
            github_repo_map={"owner/test-repo": github_repo},
            local_repo_map={"owner/test-repo": sample_local_repo},
            stats={"failed": 0, "errors": []},
            skip_llm=True
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_owner_type_change_triggers_update(self, sync_service, sample_local_repo, github_repo_factory):
        """Test that owner_type changes trigger update."""
        github_repo = github_repo_factory(owner_type="Organization")
        result = await sync_service._should_update_repo(
            name="owner/test-repo",
            github_repo_map={"owner/test-repo": github_repo},
            local_repo_map={"owner/test-repo": sample_local_repo},
            stats={"failed": 0, "errors": []},
            skip_llm=True
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_handles_null_pushed_at_in_github_repo(self, sync_service, sample_local_repo, github_repo_factory):
        """Test handling of null pushed_at in GitHub repo."""
        github_repo = github_repo_factory()
        # Explicitly set pushed_at to None after creation
        github_repo.pushed_at = None
        result = await sync_service._should_update_repo(
            name="owner/test-repo",
            github_repo_map={"owner/test-repo": github_repo},
            local_repo_map={"owner/test-repo": sample_local_repo},
            stats={"failed": 0, "errors": []},
            skip_llm=True
        )
        assert result is True  # Should trigger update due to null

    @pytest.mark.asyncio
    async def test_handles_null_pushed_at_in_local_repo(self, sync_service, sample_github_repo):
        """Test handling of null pushed_at in local repo."""
        local_repo = {
            **sample_github_repo.model_dump(),
            "pushed_at": None,
            "languages": [{"name": "Python", "size": 1000, "percent": 100.0}]
        }
        result = await sync_service._should_update_repo(
            name="owner/test-repo",
            github_repo_map={"owner/test-repo": sample_github_repo},
            local_repo_map={"owner/test-repo": local_repo},
            stats={"failed": 0, "errors": []},
            skip_llm=True
        )
        assert result is True  # Should trigger update due to null

    @pytest.mark.asyncio
    async def test_handles_null_language(self, sync_service, github_repo_factory):
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
            "owner_type": "User",
            "languages": []
        }
        github_repo = github_repo_factory(primary_language=None)
        result = await sync_service._should_update_repo(
            name="owner/test-repo",
            github_repo_map={"owner/test-repo": github_repo},
            local_repo_map={"owner/test-repo": local_repo},
            stats={"failed": 0, "errors": []},
            skip_llm=True
        )
        assert result is True  # Empty languages triggers heavy update


# ============================================================================
# full_sync() tests
# ============================================================================

class TestFullSync:
    """Tests for sync method."""

    @pytest.mark.asyncio
    async def test_sync_adds_new_repos(self, sync_service, db, mocker, github_repo_factory):
        """Test that sync adds new repositories from GitHub."""
        github_repo = github_repo_factory(
            name_with_owner="owner/new-repo",
            name="new-repo",
            description="A new repository",
            languages=[],
            readme_content=None
        )

        # Mock GitHubGraphQLClient
        mock_github = AsyncMock()
        mock_github.__aenter__ = AsyncMock(return_value=mock_github)
        mock_github.__aexit__ = AsyncMock()
        mock_github.get_authenticated_user = AsyncMock(return_value={"login": "testuser"})
        mock_github.get_starred_repositories = AsyncMock(return_value=[github_repo])

        mocker.patch("src.github.graphql.GitHubGraphQLClient", return_value=mock_github)

        # Run sync
        result = await sync_service.sync(skip_llm=True)

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

    @pytest.mark.asyncio
    async def test_sync_soft_deletes_removed_repos(self, sync_service, db, mocker):
        """Test that sync deletes repos no longer starred."""
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

        # Mock GitHubGraphQLClient returning empty list (all repos unstarred)
        mock_github = AsyncMock()
        mock_github.__aenter__ = AsyncMock(return_value=mock_github)
        mock_github.__aexit__ = AsyncMock()
        mock_github.get_authenticated_user = AsyncMock(return_value={"login": "testuser"})
        mock_github.get_starred_repositories = AsyncMock(return_value=[])

        mocker.patch("src.github.graphql.GitHubGraphQLClient", return_value=mock_github)

        # Run sync
        result = await sync_service.sync(skip_llm=True)

        # Verify results
        assert result["sync_type"] == "full"
        assert result["added"] == 0
        assert result["updated"] == 0
        assert result["deleted"] == 1

        # Verify repo was hard deleted (no longer exists in database)
        deleted_repo = await db.get_repository("owner/unstarred-repo")
        assert deleted_repo is None  # Hard delete means the row is completely removed

    @pytest.mark.asyncio
    async def test_sync_records_history(self, sync_service, db, mocker):
        """Test that sync records sync history."""
        # Mock GitHubGraphQLClient
        mock_github = AsyncMock()
        mock_github.__aenter__ = AsyncMock(return_value=mock_github)
        mock_github.__aexit__ = AsyncMock()
        mock_github.get_authenticated_user = AsyncMock(return_value={"login": "testuser"})
        mock_github.get_starred_repositories = AsyncMock(return_value=[])

        mocker.patch("src.github.graphql.GitHubGraphQLClient", return_value=mock_github)

        # Run sync
        await sync_service.sync(skip_llm=True)

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
# sync() tests - scenarios
# ============================================================================

class TestIncrementalSync:
    """Tests for sync method with various scenarios."""

    @pytest.mark.asyncio
    async def test_sync_with_no_previous_sync(self, sync_service, db, mocker, github_repo_factory):
        """Test sync when there's no previous sync (first sync)."""
        github_repo = github_repo_factory(
            name_with_owner="owner/new-repo",
            name="new-repo",
            description="A new repository",
            languages=[],
            readme_content=None
        )

        # Mock GitHubGraphQLClient
        mock_github = AsyncMock()
        mock_github.__aenter__ = AsyncMock(return_value=mock_github)
        mock_github.__aexit__ = AsyncMock()
        mock_github.get_authenticated_user = AsyncMock(return_value={"login": "testuser"})
        mock_github.get_starred_repositories = AsyncMock(return_value=[github_repo])

        mocker.patch("src.github.graphql.GitHubGraphQLClient", return_value=mock_github)

        # Run sync (no previous sync)
        result = await sync_service.sync(skip_llm=True)

        # Verify results - should add new repo
        assert result["sync_type"] == "full"
        assert result["added"] == 1

    @pytest.mark.asyncio
    async def test_sync_adds_updates_deletes(self, sync_service, db, mocker, github_repo_factory):
        """Test sync handles adds, updates, and deletes."""
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
        updated_repo = github_repo_factory(
            name_with_owner="owner/existing-repo",
            name="existing-repo",
            description="New description",  # Changed
            stargazer_count=60,  # Changed
            fork_count=15,  # Changed
            languages=[],
            readme_content=None
        )

        new_repo = github_repo_factory(
            name_with_owner="owner/new-repo",
            name="new-repo",
            description="A new repository",
            primary_language="TypeScript",
            languages=[],
            readme_content=None
        )

        # Mock GitHubGraphQLClient
        mock_github = AsyncMock()
        mock_github.__aenter__ = AsyncMock(return_value=mock_github)
        mock_github.__aexit__ = AsyncMock()
        mock_github.get_authenticated_user = AsyncMock(return_value={"login": "testuser"})
        mock_github.get_starred_repositories = AsyncMock(return_value=[updated_repo, new_repo])

        mocker.patch("src.github.graphql.GitHubGraphQLClient", return_value=mock_github)

        # Run sync
        result = await sync_service.sync(skip_llm=True)

        # Verify results
        assert result["sync_type"] == "full"
        assert result["added"] == 1  # new-repo
        assert result["updated"] == 1  # existing-repo
        assert result["deleted"] == 1  # to-delete-repo


# ============================================================================
# semantic_search integration tests
# ============================================================================

class TestSemanticSearchIntegration:
    """Tests for semantic_search integration in SyncService."""

    @pytest.mark.asyncio
    async def test_add_repository_updates_vector_index(self, sync_service_with_semantic, db, github_repo_factory):
        """Test that adding a repository also adds it to the vector index."""
        github_repo = github_repo_factory(
            name_with_owner="owner/new-repo",
            name="new-repo",
            description="A new repository",
            languages=[],
            readme_content=None
        )

        await sync_service_with_semantic._add_repository(github_repo, skip_llm=True)

        # Verify repo was added to database
        added_repo = await db.get_repository("owner/new-repo")
        assert added_repo is not None

        # Verify vector index was updated
        assert sync_service_with_semantic.semantic_search.add_repositories.called

    @pytest.mark.asyncio
    async def test_update_repository_with_semantic_field_change(self, sync_service_with_semantic, db, github_repo_factory):
        """Test that updating semantic fields triggers vector index update."""
        # Add existing repo
        await db.add_repository({
            "name_with_owner": "owner/repo1",
            "name": "repo1",
            "owner": "owner",
            "description": "Old description",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 100,
            "fork_count": 20,
            "url": "https://github.com/owner/repo1",
            "homepage_url": None,
            "pushed_at": "2023-12-01T00:00:00",
            "archived": 0,
            "visibility": "public",
            "owner_type": "User",
            "last_synced_at": datetime(2023, 11, 1).isoformat(),
            "summary": "Test",
            "categories": [],
            "features": [],
            "use_cases": []
        })

        github_repo = github_repo_factory(
            name_with_owner="owner/repo1",
            name="repo1",
            description="New description",  # Changed - semantic field
            primary_language="Python",
            languages=[],
            readme_content=None
        )

        # Update with semantic field change
        await sync_service_with_semantic._update_repository(
            name_with_owner="owner/repo1",
            github_repo=github_repo,
            change_type="light",
            changed_fields={"description": "New description"},
            needs_llm=False,
            skip_llm=True
        )

        # Verify vector index was updated
        assert sync_service_with_semantic.semantic_search.update_repository.called

    @pytest.mark.asyncio
    async def test_update_repository_without_semantic_field_change(self, sync_service_with_semantic, db, github_repo_factory):
        """Test that updating non-semantic fields does not trigger vector index update."""
        # Add existing repo
        await db.add_repository({
            "name_with_owner": "owner/repo1",
            "name": "repo1",
            "owner": "owner",
            "description": "Test description",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 100,
            "fork_count": 20,
            "url": "https://github.com/owner/repo1",
            "homepage_url": None,
            "pushed_at": "2023-12-01T00:00:00",
            "archived": 0,
            "visibility": "public",
            "owner_type": "User",
            "last_synced_at": datetime(2023, 11, 1).isoformat(),
            "summary": "Test",
            "categories": [],
            "features": [],
            "use_cases": []
        })

        github_repo = github_repo_factory(
            name_with_owner="owner/repo1",
            name="repo1",
            description="Test description",  # Same
            primary_language="Python",
            stargazer_count=150,  # Changed - not semantic field
            languages=[],
            readme_content=None
        )

        # Update without semantic field change
        await sync_service_with_semantic._update_repository(
            name_with_owner="owner/repo1",
            github_repo=github_repo,
            change_type="light",
            changed_fields={"stargazer_count": 150},
            needs_llm=False,
            skip_llm=True
        )

        # Verify vector index was NOT updated
        assert not sync_service_with_semantic.semantic_search.update_repository.called

    @pytest.mark.asyncio
    async def test_delete_repository_removes_from_vector_index(self, sync_service_with_semantic, db):
        """Test that deleting a repository also removes it from the vector index."""
        # Add existing repo
        await db.add_repository({
            "name_with_owner": "owner/repo1",
            "name": "repo1",
            "owner": "owner",
            "description": "Test description",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 100,
            "fork_count": 20,
            "url": "https://github.com/owner/repo1",
            "homepage_url": None,
            "pushed_at": "2023-12-01T00:00:00",
            "archived": 0,
            "visibility": "public",
            "owner_type": "User",
            "last_synced_at": datetime(2023, 11, 1).isoformat(),
            "summary": "Test",
            "categories": [],
            "features": [],
            "use_cases": []
        })

        # Delete repo with proper stats dict
        stats = {"deleted": 0, "failed": 0, "errors": []}
        await sync_service_with_semantic._process_deletions({"owner/repo1"}, stats)

        # Verify vector index was updated
        assert sync_service_with_semantic.semantic_search.delete_repository.called

    def test_needs_vector_update_with_semantic_fields(self, sync_service):
        """Test _needs_vector_update correctly identifies semantic field changes."""
        # Description change should trigger update
        assert sync_service._needs_vector_update({"description": "New desc"})

        # Language change should trigger update
        assert sync_service._needs_vector_update({"primary_language": "TypeScript"})

        # Topics change should trigger update
        assert sync_service._needs_vector_update({"topics": ["new"]})

        # Multiple semantic fields should trigger update
        assert sync_service._needs_vector_update({
            "description": "New desc",
            "primary_language": "TypeScript"
        })

        # Non-semantic fields should not trigger update
        assert not sync_service._needs_vector_update({"stargazer_count": 150})
        assert not sync_service._needs_vector_update({"fork_count": 25})
        assert not sync_service._needs_vector_update({"archived": 1})

        # Mixed changes with at least one semantic field should trigger update
        assert sync_service._needs_vector_update({
            "stargazer_count": 150,
            "description": "New desc"
        })
