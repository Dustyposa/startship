import pytest
from fastapi.testclient import TestClient
from src.api.app import app


def test_stats_endpoint_returns_data():
    """Test stats endpoint returns database statistics"""
    with TestClient(app) as client:
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total_repositories" in data["data"]


def test_database_is_initialized():
    """Test database is initialized on startup"""
    # The stats endpoint requires database to be initialized
    with TestClient(app) as client:
        response = client.get("/stats")
        assert response.status_code == 200
        # If database wasn't initialized, would return 503
