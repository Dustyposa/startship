from autogen_ext.models.ollama import OllamaChatCompletionClient

model_client = OllamaChatCompletionClient(
    model="qwen3:8b",
    # model_info={
    #     "vision": False,
    #     "function_calling": True,
    #     "json_output": True,
    #     "family": ModelFamily.UNKNOWN,
    #     "structured_output": True,
    # }
)
