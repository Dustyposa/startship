"""Ollama embedding service."""
import httpx
import logging
from typing import List
import requests
from requests.exceptions import Timeout, RequestException

logger = logging.getLogger(__name__)


class OllamaEmbedder:
    """Generate embeddings using Ollama API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text"
    ):
        """
        Initialize embedder.

        Args:
            base_url: Ollama API URL
            model: Embedding model name
        """
        self.base_url = base_url
        self.model = model

    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Vector embedding as list of floats
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of vector embeddings
        """
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings


class OllamaEmbeddings:
    """Ollama embedding 服务客户端"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        timeout: int = 30
    ):
        """
        初始化 Ollama embedding 客户端

        Args:
            base_url: Ollama 服务地址
            model: 使用的 embedding 模型
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self._batch_size = 10  # 每批最多处理 10 个文本

    def embed_text(self, text: str) -> List[float]:
        """
        生成单段文本的 embedding

        Args:
            text: 输入文本

        Returns:
            embedding 向量（768 维），失败返回空列表
        """
        if not text or not text.strip():
            return []

        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            embedding = data.get("embedding", [])

            if not embedding:
                logger.warning(f"Empty embedding received for text: {text[:50]}...")

            return embedding

        except Timeout:
            logger.error(f"Ollama timeout after {self.timeout}s")
            return []
        except RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {e}")
            return []

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成 embedding

        Args:
            texts: 文本列表

        Returns:
            embedding 向量列表
        """
        results = []

        # 分批处理，避免过载
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i:i + self._batch_size]

            # 并行处理当前批次
            batch_results = [self.embed_text(text) for text in batch]
            results.extend(batch_results)

        return results

    def check_health(self) -> bool:
        """
        检查 Ollama 服务是否可用

        Returns:
            True 如果服务正常，否则 False
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
