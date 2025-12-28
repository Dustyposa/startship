"""
LLM abstraction layer.
Supports multiple LLM providers through a common interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Message(BaseModel):
    """Chat message"""
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    """LLM response"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None


class LLM(ABC):
    """
    Abstract LLM interface.

    All LLM operations must be async.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize LLM client"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close LLM client"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Send chat completion request.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLM response
        """
        pass

    @abstractmethod
    async def analyze_repository(
        self,
        repo_name: str,
        description: str,
        readme: Optional[str] = None,
        language: Optional[str] = None,
        topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a repository and extract structured information.

        Args:
            repo_name: Repository name
            description: Repository description
            readme: README content
            language: Primary language
            topics: Repository topics

        Returns:
            Analysis result with categories, features, tech_stack, etc.
        """
        pass
