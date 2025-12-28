"""LLM package with factory function."""
from .base import LLM, Message, LLMResponse
from .openai import OpenAILLM

__all__ = ["LLM", "Message", "LLMResponse", "OpenAILLM", "create_llm"]


def create_llm(provider: str = "openai", **config) -> LLM:
    """
    Factory function to create LLM instance.

    Args:
        provider: LLM provider ("openai")
        **config: Configuration parameters

    Returns:
        LLM instance

    Raises:
        ValueError: If provider is not supported
    """
    if provider == "openai":
        return OpenAILLM(**config)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
