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
                 name: str = "github_repository_memory",
                 model_name: str = "all-MiniLM-L6-v2"):
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
            model_name=model_name  # SentenceTransformer支持模型名称和路径
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
    async def add_repository(self, repo_data: Dict[str, Any]) -> None:
        """
        添加仓库信息到向量存储
        
        Args:
            repo_data: 仓库数据字典，包含name, description, topics等信息
        """
        try:
            # 构建用于嵌入的文本内容
            content_parts = []
            
            # 仓库名称和所有者 - 根据mcp_models.py的StartedRepository模型
            name_with_owner = repo_data.get('name_with_owner') or repo_data.get('full_name')
            if name_with_owner:
                content_parts.append(f"Repository: {name_with_owner}")
            elif 'name' in repo_data and 'owner' in repo_data:
                # 兼容不同的owner格式
                if isinstance(repo_data['owner'], dict):
                    owner_login = repo_data['owner'].get('login', 'unknown')
                elif isinstance(repo_data['owner'], str):
                    owner_login = repo_data['owner']
                else:
                    owner_login = str(repo_data['owner'])
                name_with_owner = f"{owner_login}/{repo_data['name']}"
                content_parts.append(f"Repository: {name_with_owner}")
            elif 'name' in repo_data:
                content_parts.append(f"Repository: {repo_data['name']}")
            
            # 描述
            if repo_data.get('description'):
                content_parts.append(f"Description: {repo_data['description']}")
            
            # 主要语言 - 使用primary_language字段
            primary_language = repo_data.get('primary_language')
            if primary_language:
                content_parts.append(f"Language: {primary_language}")
            
            # 主题标签 - 使用repository_topics字段
            topics = repo_data.get('repository_topics') or repo_data.get('topics')
            if topics:
                if isinstance(topics, list):
                    content_parts.append(f"Topics: {', '.join(topics)}")
                elif isinstance(topics, str):
                    content_parts.append(f"Topics: {topics}")
            
            # README内容（如果有）
            readme_content = repo_data.get('readme_content')
            if readme_content:
                # 截取README的前800个字符，支持更好的语义搜索
                # readme_snippet = readme_content[:800]
                readme_snippet = readme_content
                content_parts.append(f"README: {readme_snippet}")
            
            # 合并所有内容
            content_text = "\n".join(content_parts)
            
            # 创建内存内容
            memory_content = MemoryContent(
                content=content_text,
                mime_type=MemoryMimeType.TEXT
            )
            
            # 添加元数据 - 根据mcp_models.py的StartedRepository模型
            metadata = {
                # 核心字段
                "repo_id": repo_data.get('repo_id', repo_data.get('id', '')),
                "name_with_owner": name_with_owner or '',
                "name": repo_data.get('name', ''),
                "owner": repo_data.get('owner', ''),
                "description": repo_data.get('description'),
                "stargazer_count": repo_data.get('stargazer_count', 0),
                "url": repo_data.get('url', repo_data.get('html_url', '')),
                "primary_language": repo_data.get('primary_language'),
                
                # 时间字段
                "starred_at": repo_data.get('starred_at'),
                "pushed_at": repo_data.get('pushed_at'),
                
                # 额外字段
                "disk_usage": repo_data.get('disk_usage'),
                "repository_topics": repo_data.get('repository_topics', []),
                "languages": repo_data.get('languages', []),
                
                # README内容（如果是StartedRepoWithReadme）
                "readme_content": repo_data.get('readme_content'),
                
                # 内部管理字段
                "added_to_memory_at": datetime.now().isoformat()
            }
            
            # 将元数据作为JSON字符串添加到内容中
            memory_content.content += f"\n\nMetadata: {orjson.dumps(metadata).decode('utf-8')}"
            # meta 信息不存储 readme
            metadata.pop("readme_content")
            # 处理 list / nest list
            memory_content.metadata = {key: convert_value(value) for key, value in metadata.items() if value is not None}
            # 添加到向量存储
            await self.memory.add(memory_content)
            
            logger.info(f"Added repository to memory: {name_with_owner or repo_data.get('name', 'Unknown')}")
            
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
            
            logger.info(f"Found {len(repositories)} repositories for query: {query}")
            return repositories
            
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
        try:
            # 这里返回基本的配置信息
            return {
                "collection_name": self.config.collection_name,
                "persistence_path": self.config.persistence_path,
                "k": self.config.k,
                "score_threshold": self.config.score_threshold,
                "embedding_model": getattr(self.config.embedding_function_config, 'model_name', 'unknown'),
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}


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

