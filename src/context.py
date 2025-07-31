from typing import List

from autogen_core.model_context import BufferedChatCompletionContext
from autogen_core.models import LLMMessage, FunctionExecutionResultMessage
from loguru import logger

class FilterBufferedChatCompletionContext(BufferedChatCompletionContext):
    async def get_messages(self) -> List[LLMMessage]:
        messages = await super().get_messages()
        filter_messages = []
        for message in messages:
            if isinstance(message, FunctionExecutionResultMessage):
                if message.function_call.name == "create_full_analysis_bundle":
                    logger.debug(f"过滤掉 create_full_analysis_bundle 函数调用结果")
                    continue
            filter_messages.append(message)
        return filter_messages
