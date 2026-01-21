"""
Graph knowledge API routes.

Provides endpoints for accessing repository relationship data from the graph database.
"""
import asyncio
import json
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel

from .utils import get_db
from ...services.graph.edges import EdgeDiscoveryService


def run_async_task(coro):
    """Run an async task in a background thread with its own event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()


router = APIRouter(prefix="/api/graph", tags=["graph"])


# ==================== Response Models ====================

class EdgeResponse(BaseModel):
    """Response model for a graph edge."""
    source: str
    target: str
    type: str
    weight: float
    metadata: Optional[str] = None


class RebuildResponse(BaseModel):
    """Response model for graph rebuild operation."""
    status: str
    edges_count: int


class RelatedRepoResponse(BaseModel):
    """Response model for a related repository."""
    name_with_owner: str
    name: str
    owner: str
    description: Optional[str] = None
    primary_language: Optional[str] = None
    stargazer_count: int
    relation_type: str
    relation_weight: float


class RelatedReposResponse(BaseModel):
    """Response model for related repositories list."""
    data: List[RelatedRepoResponse]


# ==================== Helper Functions ====================

def edge_to_response(edge: dict) -> EdgeResponse:
    """Convert database edge dict to EdgeResponse."""
    return EdgeResponse(
        source=edge['source_repo'],
        target=edge['target_repo'],
        type=edge['edge_type'],
        weight=edge['weight'],
        metadata=edge.get('metadata')
    )


def repo_to_related_response(repo: dict, edge_type: str, weight: float) -> RelatedRepoResponse:
    """Convert repository dict to RelatedRepoResponse."""
    return RelatedRepoResponse(
        name_with_owner=repo.get('name_with_owner'),
        name=repo.get('name'),
        owner=repo.get('owner'),
        description=repo.get('description'),
        primary_language=repo.get('primary_language'),
        stargazer_count=repo.get('stargazer_count', 0),
        relation_type=edge_type,
        relation_weight=weight
    )


# ==================== Endpoints ====================

@router.get("/nodes/{repo:path}/edges", response_model=List[EdgeResponse])
async def get_repo_edges(
    repo: str,
    edge_types: Optional[str] = None,
    limit: int = 50,
    db = Depends(get_db)
):
    """Get all edges for a repository, sorted by weight."""
    try:
        types = edge_types.split(',') if edge_types else None
        edges = await db.get_graph_edges(repo, edge_types=types, limit=limit)
        return [edge_to_response(e) for e in edges]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve edges for repository '{repo}': {str(e)}"
        )


@router.post("/rebuild", response_model=RebuildResponse)
async def rebuild_graph(db = Depends(get_db)):
    """Manually trigger full graph rebuild."""
    try:
        service = EdgeDiscoveryService()
        repos = await db.search_repositories(limit=1000, is_deleted=False)

        # Discover all edge types
        author_edges = await service.discover_author_edges(repos)
        ecosystem_edges = await service.discover_ecosystem_edges(repos)
        collection_edges = await service.discover_collection_edges(db)

        all_edges = author_edges + ecosystem_edges + collection_edges

        # Clear and insert new edges
        await db.execute("DELETE FROM graph_edges")
        for edge in all_edges:
            metadata_str = json.dumps(edge['metadata']) if edge.get('metadata') else None
            await db.add_graph_edge(
                source_repo=edge['source'],
                target_repo=edge['target'],
                edge_type=edge['type'],
                weight=edge['weight'],
                metadata=metadata_str
            )

        # Update graph status
        for repo in repos:
            if repo.get('id'):
                await db.update_graph_status(repo['id'], edges_computed=True)

        return RebuildResponse(status="success", edges_count=len(all_edges))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rebuild graph: {str(e)}"
        )


@router.get("/status")
async def get_graph_status(db = Depends(get_db)):
    """Get graph computation status."""
    try:
        status = await db.fetch_all(
            """SELECT repo_id, edges_computed_at, dependencies_parsed_at
               FROM graph_status
               ORDER BY edges_computed_at DESC
               LIMIT 10"""
        )
        return {"data": status}
    except Exception as e:
        if "no such table" in str(e).lower():
            return {"data": []}
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve graph status: {str(e)}"
        )


@router.post("/semantic-edges/rebuild")
async def rebuild_semantic_edges(
    background_tasks: BackgroundTasks,
    top_k: int = Query(10, ge=1, le=50, description="Number of similar repos per repo"),
    min_similarity: float = Query(0.6, ge=0.0, le=1.0, description="Minimum similarity score")
):
    """Trigger full rebuild of semantic edges."""
    from src.api.app import semantic_edge_discovery

    if not semantic_edge_discovery:
        raise HTTPException(
            status_code=503,
            detail="Semantic edge discovery not available (semantic search not configured)"
        )

    logger.info(f"Starting semantic edge rebuild with top_k={top_k}, min_similarity={min_similarity}")

    background_tasks.add_task(
        run_async_task,
        semantic_edge_discovery.discover_and_store_edges(top_k=top_k, min_similarity=min_similarity)
    )

    return {
        "status": "background_task_started",
        "message": "Semantic edge rebuild has been started in the background",
        "parameters": {"top_k": top_k, "min_similarity": min_similarity}
    }


@router.get("/nodes/{repo:path}/related", response_model=RelatedReposResponse)
async def get_related_repos(
    repo: str,
    limit: int = 5,
    db = Depends(get_db)
):
    """Get repositories related to the given repository."""
    try:
        edges = await db.get_graph_edges(repo, limit=limit)

        repos = []
        for edge in edges:
            target_repo = edge['target_repo']
            repo_data = await db.get_repository(target_repo)

            if repo_data:
                repos.append(repo_to_related_response(
                    repo_data,
                    edge['edge_type'],
                    edge['weight']
                ))

        return RelatedReposResponse(data=repos)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve related repos for '{repo}': {str(e)}"
        )
