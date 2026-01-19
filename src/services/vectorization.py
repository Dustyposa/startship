"""Vectorization service for repository embeddings."""

import logging
import re
from typing import List, Dict, Any
from src.vector.embeddings import OllamaEmbeddings
from src.vector.chroma_store import ChromaDBStore
from src.vector.readme_filter import extract_readme_summary

logger = logging.getLogger(__name__)

# Badge pattern to remove from README (same as in readme_filter.py)
BADGE_PATTERN = r'\[!\[.*?\]\(.*?\)\]\(.*?\)|\!\[.*?\]\(.*?\)'

# Constants for text processing
MIN_README_SUMMARY_LENGTH = 300
MAX_README_CONTENT_LENGTH = 2000
DESCRIPTION_REPEAT_COUNT = 4
MIN_TEXT_LENGTH = 10


class VectorizationService:
    """仓库向量化服务"""

    def __init__(
        self,
        embeddings: OllamaEmbeddings,
        store: ChromaDBStore
    ):
        """
        初始化向量化服务

        Args:
            embeddings: Embedding 生成器
            store: 向量存储
        """
        self.embeddings = embeddings
        self.store = store

    def _prepare_text(self, repo: Dict[str, Any]) -> str:
        """
        准备用于 embedding 的文本

        优化策略：
        1. 优先使用过滤后的 README（去除噪音）
        2. 如果过滤后太短，使用更多原始内容
        3. 增加 description 权重以提高区分度

        Args:
            repo: 仓库数据

        Returns:
            拼接后的文本
        """
        name = repo.get("name", "")
        description = repo.get("description", "")
        readme = repo.get("readme_content", "")

        # 提取 README 摘要
        readme_summary = extract_readme_summary(readme, max_length=500)

        # 如果过滤后太短，使用更多原始 README 内容
        if len(readme_summary) < MIN_README_SUMMARY_LENGTH and len(readme) > 0:
            readme_cleaned = re.sub(BADGE_PATTERN, '', readme)
            readme_summary = readme_cleaned[:MAX_README_CONTENT_LENGTH] if len(readme_cleaned) > MAX_README_CONTENT_LENGTH else readme_cleaned

        # 拼接文本：description 重复多次以最大化权重
        parts = []
        if name:
            parts.append(name)
        if description:
            # 重复 description 以增加其在 embedding 中的权重
            for _ in range(DESCRIPTION_REPEAT_COUNT):
                parts.append(f"- {description}")
        # 添加语言标签作为区分特征
        language = repo.get("primary_language", "")
        if language:
            parts.append(f"\n编程语言: {language}")
        if readme_summary:
            parts.append(f"\n\n{readme_summary}")

        return " ".join(parts)

    def _prepare_metadata(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备元数据

        Args:
            repo: 仓库数据

        Returns:
            元数据字典
        """
        return {
            "name": repo.get("name", ""),
            "owner": repo.get("owner", ""),
            "primary_language": repo.get("primary_language", ""),
            "stargazer_count": repo.get("stargazer_count", 0),
            "topics": str(repo.get("topics", []))
        }

    async def index_repository(self, repo: Dict[str, Any]) -> bool:
        """
        为单个仓库生成并存储 embedding

        Args:
            repo: 仓库数据

        Returns:
            是否成功
        """
        repo_id = repo.get("name_with_owner")
        if not repo_id:
            logger.warning("Repository missing name_with_owner")
            return False

        # 准备文本
        text = self._prepare_text(repo)
        if not text or len(text.strip()) < MIN_TEXT_LENGTH:
            logger.warning(f"Insufficient text for {repo_id}")
            return False

        # 生成 embedding
        embedding = self.embeddings.embed_text(text)
        if not embedding:
            logger.error(f"Failed to generate embedding for {repo_id}")
            return False

        # 准备元数据
        metadata = self._prepare_metadata(repo)

        # 存储向量
        self.store.add(repo_id, text, embedding, metadata)
        logger.debug(f"Indexed {repo_id}")
        return True

    async def index_batch(self, repos: List[Dict[str, Any]]) -> int:
        """
        批量索引仓库

        Args:
            repos: 仓库列表

        Returns:
            成功索引的数量
        """
        if not repos:
            return 0

        repo_ids = []
        texts = []
        embeddings = []
        metadata_list = []

        for repo in repos:
            repo_id = repo.get("name_with_owner")
            if not repo_id:
                continue

            # 准备文本
            text = self._prepare_text(repo)
            if not text or len(text.strip()) < MIN_TEXT_LENGTH:
                continue

            # 生成 embedding
            embedding = self.embeddings.embed_text(text)
            if not embedding:
                logger.warning(f"Skipping {repo_id}: no embedding generated")
                continue

            # 准备元数据
            metadata = self._prepare_metadata(repo)

            repo_ids.append(repo_id)
            texts.append(text)
            embeddings.append(embedding)
            metadata_list.append(metadata)

        # 批量添加到存储
        if repo_ids:
            self.store.add_batch(repo_ids, texts, embeddings, metadata_list)
            logger.info(f"Batch indexed {len(repo_ids)}/{len(repos)} repositories")

        return len(repo_ids)
