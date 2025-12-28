"""
Chat API endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model"""
    session_id: str
    message: str
    use_rag: bool = False


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str


class ConversationHistoryResponse(BaseModel):
    """Conversation history response"""
    session_id: str
    messages: List[dict]


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
