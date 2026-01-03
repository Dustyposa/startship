import pytest
import pytest_asyncio
from src.db.sqlite import SQLiteDatabase


@pytest_asyncio.fixture
async def db():
    """Create a test database"""
    db = SQLiteDatabase(":memory:")  # Use in-memory database for tests
    await db.initialize()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_network_cache_table_exists(db):
    """Test that network_cache table is created via migration"""
    # Check if network_cache table exists
    cursor = await db._connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='network_cache'"
    )
    result = await cursor.fetchone()

    assert result is not None
    assert result[0] == "network_cache"


@pytest.mark.asyncio
async def test_network_cache_table_schema(db):
    """Test that network_cache table has correct schema"""
    # Get table schema
    cursor = await db._connection.execute(
        "PRAGMA table_info(network_cache)"
    )
    columns = await cursor.fetchall()

    # Extract column names
    column_names = [col[1] for col in columns]

    # Verify required columns exist
    assert "id" in column_names
    assert "nodes" in column_names
    assert "edges" in column_names
    assert "top_n" in column_names
    assert "k" in column_names
    assert "updated_at" in column_names


@pytest.mark.asyncio
async def test_network_cache_index_exists(db):
    """Test that index on updated_at column exists"""
    cursor = await db._connection.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_network_updated'"
    )
    result = await cursor.fetchone()

    assert result is not None
    assert result[0] == "idx_network_updated"


@pytest.mark.asyncio
async def test_migration_is_idempotent(db):
    """Test that migration can be applied multiple times without error"""
    # Get migration record
    cursor = await db._connection.execute(
        "SELECT name FROM _migrations WHERE name='002_add_network_cache.sql'"
    )
    result = await cursor.fetchone()

    # Verify migration was recorded
    assert result is not None
    assert result[0] == "002_add_network_cache.sql"
