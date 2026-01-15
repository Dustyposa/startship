"""
Shared utilities for API routes.

Provides common dependencies and helpers used across multiple route modules.
"""
from fastapi import HTTPException, Depends
from src.db import Database


# ==================== Database Dependencies ====================

def get_db() -> Database:
    """Dependency injection for database instance."""
    from src.api.app import db
    return db


# ==================== Common Response Builders ====================

def build_response(results: list, count: int | None = None) -> dict:
    """Build standard API response with results and count."""
    return {
        "results": results,
        "count": count if count is not None else len(results)
    }


# ==================== Common Error Helpers ====================

def ensure_success(success: bool, error_message: str) -> None:
    """Raise HTTPException if operation failed."""
    if not success:
        raise HTTPException(status_code=500, detail=error_message)


def ensure_entity_exists(entity: object | None, error_message: str = "Entity not found") -> None:
    """Raise HTTPException if entity doesn't exist."""
    if entity is None:
        raise HTTPException(status_code=404, detail=error_message)
