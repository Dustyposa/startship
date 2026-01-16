# tests/unit/test_graph_edges.py
import pytest
from src.services.graph.edges import EdgeDiscoveryService


class TestDiscoverAuthorEdges:
    """Test suite for EdgeDiscoveryService.discover_author_edges method."""

    @pytest.mark.asyncio
    async def test_discover_author_edges_basic(self):
        """Test basic edge discovery with multiple repos from same owner."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "tiangolo/fastapi", "owner": "tiangolo"},
            {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"},
            {"name_with_owner": "python/cpython", "owner": "python"}
        ]

        edges = await service.discover_author_edges(repos)

        assert len(edges) == 1
        assert edges[0]["source"] == "tiangolo/fastapi"
        assert edges[0]["target"] == "tiangolo/typer"
        assert edges[0]["type"] == "author"
        assert edges[0]["weight"] == 1.0
        assert isinstance(edges[0]["metadata"], dict)
        assert edges[0]["metadata"]["author"] == "tiangolo"

    @pytest.mark.asyncio
    async def test_empty_input_list(self):
        """Test with empty input list."""
        service = EdgeDiscoveryService()
        edges = await service.discover_author_edges([])

        assert edges == []

    @pytest.mark.asyncio
    async def test_single_repository(self):
        """Test with single repository (no edges possible)."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "tiangolo/fastapi", "owner": "tiangolo"}
        ]

        edges = await service.discover_author_edges(repos)

        assert edges == []

    @pytest.mark.asyncio
    async def test_missing_owner_field(self):
        """Test with repositories missing owner field."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "tiangolo/fastapi"},  # Missing owner
            {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"}
        ]

        edges = await service.discover_author_edges(repos)

        # Should skip the repo without owner and create no edges
        # (only one repo has valid owner)
        assert edges == []

    @pytest.mark.asyncio
    async def test_empty_owner_field(self):
        """Test with repositories having empty owner field."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "tiangolo/fastapi", "owner": ""},  # Empty owner
            {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"}
        ]

        edges = await service.discover_author_edges(repos)

        # Should skip the repo with empty owner
        assert edges == []

    @pytest.mark.asyncio
    async def test_whitespace_only_owner(self):
        """Test with repositories having whitespace-only owner."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "tiangolo/fastapi", "owner": "   "},  # Whitespace only
            {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"}
        ]

        edges = await service.discover_author_edges(repos)

        # Should skip the repo with whitespace-only owner
        assert edges == []

    @pytest.mark.asyncio
    async def test_missing_name_with_owner(self):
        """Test with repositories missing name_with_owner field."""
        service = EdgeDiscoveryService()

        repos = [
            {"owner": "tiangolo"},  # Missing name_with_owner
            {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"}
        ]

        edges = await service.discover_author_edges(repos)

        # Should skip the repo without name_with_owner
        assert edges == []

    @pytest.mark.asyncio
    async def test_empty_name_with_owner(self):
        """Test with repositories having empty name_with_owner field."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "", "owner": "tiangolo"},  # Empty name_with_owner
            {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"}
        ]

        edges = await service.discover_author_edges(repos)

        # Should skip the repo with empty name_with_owner
        assert edges == []

    @pytest.mark.asyncio
    async def test_invalid_name_with_owner_format(self):
        """Test with repositories having invalid name_with_owner format (missing slash)."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "invalid-format", "owner": "tiangolo"},  # No slash
            {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"}
        ]

        edges = await service.discover_author_edges(repos)

        # Should skip the repo with invalid format
        assert edges == []

    @pytest.mark.asyncio
    async def test_multiple_owners(self):
        """Test with repositories from multiple owners."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "tiangolo/fastapi", "owner": "tiangolo"},
            {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"},
            {"name_with_owner": "python/cpython", "owner": "python"},
            {"name_with_owner": "python/pypi", "owner": "python"}
        ]

        edges = await service.discover_author_edges(repos)

        # Should create 2 edges (1 for tiangolo, 1 for python)
        assert len(edges) == 2

        # Check tiangolo edge
        tiangolo_edges = [e for e in edges if e["metadata"]["author"] == "tiangolo"]
        assert len(tiangolo_edges) == 1
        assert tiangolo_edges[0]["source"] == "tiangolo/fastapi"
        assert tiangolo_edges[0]["target"] == "tiangolo/typer"

        # Check python edge
        python_edges = [e for e in edges if e["metadata"]["author"] == "python"]
        assert len(python_edges) == 1
        assert python_edges[0]["source"] == "python/cpython"
        assert python_edges[0]["target"] == "python/pypi"

    @pytest.mark.asyncio
    async def test_metadata_format_is_dict(self):
        """Test that metadata is returned as a dictionary, not a string."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "tiangolo/fastapi", "owner": "tiangolo"},
            {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"}
        ]

        edges = await service.discover_author_edges(repos)

        assert isinstance(edges[0]["metadata"], dict)
        assert "author" in edges[0]["metadata"]
        assert edges[0]["metadata"]["author"] == "tiangolo"
        # Ensure it's not a JSON string
        assert not isinstance(edges[0]["metadata"], str)

    @pytest.mark.asyncio
    async def test_three_repos_same_owner(self):
        """Test with three repos from same owner (should create 3 edges)."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "tiangolo/fastapi", "owner": "tiangolo"},
            {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"},
            {"name_with_owner": "tiangolo/sqlmodel", "owner": "tiangolo"}
        ]

        edges = await service.discover_author_edges(repos)

        # Should create 3 edges: (fastapi, typer), (fastapi, sqlmodel), (typer, sqlmodel)
        assert len(edges) == 3

        edge_pairs = {(e["source"], e["target"]) for e in edges}
        expected_pairs = {
            ("tiangolo/fastapi", "tiangolo/typer"),
            ("tiangolo/fastapi", "tiangolo/sqlmodel"),
            ("tiangolo/typer", "tiangolo/sqlmodel")
        }
        assert edge_pairs == expected_pairs

    @pytest.mark.asyncio
    async def test_non_dict_repo_items(self):
        """Test with non-dict items in the repos list."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "tiangolo/fastapi", "owner": "tiangolo"},
            "not a dict",  # Invalid item
            {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"}
        ]

        edges = await service.discover_author_edges(repos)

        # Should skip the invalid item and create edge from valid repos
        assert len(edges) == 1
        assert edges[0]["source"] == "tiangolo/fastapi"
        assert edges[0]["target"] == "tiangolo/typer"

    @pytest.mark.asyncio
    async def test_invalid_input_type(self):
        """Test with invalid input type (not a list)."""
        service = EdgeDiscoveryService()

        with pytest.raises(ValueError, match="repos must be a list"):
            await service.discover_author_edges("not a list")

        with pytest.raises(ValueError, match="repos must be a list"):
            await service.discover_author_edges(None)

        with pytest.raises(ValueError, match="repos must be a list"):
            await service.discover_author_edges({})

    @pytest.mark.asyncio
    async def test_owner_with_whitespace(self):
        """Test that owner names are properly trimmed."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "tiangolo/fastapi", "owner": "  tiangolo  "},
            {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"}
        ]

        edges = await service.discover_author_edges(repos)

        # Should trim whitespace and treat as same owner
        assert len(edges) == 1
        assert edges[0]["metadata"]["author"] == "tiangolo"

    @pytest.mark.asyncio
    async def test_name_with_owner_with_whitespace(self):
        """Test that name_with_owner values are properly trimmed."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "  tiangolo/fastapi  ", "owner": "tiangolo"},
            {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"}
        ]

        edges = await service.discover_author_edges(repos)

        # Should trim whitespace and create edge
        assert len(edges) == 1
        assert edges[0]["source"] == "tiangolo/fastapi"
        assert edges[0]["target"] == "tiangolo/typer"

    @pytest.mark.asyncio
    async def test_all_repos_skipped(self):
        """Test when all repos are invalid and should be skipped."""
        service = EdgeDiscoveryService()

        repos = [
            {"owner": ""},  # Empty owner
            {"name_with_owner": ""},  # Empty name_with_owner
            {"owner": "test"},  # Missing name_with_owner
        ]

        edges = await service.discover_author_edges(repos)

        # Should skip all repos and return empty list
        assert edges == []
