from typing import List, Sequence, Any, Dict, Callable

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Handoff as HandoffBase
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_core import CancellationToken, FunctionCall
from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import CreateResult, SystemMessage, ChatCompletionClient, FunctionExecutionResult
from autogen_core.tools import Workbench, BaseTool
from pydantic import BaseModel


class MemoryStoringAssistantAgent(AssistantAgent):
    def __init__(self, name, model_client, tools, tool_result_memory, **kwargs):
        super().__init__(name, model_client, tools=tools, **kwargs)
        self.tool_result_memory = tool_result_memory

    async def _process_model_result(cls,
        model_result: CreateResult,
        inner_messages: List[BaseAgentEvent | BaseChatMessage],
        cancellation_token: CancellationToken,
        agent_name: str,
        system_messages: List[SystemMessage],
        model_context: ChatCompletionContext,
        workbench: Sequence[Workbench],
        handoff_tools: List[BaseTool[Any, Any]],
        handoffs: Dict[str, HandoffBase],
        model_client: ChatCompletionClient,
        model_client_stream: bool,
        reflect_on_tool_use: bool,
        tool_call_summary_format: str,
        tool_call_summary_formatter: Callable[[FunctionCall, FunctionExecutionResult], str] | None,
        max_tool_iterations: int,
        output_content_type: type[BaseModel] | None,
        message_id: str,
        format_string: str | None = None,
    ):
        # 复制原有的处理逻辑，但修改工具结果处理部分

        for loop_iteration in range(max_tool_iterations):
            if isinstance(model_result.content, str):
                # 处理文本响应
                yield create_text_response(model_result)
                return

                # 处理工具调用
            if isinstance(model_result.content, list):
                # 执行工具调用
                executed_calls_and_results = await self._execute_tool_calls(
                    model_result.content, stream_queue
                )

                # 关键修改：存储工具结果到 memory，但不添加到 context
                for call, result in executed_calls_and_results:
                    # 存储到自定义 memory
                    await self.tool_result_memory.add(MemoryContent(
                        content=f"Tool {call.name} result: {result.content}",
                        metadata={
                            "tool_name": call.name,
                            "call_id": call.id,
                            "timestamp": datetime.now().isoformat()
                        }
                    ))

                    # 跳过默认的上下文添加逻辑
                # 注释掉这一行：
                # await model_context.add_message(FunctionExecutionResultMessage(content=exec_results))

                # 触发 memory 更新上下文（检索相关结果并注入）
                await self.tool_result_memory.update_context(model_context)

                # 继续后续处理...