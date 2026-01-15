"""
Unit tests for SyncScheduler.

Tests the APScheduler-based background synchronization system.
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock


# ============================================================================
# Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def sync_scheduler(db):
    """Create a SyncScheduler instance for testing."""
    from src.services.scheduler import SyncScheduler

    scheduler = SyncScheduler(db)
    yield scheduler

    # Ensure scheduler is stopped after test
    if scheduler.is_running:
        scheduler.stop()


@pytest.fixture
def mock_sync_service():
    """Mock SyncService for testing scheduler methods."""
    with patch('src.services.scheduler.SyncService') as mock:
        instance = mock.return_value
        instance.incremental_sync = AsyncMock(return_value={
            'added': 5,
            'updated': 3,
            'deleted': 1,
            'failed': 0
        })
        instance.full_sync = AsyncMock(return_value={
            'added': 10,
            'updated': 5,
            'deleted': 2,
            'failed': 0
        })
        yield instance


# ============================================================================
# Initialization Tests
# ============================================================================

class TestSyncSchedulerInit:
    """Tests for SyncScheduler initialization."""

    def test_initialization(self, db):
        """Test that SyncScheduler initializes correctly."""
        from src.services.scheduler import SyncScheduler

        scheduler = SyncScheduler(db)

        assert scheduler.db is db
        assert scheduler.scheduler is not None
        assert scheduler.sync_service is not None
        assert not scheduler.is_running

    def test_sync_service_instance(self, db):
        """Test that SyncService is properly instantiated."""
        from src.services.scheduler import SyncScheduler
        from src.services.sync import SyncService

        scheduler = SyncScheduler(db)

        assert isinstance(scheduler.sync_service, SyncService)
        assert scheduler.sync_service.db is db


# ============================================================================
# Job Configuration Tests
# ============================================================================

class TestJobConfiguration:
    """Tests for scheduled job configuration."""

    @pytest.mark.asyncio
    async def test_daily_incremental_sync_job_added(self, sync_scheduler):
        """Test that daily incremental sync job is added with correct trigger."""
        sync_scheduler.start()

        jobs = sync_scheduler.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]

        assert 'daily_incremental_sync' in job_ids

        daily_job = next(j for j in jobs if j.id == 'daily_incremental_sync')
        assert daily_job.name == 'Daily Incremental Sync'
        assert daily_job.max_instances == 1

        # Cleanup
        sync_scheduler.stop()

    @pytest.mark.asyncio
    async def test_weekly_full_sync_job_added(self, sync_scheduler):
        """Test that weekly full sync job is added with correct trigger."""
        sync_scheduler.start()

        jobs = sync_scheduler.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]

        assert 'weekly_full_sync' in job_ids

        weekly_job = next(j for j in jobs if j.id == 'weekly_full_sync')
        assert weekly_job.name == 'Weekly Full Sync'
        assert weekly_job.max_instances == 1

        # Cleanup
        sync_scheduler.stop()

    @pytest.mark.asyncio
    async def test_both_jobs_added_on_start(self, sync_scheduler):
        """Test that both jobs are added when scheduler starts."""
        sync_scheduler.start()

        jobs = sync_scheduler.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]

        assert len(job_ids) == 2
        assert 'daily_incremental_sync' in job_ids
        assert 'weekly_full_sync' in job_ids

        # Cleanup
        sync_scheduler.stop()

    @pytest.mark.asyncio
    async def test_replace_existing_flag(self, sync_scheduler):
        """Test that jobs use replace_existing flag when added."""
        sync_scheduler.start()

        # Get the job IDs - verify we have the expected jobs
        jobs = sync_scheduler.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]

        # Should have exactly 2 jobs with our expected IDs
        assert len(jobs) == 2
        assert 'daily_incremental_sync' in job_ids
        assert 'weekly_full_sync' in job_ids

        # Cleanup
        sync_scheduler.stop()


# ============================================================================
# Lifecycle Tests
# ============================================================================

class TestSchedulerLifecycle:
    """Tests for scheduler start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_starts_scheduler(self, sync_scheduler):
        """Test that start() starts the scheduler."""
        assert not sync_scheduler.is_running

        sync_scheduler.start()

        assert sync_scheduler.is_running

        # Cleanup
        sync_scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop_stops_scheduler(self, sync_scheduler):
        """Test that stop() can be called to stop the scheduler."""
        sync_scheduler.start()
        assert sync_scheduler.is_running

        # Stop should not raise an exception
        sync_scheduler.stop()

    def test_stop_when_not_running_is_safe(self, sync_scheduler):
        """Test that stopping a non-running scheduler is safe."""
        # Should not raise an exception
        sync_scheduler.stop()

    @pytest.mark.asyncio
    async def test_start_multiple_times_raises_error(self, sync_scheduler):
        """Test that starting an already running scheduler raises error."""
        from apscheduler.schedulers import SchedulerAlreadyRunningError

        sync_scheduler.start()
        assert sync_scheduler.is_running

        # Starting again should raise SchedulerAlreadyRunningError
        with pytest.raises(SchedulerAlreadyRunningError):
            sync_scheduler.start()

        # Cleanup
        sync_scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop_multiple_times(self, sync_scheduler):
        """Test that calling stop multiple times is safe."""
        sync_scheduler.start()

        # First stop
        sync_scheduler.stop()

        # Second stop - should be safe (no exception raised)
        sync_scheduler.stop()


# ============================================================================
# Sync Job Methods Tests
# ============================================================================

class TestSyncJobMethods:
    """Tests for sync job execution methods."""

    @pytest.mark.asyncio
    async def test_daily_incremental_sync_success(self, db, mock_sync_service):
        """Test successful daily incremental sync."""
        from src.services.scheduler import SyncScheduler

        scheduler = SyncScheduler(db)
        scheduler.sync_service = mock_sync_service

        await scheduler._daily_incremental_sync()

        mock_sync_service.incremental_sync.assert_called_once_with(skip_llm=True)

    @pytest.mark.asyncio
    async def test_daily_incremental_sync_logs_stats(self, db, mock_sync_service, caplog):
        """Test that daily sync logs statistics."""
        from src.services.scheduler import SyncScheduler

        scheduler = SyncScheduler(db)
        scheduler.sync_service = mock_sync_service

        with patch('src.services.scheduler.log_info') as mock_log:
            await scheduler._daily_incremental_sync()

            # Check that completion was logged with stats
            mock_log.assert_any_call(
                "Daily incremental sync completed: +5 ~3 -1"
            )

    @pytest.mark.asyncio
    async def test_daily_incremental_sync_handles_errors(self, db):
        """Test that daily sync handles errors gracefully."""
        from src.services.scheduler import SyncScheduler

        scheduler = SyncScheduler(db)

        # Mock sync service to raise error
        async def failing_sync(*args, **kwargs):
            raise Exception("Sync failed!")

        scheduler.sync_service.incremental_sync = failing_sync

        with patch('src.services.scheduler.log_error') as mock_log:
            await scheduler._daily_incremental_sync()

            mock_log.assert_called_once()
            assert "Daily incremental sync failed" in mock_log.call_args[0][0]

    @pytest.mark.asyncio
    async def test_weekly_full_sync_success(self, db, mock_sync_service):
        """Test successful weekly full sync."""
        from src.services.scheduler import SyncScheduler

        scheduler = SyncScheduler(db)
        scheduler.sync_service = mock_sync_service

        await scheduler._weekly_full_sync()

        mock_sync_service.full_sync.assert_called_once_with(skip_llm=True)

    @pytest.mark.asyncio
    async def test_weekly_full_sync_logs_stats(self, db, mock_sync_service):
        """Test that weekly sync logs statistics."""
        from src.services.scheduler import SyncScheduler

        scheduler = SyncScheduler(db)
        scheduler.sync_service = mock_sync_service

        with patch('src.services.scheduler.log_info') as mock_log:
            await scheduler._weekly_full_sync()

            # Check that completion was logged with stats
            mock_log.assert_any_call(
                "Weekly full sync completed: +10 ~5 -2"
            )

    @pytest.mark.asyncio
    async def test_weekly_full_sync_handles_errors(self, db):
        """Test that weekly sync handles errors gracefully."""
        from src.services.scheduler import SyncScheduler

        scheduler = SyncScheduler(db)

        # Mock sync service to raise error
        async def failing_sync(*args, **kwargs):
            raise Exception("Sync failed!")

        scheduler.sync_service.full_sync = failing_sync

        with patch('src.services.scheduler.log_error') as mock_log:
            await scheduler._weekly_full_sync()

            mock_log.assert_called_once()
            assert "Weekly full sync failed" in mock_log.call_args[0][0]


# ============================================================================
# Module Functions Tests
# ============================================================================

class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_get_scheduler_initially_none(self):
        """Test that get_scheduler initially returns None."""
        from src.services.scheduler import get_scheduler

        scheduler = get_scheduler()
        assert scheduler is None

    def test_create_scheduler_returns_instance(self, db):
        """Test that create_scheduler returns a SyncScheduler instance."""
        from src.services.scheduler import create_scheduler, SyncScheduler

        # Reset global state for test
        import src.services.scheduler as scheduler_module
        scheduler_module._scheduler = None

        scheduler = create_scheduler(db)

        assert isinstance(scheduler, SyncScheduler)
        assert scheduler.db is db

    def test_create_scheduler_singleton(self, db):
        """Test that create_scheduler returns singleton instance."""
        from src.services.scheduler import create_scheduler

        # Reset global state for test
        import src.services.scheduler as scheduler_module
        scheduler_module._scheduler = None

        scheduler1 = create_scheduler(db)
        scheduler2 = create_scheduler(db)

        assert scheduler1 is scheduler2

    @pytest.mark.asyncio
    async def test_start_scheduler_starts_and_returns(self, db):
        """Test that start_scheduler starts and returns scheduler."""
        from src.services.scheduler import start_scheduler

        # Reset global state for test
        import src.services.scheduler as scheduler_module
        scheduler_module._scheduler = None

        scheduler = start_scheduler(db)

        assert scheduler.is_running

        # Cleanup
        scheduler.stop()
        scheduler_module._scheduler = None

    @pytest.mark.asyncio
    async def test_stop_scheduler(self, db):
        """Test that stop_scheduler stops the global scheduler."""
        from src.services.scheduler import start_scheduler, stop_scheduler, get_scheduler

        # Reset global state for test
        import src.services.scheduler as scheduler_module
        scheduler_module._scheduler = None

        start_scheduler(db)
        assert get_scheduler() is not None
        assert get_scheduler().is_running

        stop_scheduler()

        assert get_scheduler() is None

    def test_stop_scheduler_when_none_is_safe(self):
        """Test that stop_scheduler is safe when scheduler is None."""
        from src.services.scheduler import stop_scheduler

        # Reset global state
        import src.services.scheduler as scheduler_module
        scheduler_module._scheduler = None

        # Should not raise exception
        stop_scheduler()
