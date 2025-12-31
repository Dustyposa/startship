"""Database package with factory function."""
from .base import Database
from .sqlite import SQLiteDatabase

__all__ = ["Database", "SQLiteDatabase", "create_database"]


def create_database(db_type: str = "sqlite", **config):
    """
    Factory function to create database instance.

    Args:
        db_type: Type of database ("sqlite" or "postgresql")
        **config: Configuration parameters for the database

    Returns:
        Database instance
    """
    if db_type == "sqlite":
        return SQLiteDatabase(
            db_path=config.get("db_path", config.get("sqlite_path", "data/starship.db"))
        )
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
