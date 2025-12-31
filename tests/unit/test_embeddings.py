"""Tests for Ollama embedder."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.vector.embeddings import OllamaEmbedder


@pytest.mark.asyncio
async def test_ollama_embedder():
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}

        mock_client = MagicMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder()
        result = await embedder.embed("test text")

        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)
        assert result == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_ollama_embedder_batch():
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"embedding": [0.1, 0.2]}

        mock_client = MagicMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        embedder = OllamaEmbedder()
        results = await embedder.embed_batch(["text 1", "text 2"])

        assert len(results) == 2
        assert all(isinstance(r, list) for r in results)
