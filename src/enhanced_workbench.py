from typing import Any, Mapping

import orjson
from autogen_core import CancellationToken  
from autogen_core.tools import ToolResult, TextResultContent  
from autogen_core.memory import Memory, MemoryContent, MemoryMimeType  
from autogen_ext.tools.mcp import McpWorkbench  
from mcp.types import CallToolResult, TextContent  
  
class CustomMcpWorkbench(McpWorkbench):  
    def __init__(self, server_params, memory: Memory, **kwargs):
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
        original_result = await super().call_tool(name, arguments, cancellation_token, call_id)  
          

          
        # 如果结果太大，存储到 memory 并返回摘要
        if name in {"create_full_analysis_bundle"} and not original_result.is_error:
            for content in original_result.result:
                result_dict = orjson.loads(content.content)
            # 存储完整分析结果到 memory
            await self.memory.add(  
                MemoryContent(  
                    content=result_content,  
                    mime_type=MemoryMimeType.TEXT,  
                    metadata={  
                        "tool_name": name,  
                        "call_id": call_id,  
                        "size": len(result_content),  
                        "type": "large_tool_result"  
                    }  
                ),  
                cancellation_token  
            )  
              
            # 生成摘要  
            summary = result_content[:200] + "..." if len(result_content) > 200 else result_content  
              
            # 返回包含摘要的新结果  
            return ToolResult(  
                name=name,  
                result=[TextResultContent(  
                    content=f"Large result stored in memory (size: {len(result_content)} chars). Summary: {summary}"  
                )],  
                is_error=False  
            )  
          
        # 如果结果不大，直接返回原始结果  
        return original_result