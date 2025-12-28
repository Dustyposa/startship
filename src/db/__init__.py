"""
Database package with factory function.
"""
from .base import Database
from .sqlite import SQLiteDatabase

__all__ = ["Database", "SQLiteDatabase", "create_database"]


def create_database(db_type: str = "sqlite", **config) -> Database:
    """
    Factory function to create database instance.

    Args:
        db_type: Type of database ("sqlite" or "postgresql")
        **config: Configuration parameters for the database

    Returns:
        Database instance

    Raises:
        ValueError: If db_type is not supported

    Examples:
        >>> db = create_database("sqlite", db_path="data/starship.db")
        >>> db = create_database("postgresql", host="localhost", database="starship")
    """
    if db_type == "sqlite":
        return SQLiteDatabase(
            db_path=config.get("db_path", config.get("sqlite_path", "data/starship.db"))
        )
    elif db_type == "postgresql":
        # TODO: Implement PostgreSQL
        raise NotImplementedError("PostgreSQL support not yet implemented")
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
