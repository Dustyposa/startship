"""
OpenAI LLM implementation.
"""
import json
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
from src.config import settings
from src.llm.base import LLM, Message, LLMResponse


class OpenAILLM(LLM):
    """OpenAI LLM implementation"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Model name
            base_url: API base URL (for compatible APIs)
        """
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.llm_model
        self.base_url = base_url or settings.llm_base_url
        self._client: Optional[AsyncOpenAI] = None

    async def initialize(self) -> None:
        """Initialize OpenAI client"""
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self._client = AsyncOpenAI(**client_kwargs)

    async def close(self) -> None:
        """Close OpenAI client"""
        if self._client:
            await self._client.close()
            self._client = None

    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Send chat completion request"""
        if not self._client:
            raise RuntimeError("Client not initialized")

        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None
        )

    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ):
        """Send chat completion request with streaming response"""
        if not self._client:
            raise RuntimeError("Client not initialized")

        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def analyze_repository(
        self,
        repo_name: str,
        description: str,
        readme: Optional[str] = None,
        language: Optional[str] = None,
        topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze a repository using LLM"""
        # Build analysis prompt
        topics_str = ", ".join(topics) if topics else "None"

        system_prompt = """You are an expert software analyst. Analyze GitHub repositories and provide structured information.

Your response must be valid JSON with this exact structure:
{
    "summary": "One-line summary",
    "categories": ["category1", "category2"],
    "features": ["feature1", "feature2"],
    "tech_stack": ["tech1", "tech2"],
    "use_cases": ["use case1"]
}

Categories should be in Chinese and concise, such as: 工具, 前端, 后端, AI/ML, 数据库, DevOps, etc."""

        user_prompt = f"""Analyze this GitHub repository:

Name: {repo_name}
Language: {language or "Unknown"}
Description: {description or "No description"}
Topics: {topics_str}

README:
{readme[:4000] if readme else "No README available"}

Provide analysis in JSON format as specified."""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt)
        ]

        response = await self.chat(messages, temperature=0.3)

        # Parse JSON response
        try:
            # Extract JSON from response
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            result["name_with_owner"] = repo_name
            result["readme_summary"] = readme[:500] if readme else None
            return result
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            return {
                "name_with_owner": repo_name,
                "summary": description or f"{repo_name}",
                "categories": [],
                "features": [],
                "tech_stack": [language] if language else [],
                "use_cases": [],
                "readme_summary": readme[:500] if readme else None,
                "error": f"JSON parsing failed: {e}"
            }
