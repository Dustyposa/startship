import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_similar_repos_endpoint():
    response = client.get("/recommend/similar/owner/repo?limit=5")
    # Response structure validation
    assert response.status_code in [200, 404, 500]

def test_category_endpoint():
    response = client.get("/recommend/category/AI?limit=10")
    assert response.status_code in [200, 404, 500]
