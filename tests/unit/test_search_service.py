import pytest
from src.services.search import SearchService


@pytest.mark.asyncio
async def test_search_service_creation(db):
    """Test creating search service"""
    service = SearchService(db)
    assert service.db is not None


@pytest.mark.asyncio
async def test_search_empty_database(db):
    """Test searching empty database"""
    service = SearchService(db)
    results = await service.search()
    assert results == []


@pytest.mark.asyncio
async def test_search_with_data(db):
    """Test searching with data"""
    service = SearchService(db)

    # Add test data
    await db.add_repository({
        "name_with_owner": "owner/repo1",
        "name": "repo1",
        "owner": "owner",
        "primary_language": "Python",
        "stargazer_count": 100,
        "categories": ["工具"],
        "tech_stack": ["Python"]
    })

    results = await service.search(categories=["工具"])
    assert len(results) == 1
    assert results[0]["name_with_owner"] == "owner/repo1"


@pytest.mark.asyncio
async def test_get_repository(db):
    """Test getting a single repository"""
    service = SearchService(db)

    # Add test data
    await db.add_repository({
        "name_with_owner": "owner/repo1",
        "name": "repo1",
        "owner": "owner",
        "primary_language": "Python",
        "stargazer_count": 100,
        "categories": ["工具"],
        "tech_stack": ["Python"]
    })

    result = await service.get_repository("owner/repo1")
    assert result is not None
    assert result["name_with_owner"] == "owner/repo1"


@pytest.mark.asyncio
async def test_get_repository_not_found(db):
    """Test getting non-existent repository"""
    service = SearchService(db)

    result = await service.get_repository("owner/nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_get_similar_repositories(db):
    """Test finding similar repositories"""
    service = SearchService(db)

    # Add test data
    await db.add_repository({
        "name_with_owner": "owner/repo1",
        "name": "repo1",
        "owner": "owner",
        "primary_language": "Python",
        "stargazer_count": 100,
        "categories": ["工具", "后端"],
        "tech_stack": ["Python"]
    })

    await db.add_repository({
        "name_with_owner": "owner/repo2",
        "name": "repo2",
        "owner": "owner",
        "primary_language": "Python",
        "stargazer_count": 50,
        "categories": ["工具"],
        "tech_stack": ["Python"]
    })

    similar = await service.get_similar_repositories("owner/repo1")
    assert len(similar) == 1
    assert similar[0]["name_with_owner"] == "owner/repo2"


@pytest.mark.asyncio
async def test_get_similar_repositories_nonexistent(db):
    """Test finding similar repos for non-existent repo"""
    service = SearchService(db)

    similar = await service.get_similar_repositories("owner/nonexistent")
    assert similar == []


@pytest.mark.asyncio
async def test_get_categories(db):
    """Test getting categories"""
    service = SearchService(db)

    # Add test data
    await db.add_repository({
        "name_with_owner": "owner/repo1",
        "name": "repo1",
        "owner": "owner",
        "primary_language": "Python",
        "stargazer_count": 100,
        "categories": ["工具", "后端"],
        "tech_stack": ["Python"]
    })

    categories = await service.get_categories()
    assert "工具" in categories
    assert categories["工具"] >= 1
