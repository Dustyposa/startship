"""Unit tests for ChromaDB vector store."""

import pytest
import tempfile
import shutil
from src.vector.chroma_store import ChromaDBStore


@pytest.fixture
def temp_store():
    """Create temporary ChromaDB store."""
    temp_dir = tempfile.mkdtemp()
    store = ChromaDBStore(persist_path=temp_dir)
    yield store
    shutil.rmtree(temp_dir)


def test_add_repository(temp_store):
    """Test adding repository vector."""
    repo_id = "test/repo"
    text = "Test repository description"
    embedding = [0.1] * 768
    metadata = {"language": "Python", "stars": 100}

    temp_store.add(repo_id, text, embedding, metadata)

    # Verify addition succeeded
    results = temp_store.search(embedding, top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == repo_id


def test_search_returns_empty_when_no_data(temp_store):
    """Test search on empty database."""
    results = temp_store.search([0.1] * 768, top_k=5)
    assert results == []


def test_delete_repository(temp_store):
    """Test deleting repository."""
    repo_id = "test/repo"
    temp_store.add(repo_id, "test", [0.1] * 768, {"deleted": False})

    temp_store.delete(repo_id)

    results = temp_store.search([0.1] * 768, top_k=5)
    assert results == []


def test_add_batch(temp_store):
    """Test batch addition of repositories."""
    repo_ids = ["user/repo1", "user/repo2", "user/repo3"]
    texts = ["Description 1", "Description 2", "Description 3"]
    embeddings = [[0.1] * 768, [0.2] * 768, [0.3] * 768]
    metadata_list = [
        {"language": "Python"},
        {"language": "JavaScript"},
        {"language": "Go"}
    ]

    count = temp_store.add_batch(repo_ids, texts, embeddings, metadata_list)

    assert count == 3
    assert temp_store.get_count() == 3


def test_get_count(temp_store):
    """Test getting vector count."""
    assert temp_store.get_count() == 0

    temp_store.add("user/repo", "test", [0.1] * 768, {"test": True})
    assert temp_store.get_count() == 1


def test_clear(temp_store):
    """Test clearing all data."""
    temp_store.add("user/repo1", "test1", [0.1] * 768, {"id": 1})
    temp_store.add("user/repo2", "test2", [0.2] * 768, {"id": 2})
    assert temp_store.get_count() == 2

    temp_store.clear()
    assert temp_store.get_count() == 0


def test_search_with_metadata_filter(temp_store):
    """Test search with metadata filtering."""
    temp_store.add("user/repo1", "Python project", [0.1] * 768, {"language": "Python"})
    temp_store.add("user/repo2", "JS project", [0.2] * 768, {"language": "JavaScript"})

    # Search for Python only
    results = temp_store.search([0.1] * 768, top_k=10, where={"language": "Python"})

    assert len(results) == 1
    assert results[0]["id"] == "user/repo1"


def test_search_returns_metadata(temp_store):
    """Test that search results include metadata."""
    metadata = {"language": "Python", "stars": 100}
    temp_store.add("user/repo", "Test repo", [0.1] * 768, metadata)

    results = temp_store.search([0.1] * 768, top_k=1)

    assert len(results) == 1
    assert results[0]["metadata"] == metadata
