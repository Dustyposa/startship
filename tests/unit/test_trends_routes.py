import pytest
from fastapi.testclient import TestClient
from src.api.app import app


def test_timeline_endpoint():
    """Test timeline endpoint - requires lifespan for database"""
    with TestClient(app) as client:
        response = client.get("/trends/timeline")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_languages_endpoint():
    """Test languages endpoint - requires lifespan for database"""
    with TestClient(app) as client:
        response = client.get("/trends/languages")
        assert response.status_code == 200


def test_categories_endpoint():
    """Test categories endpoint - requires lifespan for database"""
    with TestClient(app) as client:
        response = client.get("/trends/categories")
        assert response.status_code == 200
