"""Tests for intent classification."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.intent import IntentClassifier, IntentResult


def test_intent_result_model():
    result = IntentResult(intent="search", keywords="API framework")
    assert result.intent == "search"
    assert result.keywords == "API framework"
    assert result.confidence == 1.0


def test_intent_result_without_keywords():
    result = IntentResult(intent="chat")
    assert result.intent == "chat"
    assert result.keywords is None
    assert result.confidence == 1.0


@pytest.mark.asyncio
async def test_intent_classifier_search():
    llm = MagicMock()
    llm.chat = AsyncMock(return_value='{"intent": "search", "keywords": "Python web"}')

    classifier = IntentClassifier(llm)
    result = await classifier.classify("有哪些 Python web 框架")

    assert result.intent == "search"
    assert result.keywords == "Python web"


@pytest.mark.asyncio
async def test_intent_classifier_stats():
    llm = MagicMock()
    llm.chat = AsyncMock(return_value='{"intent": "stats", "keywords": null}')

    classifier = IntentClassifier(llm)
    result = await classifier.classify("我收藏了多少个项目")

    assert result.intent == "stats"
    assert result.keywords is None


@pytest.mark.asyncio
async def test_intent_classifier_fallback():
    llm = MagicMock()
    llm.chat = AsyncMock(side_effect=Exception("LLM error"))

    classifier = IntentClassifier(llm)
    result = await classifier.classify("随便说点啥")

    assert result.intent == "search"  # Fallback
    assert result.keywords == "随便说点啥"
