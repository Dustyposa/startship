"""Pytest configuration and fixtures for Starship tests."""

import pytest
import pytest_asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import asyncio


@pytest_asyncio.fixture(scope="session")
async def shared_db():
    """Create a shared test database instance for the entire test session.

    This significantly improves test performance by initializing the database
    only once per session instead of per test.

    Uses a shared cache mode so the same in-memory database is accessible
    from all database connections in the test session.
    """
    from src.db import create_database

    # Use file-based database for proper sharing across connections
    # This allows session-scoped fixture to work correctly
    temp_db = tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False)
    db_path = temp_db.name
    temp_db.close()

    db = create_database("sqlite", db_path=db_path)

    # Initialize database schema once
    await db.initialize()

    yield db

    # Cleanup only at end of session
    await db.close()
    # Clean up the temp file
    try:
        Path(db_path).unlink()
    except Exception:
        pass


@pytest_asyncio.fixture
async def db(shared_db):
    """Get a database instance with cleaned data for each test.

    This uses the shared connection but cleans data between tests.
    """
    # Clean all tables before each test
    await _clean_database(shared_db)

    yield shared_db


async def _clean_database(db):
    """Clean all database tables without closing the connection."""
    tables_to_clean = [
        "repositories", "sync_history", "graph_edges",
        "user_notes", "user_tags", "user_collections", "user_collection_repos"
    ]

    for table in tables_to_clean:
        try:
            await db.execute_query(f"DELETE FROM {table}")
        except Exception:
            pass  # Table might not exist yet


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_github_client():
    """Mock GitHub client for testing."""
    with patch('src.data.github_client.GitHubClient') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_chroma_db():
    """Mock ChromaDB for testing."""
    with patch('src.vector_db.chroma_manager.ChromaManager') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_repo_data():
    """Sample repository data for testing."""
    return {
        'id': 123456,
        'name': 'test-repo',
        'full_name': 'user/test-repo',
        'description': 'A test repository',
        'html_url': 'https://github.com/user/test-repo',
        'stargazers_count': 100,
        'forks_count': 20,
        'language': 'Python',
        'created_at': '2023-01-01T00:00:00Z',
        'updated_at': '2023-12-01T00:00:00Z',
        'pushed_at': '2023-12-01T00:00:00Z',
        'archived': False,
        'private': False,
    }


@pytest.fixture
def sample_code_content():
    """Sample code content for testing."""
    return '''
def hello_world():
    """A simple hello world function."""
    print("Hello, World!")
    return "Hello, World!"


class Calculator:
    """A simple calculator class."""

    def add(self, a, b):
        """Add two numbers."""
        return a + b

    def subtract(self, a, b):
        """Subtract two numbers."""
        return a - b
'''


@pytest.fixture
def app_config():
    """Sample application configuration for testing."""
    return {
        'app': {
            'name': 'Starship Test',
            'version': '1.0.0',
            'environment': 'test'
        },
        'github': {
            'api_token': 'test_token',
            'timeout': 30
        },
        'chroma_db': {
            'host': 'localhost',
            'port': 8000,
            'persist_directory': './test_data/chroma_db'
        },
        'health_scoring': {
            'weights': {
                'activity': 0.3,
                'quality': 0.25,
                'community': 0.25,
                'maintenance': 0.2
            }
        }
    }
