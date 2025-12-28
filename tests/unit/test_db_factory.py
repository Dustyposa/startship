import pytest
from src.db import create_database, SQLiteDatabase


def test_create_sqlite_database():
    """Test creating SQLite database"""
    db = create_database("sqlite", db_path=":memory:")
    assert isinstance(db, SQLiteDatabase)


def test_create_sqlite_with_default_path():
    """Test creating SQLite database with default path"""
    db = create_database("sqlite")
    assert isinstance(db, SQLiteDatabase)
    assert db.db_path == "data/starship.db"


def test_create_unsupported_database_type():
    """Test creating unsupported database type raises error"""
    with pytest.raises(ValueError, match="Unsupported database type"):
        create_database("mysql")


def test_create_postgresql_not_implemented():
    """Test PostgreSQL is not yet implemented"""
    with pytest.raises(NotImplementedError):
        create_database("postgresql")
