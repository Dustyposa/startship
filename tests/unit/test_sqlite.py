import pytest
import pytest_asyncio
from aiosqlite import Error as AiosqliteError
from src.db.sqlite import SQLiteDatabase


@pytest_asyncio.fixture
async def db():
    """Create a test database"""
    db = SQLiteDatabase(":memory:")  # Use in-memory database for tests
    await db.initialize()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_initialize_creates_tables(db):
    """Test database initialization creates all tables"""
    async with db._connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ) as cursor:
        tables = [row[0] for row in await cursor.fetchall()]

    assert "repositories" in tables
    assert "repo_categories" in tables
    assert "conversations" in tables
    assert "messages" in tables


@pytest.mark.asyncio
async def test_add_repository(db):
    """Test adding a repository"""
    repo_data = {
        "name_with_owner": "test/repo",
        "name": "repo",
        "owner": "test",
        "description": "Test repository",
        "primary_language": "Python",
        "stargazer_count": 100,
        "fork_count": 10,
        "url": "https://github.com/test/repo",
        "categories": ["工具", "测试"],
        "summary": "A test repository"
    }

    result = await db.add_repository(repo_data)
    assert result is True

    # Verify it was added
    retrieved = await db.get_repository("test/repo")
    assert retrieved is not None
    assert retrieved["name_with_owner"] == "test/repo"
    assert retrieved["description"] == "Test repository"


@pytest.mark.asyncio
async def test_search_repositories(db):
    """Test searching repositories"""
    # Add test data
    repos = [
        {
            "name_with_owner": "owner1/repo1",
            "name": "repo1",
            "owner": "owner1",
            "primary_language": "Python",
            "stargazer_count": 100,
            "categories": ["工具"],
        },
        {
            "name_with_owner": "owner2/repo2",
            "name": "repo2",
            "owner": "owner2",
            "primary_language": "JavaScript",
            "stargazer_count": 200,
            "categories": ["前端"],
        },
        {
            "name_with_owner": "owner3/repo3",
            "name": "repo3",
            "owner": "owner3",
            "primary_language": "Python",
            "stargazer_count": 300,
            "categories": ["工具"],
        }
    ]

    for repo in repos:
        await db.add_repository(repo)

    # Test category filter
    results = await db.search_repositories(categories=["工具"])
    assert len(results) == 2

    # Test language filter
    results = await db.search_repositories(languages=["Python"])
    assert len(results) == 2

    # Test min_stars filter
    results = await db.search_repositories(min_stars=200)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_conversation_operations(db):
    """Test conversation CRUD operations"""
    session_id = "test-session-123"

    # Create conversation and add messages
    await db.save_message(session_id, "user", "Hello")
    await db.save_message(session_id, "assistant", "Hi there!")

    # Get conversation
    messages = await db.get_conversation(session_id)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hi there!"

    # Delete conversation
    result = await db.delete_conversation(session_id)
    assert result is True

    # Verify deletion
    messages = await db.get_conversation(session_id)
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_get_statistics(db):
    """Test getting database statistics"""
    # Add test data
    await db.add_repository({
        "name_with_owner": "test/repo1",
        "name": "repo1",
        "owner": "test",
        "categories": ["工具"],
    })

    stats = await db.get_statistics()
    assert stats["total_repositories"] == 1
    assert "工具" in stats["categories"]
    assert stats["categories"]["工具"] == 1


@pytest.mark.asyncio
async def test_batch_insert_graph_edges(db):
    """Test batch insertion of graph edges."""
    # First create the repositories to satisfy foreign key constraints
    await db.add_repository({
        "name_with_owner": "repo1",
        "name": "repo1",
        "owner": "owner1",
        "primary_language": "Python",
    })
    await db.add_repository({
        "name_with_owner": "repo2",
        "name": "repo2",
        "owner": "owner2",
        "primary_language": "Python",
    })
    await db.add_repository({
        "name_with_owner": "repo3",
        "name": "repo3",
        "owner": "owner3",
        "primary_language": "Python",
    })

    edges = [
        {
            "source_repo": "repo1",
            "target_repo": "repo2",
            "edge_type": "semantic",
            "weight": 0.85,
            "metadata": '{"similarity": 0.85}'
        },
        {
            "source_repo": "repo1",
            "target_repo": "repo3",
            "edge_type": "author",
            "weight": 1.0,
            "metadata": '{"author": "test"}'
        }
    ]

    await db.batch_insert_graph_edges(edges)

    # Verify edges were inserted
    result = await db.fetch_all(
        "SELECT * FROM graph_edges WHERE source_repo = 'repo1'"
    )
    assert len(result) == 2
