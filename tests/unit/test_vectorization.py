"""Unit tests for Vectorization Service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.vectorization import VectorizationService


@pytest.fixture
def mock_embeddings():
    """Mock OllamaEmbeddings instance."""
    with patch('src.services.vectorization.OllamaEmbeddings') as mock:
        instance = mock.return_value
        instance.embed_text.return_value = [0.1] * 768
        yield instance


@pytest.fixture
def mock_store():
    """Mock ChromaDBStore instance."""
    with patch('src.services.vectorization.ChromaDBStore') as mock:
        instance = mock.return_value
        instance.add_batch.return_value = 1
        yield instance


@pytest.mark.asyncio
async def test_index_repository(mock_embeddings, mock_store):
    """测试索引单个仓库"""
    service = VectorizationService(mock_embeddings, mock_store)

    repo = {
        "name_with_owner": "test/repo",
        "name": "repo",
        "description": "Test repo",
        "readme_content": "# Test\n\nA great project"
    }

    result = await service.index_repository(repo)

    assert result is True
    mock_embeddings.embed_text.assert_called_once()
    mock_store.add.assert_called_once()


@pytest.mark.asyncio
async def test_index_batch(mock_embeddings, mock_store):
    """测试批量索引"""
    service = VectorizationService(mock_embeddings, mock_store)

    repos = [
        {
            "name_with_owner": f"test/repo{i}",
            "name": f"repo{i}",
            "description": f"Test {i}",
            "readme_content": "Content"
        }
        for i in range(5)
    ]

    count = await service.index_batch(repos)

    assert count == 5
    assert mock_embeddings.embed_text.call_count == 5


@pytest.mark.asyncio
async def test_index_repository_missing_id(mock_embeddings, mock_store):
    """测试索引缺少 name_with_owner 的仓库"""
    service = VectorizationService(mock_embeddings, mock_store)

    repo = {
        "name": "repo",
        "description": "Test repo"
    }

    result = await service.index_repository(repo)

    assert result is False
    mock_embeddings.embed_text.assert_not_called()
    mock_store.add.assert_not_called()


@pytest.mark.asyncio
async def test_index_repository_insufficient_text(mock_embeddings, mock_store):
    """测试索引文本不足的仓库"""
    service = VectorizationService(mock_embeddings, mock_store)

    repo = {
        "name_with_owner": "test/repo",
        "name": "x"
    }

    result = await service.index_repository(repo)

    assert result is False
    mock_embeddings.embed_text.assert_not_called()


@pytest.mark.asyncio
async def test_index_repository_embedding_failure(mock_embeddings, mock_store):
    """测试 embedding 生成失败的情况"""
    mock_embeddings.embed_text.return_value = []
    service = VectorizationService(mock_embeddings, mock_store)

    repo = {
        "name_with_owner": "test/repo",
        "name": "repo",
        "description": "Test repo with sufficient description text here"
    }

    result = await service.index_repository(repo)

    assert result is False
    mock_store.add.assert_not_called()


@pytest.mark.asyncio
async def test_index_batch_empty_list(mock_embeddings, mock_store):
    """测试批量索引空列表"""
    service = VectorizationService(mock_embeddings, mock_store)

    count = await service.index_batch([])

    assert count == 0
    mock_embeddings.embed_text.assert_not_called()
    mock_store.add_batch.assert_not_called()


@pytest.mark.asyncio
async def test_index_batch_partial_failures(mock_embeddings, mock_store):
    """测试批量索引部分失败的情况"""
    # 第3个调用返回空embedding
    mock_embeddings.embed_text.side_effect = [[0.1] * 768, [0.2] * 768, [], [0.4] * 768, [0.5] * 768]

    service = VectorizationService(mock_embeddings, mock_store)

    repos = [
        {
            "name_with_owner": f"test/repo{i}",
            "name": f"repo{i}",
            "description": f"Test {i}",
        }
        for i in range(5)
    ]

    count = await service.index_batch(repos)

    # 应该成功4个，失败1个
    assert count == 4
    mock_store.add_batch.assert_called_once()


def test_prepare_text_full_repo(mock_embeddings, mock_store):
    """测试文本准备 - 完整仓库信息"""
    service = VectorizationService(mock_embeddings, mock_store)

    repo = {
        "name": "test-repo",
        "description": "A test repository",
        "readme_content": "# Test Repo\n\nThis is a great project for testing."
    }

    text = service._prepare_text(repo)

    assert "test-repo" in text
    assert "A test repository" in text
    assert "Test Repo" in text


def test_prepare_metadata(mock_embeddings, mock_store):
    """测试元数据准备"""
    service = VectorizationService(mock_embeddings, mock_store)

    repo = {
        "name": "test-repo",
        "owner": "testuser",
        "primary_language": "Python",
        "stargazer_count": 100,
        "topics": ["ai", "ml", "python"]
    }

    metadata = service._prepare_metadata(repo)

    assert metadata["name"] == "test-repo"
    assert metadata["owner"] == "testuser"
    assert metadata["primary_language"] == "Python"
    assert metadata["stargazer_count"] == 100
    assert "ai" in metadata["topics"]
