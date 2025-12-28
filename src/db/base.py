"""
Database abstraction layer.
Supports SQLite and PostgreSQL through a common interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MemoryItem:
    """Memory item for conversation storage"""
    item_id: str
    content: str
    metadata: Dict[str, Any]


class Database(ABC):
    """
    Abstract database interface.

    All database operations must be async.
    Supports both SQLite and PostgreSQL implementations.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize database connection and create tables"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close database connection"""
        pass

    # ==================== Repository Operations ====================

    @abstractmethod
    async def add_repository(self, repo_data: Dict[str, Any]) -> bool:
        """
        Add a repository to the database.

        Args:
            repo_data: Repository data including metadata and LLM analysis

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_repository(
        self,
        name_with_owner: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a repository by name_with_owner.

        Args:
            name_with_owner: Format "owner/repo"

        Returns:
            Repository data or None if not found
        """
        pass

    @abstractmethod
    async def search_repositories(
        self,
        categories: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search repositories with filters.

        Args:
            categories: Filter by categories
            languages: Filter by programming languages
            min_stars: Minimum star count
            max_stars: Maximum star count
            limit: Maximum number of results

        Returns:
            List of matching repositories
        """
        pass

    @abstractmethod
    async def update_repository(
        self,
        name_with_owner: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update an existing repository"""
        pass

    @abstractmethod
    async def delete_repository(self, name_with_owner: str) -> bool:
        """Delete a repository"""
        pass

    # ==================== Conversation Operations ====================

    @abstractmethod
    async def create_conversation(
        self,
        session_id: str
    ) -> int:
        """
        Create a new conversation session.

        Args:
            session_id: Unique session identifier

        Returns:
            Conversation ID
        """
        pass

    @abstractmethod
    async def get_conversation(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all messages in a conversation.

        Args:
            session_id: Session identifier

        Returns:
            List of messages with role and content
        """
        pass

    @abstractmethod
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> int:
        """
        Save a message to a conversation.

        Args:
            session_id: Session identifier
            role: Message role ("user" or "assistant")
            content: Message content

        Returns:
            Message ID
        """
        pass

    @abstractmethod
    async def delete_conversation(self, session_id: str) -> bool:
        """Delete a conversation and all its messages"""
        pass

    # ==================== Statistics ====================

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with counts and metadata
        """
        pass
