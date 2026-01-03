import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.network import NetworkService

@pytest.mark.asyncio
async def test_calculate_category_similarity():
    db = MagicMock()

    service = NetworkService(db)

    # Test with shared categories
    repo_a = {"categories": ["AI", "ML"]}
    repo_b = {"categories": ["AI", "ML", "DL"]}

    similarity = await service.calculate_category_similarity(repo_a, repo_b)

    # Jaccard: |AI,ML| ∩ |AI,ML,DL| = 2
    #          |AI,ML| ∪ |AI,ML,DL| = 3
    #          = 2/3 = 0.666...
    assert abs(similarity - 0.666) < 0.01

@pytest.mark.asyncio
async def test_calculate_category_similarity_no_overlap():
    db = MagicMock()
    service = NetworkService(db)

    repo_a = {"categories": ["AI"]}
    repo_b = {"categories": ["Web"]}

    similarity = await service.calculate_category_similarity(repo_a, repo_b)

    assert similarity == 0.0

@pytest.mark.asyncio
async def test_calculate_semantic_similarity_with_chromadb():
    db = MagicMock()
    mock_semantic = MagicMock()
    mock_semantic.search = AsyncMock(return_value=[
        {"name_with_owner": "owner/repo1", "similarity_score": 0.8},
        {"name_with_owner": "owner/repo3", "similarity_score": 0.6}
    ])

    service = NetworkService(db, semantic=mock_semantic)

    repo_a = {"name_with_owner": "owner/repo1"}
    repo_b = {"name_with_owner": "owner/repo2"}

    similarity = await service.calculate_semantic_similarity(repo_a, repo_b)

    assert similarity == 0.8
    mock_semantic.search.assert_called_once()

@pytest.mark.asyncio
async def test_calculate_semantic_similarity_fallback():
    db = MagicMock()
    service = NetworkService(db, semantic=None)

    repo_a = {"name_with_owner": "owner/repo1"}
    repo_b = {"name_with_owner": "owner/repo2"}

    similarity = await service.calculate_semantic_similarity(repo_a, repo_b)

    # Should return 0.0 when semantic search not available
    assert similarity == 0.0

@pytest.mark.asyncio
async def test_calculate_combined_similarity():
    db = MagicMock()
    mock_semantic = MagicMock()
    mock_semantic.search = AsyncMock(return_value=[
        {"name_with_owner": "owner/repo1", "similarity_score": 0.6}
    ])

    service = NetworkService(db, semantic=mock_semantic)

    repo_a = {"name_with_owner": "owner/repo1", "categories": ["AI", "ML"]}
    repo_b = {"name_with_owner": "owner/repo2", "categories": ["AI", "ML", "DL"]}

    similarity = await service.calculate_similarity(repo_a, repo_b)

    # Category: 0.666, Semantic: 0.6
    # Combined: 0.5 * 0.666 + 0.5 * 0.6 = 0.633
    expected = 0.5 * 0.666 + 0.5 * 0.6
    assert abs(similarity - expected) < 0.01

@pytest.mark.asyncio
async def test_calculate_combined_similarity_no_semantic():
    db = MagicMock()
    service = NetworkService(db, semantic=None)

    repo_a = {"name_with_owner": "owner/repo1", "categories": ["AI"]}
    repo_b = {"name_with_owner": "owner/repo2", "categories": ["AI"]}

    similarity = await service.calculate_similarity(repo_a, repo_b)

    # Category: 1.0, Semantic: 0.0
    # When semantic is unavailable, return category score directly
    assert similarity == 1.0

@pytest.mark.asyncio
async def test_build_network_creates_nodes_and_edges():
    db = MagicMock()
    mock_cursor = MagicMock()

    # Mock database response - return 3 repos
    mock_rows = [
        ("owner/repo1", "Repo 1", 1000, '["AI"]', "Python"),
        ("owner/repo2", "Repo 2", 500, '["AI", "ML"]', "JavaScript"),
        ("owner/repo3", "Repo 3", 2000, '["Web"]', "TypeScript"),
    ]
    mock_cursor.fetchall = AsyncMock(return_value=mock_rows)
    db._connection.execute = AsyncMock(return_value=mock_cursor)

    service = NetworkService(db, semantic=None)

    network = await service.build_network(top_n=3, k=2)

    # Verify structure
    assert "nodes" in network
    assert "edges" in network
    assert len(network["nodes"]) == 3

    # Verify nodes have required fields
    node = network["nodes"][0]
    assert "id" in node
    assert "name" in node
    assert "size" in node
    assert "color" in node

@pytest.mark.asyncio
async def test_save_and_load_cached_network():
    db = MagicMock()

    service = NetworkService(db, semantic=None)

    network_data = {
        "nodes": [{"id": "test"}],
        "edges": [{"source": "a", "target": "b"}]
    }

    # Mock database execute and commit
    db._connection.execute = AsyncMock()
    db._connection.commit = AsyncMock()

    await service.save_network(network_data, top_n=100, k=5)

    # Verify execute was called once (atomic INSERT OR REPLACE)
    assert db._connection.execute.call_count == 1
    # Verify commit was called
    assert db._connection.commit.called

@pytest.mark.asyncio
async def test_get_cached_network():
    db = MagicMock()
    mock_cursor = MagicMock()

    # Mock cached data
    mock_cursor.fetchone = AsyncMock(return_value=(
        '[{"id": "test"}]',
        '[{"source": "a", "target": "b"}]'
    ))
    db._connection.execute = AsyncMock(return_value=mock_cursor)

    service = NetworkService(db, semantic=None)

    network = await service.get_cached_network()

    assert network["nodes"] == [{"id": "test"}]
    assert network["edges"] == [{"source": "a", "target": "b"}]

@pytest.mark.asyncio
async def test_get_cached_network_handles_corrupted_cache():
    db = MagicMock()
    mock_cursor = MagicMock()

    # Mock corrupted cache data (invalid JSON)
    mock_cursor.fetchone = AsyncMock(return_value=(
        'not valid json',
        'also not valid'
    ))
    db._connection.execute = AsyncMock(return_value=mock_cursor)
    db._connection.commit = AsyncMock()

    service = NetworkService(db, semantic=None)

    network = await service.get_cached_network()

    # Should return None and delete corrupted cache
    assert network is None
    # Verify DELETE was called to clean up corrupted cache
    assert db._connection.execute.call_count == 2  # SELECT + DELETE
    assert db._connection.commit.called
