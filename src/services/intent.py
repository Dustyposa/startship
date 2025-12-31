"""Intent classification service."""
import json
from pydantic import BaseModel
from typing import Literal
from src.llm import Message, LLM


class IntentResult(BaseModel):
    """Result of intent classification."""
    intent: Literal["chat", "stats", "search"]
    keywords: str | None = None
    confidence: float = 1.0


class IntentClassifier:
    """Classify user intent using LLM."""

    def __init__(self, llm: LLM):
        """
        Initialize classifier.

        Args:
            llm: LLM instance for classification
        """
        self.llm = llm
        self._system_prompt = """分类用户意图，只返回 JSON：
{
  "intent": "chat|stats|search",
  "keywords": "提取的核心搜索词（仅 search 需要，否则 null）"
}

规则：
- "你好、在吗、谢谢" → chat
- "多少、分布、统计" → stats
- "找、推荐、有哪些、怎么、如何" → search"""

    async def classify(self, query: str) -> IntentResult:
        """
        Classify user intent.

        Args:
            query: User query text

        Returns:
            IntentResult with classified intent and extracted keywords
        """
        messages = [
            Message(role="system", content=self._system_prompt),
            Message(role="user", content=query)
        ]

        try:
            response = await self.llm.chat(messages, temperature=0.0)
            data = json.loads(response)
            return IntentResult(**data)
        except Exception:
            # Fallback to search on error
            return IntentResult(intent="search", keywords=query)
