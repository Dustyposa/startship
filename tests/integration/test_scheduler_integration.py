"""
Integration tests for SyncScheduler.

Tests the scheduler lifecycle and job configuration.
"""
import pytest
import asyncio
from unittest.mock import patch
from datetime import datetime

# Import shared test helpers
from tests.integration.test_sync_service_integration import (
    create_test_repo,
    create_mock_github_client_class,
)


# ============================================================================
# Scheduler Lifecycle Tests
# ============================================================================

class TestSchedulerLifecycle:
    """Integration tests for scheduler lifecycle."""

    @pytest.mark.asyncio
    async def test_scheduler_starts_and_stops(self, integration_db):
        """Test that scheduler can start and stop without errors."""
        from src.services.scheduler import SyncScheduler
        from apscheduler.schedulers.base import STATE_STOPPED

        scheduler = SyncScheduler(integration_db)
        scheduler.start()
        assert scheduler.scheduler.running

        scheduler.stop()
        await asyncio.sleep(0.1)
        assert scheduler.scheduler.state == STATE_STOPPED

    @pytest.mark.asyncio
    async def test_scheduler_registers_jobs(self, integration_db):
        """Test that scheduler registers all required jobs."""
        from src.services.scheduler import SyncScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = SyncScheduler(integration_db)
        scheduler.start()

        jobs = scheduler.scheduler.get_jobs()
        job_map = {job.id: job for job in jobs}

        assert 'daily_incremental_sync' in job_map
        assert 'weekly_full_sync' in job_map
        assert isinstance(job_map['daily_incremental_sync'].trigger, CronTrigger)
        assert isinstance(job_map['weekly_full_sync'].trigger, CronTrigger)

        scheduler.stop()


# ============================================================================
# Job Execution Tests
# ============================================================================

class TestJobExecution:
    """Integration tests for job execution."""

    @pytest.mark.asyncio
    async def test_daily_sync_job_executes(self, integration_db):
        """Test that daily sync job can execute."""
        from src.services.scheduler import SyncScheduler

        mock_repos = [create_test_repo(1, "test-repo-1", language="Python")]
        MockClient = create_mock_github_client_class(mock_repos)

        scheduler = SyncScheduler(integration_db)

        with patch('src.services.sync.GitHubClient', MockClient):
            await scheduler._daily_incremental_sync()

        repo = await integration_db.get_repository("user/test-repo-1")
        assert repo is not None

    @pytest.mark.asyncio
    async def test_weekly_sync_job_executes(self, integration_db):
        """Test that weekly sync job can execute."""
        from src.services.scheduler import SyncScheduler

        mock_repos = [create_test_repo(1, "test-repo-2", language="JavaScript")]
        MockClient = create_mock_github_client_class(mock_repos)

        scheduler = SyncScheduler(integration_db)

        with patch('src.services.sync.GitHubClient', MockClient):
            await scheduler._weekly_full_sync()

        repo = await integration_db.get_repository("user/test-repo-2")
        assert repo is not None

    @pytest.mark.asyncio
    async def test_job_handles_errors_gracefully(self, integration_db):
        """Test that jobs handle errors without crashing."""
        from src.services.scheduler import SyncScheduler

        scheduler = SyncScheduler(integration_db)

        with patch.object(scheduler.sync_service, 'incremental_sync', side_effect=Exception("Test error")):
            await scheduler._daily_incremental_sync()


# ============================================================================
# Scheduler State Tests
# ============================================================================

class TestSchedulerState:
    """Integration tests for scheduler state management."""

    @pytest.mark.asyncio
    async def test_scheduler_persists_state(self, integration_db):
        """Test that scheduler maintains state across operations."""
        from src.services.scheduler import SyncScheduler
        from apscheduler.schedulers.base import STATE_STOPPED

        scheduler = SyncScheduler(integration_db)

        scheduler.start()
        assert scheduler.scheduler.running

        scheduler.stop()
        await asyncio.sleep(0.1)
        assert scheduler.scheduler.state == STATE_STOPPED

    @pytest.mark.asyncio
    async def test_scheduler_with_no_github_token(self, integration_db):
        """Test scheduler behavior when no GitHub token is configured."""
        from src.services.scheduler import SyncScheduler
        import os

        original_token = os.getenv('GITHUB_TOKEN')
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']

        try:
            scheduler = SyncScheduler(integration_db)
            scheduler.start()
            assert scheduler.scheduler.running
            scheduler.stop()
        finally:
            if original_token:
                os.environ['GITHUB_TOKEN'] = original_token


# ============================================================================
# Manual Sync Integration Tests
# ============================================================================

class TestManualSyncIntegration:
    """Integration tests for manual sync interaction with scheduler."""

    @pytest.mark.asyncio
    async def test_manual_sync_does_not_interrupt_scheduler(self, integration_db):
        """Test that manual sync operations don't interfere with scheduler."""
        from src.services.scheduler import SyncScheduler

        mock_repos = [create_test_repo(1, "test-repo-1", language="Python")]
        MockClient = create_mock_github_client_class(mock_repos)

        scheduler = SyncScheduler(integration_db)
        scheduler.start()

        with patch('src.services.sync.GitHubClient', MockClient):
            await scheduler.sync_service.full_sync(skip_llm=True)

        assert scheduler.scheduler.running

        repo = await integration_db.get_repository("user/test-repo-1")
        assert repo is not None

        scheduler.stop()

    @pytest.mark.asyncio
    async def test_scheduler_and_manual_sync_share_database(self, integration_db):
        """Test that scheduler and manual sync properly share the database."""
        from src.services.scheduler import SyncScheduler

        scheduler = SyncScheduler(integration_db)
        scheduler.start()

        mock_repos_1 = [create_test_repo(1, "manual-repo", language="Python")]
        MockClient1 = create_mock_github_client_class(mock_repos_1)

        with patch('src.services.sync.GitHubClient', MockClient1):
            await scheduler.sync_service.full_sync(skip_llm=True)

        mock_repos_2 = [create_test_repo(2, "scheduled-repo", language="JavaScript")]
        MockClient2 = create_mock_github_client_class(mock_repos_2)

        with patch('src.services.sync.GitHubClient', MockClient2):
            await scheduler._daily_incremental_sync()

        repo1 = await integration_db.get_repository("user/manual-repo")
        repo2 = await integration_db.get_repository("user/scheduled-repo")

        assert repo1 is not None
        assert repo2 is not None

        scheduler.stop()


# ============================================================================
# Job Timing Tests
# ============================================================================

class TestJobTiming:
    """Integration tests for job timing configuration."""

    @pytest.mark.asyncio
    async def test_jobs_use_cron_trigger(self, integration_db):
        """Test that scheduled jobs use CronTrigger."""
        from src.services.scheduler import SyncScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = SyncScheduler(integration_db)
        scheduler.start()

        jobs = scheduler.scheduler.get_jobs()
        job_map = {job.id: job for job in jobs}

        daily_job = job_map.get('daily_incremental_sync')
        weekly_job = job_map.get('weekly_full_sync')

        assert daily_job is not None
        assert isinstance(daily_job.trigger, CronTrigger)
        assert weekly_job is not None
        assert isinstance(weekly_job.trigger, CronTrigger)

        scheduler.stop()

    @pytest.mark.asyncio
    async def test_jobs_prevent_overlap(self, integration_db):
        """Test that scheduler prevents job overlap via max_instances."""
        from src.services.scheduler import SyncScheduler

        scheduler = SyncScheduler(integration_db)
        scheduler.start()

        jobs = scheduler.scheduler.get_jobs()

        for job in jobs:
            assert job.max_instances == 1

        scheduler.stop()
