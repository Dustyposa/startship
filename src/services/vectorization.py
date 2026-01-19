"""Vectorization service for repository embeddings."""

import logging
from typing import List, Dict, Any
from src.vector.embeddings import OllamaEmbeddings
from src.vector.chroma_store import ChromaDBStore
from src.vector.readme_filter import extract_readme_summary

logger = logging.getLogger(__name__)


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
        # 阈值设为 300 字符（提高到 300）
        if len(readme_summary) < 300 and len(readme) > 0:
            # 使用原始 README 的前 2000 字符（提高到 2000）
            import re
            badge_pattern = r'\[!\[.*?\]\(.*?\)\]\(.*?\)|\!\[.*?\]\(.*?\)'
            readme_cleaned = re.sub(badge_pattern, '', readme)
            # 取前 2000 字符
            readme_summary = readme_cleaned[:2000] if len(readme_cleaned) > 2000 else readme_cleaned

        # 拼接文本：description 重复 4 次以最大化权重
        parts = []
        if name:
            parts.append(name)
        if description:
            # 重复 4 次
            for _ in range(4):
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
        try:
            repo_id = repo.get("name_with_owner")
            if not repo_id:
                logger.warning("Repository missing name_with_owner")
                return False

            # 准备文本
            text = self._prepare_text(repo)
            if not text or len(text.strip()) < 10:
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

        except Exception as e:
            logger.error(f"Failed to index repository: {e}")
            return False

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

        success_count = 0

        for repo in repos:
            try:
                repo_id = repo.get("name_with_owner")
                if not repo_id:
                    continue

                # 准备文本
                text = self._prepare_text(repo)
                if not text or len(text.strip()) < 10:
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
                success_count += 1

            except Exception as e:
                logger.error(f"Failed to prepare {repo.get('name_with_owner')}: {e}")

        # 批量添加到存储
        if repo_ids:
            self.store.add_batch(repo_ids, texts, embeddings, metadata_list)
            logger.info(f"Batch indexed {success_count}/{len(repos)} repositories")

        return success_count
