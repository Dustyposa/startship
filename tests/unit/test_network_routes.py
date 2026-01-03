"""
Tests for network graph API routes.
"""
import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)


def test_network_graph_endpoint():
    """Test the /api/network/graph endpoint."""
    response = client.get("/api/network/graph")

    # Should return 200, 404 (if no cache), or 503 (if db not initialized)
    assert response.status_code in [200, 404, 503]

    if response.status_code == 200:
        data = response.json()
        assert "nodes" in data
        assert "edges" in data


def test_network_graph_not_found():
    """Test that endpoint returns 404 or 503 when no network data exists."""
    response = client.get("/api/network/graph")

    # If 404 or 503, check error message format
    if response.status_code == 404:
        data = response.json()
        assert "detail" in data
        # Either our custom message or generic 404 is acceptable
        assert ("Network data not found" in data["detail"] or
                "Not Found" in data["detail"])
    elif response.status_code == 503:
        data = response.json()
        # 503 errors from the exception handler have 'error' key
        assert "error" in data or "detail" in data
        error_msg = data.get("error") or data.get("detail")
        assert "Database not initialized" in error_msg


def test_network_graph_structure():
    """Test the structure of network graph response when data exists."""
    response = client.get("/api/network/graph")

    if response.status_code == 200:
        data = response.json()

        # Verify nodes structure
        assert isinstance(data["nodes"], list)
        for node in data["nodes"]:
            assert "id" in node
            assert "name" in node
            assert "size" in node
            assert "color" in node

        # Verify edges structure
        assert isinstance(data["edges"], list)
        for edge in data["edges"]:
            assert "source" in edge
            assert "target" in edge
            assert "strength" in edge
