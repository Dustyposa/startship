import pytest
from fastapi.testclient import TestClient
from src.api.app import app


def test_full_request_flow():
    """Test complete request flow"""
    with TestClient(app) as client:
        # 1. Check health
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # 2. Get stats (should have empty database)
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_repositories"] == 0

        # 3. Root endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert "service" in response.json()


def test_error_handling():
    """Test error handling"""
    with TestClient(app) as client:
        # Test 404
        response = client.get("/nonexistent")
        assert response.status_code == 404

        # Test invalid method
        response = client.post("/health")
        # Should either return 405 or handle gracefully
        assert response.status_code in [200, 405]
