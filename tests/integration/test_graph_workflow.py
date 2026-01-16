"""
Integration tests for graph knowledge workflow.

Tests the complete graph workflow from building to querying edges.
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
# Graph Workflow Tests
# ============================================================================

class TestGraphWorkflow:
    """Integration tests for complete graph workflow."""

    @pytest.mark.asyncio
    async def test_graph_workflow(self, integration_client, integration_db):
        """Test complete graph workflow: build -> query -> display."""
        # Step 1: Add test repositories to database
        # Create repos with relationships for graph testing
        test_repos = [
            {
                "name_with_owner": "tiangolo/fastapi",
                "name": "fastapi",
                "owner": "tiangolo",
                "description": "FastAPI framework",
                "primary_language": "Python",
                "topics": ["api", "web", "framework"],
                "stargazer_count": 50000,
                "fork_count": 5000,
                "url": "https://github.com/tiangolo/fastapi",
                "homepage_url": None,
                "pushed_at": "2024-01-01T00:00:00Z",
                "archived": False,
                "visibility": "public",
                "owner_type": "User",
                "organization": None,
                "starred_at": "2024-01-01T00:00:00Z",
                "last_synced_at": datetime.now().isoformat(),
                "summary": "FastAPI framework",
                "categories": ["web"],
                "features": ["async"],
                "tech_stack": ["Python"],
                "use_cases": []
            },
            {
                "name_with_owner": "tiangolo/typer",
                "name": "typer",
                "owner": "tiangolo",
                "description": "Typer CLI framework",
                "primary_language": "Python",
                "topics": ["cli", "framework"],
                "stargazer_count": 10000,
                "fork_count": 500,
                "url": "https://github.com/tiangolo/typer",
                "homepage_url": None,
                "pushed_at": "2024-01-01T00:00:00Z",
                "archived": False,
                "visibility": "public",
                "owner_type": "User",
                "organization": None,
                "starred_at": "2024-01-01T00:00:00Z",
                "last_synced_at": datetime.now().isoformat(),
                "summary": "Typer CLI framework",
                "categories": ["cli"],
                "features": [],
                "tech_stack": ["Python"],
                "use_cases": []
            },
            {
                "name_with_owner": "encode/starlette",
                "name": "starlette",
                "owner": "encode",
                "description": "Starlette framework",
                "primary_language": "Python",
                "topics": ["api", "web", "asgi"],
                "stargazer_count": 8000,
                "fork_count": 600,
                "url": "https://github.com/encode/starlette",
                "homepage_url": None,
                "pushed_at": "2024-01-01T00:00:00Z",
                "archived": False,
                "visibility": "public",
                "owner_type": "Organization",
                "organization": "encode",
                "starred_at": "2024-01-01T00:00:00Z",
                "last_synced_at": datetime.now().isoformat(),
                "summary": "Starlette framework",
                "categories": ["web"],
                "features": ["async"],
                "tech_stack": ["Python"],
                "use_cases": []
            },
            {
                "name_with_owner": "encode/httpx",
                "name": "httpx",
                "owner": "encode",
                "description": "HTTPX HTTP client",
                "primary_language": "Python",
                "topics": ["http", "client", "async"],
                "stargazer_count": 6000,
                "fork_count": 400,
                "url": "https://github.com/encode/httpx",
                "homepage_url": None,
                "pushed_at": "2024-01-01T00:00:00Z",
                "archived": False,
                "visibility": "public",
                "owner_type": "Organization",
                "organization": "encode",
                "starred_at": "2024-01-01T00:00:00Z",
                "last_synced_at": datetime.now().isoformat(),
                "summary": "HTTPX HTTP client",
                "categories": ["web"],
                "features": ["async"],
                "tech_stack": ["Python"],
                "use_cases": []
            },
        ]

        for repo_data in test_repos:
            await integration_db.add_repository(repo_data)

        # Step 2: Rebuild graph
        response = await integration_client.post("/api/graph/rebuild")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["edges_count"] > 0
        edges_created = data["edges_count"]

        # Step 3: Query edges for a specific repository
        response = await integration_client.get("/api/graph/nodes/tiangolo/fastapi/edges")
        assert response.status_code == 200
        edges = response.json()
        assert isinstance(edges, list)

        # Verify we have edges (should have author edge to typer, ecosystem edges to other Python repos)
        assert len(edges) > 0

        # Verify edge structure
        edge = edges[0]
        assert "source" in edge
        assert "target" in edge
        assert "type" in edge
        assert "weight" in edge

        # Step 4: Check graph status
        response = await integration_client.get("/api/graph/status")
        assert response.status_code == 200
        status = response.json()
        assert "data" in status
        assert isinstance(status["data"], list)

        # Step 5: Query related repos
        response = await integration_client.get("/api/graph/nodes/tiangolo/fastapi/related?limit=5")
        assert response.status_code == 200
        related = response.json()
        assert "data" in related
        assert isinstance(related["data"], list)

        # Verify we have related repos with full data
        if len(related["data"]) > 0:
            related_repo = related["data"][0]
            assert "name_with_owner" in related_repo
            assert "name" in related_repo
            assert "relation_type" in related_repo
            assert "relation_weight" in related_repo


# ============================================================================
# Graph Rebuild Tests
# ============================================================================

class TestGraphRebuild:
    """Integration tests for graph rebuild endpoint."""

    @pytest.mark.asyncio
    async def test_rebuild_empty_database(self, integration_client, integration_db):
        """Test graph rebuild with empty database."""
        response = await integration_client.post("/api/graph/rebuild")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        # With no repos, should have 0 edges
        assert data["edges_count"] == 0

    @pytest.mark.asyncio
    async def test_rebuild_with_repos(self, integration_client, integration_db):
        """Test graph rebuild with repositories."""
        # Add test repos
        await integration_db.add_repository({
            "name_with_owner": "user/repo1",
            "name": "repo1",
            "owner": "user",
            "description": "Test repo 1",
            "primary_language": "Python",
            "topics": ["test"],
            "stargazer_count": 100,
            "fork_count": 20,
            "url": "https://github.com/user/repo1",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Test repo 1",
            "categories": [],
            "features": [],
            "tech_stack": ["Python"],
            "use_cases": []
        })

        await integration_db.add_repository({
            "name_with_owner": "user/repo2",
            "name": "repo2",
            "owner": "user",
            "description": "Test repo 2",
            "primary_language": "Python",
            "topics": ["test"],
            "stargazer_count": 50,
            "fork_count": 10,
            "url": "https://github.com/user/repo2",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Test repo 2",
            "categories": [],
            "features": [],
            "tech_stack": ["Python"],
            "use_cases": []
        })

        # Rebuild graph
        response = await integration_client.post("/api/graph/rebuild")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        # Should have created edges (same owner, same language)
        assert data["edges_count"] > 0


# ============================================================================
# Graph Query Tests
# ============================================================================

class TestGraphQueries:
    """Integration tests for graph query endpoints."""

    @pytest.mark.asyncio
    async def test_get_repo_edges_no_edges(self, integration_client, integration_db):
        """Test getting edges for a repository with no edges."""
        # Add a repo without building graph
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
            "tech_stack": ["Python"],
            "use_cases": []
        })

        response = await integration_client.get("/api/graph/nodes/user/test-repo/edges")
        assert response.status_code == 200

        edges = response.json()
        assert isinstance(edges, list)
        # Should return empty list if no edges
        assert len(edges) == 0

    @pytest.mark.asyncio
    async def test_get_repo_edges_with_filter(self, integration_client, integration_db):
        """Test getting edges with type filter."""
        # Add repos and build graph
        await integration_db.add_repository({
            "name_with_owner": "user/repo1",
            "name": "repo1",
            "owner": "user",
            "description": "Test repo 1",
            "primary_language": "Python",
            "topics": ["web"],
            "stargazer_count": 100,
            "fork_count": 20,
            "url": "https://github.com/user/repo1",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Test repo 1",
            "categories": [],
            "features": [],
            "tech_stack": ["Python"],
            "use_cases": []
        })

        await integration_db.add_repository({
            "name_with_owner": "user/repo2",
            "name": "repo2",
            "owner": "user",
            "description": "Test repo 2",
            "primary_language": "Python",
            "topics": ["web"],
            "stargazer_count": 50,
            "fork_count": 10,
            "url": "https://github.com/user/repo2",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Test repo 2",
            "categories": [],
            "features": [],
            "tech_stack": ["Python"],
            "use_cases": []
        })

        # Build graph
        await integration_client.post("/api/graph/rebuild")

        # Query edges with author type filter
        response = await integration_client.get(
            "/api/graph/nodes/user/repo1/edges?edge_types=author"
        )
        assert response.status_code == 200

        edges = response.json()
        assert isinstance(edges, list)

        # All returned edges should be of type 'author'
        for edge in edges:
            assert edge["type"] == "author"

    @pytest.mark.asyncio
    async def test_get_related_repos(self, integration_client, integration_db):
        """Test getting related repositories."""
        # Add repos and build graph
        await integration_db.add_repository({
            "name_with_owner": "user/main-repo",
            "name": "main-repo",
            "owner": "user",
            "description": "Main repository",
            "primary_language": "Python",
            "topics": ["api"],
            "stargazer_count": 1000,
            "fork_count": 200,
            "url": "https://github.com/user/main-repo",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Main repository",
            "categories": [],
            "features": [],
            "tech_stack": ["Python"],
            "use_cases": []
        })

        await integration_db.add_repository({
            "name_with_owner": "user/related-repo",
            "name": "related-repo",
            "owner": "user",
            "description": "Related repository",
            "primary_language": "Python",
            "topics": ["api"],
            "stargazer_count": 500,
            "fork_count": 100,
            "url": "https://github.com/user/related-repo",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Related repository",
            "categories": [],
            "features": [],
            "tech_stack": ["Python"],
            "use_cases": []
        })

        # Build graph
        await integration_client.post("/api/graph/rebuild")

        # Get related repos
        response = await integration_client.get(
            "/api/graph/nodes/user/main-repo/related?limit=5"
        )
        assert response.status_code == 200

        related = response.json()
        assert "data" in related
        assert isinstance(related["data"], list)

        # Verify related repos structure
        for repo in related["data"]:
            assert "name_with_owner" in repo
            assert "relation_type" in repo
            assert "relation_weight" in repo
