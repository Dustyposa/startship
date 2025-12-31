"""
FastAPI application module for GitHub Star RAG Service.
Provides global database instance for route handlers.
"""
from src.db import create_database
from src.config import settings

# Global database instance (will be initialized by app startup)
db = None


def get_db():
    """Get database instance."""
    return db


async def initialize_db():
    """Initialize database connection."""
    global db
    db = create_database(
        db_type=settings.db_type,
        sqlite_path=settings.sqlite_path
    )
    await db.initialize()


async def close_db():
    """Close database connection."""
    global db
    if db:
        await db.close()
