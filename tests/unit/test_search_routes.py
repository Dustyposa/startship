import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


@pytest_asyncio.fixture
async def search_client(db):
    """Create test client with search service initialized"""
    from src.api.app import app
    from src.services.search import SearchService
    import src.api.routes.search as search_routes

    # Create search service with test db
    search_service = SearchService(db)

    # Set the global search_service in app module
    import src.api.app as app_module
    app_module.search_service = search_service

    # Override the dependency
    app.dependency_overrides[search_routes.get_search_service] = lambda: search_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()
    app_module.search_service = None


@pytest.mark.asyncio
async def test_search_endpoint(search_client, db):
    """Test search endpoint"""
    # Add test data
    await db.add_repository({
        "name_with_owner": "test/repo",
        "name": "repo",
        "owner": "test",
        "primary_language": "Python",
        "stargazer_count": 100,
        "categories": ["工具"],
    })

    response = await search_client.get("/api/search?categories=工具")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0


@pytest.mark.asyncio
async def test_categories_endpoint(search_client):
    """Test categories endpoint"""
    response = await search_client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data


@pytest.mark.asyncio
async def test_get_repo_endpoint(search_client, db):
    """Test get repository endpoint"""
    # Add test data
    await db.add_repository({
        "name_with_owner": "test/repo",
        "name": "repo",
        "owner": "test",
        "primary_language": "Python",
        "stargazer_count": 100,
        "categories": ["工具"],
    })

    response = await search_client.get("/api/repo/test/repo")
    assert response.status_code == 200
    data = response.json()
    assert data["name_with_owner"] == "test/repo"


@pytest.mark.asyncio
async def test_get_repo_not_found(search_client):
    """Test get repository returns 404 for non-existent repo"""
    response = await search_client.get("/api/repo/nonexistent/repo")
    assert response.status_code == 404
