from typing import Any, Mapping

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
              
            # 返回包含摘要的新结果  
            return ToolResult(  
                name=name,  
                result=[TextResultContent(  
                    content=f"已经抓取了{repo_lens}个仓库,可以进行分析了。"
                )],  
                is_error=False  
            )  

        return original_result