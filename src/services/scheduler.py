"""
Background scheduler for periodic data synchronization.

Uses APScheduler to run daily incremental syncs and weekly full syncs.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Optional

from src.db import Database
from src.services.sync import SyncService
from src.utils import log_info, log_error


class SyncScheduler:
    """
    Scheduler for automatic repository synchronization.

    Schedules:
    - Daily incremental sync at 2:00 AM
    - Weekly full sync at 3:00 AM on Sunday

    Note:
        Requires GitHub Token to be configured.
    """

    def __init__(self, db: Database, semantic_search=None, semantic_edge_discovery=None):
        """
        Initialize scheduler.

        Args:
            db: Database instance
            semantic_search: Optional SemanticSearch instance for vector updates
            semantic_edge_discovery: Optional SemanticEdgeDiscovery instance for graph updates
        """
        self.db = db
        self.scheduler = AsyncIOScheduler()
        self.sync_service = SyncService(db, semantic_search, semantic_edge_discovery)

    def start(self) -> None:
        """Start the scheduler with daily and weekly jobs."""
        # Daily incremental sync at 2:00 AM
        self.scheduler.add_job(
            self._daily_incremental_sync,
            CronTrigger(hour=2, minute=0),
            id='daily_incremental_sync',
            name='Daily Incremental Sync',
            max_instances=1,
            replace_existing=True
        )

        # Weekly full sync on Sunday at 3:00 AM
        self.scheduler.add_job(
            self._weekly_full_sync,
            CronTrigger(day_of_week='sun', hour=3, minute=0),
            id='weekly_full_sync',
            name='Weekly Full Sync',
            max_instances=1,
            replace_existing=True
        )

        self.scheduler.start()
        log_info("Sync scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            log_info("Sync scheduler stopped")

    async def _daily_incremental_sync(self) -> None:
        """Run daily incremental synchronization."""
        log_info("Starting daily incremental sync")
        try:
            stats = await self.sync_service.incremental_sync(skip_llm=True)
            log_info(
                f"Daily incremental sync completed: "
                f"+{stats['added']} ~{stats['updated']} -{stats['deleted']}"
            )
        except Exception as e:
            log_error(f"Daily incremental sync failed: {e}")

    async def _weekly_full_sync(self) -> None:
        """Run weekly full synchronization."""
        log_info("Starting weekly full sync")
        try:
            stats = await self.sync_service.full_sync(skip_llm=True)
            log_info(
                f"Weekly full sync completed: "
                f"+{stats['added']} ~{stats['updated']} -{stats['deleted']}"
            )
        except Exception as e:
            log_error(f"Weekly full sync failed: {e}")

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.scheduler.running


# Global scheduler instance
_scheduler: Optional[SyncScheduler] = None


def get_scheduler() -> Optional[SyncScheduler]:
    """Get the global scheduler instance."""
    return _scheduler


def create_scheduler(db: Database, semantic_search=None, semantic_edge_discovery=None) -> SyncScheduler:
    """
    Create and return a new scheduler instance.

    Args:
        db: Database instance
        semantic_search: Optional SemanticSearch instance for vector updates
        semantic_edge_discovery: Optional SemanticEdgeDiscovery instance for graph updates

    Returns:
        SyncScheduler instance
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = SyncScheduler(db, semantic_search, semantic_edge_discovery)
    return _scheduler


def start_scheduler(db: Database, semantic_search=None, semantic_edge_discovery=None) -> SyncScheduler:
    """
    Create and start the scheduler.

    Args:
        db: Database instance
        semantic_search: Optional SemanticSearch instance for vector updates
        semantic_edge_discovery: Optional SemanticEdgeDiscovery instance for graph updates

    Returns:
        Started SyncScheduler instance

    Note:
        Requires GitHub Token to be configured.
    """
    scheduler = create_scheduler(db, semantic_search, semantic_edge_discovery)
    scheduler.start()
    return scheduler


def stop_scheduler() -> None:
    """Stop the global scheduler if running."""
    global _scheduler
    if _scheduler and _scheduler.is_running:
        _scheduler.stop()
        _scheduler = None
