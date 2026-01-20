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
async def test_semantic_search_update_repository():
    """Test updating a single repository in vector store."""
    with patch('src.vector.semantic.chromadb.PersistentClient'):
        semantic = SemanticSearch()

        # Mock collection
        semantic.collection = MagicMock()
        semantic.collection.delete = MagicMock()
        semantic.collection.add = MagicMock()

        repo = {
            "name_with_owner": "test/repo1",
            "name": "repo1",
            "description": "Updated test repo",
            "primary_language": "Python",
            "url": "https://github.com/test/repo1",
            "topics": ["test", "updated"]
        }

        with patch.object(semantic, 'embedder') as mock_embedder:
            mock_embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

            await semantic.update_repository(repo)

            # Should have called delete and then add
            assert semantic.collection.delete.called
            semantic.collection.delete.assert_called_once_with(ids=["test/repo1"])


@pytest.mark.asyncio
async def test_semantic_search_update_repository_empty():
    """Test updating with empty repo does nothing."""
    with patch('src.vector.semantic.chromadb.PersistentClient'):
        semantic = SemanticSearch()

        # Mock collection
        semantic.collection = MagicMock()
        semantic.collection.delete = MagicMock()

        await semantic.update_repository({})

        # Should not have called delete
        assert not semantic.collection.delete.called


@pytest.mark.asyncio
async def test_semantic_search_delete_repository():
    """Test deleting a repository from vector store."""
    with patch('src.vector.semantic.chromadb.PersistentClient'):
        semantic = SemanticSearch()

        # Mock collection
        semantic.collection = MagicMock()
        semantic.collection.delete = MagicMock()

        await semantic.delete_repository("test/repo1")

        # Should have called delete
        assert semantic.collection.delete.called
        semantic.collection.delete.assert_called_once_with(ids=["test/repo1"])


@pytest.mark.asyncio
async def test_semantic_search_delete_repository_empty():
    """Test deleting with empty name does nothing."""
    with patch('src.vector.semantic.chromadb.PersistentClient'):
        semantic = SemanticSearch()

        # Mock collection
        semantic.collection = MagicMock()
        semantic.collection.delete = MagicMock()

        await semantic.delete_repository("")

        # Should not have called delete
        assert not semantic.collection.delete.called


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
