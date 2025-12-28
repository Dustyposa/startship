import pytest


@pytest.mark.asyncio
async def test_fts_search(db):
    """Test FTS5 full-text search"""
    # Add test data
    await db.add_repository({
        "name_with_owner": "test/awesome-python-project",
        "name": "awesome-python-project",
        "owner": "test",
        "description": "An awesome Python project for doing great things",
        "summary": "This is a great Python tool",
        "primary_language": "Python",
        "stargazer_count": 100,
        "categories": ["工具"],
        "tech_stack": ["Python"]
    })

    # Search for "Python"
    results = await db.search_repositories_fulltext("Python")
    assert len(results) > 0
    assert "python" in results[0]["name_with_owner"].lower() or \
           "python" in (results[0].get("description") or "").lower()


@pytest.mark.asyncio
async def test_fts_search_empty_query(db):
    """Test FTS5 with empty query returns empty list"""
    results = await db.search_repositories_fulltext("")
    assert results == []


@pytest.mark.asyncio
async def test_fts_search_no_results(db):
    """Test FTS5 with query that has no matches"""
    results = await db.search_repositories_fulltext("nonexistentqueryterm123")
    assert results == []
