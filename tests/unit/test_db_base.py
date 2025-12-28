import pytest
from src.db.base import Database


def test_database_is_abstract():
    """Test Database cannot be instantiated directly"""
    with pytest.raises(TypeError):
        Database()


def test_database_has_required_methods():
    """Test Database defines all required abstract methods"""
    abstract_methods = Database.__abstractmethods__

    required_methods = [
        'initialize', 'close',
        'add_repository', 'get_repository', 'search_repositories',
        'update_repository', 'delete_repository',
        'create_conversation', 'get_conversation',
        'save_message', 'delete_conversation',
        'get_statistics'
    ]

    for method in required_methods:
        assert method in abstract_methods, f"Missing abstract method: {method}"
