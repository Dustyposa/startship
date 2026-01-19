"""Unit tests for Ollama Embeddings client."""

import pytest
from unittest.mock import Mock, patch
from requests.exceptions import Timeout

from src.vector.embeddings import OllamaEmbeddings


class TestOllamaEmbeddings:
    """Test suite for OllamaEmbeddings client."""

    @pytest.fixture
    def client(self):
        """Create OllamaEmbeddings client instance."""
        return OllamaEmbeddings(
            base_url="http://localhost:11434",
            model="nomic-embed-text",
            timeout=30
        )

    def test_embed_text_success(self, client):
        """Test successful text embedding generation."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
        }

        with patch("src.vector.embeddings.requests.post", return_value=mock_response):
            result = client.embed_text("test text")

            # Verify embedding is returned
            assert isinstance(result, list)
            assert len(result) == 5
            assert result == [0.1, 0.2, 0.3, 0.4, 0.5]

            # Verify API was called correctly
            mock_response.json.assert_called_once()

    def test_embed_text_timeout(self, client):
        """Test text embedding with timeout error."""
        # Mock timeout exception
        with patch("src.vector.embeddings.requests.post", side_effect=Timeout()):
            result = client.embed_text("test text")

            # Verify empty list is returned on timeout
            assert result == []

    def test_embed_batch(self, client):
        """Test batch embedding generation."""
        # Mock successful API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embedding": [0.1, 0.2, 0.3]
        }

        texts = ["text1", "text2", "text3"]

        with patch("src.vector.embeddings.requests.post", return_value=mock_response):
            results = client.embed_batch(texts)

            # Verify all embeddings are returned
            assert len(results) == 3
            assert all(isinstance(embedding, list) for embedding in results)
            assert results[0] == [0.1, 0.2, 0.3]
            assert results[1] == [0.1, 0.2, 0.3]
            assert results[2] == [0.1, 0.2, 0.3]

            # Verify API was called 3 times
            assert mock_response.json.call_count == 3
