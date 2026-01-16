"""
Graph knowledge API routes.

Provides endpoints for accessing repository relationship data from the graph database.
"""
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .utils import get_db
from ...services.graph.edges import EdgeDiscoveryService


router = APIRouter(prefix="/api/graph", tags=["graph"])


# ==================== Response Models ====================

class EdgeResponse(BaseModel):
    """Response model for a graph edge."""
    source: str
    target: str
    type: str
    weight: float
    metadata: Optional[str] = None


class GraphStatusResponse(BaseModel):
    """Response model for graph computation status."""
    repo_id: str
    edges_computed_at: Optional[str] = None
    dependencies_parsed_at: Optional[str] = None


class RebuildResponse(BaseModel):
    """Response model for graph rebuild operation."""
    status: str
    edges_count: int


# ==================== Endpoints ====================

@router.get("/nodes/{repo}/edges", response_model=List[EdgeResponse])
async def get_repo_edges(
    repo: str,
    edge_types: Optional[str] = None,
    limit: int = 50,
    db = Depends(get_db)
):
    """
    Get all edges for a repository, sorted by weight.

    Args:
        repo: Repository name_with_owner (e.g., "owner/repo")
        edge_types: Optional comma-separated list of edge types to filter
                   (e.g., "author,ecosystem,collection")
        limit: Maximum number of edges to return (default: 50)

    Returns:
        List of edges connected to the specified repository

    Raises:
        HTTPException: If database query fails
    """
    try:
        # Parse edge types from comma-separated string
        types = edge_types.split(',') if edge_types else None

        # Get edges from database
        edges = await db.get_graph_edges(repo, edge_types=types, limit=limit)

        # Convert database results to response models
        # Note: metadata is stored as JSON string in database
        return [
            EdgeResponse(
                source=e['source_repo'],
                target=e['target_repo'],
                type=e['edge_type'],
                weight=e['weight'],
                metadata=e.get('metadata')
            )
            for e in edges
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve edges for repository '{repo}': {str(e)}"
        )


@router.post("/rebuild", response_model=RebuildResponse)
async def rebuild_graph(db = Depends(get_db)):
    """
    Manually trigger full graph rebuild.

    This endpoint:
    1. Fetches all repositories from the database
    2. Discovers all edge types (author, ecosystem, collection)
    3. Clears existing graph edges
    4. Inserts newly computed edges

    Returns:
        Status message with count of edges created

    Raises:
        HTTPException: If rebuild process fails
    """
    try:
        service = EdgeDiscoveryService()

        # Get all repos (limit to 1000 to prevent memory issues)
        repos = await db.search_repositories(limit=1000, is_deleted=False)

        # Discover all edge types
        all_edges = []

        # Author edges (same owner)
        all_edges.extend(await service.discover_author_edges(repos))

        # Ecosystem edges (same language or topics)
        all_edges.extend(await service.discover_ecosystem_edges(repos))

        # Collection edges (repos in same collection)
        all_edges.extend(await service.discover_collection_edges(db))

        # Clear existing edges
        await db.execute("DELETE FROM graph_edges")

        # Insert new edges
        # Convert metadata dict to JSON string for storage
        for edge in all_edges:
            metadata_str = None
            if edge.get('metadata'):
                metadata_str = json.dumps(edge['metadata'])

            await db.add_graph_edge(
                source_repo=edge['source'],
                target_repo=edge['target'],
                edge_type=edge['type'],
                weight=edge['weight'],
                metadata=metadata_str
            )

        return RebuildResponse(
            status="success",
            edges_count=len(all_edges)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rebuild graph: {str(e)}"
        )


@router.get("/status")
async def get_graph_status(db = Depends(get_db)):
    """
    Get graph computation status.

    Returns a list of repositories with their edge computation timestamps.
    Limited to 10 most recently updated repositories.

    Returns:
        Dictionary containing list of status entries

    Raises:
        HTTPException: If status query fails
    """
    try:
        # Query graph status table
        status = await db.fetch_all(
            """SELECT repo_id, edges_computed_at, dependencies_parsed_at
               FROM graph_status
               ORDER BY edges_computed_at DESC
               LIMIT 10"""
        )

        return {"data": status}

    except Exception as e:
        # If table doesn't exist yet, return empty data
        if "no such table" in str(e).lower():
            return {"data": []}

        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve graph status: {str(e)}"
        )
