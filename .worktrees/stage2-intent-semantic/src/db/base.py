"""Base database interface."""

from abc import ABC, abstractmethod


class Database(ABC):
    """Abstract base class for database implementations."""

    def __init__(self):
        self._connection = None

    @abstractmethod
    async def initialize(self):
        """Initialize database connection."""
        pass

    @abstractmethod
    async def close(self):
        """Close database connection."""
        pass
