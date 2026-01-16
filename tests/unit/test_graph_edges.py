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


class TestDiscoverEcosystemEdges:
    """Test suite for EdgeDiscoveryService.discover_ecosystem_edges method."""

    @pytest.mark.asyncio
    async def test_discover_language_edges_basic(self):
        """Test basic edge discovery with repos sharing same language."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1", "primary_language": "Python"},
            {"name_with_owner": "owner/repo2", "primary_language": "Python"},
            {"name_with_owner": "owner/repo3", "primary_language": "JavaScript"}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should create 1 edge for the 2 Python repos
        assert len(edges) == 1
        assert edges[0]["source"] == "owner/repo1"
        assert edges[0]["target"] == "owner/repo2"
        assert edges[0]["type"] == "ecosystem"
        assert edges[0]["weight"] == 0.6
        assert isinstance(edges[0]["metadata"], dict)
        assert edges[0]["metadata"]["language"] == "Python"

    @pytest.mark.asyncio
    async def test_discover_topic_edges_jaccard(self):
        """Test topic-based edge discovery with Jaccard similarity."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1", "topics": ["web", "api", "rest"]},
            {"name_with_owner": "owner/repo2", "topics": ["web", "api", "graphql"]},
            {"name_with_owner": "owner/repo3", "topics": ["database", "sql"]}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # repo1 and repo2 share 2 topics (web, api) out of 4 unique (web, api, rest, graphql)
        # Jaccard = 2/4 = 0.5, which is > 0.3 threshold
        assert len(edges) == 1
        assert edges[0]["source"] == "owner/repo1"
        assert edges[0]["target"] == "owner/repo2"
        assert edges[0]["type"] == "ecosystem"
        assert edges[0]["weight"] == 0.5
        assert edges[0]["metadata"]["common_topics"] == 2

    @pytest.mark.asyncio
    async def test_empty_input_list(self):
        """Test with empty input list."""
        service = EdgeDiscoveryService()
        edges = await service.discover_ecosystem_edges([])

        assert edges == []

    @pytest.mark.asyncio
    async def test_single_repository(self):
        """Test with single repository (no edges possible)."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1", "primary_language": "Python"}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        assert edges == []

    @pytest.mark.asyncio
    async def test_missing_name_with_owner(self):
        """Test with repositories missing name_with_owner field."""
        service = EdgeDiscoveryService()

        repos = [
            {"primary_language": "Python"},  # Missing name_with_owner
            {"name_with_owner": "owner/repo2", "primary_language": "Python"}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should skip the repo without name_with_owner
        assert edges == []

    @pytest.mark.asyncio
    async def test_empty_name_with_owner(self):
        """Test with repositories having empty name_with_owner field."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "", "primary_language": "Python"},
            {"name_with_owner": "owner/repo2", "primary_language": "Python"}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should skip the repo with empty name_with_owner
        assert edges == []

    @pytest.mark.asyncio
    async def test_invalid_name_with_owner_format(self):
        """Test with repositories having invalid name_with_owner format (missing slash)."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "invalid-format", "primary_language": "Python"},
            {"name_with_owner": "owner/repo2", "primary_language": "Python"}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should skip the repo with invalid format
        assert edges == []

    @pytest.mark.asyncio
    async def test_no_common_language_or_topics(self):
        """Test with repos that have no common language or topics."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1", "primary_language": "Python", "topics": ["web"]},
            {"name_with_owner": "owner/repo2", "primary_language": "JavaScript", "topics": ["database"]}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # No common language or topics, so no edges
        assert edges == []

    @pytest.mark.asyncio
    async def test_popular_language_no_edges(self):
        """Test that popular languages (50+ repos) don't create edges."""
        service = EdgeDiscoveryService()

        # Create 51 repos with Python language (simulating popular language)
        repos = [
            {"name_with_owner": f"owner/repo{i}", "primary_language": "Python"}
            for i in range(51)
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should not create edges for popular languages
        assert len(edges) == 0

    @pytest.mark.asyncio
    async def test_language_limit_per_language(self):
        """Test that only 20 repos per language are considered for edges."""
        service = EdgeDiscoveryService()

        # Create 25 repos with Rust language (less than 50, more than 20)
        repos = [
            {"name_with_owner": f"owner/repo{i}", "primary_language": "Rust"}
            for i in range(25)
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should create edges for first 20 repos only
        # C(20, 2) = 190 edges
        assert len(edges) == 190

    @pytest.mark.asyncio
    async def test_insufficient_common_topics(self):
        """Test that repos with less than 2 common topics don't create edges."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1", "topics": ["web", "api"]},
            {"name_with_owner": "owner/repo2", "topics": ["web", "database"]}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Only 1 common topic (web), so no edge
        assert len(edges) == 0

    @pytest.mark.asyncio
    async def test_jaccard_threshold(self):
        """Test that Jaccard similarity below 0.3 doesn't create edges."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1", "topics": ["web", "api", "rest", "graphql", "database", "cache", "auth"]},
            {"name_with_owner": "owner/repo2", "topics": ["web", "api", "mobile", "ios", "android", "react", "vue"]}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # 2 common topics out of 12 unique: Jaccard = 2/12 = 0.167 < 0.3
        assert len(edges) == 0

    @pytest.mark.asyncio
    async def test_metadata_format_is_dict(self):
        """Test that metadata is returned as a dictionary, not a string."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1", "primary_language": "Python"},
            {"name_with_owner": "owner/repo2", "primary_language": "Python"}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        assert isinstance(edges[0]["metadata"], dict)
        assert "language" in edges[0]["metadata"]
        assert edges[0]["metadata"]["language"] == "Python"
        # Ensure it's not a JSON string
        assert not isinstance(edges[0]["metadata"], str)

    @pytest.mark.asyncio
    async def test_non_dict_repo_items(self):
        """Test with non-dict items in the repos list."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1", "primary_language": "Python"},
            "not a dict",  # Invalid item
            {"name_with_owner": "owner/repo2", "primary_language": "Python"}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should skip the invalid item and create edge from valid repos
        assert len(edges) == 1
        assert edges[0]["source"] == "owner/repo1"
        assert edges[0]["target"] == "owner/repo2"

    @pytest.mark.asyncio
    async def test_invalid_input_type(self):
        """Test with invalid input type (not a list)."""
        service = EdgeDiscoveryService()

        with pytest.raises(ValueError, match="repos must be a list"):
            await service.discover_ecosystem_edges("not a list")

        with pytest.raises(ValueError, match="repos must be a list"):
            await service.discover_ecosystem_edges(None)

        with pytest.raises(ValueError, match="repos must be a list"):
            await service.discover_ecosystem_edges({})

    @pytest.mark.asyncio
    async def test_empty_topics_list(self):
        """Test with repos having empty topics lists."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1", "topics": []},
            {"name_with_owner": "owner/repo2", "topics": []},
            {"name_with_owner": "owner/repo3", "topics": ["web"]}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # No edges from empty topics
        assert len(edges) == 0

    @pytest.mark.asyncio
    async def test_missing_topics_field(self):
        """Test with repos missing topics field."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1"},  # Missing topics
            {"name_with_owner": "owner/repo2", "topics": ["web"]}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should handle missing topics gracefully
        assert len(edges) == 0

    @pytest.mark.asyncio
    async def test_non_list_topics_field(self):
        """Test with repos having non-list topics field."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1", "topics": "not-a-list"},
            {"name_with_owner": "owner/repo2", "topics": ["web"]}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should convert non-list topics to empty list
        assert len(edges) == 0

    @pytest.mark.asyncio
    async def test_missing_primary_language(self):
        """Test with repos missing primary_language field."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1"},  # Missing primary_language
            {"name_with_owner": "owner/repo2", "primary_language": "Python"}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should handle missing language gracefully
        assert len(edges) == 0

    @pytest.mark.asyncio
    async def test_empty_primary_language(self):
        """Test with repos having empty primary_language field."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1", "primary_language": ""},
            {"name_with_owner": "owner/repo2", "primary_language": ""}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should skip repos with empty language
        assert len(edges) == 0

    @pytest.mark.asyncio
    async def test_combined_language_and_topic_edges(self):
        """Test that both language and topic edges can be created."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "owner/repo1", "primary_language": "Rust", "topics": ["web", "api", "async"]},
            {"name_with_owner": "owner/repo2", "primary_language": "Rust", "topics": ["web", "api", "graphql"]},
            {"name_with_owner": "owner/repo3", "primary_language": "Rust", "topics": ["database", "sql"]}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should create:
        # - 3 language edges (3 choose 2 = 3)
        # - 1 topic edge between repo1 and repo2
        assert len(edges) == 4

        # Check language edges
        lang_edges = [e for e in edges if "language" in e["metadata"]]
        assert len(lang_edges) == 3

        # Check topic edge
        topic_edges = [e for e in edges if "common_topics" in e["metadata"]]
        assert len(topic_edges) == 1
        assert topic_edges[0]["metadata"]["common_topics"] == 2

    @pytest.mark.asyncio
    async def test_name_with_owner_with_whitespace(self):
        """Test that name_with_owner values are properly trimmed."""
        service = EdgeDiscoveryService()

        repos = [
            {"name_with_owner": "  owner/repo1  ", "primary_language": "Python"},
            {"name_with_owner": "owner/repo2", "primary_language": "Python"}
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should trim whitespace and create edge
        assert len(edges) == 1
        assert edges[0]["source"] == "owner/repo1"
        assert edges[0]["target"] == "owner/repo2"

    @pytest.mark.asyncio
    async def test_all_repos_skipped(self):
        """Test when all repos are invalid and should be skipped."""
        service = EdgeDiscoveryService()

        repos = [
            {"primary_language": "Python"},  # Missing name_with_owner
            {"name_with_owner": ""},  # Empty name_with_owner
            {"name_with_owner": "invalid-format"},  # Invalid format
        ]

        edges = await service.discover_ecosystem_edges(repos)

        # Should skip all repos and return empty list
        assert edges == []
