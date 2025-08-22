from typing import Any, Mapping, Dict, List

import orjson
from autogen_core import CancellationToken  
from autogen_core.tools import ToolResult, TextResultContent  
from autogen_ext.tools.mcp import McpWorkbench
from loguru import logger

from src.github_memory import GitHubRepositoryMemory


class CustomMcpWorkbench(McpWorkbench):  
    def __init__(self, server_params, memory: GitHubRepositoryMemory, **kwargs):
        super().__init__(server_params, **kwargs)  
        self.memory = memory  

    async def call_tool(  
        self,  
        name: str,  
        arguments: Mapping[str, Any] | None = None,  
        cancellation_token: CancellationToken | None = None,  
        call_id: str | None = None,  
    ) -> ToolResult:  
        # 调用父类的 call_tool 方法获取原始结果
        from pathlib import Path

        file_path = Path("original_result.json")
        if not file_path.exists():
            original_result = await super().call_tool(name, arguments, cancellation_token, call_id)
            logger.info("成功获取到 mcp tool 的结果")
            file_path.write_text(original_result.model_dump_json())
            logger.info(f"文件写入成功！")
        else:
            original_result = ToolResult(**orjson.loads(file_path.read_bytes()))
            logger.info(f"文件读取成功！")

        # 如果结果太大，存储到 memory 并返回摘要
        if name in {"create_full_analysis_bundle"} and not original_result.is_error:
            repo_lens = 0
            for content in original_result.result:
                result_dict = orjson.loads(content.content)
                repositories, total_count = result_dict["repositories"], result_dict["total_count"]
                # 存储完整分析结果到 memory
                await self.memory.add_repositories_batch(repositories)
                repo_lens += len(repositories)
            result_content = await self.get_repository_summary()
            # 返回包含摘要的新结果  
            return ToolResult(  
                name=name,  
                result=[TextResultContent(  
                    content=result_content
                )],  
                is_error=False,
            )

        return original_result
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        获取 memory 中的统计信息
        
        Returns:
            包含仓库统计信息的字典
        """
        try:
            stats = await self.memory.get_memory_stats()
            return stats
        except Exception as e:
            logger.error(f"Failed to get memory statistics: {e}")
            return {"error": str(e)}
    
    async def get_repository_summary(self) -> str:
        """
        获取仓库的简要摘要信息
        
        Returns:
            格式化的摘要字符串
        """
        try:
            stats = await self.get_memory_statistics()
            
            if "error" in stats:
                return f"获取统计信息失败: {stats['error']}"

            # 解构统计信息
            total_count = stats["total_count"]
            top_languages_status = stats["top_languages_status"]
            top_stars_dict = stats["top_stars"]

            # 格式化语言统计
            languages_summary = ", ".join([
                f"{lang}: {count}" for lang, count in top_languages_status.items()
            ]) if top_languages_status else "暂无数据"

            # 格式化星标统计
            stars_summary = ", ".join([
                f"{repo}: {stars}" for repo, stars in list(top_stars_dict.items())[:5]
            ]) if top_stars_dict else "暂无数据"

            # 构建完整摘要
            summary = f"""仓库统计摘要:
        - 总仓库数: {total_count}
        - 热门语言: {languages_summary}
        - 热门星标项目(前5): {stars_summary}"""

            return summary


        except Exception as e:
            logger.error(f"Failed to generate repository summary: {e}")
            return f"生成摘要失败: {str(e)}"
    
    async def search_memory_repositories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        在 memory 中搜索仓库
        
        Args:
            query: 搜索查询
            limit: 返回结果数量限制
            
        Returns:
            匹配的仓库列表
        """
        try:
            results = await self.memory.search_repositories(query, limit=limit)
            return results
        except Exception as e:
            logger.error(f"Failed to search repositories: {e}")
            return []