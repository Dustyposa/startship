import pytest
from src.db import create_database

@pytest.mark.asyncio
async def test_starred_at_column_exists():
    db = create_database()
    await db.initialize()

    # Check if starred_at column exists
    cursor = await db._connection.execute(
        "PRAGMA table_info(repositories)"
    )
    columns = await cursor.fetchall()
    column_names = [col[1] for col in columns]

    assert "starred_at" in column_names

    await db.close()
