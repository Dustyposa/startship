"""
Sync API routes.

Provides endpoints for synchronizing GitHub starred repositories.
"""
import asyncio
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from src.services.sync import SyncService
from src.db import Database


router = APIRouter(prefix="/api/sync", tags=["sync"])


# ==================== Dependencies ====================

def get_db() -> Database:
    """Dependency to get database instance."""
    from src.api.app import db
    return db


def get_semantic_search():
    """Dependency to get semantic search instance."""
    from src.api.app import hybrid_search
    return hybrid_search


def get_semantic_edge_discovery():
    """Dependency to get semantic edge discovery instance."""
    from src.api.app import semantic_edge_discovery
    return semantic_edge_discovery


def run_async_task(coro):
    """Run an async task in a background thread with its own event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()


# ==================== Response Models ====================

class SyncStatusResponse(BaseModel):
    """Sync status response."""
    last_sync_at: Optional[str] = None
    sync_type: Optional[str] = None
    total_repos: int = 0
    pending_updates: int = 0


class ManualSyncRequest(BaseModel):
    """Manual sync request."""
    reanalyze: bool = False
    force_update: bool = False
    full_sync: bool = False  # Alias for force_update


class SyncHistoryResponse(BaseModel):
    """Sync history response."""
    id: int
    sync_type: str
    started_at: str
    completed_at: Optional[str] = None
    stats_added: int = 0
    stats_updated: int = 0
    stats_deleted: int = 0
    stats_failed: int = 0
    error_message: Optional[str] = None


# ==================== Endpoints ====================

@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(db: Database = Depends(get_db)):
    """Get current synchronization status."""
    cursor = await db._connection.execute(
        """SELECT * FROM sync_history
           ORDER BY started_at DESC
           LIMIT 1"""
    )
    row = await cursor.fetchone()
    last_sync = dict(row) if row else None

    cursor = await db._connection.execute(
        """SELECT COUNT(*) FROM repositories WHERE is_deleted = 0"""
    )
    total_repos = (await cursor.fetchone())[0]

    cursor = await db._connection.execute(
        """SELECT COUNT(*) FROM repositories
           WHERE is_deleted = 0
           AND (last_synced_at IS NULL
                OR datetime(last_synced_at) < datetime('now', '-1 day'))"""
    )
    pending_updates = (await cursor.fetchone())[0]

    return SyncStatusResponse(
        last_sync_at=last_sync["started_at"] if last_sync else None,
        sync_type=last_sync["sync_type"] if last_sync else None,
        total_repos=total_repos,
        pending_updates=pending_updates
    )


@router.post("/manual")
async def manual_sync(
    request: ManualSyncRequest,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db),
    semantic_search = Depends(get_semantic_search),
    semantic_edge_discovery = Depends(get_semantic_edge_discovery)
):
    """Trigger manual synchronization."""
    sync_service = SyncService(db, semantic_search, semantic_edge_discovery)

    force_update = request.force_update or request.full_sync
    sync_type = "full" if force_update else "incremental"

    background_tasks.add_task(
        run_async_task,
        sync_service.sync(skip_llm=not request.reanalyze, force_update=force_update)
    )

    return {
        "success": True,
        "message": "Sync started in background",
        "sync_type": sync_type
    }


@router.get("/history")
async def get_sync_history(limit: int = 20, db: Database = Depends(get_db)):
    """Get synchronization history."""
    cursor = await db._connection.execute(
        """SELECT * FROM sync_history
           ORDER BY started_at DESC
           LIMIT ?""",
        (limit,)
    )
    rows = await cursor.fetchall()

    return {"results": [dict(row) for row in rows]}


@router.post("/repo/{name_with_owner:path}/reanalyze")
async def reanalyze_repo(
    name_with_owner: str,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db)
):
    """Re-analyze a repository with LLM."""
    background_tasks.add_task(
        run_async_task,
        _reanalyze_task(name_with_owner, db)
    )

    return {
        "success": True,
        "message": f"Repository {name_with_owner} reanalysis queued",
        "status": "queued"
    }


async def _reanalyze_task(name_with_owner: str, db: Database):
    """Async task for reanalyzing a repository."""
    from src.utils import log_error, log_debug

    parts = name_with_owner.split("/")
    if len(parts) != 2:
        log_debug(f"Invalid repo format for reanalysis: {name_with_owner}")
        return

    owner, repo_name = parts

    repo = await db.get_repository(name_with_owner)
    if not repo:
        log_debug(f"Repository not found for reanalysis: {name_with_owner}")
        return

    try:
        from src.github.graphql import GitHubGraphQLClient
        async with GitHubGraphQLClient() as github:
            readme = await github.get_readme_content(owner, repo_name)

        from src.llm import create_llm
        llm = create_llm("openai")

        analysis = await llm.analyze_repository(
            repo_name=name_with_owner,
            description=repo.get("description") or "",
            readme=readme,
            language=repo.get("primary_language"),
            topics=repo.get("topics") or []
        )

        from datetime import datetime
        await db.update_repository(name_with_owner, {
            "summary": analysis.get("summary", repo.get("description")),
            "categories": analysis.get("categories", []),
            "features": analysis.get("features", []),
            "use_cases": analysis.get("use_cases", []),
            "last_analyzed_at": datetime.now().isoformat()
        })

        log_debug(f"Successfully reanalyzed: {name_with_owner}")

    except Exception as e:
        log_error(f"Error reanalyzing {name_with_owner}: {e}")
