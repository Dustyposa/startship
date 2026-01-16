# tests/unit/test_graph_edges.py
import pytest
from src.services.graph.edges import EdgeDiscoveryService


@pytest.mark.asyncio
async def test_discover_author_edges():
    service = EdgeDiscoveryService()

    repos = [
        {"name_with_owner": "tiangolo/fastapi", "owner": "tiangolo"},
        {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"},
        {"name_with_owner": "python/cpython", "owner": "python"}
    ]

    edges = await service.discover_author_edges(repos)

    assert len(edges) == 1
    assert edges[0]["source"] == "tiangolo/fastapi"
    assert edges[0]["target"] == "tiangolo/typer"
    assert edges[0]["type"] == "author"
