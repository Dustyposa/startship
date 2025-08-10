"""GitHub仓库信息的ChromaDB Memory实现 - 基于AutoGen原生Memory接口"""

import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path

import orjson
from autogen_core.memory import Memory, MemoryContent, MemoryMimeType, UpdateContextResult
from autogen_core import CancellationToken
from autogen_core.model_context import ChatCompletionContext
from autogen_ext.memory.chromadb import (
    ChromaDBVectorMemory,
    PersistentChromaDBVectorMemoryConfig,
    SentenceTransformerEmbeddingFunctionConfig
)
from loguru import logger
import polars as pl


def convert_value(value):
    if isinstance(value, list):
        return ','.join(map(str, value))
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        # 字符串或其他类型保持不变
        return value

class GitHubRepositoryMemory(Memory):
    """GitHub仓库信息的ChromaDB向量存储实现 - 实现AutoGen Memory协议"""
    
    def __init__(self, 
                 collection_name: str = "github_repositories",
                 persistence_path: Optional[str] = None,
                 k: int = 5,
                 score_threshold: float = 0.3,
                 name: str = "github_repository_memory"):
        """
        初始化GitHub仓库Memory
        
        Args:
            collection_name: ChromaDB集合名称
            persistence_path: 持久化存储路径
            k: 检索时返回的最大结果数
            score_threshold: 相似度阈值
            name: Memory实例名称
            model_name: 模型名称或本地路径，支持在线模型名称和本地模型路径
        """
        self._name = name
        
        if persistence_path is None:
            persistence_path = os.path.join(str(Path.home()), ".chromadb_github_repos")
        
        # 配置ChromaDB向量存储
        embedding_function_config = SentenceTransformerEmbeddingFunctionConfig(
            model_name="/Users/dustyposa/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf"  # SentenceTransformer支持模型名称和路径
        )

        self.config = PersistentChromaDBVectorMemoryConfig(
            collection_name=collection_name,
            persistence_path=persistence_path,
            k=k,
            score_threshold=score_threshold,
            embedding_function_config=embedding_function_config
        )
        
        # 创建ChromaDB向量存储实例
        self.memory = ChromaDBVectorMemory(config=self.config)
        self.memory._ensure_initialized()
        self.memory_collection = self.memory._collection

        logger.info(f"GitHubRepositoryMemory initialized with collection: {collection_name}")


    
    @property
    def name(self) -> str:
        """返回Memory实例名称"""
        return self._name

    async def update_context(
        self,
        model_context: ChatCompletionContext,
    ) -> UpdateContextResult:
        return await self.memory.update_context(model_context)

    # AutoGen Memory协议方法
    async def query(
        self,
        query: Union[str, MemoryContent],
        cancellation_token: Optional[CancellationToken] = None,
        **kwargs
    ) -> List[MemoryContent]:
        """
        查询相关的仓库信息
        
        Args:
            query: 查询内容（字符串或MemoryContent）
            cancellation_token: 取消令牌
            **kwargs: 额外参数
        
        Returns:
            相关的MemoryContent列表
        """
        try:
            # 将查询转换为字符串
            if isinstance(query, MemoryContent):
                query_str = query.content
            else:
                query_str = str(query)
            
            # 使用底层ChromaDB memory进行查询
            query_content = MemoryContent(content=query_str, mime_type=MemoryMimeType.TEXT)
            results = await self.memory.query(query_content, cancellation_token, **kwargs)
            
            logger.info(f"Found {len(results)} results for query: {query_str[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query memory: {e}", exc_info=True)
            return []
    
    async def add(
        self,
        content: MemoryContent,
        cancellation_token: Optional[CancellationToken] = None
    ) -> None:
        """
        添加内容到memory
        
        Args:
            content: 要添加的内容
            cancellation_token: 取消令牌
        """
        try:
            await self.memory.add(content, cancellation_token)
            logger.info(f"Added content to memory: {content.content[:100]}...")
        except Exception as e:
            logger.error(f"Failed to add content to memory: {e}", exc_info=True)
            raise

    
    async def clear(self) -> None:
        """清空所有memory内容"""
        try:
            await self.memory.clear()
            logger.info("Cleared all memory content")
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}", exc_info=True)
            raise
    
    async def close(self) -> None:
        """关闭memory连接并清理资源"""
        try:
            await self.memory.close()
            logger.info("Closed memory connection")
        except Exception as e:
            logger.error(f"Failed to close memory: {e}", exc_info=True)
    
    # GitHub特定的便利方法
    def _extract_name_with_owner(self, repo_data: Dict[str, Any]) -> str:
        """
        提取仓库的完整名称（owner/name格式）
        
        Args:
            repo_data: 仓库数据字典
            
        Returns:
            格式化的仓库名称
        """
        # 优先使用已有的完整名称（驼峰命名）
        name_with_owner = repo_data.get('nameWithOwner')
        if name_with_owner:
            return name_with_owner
            
        # 从name和owner字段构建
        name = repo_data.get('name')
        owner = repo_data.get('owner')
        
        if name and owner:
            # 处理不同的owner格式
            if isinstance(owner, dict):
                owner_login = owner.get('login', 'unknown')
            elif isinstance(owner, str):
                owner_login = owner
            else:
                owner_login = str(owner)
            return f"{owner_login}/{name}"
            
        # 仅有name的情况
        return name or 'Unknown'
    
    def _build_content_text(self, repo_data: Dict[str, Any], name_with_owner: str) -> str:
        """
        构建用于向量嵌入的文本内容
        
        Args:
            repo_data: 仓库数据字典
            name_with_owner: 仓库完整名称
            
        Returns:
            格式化的文本内容
        """
        content_parts = [f"Repository: {name_with_owner}"]
        
        # 添加描述
        if description := repo_data.get('description'):
            content_parts.append(f"Description: {description}")
        
        # 添加主要语言（使用驼峰命名）
        if primary_language := repo_data.get('primaryLanguage'):
            content_parts.append(f"Language: {primary_language}")
        
        # 添加主题标签（使用驼峰命名）
        topics = repo_data.get('repositoryTopics') or repo_data.get('topics')
        if topics:
            if isinstance(topics, list):
                content_parts.append(f"Topics: {', '.join(topics)}")
            elif isinstance(topics, str):
                content_parts.append(f"Topics: {topics}")
        
        # 添加README内容（使用驼峰命名）
        if readme_content := repo_data.get('readmeContent'):
            content_parts.append(f"README: {readme_content}")
        
        return "\n".join(content_parts)
    
    def _build_metadata(self, repo_data: Dict[str, Any], name_with_owner: str) -> Dict[str, Any]:
        """
        构建仓库元数据
        
        Args:
            repo_data: 仓库数据字典
            name_with_owner: 仓库完整名称
            
        Returns:
            元数据字典
        """
        return {
            # 核心字段（优先使用驼峰命名）
            "repo_id": repo_data.get('id') or repo_data.get('repo_id', ''),
            "name_with_owner": name_with_owner,
            "name": repo_data.get('name', ''),
            "owner": repo_data.get('owner', ''),
            "description": repo_data.get('description'),
            "stargazer_count": repo_data.get('stargazerCount', 0),
            "url": repo_data.get('url', ''),
            "primary_language": repo_data.get('primaryLanguage'),
            
            # 时间字段（使用驼峰命名）
            "starred_at": repo_data.get('starredAt'),
            "pushed_at": repo_data.get('pushedAt'),
            
            # 额外字段（使用驼峰命名）
            "disk_usage": repo_data.get('diskUsage'),
            "repository_topics": repo_data.get('repositoryTopics', []),
            "languages": repo_data.get('languages', []),
            "readme_content": repo_data.get('readmeContent'),
            
            # 内部管理字段
            "added_to_memory_at": datetime.now().isoformat()
        }
    
    async def add_repository(self, repo_data: Dict[str, Any]) -> None:
        """
        添加仓库信息到向量存储
        
        Args:
            repo_data: 仓库数据字典，包含name, description, topics等信息
        """
        try:
            # 提取仓库完整名称
            name_with_owner = self._extract_name_with_owner(repo_data)
            
            # 构建文本内容
            content_text = self._build_content_text(repo_data, name_with_owner)
            
            # 构建元数据
            metadata = self._build_metadata(repo_data, name_with_owner)
            
            # 创建内存内容
            memory_content = MemoryContent(
                content=content_text,
                mime_type=MemoryMimeType.TEXT
            )
            
            # 将元数据作为JSON字符串添加到内容中
            memory_content.content += f"\n\nMetadata: {orjson.dumps(metadata).decode('utf-8')}"
            
            # 准备存储的元数据（不包含readme_content以节省空间）
            storage_metadata = {k: v for k, v in metadata.items() if k != "readme_content"}
            memory_content.metadata = {
                key: convert_value(value) 
                for key, value in storage_metadata.items() 
                if value is not None
            }
            
            # 添加到向量存储
            await self.memory.add(memory_content)
            
            logger.info(f"Added repository to memory: {name_with_owner}")
            
        except Exception as e:
            logger.error(f"Failed to add repository to memory: {e}", exc_info=True)
            raise
    
    async def add_repositories_batch(self, repos_data: List[Dict[str, Any]]) -> None:
        """
        批量添加仓库信息
        
        Args:
            repos_data: 仓库数据列表
        """
        for repo_data in repos_data:
            await self.add_repository(repo_data)
        
        logger.info(f"Added {len(repos_data)} repositories to memory")
    
    async def search_repositories(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        搜索相关的仓库
        
        Args:
            query: 搜索查询
            limit: 限制返回结果数量
        
        Returns:
            匹配的仓库信息列表
        """
        try:
            # 查询向量存储
            query_content = MemoryContent(content=query, mime_type=MemoryMimeType.TEXT)
            results = await self.memory.query(query_content)
            
            repositories = []
            for result in results:
                try:
                    # 检查result是否有content属性
                    if hasattr(result, 'content'):
                        content = result.content
                    else:
                        # 如果result是tuple或其他格式，尝试获取内容
                        content = str(result)
                    
                    # 解析内容中的元数据
                    if "\n\nMetadata: " in content:
                        content_text, metadata_json = content.rsplit("\n\nMetadata: ", 1)
                        metadata = orjson.loads(metadata_json)
                        
                        # 构建仓库信息
                        repo_info = {
                            "content": content_text,
                            "metadata": metadata,
                            "score": getattr(result, 'score', 0.0)
                        }
                        repositories.append(repo_info)
                    else:
                        # 如果没有元数据，检查是否有metadata属性
                        metadata = getattr(result, 'metadata', {})
                        repo_info = {
                            "content": content,
                            "metadata": metadata,
                            "score": getattr(result, 'score', 0.0)
                        }
                        repositories.append(repo_info)
                        
                except (orjson.JSONDecodeError, AttributeError) as e:
                    logger.warning(f"Failed to parse repository metadata: {e}")
                    # 如果解析失败，至少返回内容
                    content = getattr(result, 'content', str(result))
                    repositories.append({
                        "content": content,
                        "metadata": {},
                        "score": getattr(result, 'score', 0.0)
                    })
            
            # 应用限制
            if limit and limit > 0:
                repositories = repositories[:limit]
            
            # 转换为直接的仓库信息格式
            repo_list = []
            for repo in repositories:
                metadata = repo.get('metadata', {})
                # 如果metadata为空，尝试从content中提取基本信息
                if not metadata:
                    content = repo.get('content', '')
                    # 创建基本的仓库信息
                    metadata = {
                        'name_with_owner': 'Unknown',
                        'description': 'No description',
                        'stargazer_count': 0,
                        'primary_language': 'Unknown',
                        'repository_topics': [],
                        'owner': 'Unknown'
                    }
                
                repo_list.append(metadata)
            
            logger.info(f"Found {len(repo_list)} repositories for query: {query}")
            return repo_list
            
        except Exception as e:
            logger.error(f"Failed to search repositories: {e}", exc_info=True)
            return []
    
    async def get_repositories_by_language(self, language: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        根据编程语言搜索仓库
        
        Args:
            language: 编程语言名称
            limit: 限制返回结果数量
        
        Returns:
            匹配的仓库信息列表
        """
        query = f"Language: {language} programming {language} development"
        return await self.search_repositories(query, limit)
    
    async def get_repositories_by_topic(self, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        根据主题搜索仓库
        
        Args:
            topic: 主题名称
            limit: 限制返回结果数量
        
        Returns:
            匹配的仓库信息列表
        """
        query = f"Topics: {topic} {topic} related"
        return await self.search_repositories(query, limit)
    
    async def find_similar_repositories(self, repo_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        查找与指定仓库相似的项目
        
        Args:
            repo_name: 仓库名称
            limit: 限制返回结果数量
        
        Returns:
            相似的仓库信息列表
        """
        query = f"Repository: {repo_name} similar projects like {repo_name}"
        return await self.search_repositories(query, limit)
    
    async def clear_memory(self) -> None:
        """
        清空内存存储
        """
        try:
            # 注意：ChromaDBVectorMemory可能没有直接的clear方法
            # 这里我们可能需要重新创建集合或使用其他方法
            logger.warning("Clear memory operation may not be fully supported by ChromaDBVectorMemory")
            
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}", exc_info=True)
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取内存存储统计信息
        
        Returns:
            统计信息字典
        """
        total_count = self.memory_collection.count()
        result = self.memory_collection.get(
            include=["metadatas"]
        )
        df = pl.from_dicts(result["metadatas"])
        top_stars_df = df.top_k(10, by="stargazer_count").sort(by="stargazer_count", descending=True)
        top_languages_proportion = (df.with_columns(
            pl.col("languages").str.strip_chars().str.split(",").alias("elements")
        )
        .explode("elements")
        .select("elements")
        .to_series()
        .value_counts(sort=True, normalize=True).with_columns(
            pl.col("proportion").round(4)  # 将比例值保留4位小数
        ).head(15))
        top_languages_status = {row[0]: row[1] for row in top_languages_proportion.rows()}

        top_stars_dict = {row[0]: row[1] for row in top_stars_df.select(["name_with_owner", "stargazer_count"]).rows()}
        return {"total_count": total_count, "top_languages_status": top_languages_status, "top_stars": top_stars_dict}


# 工厂函数
def create_github_repository_memory(
    collection_name: str = "github_repositories",
    persistence_path: Optional[str] = None,
    k: int = 5,
    score_threshold: float = 0.3,
    name: str = "github_repository_memory",
) -> GitHubRepositoryMemory:
    """
    创建GitHub仓库Memory实例的工厂函数
    
    Args:
        collection_name: ChromaDB集合名称
        persistence_path: 持久化存储路径
        k: 检索时返回的最大结果数
        score_threshold: 相似度阈值
        name: Memory实例名称
        model_name: 模型名称或本地路径，支持在线模型名称和本地模型路径
    
    Returns:
        GitHubRepositoryMemory实例
    """
    return GitHubRepositoryMemory(
        collection_name=collection_name,
        persistence_path=persistence_path,
        k=k,
        score_threshold=score_threshold,
        name=name,
    )


if __name__ == '__main__':
    async def main():
        memory = create_github_repository_memory()
        print(await memory.get_memory_stats())
    import asyncio
    asyncio.run(main())