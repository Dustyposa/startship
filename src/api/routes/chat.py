"""
Chat API endpoints.
"""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model"""
    session_id: str
    message: str
    use_rag: bool = True
    llm_config: dict | None = None  # Optional LLM config override


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str


class ConversationHistoryResponse(BaseModel):
    """Conversation history response"""
    session_id: str
    messages: list


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response with intent-based routing.

    Routes to:
    - chat: Simple conversation
    - stats: Statistics aggregation
    - search: Hybrid search + RAG
    """
    from src.api.app import db
    from src.llm import create_llm, Message
    from src.services.intent import IntentClassifier
    from src.services.stats import StatsService
    from src.services.hybrid_search import HybridSearch
    from src.services.chat import ChatService
    from src.vector.semantic import SemanticSearch

    # Create LLM
    llm_kwargs = {}
    if request.llm_config and request.llm_config.get("api_key"):
        llm_kwargs["api_key"] = request.llm_config["api_key"]
    if request.llm_config and request.llm_config.get("base_url"):
        llm_kwargs["base_url"] = request.llm_config["base_url"]

    llm = create_llm("openai", **llm_kwargs)
    await llm.initialize()

    # Classify intent
    classifier = IntentClassifier(llm)
    intent = await classifier.classify(request.message)

    async def event_generator():
        yield f"data: {json.dumps({'type': 'intent', 'data': intent.intent})}\n\n"

        try:
            if intent.intent == "chat":
                # Simple chat
                async for chunk in _simple_chat_stream(llm, request.message):
                    yield chunk

            elif intent.intent == "stats":
                # Statistics
                stats_service = StatsService()
                stats_text = await stats_service.get_stats(request.message, db)
                yield f"data: {json.dumps({'type': 'content', 'content': stats_text})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

            else:  # search
                # Hybrid search + RAG
                try:
                    semantic = SemanticSearch()
                except Exception:
                    semantic = None

                hybrid = HybridSearch(db, semantic) if semantic else None

                search_results = []
                if hybrid:
                    search_results = await hybrid.search(
                        request.message,
                        intent.keywords
                    )

                yield f"data: {json.dumps({'type': 'search_results', 'data': search_results})}\n\n"

                # RAG generation
                chat_service = ChatService(db, llm, None)
                async for chunk in chat_service.chat_with_rag_stream(
                    session_id=request.session_id,
                    user_message=request.message,
                    search_results=search_results
                ):
                    yield chunk
        finally:
            await llm.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


async def _simple_chat_stream(llm, message: str):
    """Simple chat without RAG."""
    from src.llm import Message

    system_prompt = "You are a helpful assistant for GitHub Star Helper."
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=message)
    ]

    async for chunk in llm.chat_stream(messages):
        yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a chat message and get response.

    - **session_id**: Unique session identifier
    - **message**: User's message
    - **use_rag**: Whether to use RAG (search repositories)
    """
    from src.api.app import db
    from src.llm import create_llm
    from src.services.chat import ChatService
    from src.services.search import SearchService

    # Create services
    llm = create_llm("openai")
    await llm.initialize()
    search_service = SearchService(db)
    chat_service = ChatService(db, llm, search_service)

    try:
        if request.use_rag:
            response = await chat_service.chat_with_rag(
                session_id=request.session_id,
                user_message=request.message
            )
        else:
            response = await chat_service.chat(
                session_id=request.session_id,
                user_message=request.message
            )

        return ChatResponse(response=response)

    finally:
        await llm.close()


@router.get("/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation(session_id: str):
    """
    Get conversation history.

    - **session_id**: Session identifier
    """
    from src.api.app import db

    messages = await db.get_conversation(session_id)

    return ConversationHistoryResponse(
        session_id=session_id,
        messages=messages
    )


@router.delete("/{session_id}")
async def delete_conversation(session_id: str):
    """
    Delete a conversation.

    - **session_id**: Session identifier
    """
    from src.api.app import db

    result = await db.delete_conversation(session_id)

    return {"success": result}
