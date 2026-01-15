"""
Integration tests for sync API endpoints.

Tests the complete API flow from HTTP request to database.
"""
import pytest
from datetime import datetime
from unittest.mock import patch

# Import shared test helpers from test_sync_service_integration
from tests.integration.test_sync_service_integration import (
    create_test_repo,
    create_mock_github_client_class,
)


# ============================================================================
# Manual Sync API Tests
# ============================================================================

class TestManualSyncAPI:
    """Integration tests for POST /api/sync/manual endpoint."""

    @pytest.mark.asyncio
    async def test_manual_incremental_sync_api(self, integration_client, integration_db):
        """Test manual incremental sync through the API."""
        # Create mock repos
        mock_repos = [
            create_test_repo(1, "test-repo-1", language="Python"),
            create_test_repo(2, "test-repo-2", language="JavaScript"),
        ]
        MockClient = create_mock_github_client_class(mock_repos)

        # Perform manual sync with mocked GitHub client
        with patch('src.services.sync.GitHubClient', MockClient):
            response = await integration_client.post("/api/sync/manual", json={})

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "sync_type" in data
        assert data["sync_type"] == "incremental"

        # Verify repositories were added to database
        repo1 = await integration_db.get_repository("user/test-repo-1")
        assert repo1 is not None

    @pytest.mark.asyncio
    async def test_manual_full_sync_api(self, integration_client, integration_db):
        """Test manual full sync through the API."""
        # Create mock repos
        mock_repos = [
            create_test_repo(1, "test-repo-1", language="Python"),
        ]
        MockClient = create_mock_github_client_class(mock_repos)

        # Perform manual full sync
        with patch('src.services.sync.GitHubClient', MockClient):
            response = await integration_client.post("/api/sync/manual", json={"full_sync": True})

        assert response.status_code == 200

        data = response.json()
        assert data["sync_type"] == "full"

    @pytest.mark.asyncio
    async def test_manual_sync_with_reanalyze(self, integration_client, integration_db):
        """Test manual sync with reanalyze flag through the API."""
        # Create mock repos
        mock_repos = [
            create_test_repo(1, "test-repo-1", language="Python"),
        ]
        MockClient = create_mock_github_client_class(mock_repos)

        # Perform manual sync with reanalyze
        with patch('src.services.sync.GitHubClient', MockClient):
            response = await integration_client.post("/api/sync/manual", json={
                "full_sync": True,
                "reanalyze": True
            })

        assert response.status_code == 200


# ============================================================================
# Sync Status API Tests
# ============================================================================

class TestSyncStatusAPI:
    """Integration tests for GET /api/sync/status endpoint."""

    @pytest.mark.asyncio
    async def test_sync_status_api_empty(self, integration_client):
        """Test sync status API when there's no data."""
        response = await integration_client.get("/api/sync/status")
        assert response.status_code == 200

        data = response.json()
        assert "total_repos" in data
        assert data["total_repos"] == 0

    @pytest.mark.asyncio
    async def test_sync_status_api_with_repos(self, integration_client, integration_db):
        """Test sync status API with repositories in database."""
        # Add some test repos
        await integration_db.add_repository({
            "name_with_owner": "user/test-repo",
            "name": "test-repo",
            "owner": "user",
            "description": "Test repo",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 100,
            "fork_count": 20,
            "url": "https://github.com/user/test-repo",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Test repo",
            "categories": [],
            "features": [],
            "tech_stack": [],
            "use_cases": []
        })

        response = await integration_client.get("/api/sync/status")
        assert response.status_code == 200

        data = response.json()
        assert data["total_repos"] == 1
        assert data["deleted_repos"] == 0


# ============================================================================
# Sync History API Tests
# ============================================================================

class TestSyncHistoryAPI:
    """Integration tests for GET /api/sync/history endpoint."""

    @pytest.mark.asyncio
    async def test_sync_history_api_empty(self, integration_client):
        """Test sync history API when empty."""
        response = await integration_client.get("/api/sync/history")
        assert response.status_code == 200

        data = response.json()
        assert "results" in data
        assert data["results"] == []

    @pytest.mark.asyncio
    async def test_sync_history_api_with_records(self, integration_client, integration_db):
        """Test sync history API with records."""
        # Create mock repos
        mock_repos = [
            create_test_repo(1, "test-repo", language="Python"),
        ]
        MockClient = create_mock_github_client_class(mock_repos)

        # Perform a sync to create history
        with patch('src.services.sync.GitHubClient', MockClient):
            await integration_client.post("/api/sync/manual", json={})

        # Get sync history
        response = await integration_client.get("/api/sync/history")
        assert response.status_code == 200

        data = response.json()
        assert len(data["results"]) >= 1


# ============================================================================
# Deleted Repos API Tests
# ============================================================================

class TestDeletedReposAPI:
    """Integration tests for GET /api/sync/repos/deleted endpoint."""

    @pytest.mark.asyncio
    async def test_deleted_repos_api_empty(self, integration_client):
        """Test deleted repos API when none exist."""
        response = await integration_client.get("/api/sync/repos/deleted")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_deleted_repos_api_with_records(self, integration_client, integration_db):
        """Test deleted repos API with soft-deleted repos."""
        # Add a soft-deleted repo
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
            "summary": "Deleted",
            "categories": [],
            "features": [],
            "tech_stack": [],
            "use_cases": []
        })
        await integration_db.update_repository("user/deleted-repo", {"is_deleted": 1})

        # Get deleted repos
        response = await integration_client.get("/api/sync/repos/deleted")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1


# ============================================================================
# Restore Repo API Tests
# ============================================================================

class TestRestoreRepoAPI:
    """Integration tests for POST /api/sync/repo/{name}/restore endpoint."""

    @pytest.mark.asyncio
    async def test_restore_repo_api(self, integration_client, integration_db):
        """Test restoring a soft-deleted repository through the API."""
        # Add a soft-deleted repo
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
            "summary": "Deleted",
            "categories": [],
            "features": [],
            "tech_stack": [],
            "use_cases": []
        })
        await integration_db.update_repository("user/deleted-repo", {"is_deleted": 1})

        # Restore the repo
        response = await integration_client.post("/api/sync/repo/user%2Fdeleted-repo/restore")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Verify repo was restored
        repo = await integration_db.get_repository("user/deleted-repo")
        assert repo['is_deleted'] == 0

    @pytest.mark.asyncio
    async def test_restore_nonexistent_repo_api(self, integration_client):
        """Test restoring a non-existent repository through the API."""
        response = await integration_client.post("/api/sync/repo/user%2Fnonexistent/restore")
        # Should return success even if repo doesn't exist (idempotent)
        assert response.status_code == 200
