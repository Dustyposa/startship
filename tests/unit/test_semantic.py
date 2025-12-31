"""Tests for semantic search."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.vector.semantic import SemanticSearch


@pytest.mark.asyncio
async def test_semantic_search_add_repos():
    with patch('src.vector.semantic.chromadb.PersistentClient'):
        semantic = SemanticSearch()

        # Mock collection
        semantic.collection = MagicMock()
        semantic.collection.add = MagicMock()

        repos = [
            {
                "name_with_owner": "test/repo1",
                "name": "repo1",
                "description": "A test repo",
                "primary_language": "Python",
                "url": "https://github.com/test/repo1",
                "topics": ["test"]
            }
        ]

        with patch.object(semantic, 'embedder') as mock_embedder:
            mock_embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

            await semantic.add_repositories(repos)

            assert semantic.collection.add.called


@pytest.mark.asyncio
async def test_repo_to_text():
    semantic = SemanticSearch()
    repo = {
        "name": "test-repo",
        "description": "A test repository",
        "topics": ["python", "api"]
    }

    text = semantic._repo_to_text(repo)

    assert "test-repo" in text
    assert "A test repository" in text
    assert "python" in text
    assert "api" in text


def test_repo_to_text_empty():
    semantic = SemanticSearch()
    repo = {
        "name": "test",
        "description": None,
        "topics": []
    }

    text = semantic._repo_to_text(repo)

    assert "test" in text
