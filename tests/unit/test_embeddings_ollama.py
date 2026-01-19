"""Tests for Ollama Embeddings client."""
import pytest
from unittest.mock import Mock, patch
from src.vector.embeddings import OllamaEmbeddings


@pytest.fixture
def embeddings():
    """Create an OllamaEmbeddings instance for testing."""
    return OllamaEmbeddings(base_url="http://localhost:11434")


def test_embed_text_success(embeddings):
    """测试成功生成 embedding"""
    # Mock ollama 响应
    mock_response = Mock()
    mock_response.json.return_value = {"embedding": [0.1] * 768}
    mock_response.raise_for_status = Mock()

    with patch('requests.post', return_value=mock_response):
        result = embeddings.embed_text("test text")

    assert len(result) == 768
    assert all(isinstance(x, float) for x in result)


def test_embed_text_timeout(embeddings):
    """测试超时处理"""
    from requests.exceptions import Timeout

    with patch('requests.post', side_effect=Timeout()):
        result = embeddings.embed_text("test")

    # 超时时返回空向量
    assert result == []


def test_embed_text_request_exception(embeddings):
    """测试请求异常处理"""
    from requests.exceptions import RequestException

    with patch('requests.post', side_effect=RequestException("Connection error")):
        result = embeddings.embed_text("test")

    # 异常时返回空向量
    assert result == []


def test_embed_text_empty_text(embeddings):
    """测试空文本处理"""
    result = embeddings.embed_text("")

    # 空文本返回空向量
    assert result == []

    result = embeddings.embed_text("   ")

    # 只有空白的文本返回空向量
    assert result == []


def test_embed_text_empty_embedding(embeddings):
    """测试返回空 embedding 的情况"""
    mock_response = Mock()
    mock_response.json.return_value = {"embedding": []}
    mock_response.raise_for_status = Mock()

    with patch('requests.post', return_value=mock_response):
        result = embeddings.embed_text("test")

    # 返回空 embedding 时应该返回空列表
    assert result == []


def test_embed_batch(embeddings):
    """测试批量 embedding"""
    mock_response = Mock()
    mock_response.json.return_value = {"embedding": [0.1] * 768}
    mock_response.raise_for_status = Mock()

    with patch('requests.post', return_value=mock_response):
        texts = ["text1", "text2", "text3"]
        results = embeddings.embed_batch(texts)

    assert len(results) == 3
    assert all(len(r) == 768 for r in results)


def test_embed_batch_with_empty_text(embeddings):
    """测试批量处理包含空文本"""
    mock_response = Mock()
    mock_response.json.return_value = {"embedding": [0.1] * 768}
    mock_response.raise_for_status = Mock()

    with patch('requests.post', return_value=mock_response):
        texts = ["text1", "", "text3"]
        results = embeddings.embed_batch(texts)

    assert len(results) == 3
    # 第二个应该是空向量
    assert results[1] == []
    # 其他应该是正常向量
    assert len(results[0]) == 768
    assert len(results[2]) == 768


def test_embed_batch_large_batch(embeddings):
    """测试大批量处理（超过 batch_size）"""
    mock_response = Mock()
    mock_response.json.return_value = {"embedding": [0.1] * 768}
    mock_response.raise_for_status = Mock()

    with patch('requests.post', return_value=mock_response):
        # 创建 25 个文本（超过默认 batch_size 10）
        texts = [f"text{i}" for i in range(25)]
        results = embeddings.embed_batch(texts)

    assert len(results) == 25
    assert all(len(r) == 768 for r in results)


def test_check_health_success(embeddings):
    """测试健康检查成功"""
    mock_response = Mock()
    mock_response.status_code = 200

    with patch('requests.get', return_value=mock_response):
        result = embeddings.check_health()

    assert result is True


def test_check_health_failure(embeddings):
    """测试健康检查失败"""
    with patch('requests.get', side_effect=Exception("Service unavailable")):
        result = embeddings.check_health()

    assert result is False


def test_check_health_timeout(embeddings):
    """测试健康检查超时"""
    from requests.exceptions import Timeout

    with patch('requests.get', side_effect=Timeout()):
        result = embeddings.check_health()

    assert result is False


def test_custom_model_and_timeout():
    """测试自定义模型和超时设置"""
    embeddings = OllamaEmbeddings(
        base_url="http://localhost:11434",
        model="custom-model",
        timeout=60
    )

    assert embeddings.model == "custom-model"
    assert embeddings.timeout == 60
