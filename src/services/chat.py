"""
Service for handling chat conversations.
"""
from typing import List, Dict, Any, Optional
from src.db import Database
from src.llm import LLM, Message


class ChatService:
    """Service for managing conversations and chat with LLM"""

    def __init__(self, db: Database, llm: LLM, search_service):
        """
        Initialize chat service.

        Args:
            db: Database instance
            llm: LLM instance
            search_service: Search service for RAG
        """
        self.db = db
        self.llm = llm
        self.search_service = search_service

    async def create_conversation(self, session_id: str) -> int:
        """Create a new conversation"""
        return await self.db.create_conversation(session_id)

    async def get_conversation_history(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return await self.db.get_conversation(session_id)

    async def chat(
        self,
        session_id: str,
        user_message: str,
        context_limit: int = 10
    ) -> str:
        """
        Send a chat message and get response.

        Args:
            session_id: Session identifier
            user_message: User's message
            context_limit: Number of previous messages to include

        Returns:
            Assistant's response
        """
        # Save user message
        await self.db.save_message(session_id, "user", user_message)

        # Get conversation history
        history = await self.db.get_conversation(session_id)

        # Build messages for LLM
        messages = [
            Message(
                role="system",
                content="You are GitHub Star Helper, an AI assistant that helps users analyze and discover their starred GitHub repositories. Be helpful, concise, and respond in Chinese."
            )
        ]

        # Add recent conversation (excluding the one we just saved)
        for msg in history[-context_limit:-1]:
            messages.append(Message(role=msg["role"], content=msg["content"]))

        # Add current user message
        messages.append(Message(role="user", content=user_message))

        # Get LLM response
        response = await self.llm.chat(messages, temperature=0.7)

        # Save assistant response
        await self.db.save_message(session_id, "assistant", response.content)

        return response.content

    async def chat_with_rag(
        self,
        session_id: str,
        user_message: str,
        search_results: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Chat with RAG (Retrieval Augmented Generation).

        Args:
            session_id: Session identifier
            user_message: User's message
            search_results: Pre-fetched search results

        Returns:
            Assistant's response
        """
        # Save user message
        await self.db.save_message(session_id, "user", user_message)

        # Build context from search results
        context = ""
        if search_results:
            context = "\n\nRelevant repositories:\n"
            for repo in search_results[:5]:
                context += f"- {repo['name_with_owner']}: {repo.get('summary', repo.get('description', ''))}\n"

        # Build messages
        messages = [
            Message(
                role="system",
                content=f"""You are GitHub Star Helper, an AI assistant that helps users analyze and discover their starred GitHub repositories.

{context}

Be helpful, concise, and respond in Chinese. Use the repository information above when relevant to the user's question."""
            )
        ]

        # Get recent history
        history = await self.db.get_conversation(session_id)
        for msg in history[-10:-1]:
            messages.append(Message(role=msg["role"], content=msg["content"]))

        # Add current message
        messages.append(Message(role="user", content=user_message))

        # Get response
        response = await self.llm.chat(messages, temperature=0.7)

        # Save and return
        await self.db.save_message(session_id, "assistant", response.content)
        return response.content

    async def delete_conversation(self, session_id: str) -> bool:
        """Delete a conversation"""
        return await self.db.delete_conversation(session_id)
