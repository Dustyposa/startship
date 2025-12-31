import pytest
import pytest_asyncio
from src.db import create_database

@pytest_asyncio.fixture
async def db():
    """Create and initialize a database instance for testing.

    Yields:
        Database: An initialized database instance using in-memory storage.
    """
    db = create_database()
    await db.initialize()
    yield db
    await db.close()

@pytest.mark.asyncio
async def test_starred_at_column_exists(db):
    """Test that the starred_at column exists after migrations run.

    This test verifies that the database migration system correctly
    applies the 001_add_starred_at.sql migration, adding the starred_at
    TIMESTAMP column to the repositories table.

    Args:
        db: Database fixture providing an initialized database instance.
    """
    # Check if starred_at column exists
    cursor = await db._connection.execute(
        "PRAGMA table_info(repositories)"
    )
    columns = await cursor.fetchall()
    column_names = [col[1] for col in columns]

    assert "starred_at" in column_names
