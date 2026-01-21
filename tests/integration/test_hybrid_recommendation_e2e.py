"""
Integration tests for hybrid recommendation system.

Tests the complete end-to-end flow of the hybrid recommendation system,
including graph edges, semantic similarity, and API endpoints.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch


# ============================================================================
# Test Helpers
# ============================================================================

async def setup_test_repos_with_semantic_edges(db):
    """Create test repositories with both graph and semantic edges."""
    test_repos = [
        {
            "name_with_owner": "anthropic/claude-docs",
            "name": "claude-docs",
            "owner": "anthropic",
            "description": "Official Claude documentation",
            "primary_language": "Python",
            "topics": ["documentation", "ai"],
            "stargazer_count": 5000,
            "fork_count": 500,
            "url": "https://github.com/anthropic/claude-docs",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "Organization",
            "organization": "anthropic",
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Claude documentation",
            "categories": ["ai"],
            "features": [],
            "use_cases": []
        },
        {
            "name_with_owner": "anthropic/claude-python",
            "name": "claude-python",
            "owner": "anthropic",
            "description": "Claude Python SDK",
            "primary_language": "Python",
            "topics": ["sdk", "ai"],
            "stargazer_count": 3000,
            "fork_count": 300,
            "url": "https://github.com/anthropic/claude-python",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "Organization",
            "organization": "anthropic",
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Claude Python SDK",
            "categories": ["ai"],
            "features": [],
            "use_cases": []
        },
        {
            "name_with_owner": "openai/openai-python",
            "name": "openai-python",
            "owner": "openai",
            "description": "OpenAI Python library",
            "primary_language": "Python",
            "topics": ["sdk", "ai"],
            "stargazer_count": 15000,
            "fork_count": 2000,
            "url": "https://github.com/openai/openai-python",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "Organization",
            "organization": "openai",
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "OpenAI Python library",
            "categories": ["ai"],
            "features": [],
            "use_cases": []
        },
        {
            "name_with_owner": "langchain-ai/langchain",
            "name": "langchain",
            "owner": "langchain-ai",
            "description": "LangChain framework",
            "primary_language": "Python",
            "topics": ["framework", "ai"],
            "stargazer_count": 60000,
            "fork_count": 8000,
            "url": "https://github.com/langchain-ai/langchain",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "Organization",
            "organization": "langchain-ai",
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "LangChain framework",
            "categories": ["ai"],
            "features": [],
            "use_cases": []
        },
    ]

    for repo_data in test_repos:
        await db.add_repository(repo_data)

    return test_repos


async def setup_graph_edges(db):
    """Create test graph edges for testing."""
    import json

    edges = [
        {
            "source_repo": "anthropic/claude-docs",
            "target_repo": "anthropic/claude-python",
            "edge_type": "author",
            "weight": 1.0,
            "metadata": json.dumps({"relationship": "same organization"})
        },
        {
            "source_repo": "anthropic/claude-docs",
            "target_repo": "openai/openai-python",
            "edge_type": "ecosystem",
            "weight": 0.8,
            "metadata": json.dumps({"language": "Python", "topic": "ai"})
        },
        {
            "source_repo": "anthropic/claude-docs",
            "target_repo": "langchain-ai/langchain",
            "edge_type": "ecosystem",
            "weight": 0.7,
            "metadata": json.dumps({"language": "Python", "topic": "ai"})
        },
    ]

    for edge in edges:
        await db.add_graph_edge(
            source_repo=edge["source_repo"],
            target_repo=edge["target_repo"],
            edge_type=edge["edge_type"],
            weight=edge["weight"],
            metadata=edge["metadata"]
        )


# ============================================================================
# Hybrid Recommendation Flow Tests
# ============================================================================

class TestHybridRecommendationFlow:
    """Integration tests for complete hybrid recommendation flow."""

    @pytest.mark.asyncio
    async def test_hybrid_recommendation_flow_with_semantic(self, integration_db):
        """Test complete recommendation flow including semantic similarity."""
        from src.services.hybrid_recommendation import HybridRecommendationService

        # Step 1: Setup test repositories
        await setup_test_repos_with_semantic_edges(integration_db)

        # Step 2: Setup graph edges
        await setup_graph_edges(integration_db)

        # Step 3: Mock semantic search
        mock_semantic = AsyncMock()
        mock_semantic.get_similar_repos.return_value = [
            {
                "name_with_owner": "openai/openai-python",
                "score": 0.85
            },
            {
                "name_with_owner": "langchain-ai/langchain",
                "score": 0.75
            }
        ]

        # Step 4: Create hybrid recommendation service
        service = HybridRecommendationService(integration_db, mock_semantic)

        # Step 5: Get recommendations
        recommendations = await service.get_recommendations(
            repo_name="anthropic/claude-docs",
            limit=5,
            include_semantic=True
        )

        # Step 6: Verify results
        assert len(recommendations) > 0

        # Check first recommendation structure
        rec = recommendations[0]
        assert "name_with_owner" in rec
        assert "final_score" in rec
        assert "sources" in rec
        assert "graph_score" in rec
        assert "semantic_score" in rec

        # Verify that both graph and semantic sources are used
        assert any("author" in s or "ecosystem" in s for s in rec["sources"])
        assert any("semantic" in s for s in rec["sources"])

    @pytest.mark.asyncio
    async def test_hybrid_recommendation_flow_without_semantic(self, integration_db):
        """Test recommendation flow with only graph edges (no semantic)."""
        from src.services.hybrid_recommendation import HybridRecommendationService

        # Setup test data
        await setup_test_repos_with_semantic_edges(integration_db)
        await setup_graph_edges(integration_db)

        # Create service without semantic search
        service = HybridRecommendationService(integration_db, semantic_search=None)

        # Get recommendations
        recommendations = await service.get_recommendations(
            repo_name="anthropic/claude-docs",
            limit=5,
            include_semantic=False
        )

        # Verify results
        assert len(recommendations) > 0

        # Check that only graph sources are used
        for rec in recommendations:
            assert "graph_score" in rec
            assert rec["semantic_score"] is None
            assert "semantic" not in rec["sources"]

    @pytest.mark.asyncio
    async def test_hybrid_recommendation_exclude_repos(self, integration_db):
        """Test recommendation flow with excluded repositories."""
        from src.services.hybrid_recommendation import HybridRecommendationService

        # Setup test data
        await setup_test_repos_with_semantic_edges(integration_db)
        await setup_graph_edges(integration_db)

        # Create service
        service = HybridRecommendationService(integration_db, semantic_search=None)

        # Get recommendations with exclusions
        recommendations = await service.get_recommendations(
            repo_name="anthropic/claude-docs",
            limit=10,
            include_semantic=False,
            exclude_repos={"anthropic/claude-python"}
        )

        # Verify excluded repo is not in results
        repo_names = [rec["name_with_owner"] for rec in recommendations]
        assert "anthropic/claude-python" not in repo_names

    @pytest.mark.asyncio
    async def test_hybrid_recommendation_diversity_optimization(self, integration_db):
        """Test that diversity optimization limits same-author repos."""
        from src.services.hybrid_recommendation import HybridRecommendationService

        # Add source repository first
        await integration_db.add_repository({
            "name_with_owner": "source/repo",
            "name": "repo",
            "owner": "source",
            "description": "Source repository",
            "primary_language": "Python",
            "topics": [],
            "stargazer_count": 100,
            "fork_count": 10,
            "url": "https://github.com/source/repo",
            "homepage_url": None,
            "pushed_at": "2024-01-01T00:00:00Z",
            "archived": False,
            "visibility": "public",
            "owner_type": "User",
            "organization": None,
            "starred_at": "2024-01-01T00:00:00Z",
            "last_synced_at": datetime.now().isoformat(),
            "summary": "Source repo",
            "categories": [],
            "features": [],
            "use_cases": []
        })

        # Setup test data with multiple repos from same author
        test_repos = [
            {
                "name_with_owner": "author/repo1",
                "name": "repo1",
                "owner": "author",
                "description": "Repo 1",
                "primary_language": "Python",
                "topics": [],
                "stargazer_count": 100,
                "fork_count": 10,
                "url": "https://github.com/author/repo1",
                "homepage_url": None,
                "pushed_at": "2024-01-01T00:00:00Z",
                "archived": False,
                "visibility": "public",
                "owner_type": "User",
                "organization": None,
                "starred_at": "2024-01-01T00:00:00Z",
                "last_synced_at": datetime.now().isoformat(),
                "summary": "Repo 1",
                "categories": [],
                "features": [],
                "use_cases": []
            },
            {
                "name_with_owner": "author/repo2",
                "name": "repo2",
                "owner": "author",
                "description": "Repo 2",
                "primary_language": "Python",
                "topics": [],
                "stargazer_count": 90,
                "fork_count": 9,
                "url": "https://github.com/author/repo2",
                "homepage_url": None,
                "pushed_at": "2024-01-01T00:00:00Z",
                "archived": False,
                "visibility": "public",
                "owner_type": "User",
                "organization": None,
                "starred_at": "2024-01-01T00:00:00Z",
                "last_synced_at": datetime.now().isoformat(),
                "summary": "Repo 2",
                "categories": [],
                "features": [],
                "use_cases": []
            },
            {
                "name_with_owner": "author/repo3",
                "name": "repo3",
                "owner": "author",
                "description": "Repo 3",
                "primary_language": "Python",
                "topics": [],
                "stargazer_count": 80,
                "fork_count": 8,
                "url": "https://github.com/author/repo3",
                "homepage_url": None,
                "pushed_at": "2024-01-01T00:00:00Z",
                "archived": False,
                "visibility": "public",
                "owner_type": "User",
                "organization": None,
                "starred_at": "2024-01-01T00:00:00Z",
                "last_synced_at": datetime.now().isoformat(),
                "summary": "Repo 3",
                "categories": [],
                "features": [],
                "use_cases": []
            },
        ]

        for repo_data in test_repos:
            await integration_db.add_repository(repo_data)

        # Create edges from a source repo
        await integration_db.add_graph_edge(
            source_repo="source/repo",
            target_repo="author/repo1",
            edge_type="author",
            weight=1.0,
            metadata=None
        )
        await integration_db.add_graph_edge(
            source_repo="source/repo",
            target_repo="author/repo2",
            edge_type="author",
            weight=0.9,
            metadata=None
        )
        await integration_db.add_graph_edge(
            source_repo="source/repo",
            target_repo="author/repo3",
            edge_type="author",
            weight=0.8,
            metadata=None
        )

        # Create service
        service = HybridRecommendationService(integration_db, semantic_search=None)

        # Get recommendations
        recommendations = await service.get_recommendations(
            repo_name="source/repo",
            limit=10,
            include_semantic=False
        )

        # Count repos from same author
        author_count = sum(1 for rec in recommendations if rec["owner"] == "author")

        # Should limit to max 2 repos per author
        assert author_count <= 2


# ============================================================================
# Recommendation API Integration Tests
# ============================================================================

class TestRecommendationAPIIntegration:
    """Integration tests for recommendation API endpoints."""

    @pytest.mark.asyncio
    async def test_recommendation_api_integration(self, integration_client, integration_db):
        """Test recommendation API endpoint with real data."""
        # Setup test data
        await setup_test_repos_with_semantic_edges(integration_db)
        await setup_graph_edges(integration_db)

        # Mock semantic search in app
        from src.api import app as api_app
        from src.services.hybrid_recommendation import HybridRecommendationService

        mock_semantic = AsyncMock()
        mock_semantic.get_similar_repos.return_value = [
            {
                "name_with_owner": "openai/openai-python",
                "score": 0.85
            }
        ]

        # Create service instance
        hybrid_service = HybridRecommendationService(integration_db, mock_semantic)

        # Patch both the service and db in app
        with patch.object(api_app, 'hybrid_recommendation_service', hybrid_service), \
             patch.object(api_app, 'db', integration_db):

            # Call API
            response = await integration_client.get(
                "/api/recommendations/anthropic/claude-docs?limit=5&include_semantic=true"
            )

            assert response.status_code == 200

            recommendations = response.json()
            assert isinstance(recommendations, list)

            if len(recommendations) > 0:
                rec = recommendations[0]
                assert "name_with_owner" in rec
                assert "name" in rec
                assert "owner" in rec
                assert "description" in rec
                assert "final_score" in rec
                assert "sources" in rec
                assert "graph_score" in rec
                assert "semantic_score" in rec

    @pytest.mark.asyncio
    async def test_recommendation_api_without_semantic(self, integration_client, integration_db):
        """Test recommendation API with semantic disabled."""
        # Setup test data
        await setup_test_repos_with_semantic_edges(integration_db)
        await setup_graph_edges(integration_db)

        # Mock semantic search as None (disabled)
        from src.api import app as api_app

        with patch.object(api_app, 'hybrid_recommendation_service', None):
            # Call API - should return 503
            response = await integration_client.get(
                "/api/recommendations/anthropic/claude-docs"
            )

            assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_recommendation_api_exclude_repos_parameter(self, integration_client, integration_db):
        """Test recommendation API with exclude_repos parameter."""
        # Setup test data
        await setup_test_repos_with_semantic_edges(integration_db)
        await setup_graph_edges(integration_db)

        # Mock service
        from src.api import app as api_app
        from src.services.hybrid_recommendation import HybridRecommendationService

        service = HybridRecommendationService(integration_db, semantic_search=None)

        with patch.object(api_app, 'hybrid_recommendation_service', service), \
             patch.object(api_app, 'db', integration_db):

            # Call API with exclude parameter
            response = await integration_client.get(
                "/api/recommendations/anthropic/claude-docs?exclude_repos=anthropic/claude-python,openai/openai-python"
            )

            assert response.status_code == 200

            recommendations = response.json()
            repo_names = [rec["name_with_owner"] for rec in recommendations]

            # Verify excluded repos are not in results
            assert "anthropic/claude-python" not in repo_names
            assert "openai/openai-python" not in repo_names


# ============================================================================
# Semantic Edge Rebuild API Tests
# ============================================================================

class TestSemanticEdgeRebuildAPI:
    """Integration tests for semantic edge rebuild API."""

    @pytest.mark.asyncio
    async def test_semantic_edge_rebuild_api(self, integration_client, integration_db):
        """Test semantic edge rebuild API endpoint."""
        # Setup test repositories
        await setup_test_repos_with_semantic_edges(integration_db)

        # Mock semantic edge discovery
        from src.api import app as api_app

        mock_discovery = AsyncMock()
        mock_discovery.discover_and_store_edges.return_value = {
            "repos_processed": 4,
            "edges_created": 8
        }

        with patch.object(api_app, 'semantic_edge_discovery', mock_discovery):
            # Call rebuild API
            response = await integration_client.post(
                "/api/graph/semantic-edges/rebuild?top_k=10&min_similarity=0.6"
            )

            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "background_task_started"
            assert "message" in data
            assert data["parameters"]["top_k"] == 10
            assert data["parameters"]["min_similarity"] == 0.6

    @pytest.mark.asyncio
    async def test_semantic_edge_rebuild_api_not_configured(self, integration_client):
        """Test semantic edge rebuild when semantic search is not configured."""
        # Mock semantic edge discovery as None
        from src.api import app as api_app

        with patch.object(api_app, 'semantic_edge_discovery', None):
            # Call rebuild API - should return 503
            response = await integration_client.post(
                "/api/graph/semantic-edges/rebuild"
            )

            assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_semantic_edge_rebuild_api_validation(self, integration_client, integration_db):
        """Test semantic edge rebuild API parameter validation."""
        # Setup test repositories
        await setup_test_repos_with_semantic_edges(integration_db)

        # Mock semantic edge discovery
        from src.api import app as api_app

        mock_discovery = AsyncMock()
        mock_discovery.discover_and_store_edges.return_value = {
            "repos_processed": 4,
            "edges_created": 8
        }

        with patch.object(api_app, 'semantic_edge_discovery', mock_discovery):
            # Test with top_k out of range (should fail validation)
            response = await integration_client.post(
                "/api/graph/semantic-edges/rebuild?top_k=100"
            )

            # FastAPI validation should reject this
            assert response.status_code == 422

            # Test with min_similarity out of range
            response = await integration_client.post(
                "/api/graph/semantic-edges/rebuild?min_similarity=1.5"
            )

            # FastAPI validation should reject this
            assert response.status_code == 422
