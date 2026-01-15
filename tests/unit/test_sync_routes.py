"""
Unit tests for Sync API routes.

Tests the API endpoints for synchronization functionality.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime


@pytest_asyncio.fixture
async def sync_client(db):
    """Create test client with database for sync API."""
    from src.api.app import app
    import src.api.routes.sync as sync_routes

    # Override the get_db dependency to use test db
    app.dependency_overrides[sync_routes.get_db] = lambda: db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()


# ============================================================================
# GET /api/sync/status
# ============================================================================

class TestSyncStatus:
    """Tests for GET /api/sync/status endpoint."""

    @pytest.mark.asyncio
    async def test_get_sync_status_no_history(self, sync_client):
        """Test getting sync status when there's no sync history."""
        response = await sync_client.get("/api/sync/status")
        assert response.status_code == 200

        data = response.json()
        assert "last_sync_at" in data
        assert "sync_type" in data
        assert "total_repos" in data
        assert "deleted_repos" in data
        assert data["total_repos"] == 0
        assert data["deleted_repos"] == 0

    @pytest.mark.asyncio
    async def test_get_sync_status_with_repos(self, sync_client, db):
        """Test getting sync status with repositories in database."""
        # Add some test repos
        for i in range(5):
            await db.add_repository({
                "name_with_owner": f"owner/repo{i}",
                "name": f"repo{i}",
                "owner": "owner",
                "description": f"Test repo {i}",
                "primary_language": "Python",
                "topics": [],
                "stargazer_count": 100 + i,
                "fork_count": 20,
                "url": f"https://github.com/owner/repo{i}",
                "homepage_url": None,
                "pushed_at": "2023-12-01T00:00:00",
                "archived": False,
                "visibility": "public",
                "owner_type": "User",
                "organization": None,
                "starred_at": "2023-06-01T00:00:00",
                "last_synced_at": datetime.now().isoformat(),
                "summary": f"Test repo {i}",
                "categories": [],
                "features": [],
                "tech_stack": ["Python"],
                "use_cases": []
            })

        # Add a soft-deleted repo
        await db.add_repository({
            "name_with_owner": "owner/deleted-repo",
            "name": "deleted-repo",
            "owner": "owner",
            "description": "Deleted repo",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 50,
            "fork_count": 10,
            "url": "https://github.com/owner/deleted-repo",
            "homepage_url": None,
            "pushed_at": "2023-12-01T00:00:00",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2023-06-01T00:00:00",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Deleted",
            "categories": [],
            "features": [],
            "tech_stack": ["Python"],
            "use_cases": []
        })
        # Mark as deleted using update
        await db.update_repository("owner/deleted-repo", {"is_deleted": 1})

        response = await sync_client.get("/api/sync/status")
        assert response.status_code == 200

        data = response.json()
        assert data["total_repos"] == 5  # Active repos
        assert data["deleted_repos"] == 1  # Deleted repos

    @pytest.mark.asyncio
    async def test_get_sync_status_with_history(self, sync_client, db):
        """Test getting sync status with existing sync history."""
        # Add a sync history record
        await db.execute_query("""
            INSERT INTO sync_history (
                sync_type, started_at, completed_at,
                stats_added, stats_updated, stats_deleted, stats_failed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "full",
            "2023-12-01T10:00:00",
            "2023-12-01T10:05:00",
            10, 5, 2, 0
        ))

        response = await sync_client.get("/api/sync/status")
        assert response.status_code == 200

        data = response.json()
        assert data["last_sync_at"] == "2023-12-01T10:00:00"
        assert data["sync_type"] == "full"


# ============================================================================
# POST /api/sync/manual
# ============================================================================

class TestManualSync:
    """Tests for POST /api/sync/manual endpoint."""

    @pytest.mark.asyncio
    async def test_manual_sync_incremental_default(self, sync_client):
        """Test manual sync with default parameters (incremental)."""
        response = await sync_client.post("/api/sync/manual", json={})
        # The response will be 200 since it starts a background task
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "sync_type" in data
        assert data["sync_type"] == "incremental"

    @pytest.mark.asyncio
    async def test_manual_sync_full_sync(self, sync_client):
        """Test manual sync with full_sync flag."""
        response = await sync_client.post("/api/sync/manual", json={"full_sync": True})
        assert response.status_code == 200

        data = response.json()
        assert data["sync_type"] == "full"

    @pytest.mark.asyncio
    async def test_manual_sync_with_reanalyze(self, sync_client):
        """Test manual sync with reanalyze flag."""
        response = await sync_client.post("/api/sync/manual", json={
            "full_sync": True,
            "reanalyze": True
        })
        assert response.status_code == 200


# ============================================================================
# GET /api/sync/history
# ============================================================================

class TestSyncHistory:
    """Tests for GET /api/sync/history endpoint."""

    @pytest.mark.asyncio
    async def test_get_sync_history_empty(self, sync_client):
        """Test getting sync history when empty."""
        response = await sync_client.get("/api/sync/history")
        assert response.status_code == 200

        data = response.json()
        assert "results" in data
        assert data["results"] == []

    @pytest.mark.asyncio
    async def test_get_sync_history_with_records(self, sync_client, db):
        """Test getting sync history with records."""
        # Add some sync history records with specific dates to control order
        await db.execute_query("""
            INSERT INTO sync_history (
                sync_type, started_at, completed_at,
                stats_added, stats_updated, stats_deleted, stats_failed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("full", "2023-12-03T10:00:00", "2023-12-03T10:05:00", 12, 7, 2, 0))

        await db.execute_query("""
            INSERT INTO sync_history (
                sync_type, started_at, completed_at,
                stats_added, stats_updated, stats_deleted, stats_failed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("incremental", "2023-12-02T10:00:00", "2023-12-02T10:05:00", 11, 6, 2, 0))

        await db.execute_query("""
            INSERT INTO sync_history (
                sync_type, started_at, completed_at,
                stats_added, stats_updated, stats_deleted, stats_failed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("incremental", "2023-12-01T10:00:00", "2023-12-01T10:05:00", 10, 5, 2, 0))

        response = await sync_client.get("/api/sync/history")
        assert response.status_code == 200

        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 3

        # Check that results are ordered by started_at DESC (most recent first)
        assert data["results"][0]["sync_type"] == "full"
        assert data["results"][0]["started_at"] == "2023-12-03T10:00:00"

    @pytest.mark.asyncio
    async def test_get_sync_history_with_limit(self, sync_client, db):
        """Test getting sync history with limit parameter."""
        # Add 5 sync history records
        for i in range(5):
            await db.execute_query("""
                INSERT INTO sync_history (
                    sync_type, started_at, completed_at,
                    stats_added, stats_updated, stats_deleted, stats_failed
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "incremental",
                f"2023-12-0{i+1}T10:00:00",
                f"2023-12-0{i+1}T10:05:00",
                10, 5, 2, 0
            ))

        response = await sync_client.get("/api/sync/history?limit=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data["results"]) == 2


# ============================================================================
# GET /api/sync/repos/deleted
# ============================================================================

class TestDeletedRepos:
    """Tests for GET /api/sync/repos/deleted endpoint."""

    @pytest.mark.asyncio
    async def test_get_deleted_repos_empty(self, sync_client):
        """Test getting deleted repos when none exist."""
        response = await sync_client.get("/api/sync/repos/deleted")
        assert response.status_code == 200

        data = response.json()
        assert "results" in data
        assert "total" in data
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_deleted_repos_with_records(self, sync_client, db):
        """Test getting deleted repos with records."""
        # Add a deleted repo
        await db.add_repository({
            "name_with_owner": "owner/deleted-repo",
            "name": "deleted-repo",
            "owner": "owner",
            "description": "Deleted repo",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 50,
            "fork_count": 10,
            "url": "https://github.com/owner/deleted-repo",
            "homepage_url": None,
            "pushed_at": "2023-12-01T00:00:00",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2023-06-01T00:00:00",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Deleted",
            "categories": [],
            "features": [],
            "tech_stack": ["Python"],
            "use_cases": []
        })
        await db.update_repository("owner/deleted-repo", {"is_deleted": 1})

        # Add an active repo (should not appear in results)
        await db.add_repository({
            "name_with_owner": "owner/active-repo",
            "name": "active-repo",
            "owner": "owner",
            "description": "Active repo",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 100,
            "fork_count": 20,
            "url": "https://github.com/owner/active-repo",
            "homepage_url": None,
            "pushed_at": "2023-12-01T00:00:00",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2023-06-01T00:00:00",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Active",
            "categories": [],
            "features": [],
            "tech_stack": ["Python"],
            "use_cases": []
        })

        response = await sync_client.get("/api/sync/repos/deleted")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["name_with_owner"] == "owner/deleted-repo"


# ============================================================================
# POST /api/sync/repo/{name}/restore
# ============================================================================

class TestRestoreRepo:
    """Tests for POST /api/sync/repo/{name}/restore endpoint."""

    @pytest.mark.asyncio
    async def test_restore_repo_success(self, sync_client, db):
        """Test restoring a soft-deleted repository."""
        # Add a deleted repo
        await db.add_repository({
            "name_with_owner": "owner/deleted-repo",
            "name": "deleted-repo",
            "owner": "owner",
            "description": "Deleted repo",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 50,
            "fork_count": 10,
            "url": "https://github.com/owner/deleted-repo",
            "homepage_url": None,
            "pushed_at": "2023-12-01T00:00:00",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2023-06-01T00:00:00",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Deleted",
            "categories": [],
            "features": [],
            "tech_stack": ["Python"],
            "use_cases": []
        })
        await db.update_repository("owner/deleted-repo", {"is_deleted": 1})

        response = await sync_client.post("/api/sync/repo/owner%2Fdeleted-repo/restore")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "restored" in data["message"].lower()

        # Verify repo is restored
        repo = await db.get_repository("owner/deleted-repo")
        assert repo["is_deleted"] == 0

    @pytest.mark.asyncio
    async def test_restore_nonexistent_repo(self, sync_client):
        """Test restoring a non-existent repository."""
        response = await sync_client.post("/api/sync/repo/owner%2Fnonexistent/restore")
        # Should return success even if repo doesn't exist (idempotent)
        assert response.status_code == 200


# ============================================================================
# POST /api/sync/repo/{name}/reanalyze
# ============================================================================

class TestReanalyzeRepo:
    """Tests for POST /api/sync/repo/{name}/reanalyze endpoint."""

    @pytest.mark.asyncio
    async def test_reanalyze_repo_queues_task(self, sync_client, db):
        """Test that reanalyze request queues the background task."""
        # Add a test repo
        await db.add_repository({
            "name_with_owner": "owner/test-repo",
            "name": "test-repo",
            "owner": "owner",
            "description": "Test repo",
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
            "summary": "Old summary",
            "categories": ["old-category"],
            "features": [],
            "tech_stack": [],
            "use_cases": []
        })

        response = await sync_client.post("/api/sync/repo/owner%2Ftest-repo/reanalyze")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["status"] == "queued"
        assert "test-repo" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_reanalyze_nonexistent_repo(self, sync_client):
        """Test reanalyzing a non-existent repository."""
        # Should still return success (background task handles the check)
        response = await sync_client.post("/api/sync/repo/owner%2Fnonexistent/reanalyze")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_reanalyze_invalid_format(self, sync_client):
        """Test reanalyzing with invalid repo format."""
        response = await sync_client.post("/api/sync/repo/invalid-format/reanalyze")
        # Should still return success (background task handles the check)
        assert response.status_code == 200

