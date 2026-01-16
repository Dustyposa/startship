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


def get_db() -> Database:
    """Dependency to get database instance."""
    from src.api.app import db
    return db


class SyncStatusResponse(BaseModel):
    """Sync status response."""
    last_sync_at: Optional[str] = None
    sync_type: Optional[str] = None
    total_repos: int = 0
    pending_updates: int = 0


class ManualSyncRequest(BaseModel):
    """Manual sync request."""
    reanalyze: bool = False


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


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(db: Database = Depends(get_db)):
    """
    Get current synchronization status.

    Returns information about the last sync and pending updates.
    """
    # Get last sync history
    cursor = await db._connection.execute(
        """SELECT * FROM sync_history
           ORDER BY started_at DESC
           LIMIT 1"""
    )
    row = await cursor.fetchone()
    last_sync = dict(row) if row else None

    # Count active repos (non-deleted)
    cursor = await db._connection.execute(
        """SELECT COUNT(*) FROM repositories WHERE is_deleted = 0"""
    )
    total_repos = (await cursor.fetchone())[0]


    # Count repos that haven't been synced in over 24 hours (potentially need updates)
    # This is a lightweight proxy - actual changes can only be detected by fetching from GitHub
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
    db: Database = Depends(get_db)
):
    """
    Trigger manual synchronization.

    Args:
        request: Sync request with reanalyze flag
        background_tasks: FastAPI background tasks
        db: Database instance

    Note:
        Requires GitHub Token to be configured.
    """
    sync_service = SyncService(db)

    def run_sync():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                sync_service.sync(skip_llm=not request.reanalyze)
            )
        finally:
            loop.close()

    background_tasks.add_task(run_sync)

    return {
        "success": True,
        "message": "Sync started in background"
    }


@router.get("/history")
async def get_sync_history(limit: int = 20, db: Database = Depends(get_db)):
    """
    Get synchronization history.

    Returns recent sync operations with statistics.
    """
    cursor = await db._connection.execute(
        """SELECT * FROM sync_history
           ORDER BY started_at DESC
           LIMIT ?""",
        (limit,)
    )
    rows = await cursor.fetchall()

    return {
        "results": [dict(row) for row in rows]
    }


@router.post("/repo/{name_with_owner:path}/reanalyze")
async def reanalyze_repo(
    name_with_owner: str,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db)
):
    """
    Re-analyze a repository with LLM.

    Args:
        name_with_owner: Repository name in format "owner/repo"
        background_tasks: FastAPI background tasks
        db: Database instance
    """
    def run_reanalyze():
        """Run the reanalysis in background."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_reanalyze_task(name_with_owner, db))
        except Exception as e:
            print(f"Error reanalyzing {name_with_owner}: {e}")
        finally:
            loop.close()

    background_tasks.add_task(run_reanalyze)

    return {
        "success": True,
        "message": f"Repository {name_with_owner} reanalysis queued",
        "status": "queued"
    }


async def _reanalyze_task(name_with_owner: str, db: Database):
    """Async task for reanalyzing a repository."""
    try:
        # Parse owner and repo
        parts = name_with_owner.split("/")
        if len(parts) != 2:
            return

        owner, repo_name = parts

        # Get existing repository
        repo = await db.get_repository(name_with_owner)
        if not repo:
            return

        # Fetch README from GitHub
        from src.github.client import GitHubClient
        async with GitHubClient() as github:
            readme = await github.get_readme_content(owner, repo_name)

        # Get LLM instance
        from src.llm import create_llm
        llm = create_llm("openai")

        # Analyze with LLM
        analysis = await llm.analyze_repository(
            repo_name=name_with_owner,
            description=repo.get("description") or "",
            readme=readme,
            language=repo.get("primary_language"),
            topics=repo.get("topics") or []
        )

        # Update database with new analysis
        from datetime import datetime
        update_data = {
            "summary": analysis.get("summary", repo.get("description")),
            "categories": analysis.get("categories", []),
            "features": analysis.get("features", []),
            "tech_stack": analysis.get("tech_stack", []),
            "use_cases": analysis.get("use_cases", []),
            "last_analyzed_at": datetime.now().isoformat()
        }

        await db.update_repository(name_with_owner, update_data)

    except Exception as e:
        # Log error but don't fail the request
        print(f"Error reanalyzing {name_with_owner}: {e}")
