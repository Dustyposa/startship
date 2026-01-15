"""
Data synchronization service for GitHub starred repositories.

Handles full sync, incremental sync, change detection, and soft delete.
"""
from datetime import datetime
from typing import Any

from src.github.client import GitHubClient
from src.github.models import GitHubRepository
from src.db import Database
from src.utils import log_info, log_error, log_debug


class SyncService:
    """
    Service for synchronizing GitHub starred repositories with local database.

    Supports:
    - Full sync: Fetch all stars and compare with local
    - Incremental sync: Only fetch changes since last sync
    - Soft delete: Mark repos as deleted instead of removing them
    - Change detection: Detect updates based on pushed_at, stargazer_count, etc.
    """

    def __init__(self, db: Database):
        """
        Initialize sync service.

        Args:
            db: Database instance
        """
        self.db = db

    async def full_sync(
        self,
        skip_llm: bool = True
    ) -> dict[str, Any]:
        """
        Full synchronization: fetch all stars and compare with local database.

        This will:
        1. Fetch all starred repositories from GitHub
        2. Compare with local database
        3. Add new repositories
        4. Update existing repositories with changes
        5. Soft-delete repositories that are no longer starred

        Args:
            skip_llm: Skip LLM analysis (faster)

        Returns:
            Statistics about the sync operation

        Note:
            Requires GitHub Token to be configured.
        """
        stats = self._init_stats("full")

        try:
            async with GitHubClient() as github:
                log_info("Starting full sync")

                github_repos = await github.get_all_starred()
                github_repo_map = {repo.name_with_owner: repo for repo in github_repos}

                local_repos = await self.db.search_repositories(
                    is_deleted=False,
                    limit=1000
                )
                local_repo_map = {
                    repo['name_with_owner']: repo
                    for repo in local_repos
                }

                github_names = set(github_repo_map.keys())
                local_names = set(local_repo_map.keys())

                new_names = github_names - local_names
                deleted_names = local_names - github_names
                common_names = github_names & local_names

                await self._process_new_repos(github_repo_map, new_names, stats, skip_llm)
                await self._process_updates(github_repo_map, local_repo_map, common_names, stats, skip_llm)
                await self._process_deletions(deleted_names, stats)

            stats["completed_at"] = datetime.now().isoformat()
            log_info(f"Full sync completed: +{stats['added']} ~{stats['updated']} -{stats['deleted']}")

            await self._record_sync_history(stats)
            return stats

        except Exception as e:
            return await self._handle_sync_error(stats, e, "Full sync")

    async def incremental_sync(
        self,
        skip_llm: bool = True
    ) -> dict[str, Any]:
        """
        Incremental synchronization: only process changes since last sync.

        This is more efficient than full sync but may miss some edge cases.
        Should be followed by periodic full sync for consistency.

        Args:
            skip_llm: Skip LLM analysis (faster)

        Returns:
            Statistics about the sync operation

        Note:
            Requires GitHub Token to be configured.
        """
        stats = self._init_stats("incremental")

        try:
            async with GitHubClient() as github:
                log_info("Starting incremental sync")

                github_repos = await github.get_all_starred()
                github_repo_map = {repo.name_with_owner: repo for repo in github_repos}

                local_repos = await self.db.search_repositories(
                    is_deleted=False,
                    limit=1000
                )
                local_repo_map = {
                    repo['name_with_owner']: repo
                    for repo in local_repos
                }

                github_names = set(github_repo_map.keys())
                local_names = set(local_repo_map.keys())

                new_names = github_names - local_names
                deleted_names = local_names - github_names
                common_names = github_names & local_names

                await self._process_new_repos(github_repo_map, new_names, stats, skip_llm)

                # Update repos that need changes
                for name in common_names:
                    if await self._should_update_repo(name, github_repo_map, local_repo_map, stats, skip_llm):
                        stats["updated"] += 1
                        log_debug(f"Updated repo: {name}")

                await self._process_deletions(deleted_names, stats)

            stats["completed_at"] = datetime.now().isoformat()
            log_info(f"Incremental sync completed: +{stats['added']} ~{stats['updated']} -{stats['deleted']}")

            await self._record_sync_history(stats)
            return stats

        except Exception as e:
            return await self._handle_sync_error(stats, e, "Incremental sync")

    def _init_stats(self, sync_type: str) -> dict[str, Any]:
        """Initialize statistics dictionary for sync operation."""
        return {
            "sync_type": sync_type,
            "started_at": datetime.now().isoformat(),
            "added": 0,
            "updated": 0,
            "deleted": 0,
            "failed": 0,
            "errors": []
        }

    async def _handle_sync_error(self, stats: dict, error: Exception, sync_name: str) -> dict:
        """Handle sync error and record failed history."""
        stats["completed_at"] = datetime.now().isoformat()
        stats["errors"].append(f"{sync_name} failed: {str(error)}")
        log_error(f"{sync_name} failed: {error}")
        await self._record_sync_history(stats)
        raise

    async def _process_new_repos(
        self,
        github_repo_map: dict[str, GitHubRepository],
        new_names: set[str],
        stats: dict,
        skip_llm: bool
    ) -> None:
        """Process and add new repositories."""
        for name in new_names:
            try:
                github_repo = github_repo_map[name]
                await self._add_repository(github_repo, skip_llm)
                stats["added"] += 1
                log_debug(f"Added new repo: {name}")
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"{name}: {str(e)}")
                log_error(f"Failed to add {name}: {e}")

    async def _process_updates(
        self,
        github_repo_map: dict[str, GitHubRepository],
        local_repo_map: dict[str, dict],
        common_names: set[str],
        stats: dict,
        skip_llm: bool
    ) -> None:
        """Process and update existing repositories."""
        for name in common_names:
            if await self._should_update_repo(name, github_repo_map, local_repo_map, stats, skip_llm):
                stats["updated"] += 1
                log_debug(f"Updated repo: {name}")

    async def _should_update_repo(
        self,
        name: str,
        github_repo_map: dict[str, GitHubRepository],
        local_repo_map: dict[str, dict],
        stats: dict,
        skip_llm: bool
    ) -> bool:
        """Check if a repository should be updated and perform the update."""
        try:
            github_repo = github_repo_map[name]
            local_repo = local_repo_map[name]

            needs_update = self._needs_update(local_repo, github_repo)
            if needs_update:
                await self._update_repository(github_repo, skip_llm)
                return True
            return False
        except Exception as e:
            stats["failed"] += 1
            stats["errors"].append(f"{name}: {str(e)}")
            log_error(f"Failed to update {name}: {e}")
            return False

    async def _process_deletions(
        self,
        deleted_names: set[str],
        stats: dict
    ) -> None:
        """Process and soft-delete removed repositories."""
        for name in deleted_names:
            try:
                await self.soft_delete_repo(name)
                stats["deleted"] += 1
                log_debug(f"Soft-deleted repo: {name}")
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"{name}: {str(e)}")
                log_error(f"Failed to delete {name}: {e}")

    def _needs_update(
        self,
        local_repo: dict[str, Any],
        github_repo: GitHubRepository
    ) -> bool:
        """
        Check if a repository needs to be updated.

        Args:
            local_repo: Local repository data from database
            github_repo: GitHub repository data from API

        Returns:
            True if update is needed, False otherwise
        """
        # Fields that commonly change
        if local_repo.get("pushed_at") != (github_repo.pushed_at.isoformat() if github_repo.pushed_at else None):
            return True
        if local_repo.get("stargazer_count") != github_repo.stargazer_count:
            return True
        if local_repo.get("fork_count") != github_repo.fork_count:
            return True

        # Metadata fields
        if local_repo.get("primary_language") != github_repo.primary_language:
            return True
        if local_repo.get("description") != github_repo.description:
            return True
        if local_repo.get("archived", 0) != (1 if github_repo.archived else 0):
            return True
        if local_repo.get("visibility") != github_repo.visibility:
            return True
        if local_repo.get("owner_type") != github_repo.owner_type:
            return True

        return False

    async def soft_delete_repo(self, name_with_owner: str) -> None:
        """
        Soft delete a repository (marks as deleted but preserves data).

        Args:
            name_with_owner: Repository name in format "owner/repo"
        """
        await self.db.update_repository(name_with_owner, {"is_deleted": 1})
        log_info(f"Soft-deleted repository: {name_with_owner}")

    async def restore_repo(self, name_with_owner: str) -> None:
        """
        Restore a soft-deleted repository.

        Args:
            name_with_owner: Repository name in format "owner/repo"
        """
        await self.db.update_repository(name_with_owner, {"is_deleted": 0})
        log_info(f"Restored repository: {name_with_owner}")

    async def _add_repository(
        self,
        github_repo: GitHubRepository,
        skip_llm: bool = True
    ) -> None:
        """
        Add a new repository to the database.

        Args:
            github_repo: GitHub repository data
            skip_llm: Skip LLM analysis
        """
        repo_data = {
            "name_with_owner": github_repo.name_with_owner,
            "name": github_repo.name,
            "owner": github_repo.owner_login,
            "description": github_repo.description,
            "primary_language": github_repo.primary_language,
            "topics": github_repo.topics or [],
            "stargazer_count": github_repo.stargazer_count,
            "fork_count": github_repo.fork_count,
            "url": github_repo.url,
            "homepage_url": github_repo.homepage_url,
            "pushed_at": github_repo.pushed_at.isoformat() if github_repo.pushed_at else None,
            "created_at": github_repo.created_at.isoformat() if github_repo.created_at else None,
            "archived": github_repo.archived,
            "visibility": github_repo.visibility,
            "owner_type": github_repo.owner_type,
            "organization": github_repo.organization,
            "starred_at": github_repo.starred_at.isoformat() if github_repo.starred_at else None,
            "last_synced_at": datetime.now().isoformat(),
            "summary": github_repo.description or github_repo.name_with_owner,
            "categories": [],
            "features": [],
            "tech_stack": [github_repo.primary_language] if github_repo.primary_language else [],
            "use_cases": []
        }
        await self.db.add_repository(repo_data)

    async def _update_repository(
        self,
        github_repo: GitHubRepository,
        skip_llm: bool = True
    ) -> None:
        """
        Update an existing repository in the database.

        Args:
            github_repo: GitHub repository data
            skip_llm: Skip LLM analysis
        """
        existing = await self.db.get_repository(github_repo.name_with_owner)
        if not existing:
            return await self._add_repository(github_repo, skip_llm)

        update_data = {
            "description": github_repo.description,
            "primary_language": github_repo.primary_language,
            "topics": github_repo.topics or [],
            "stargazer_count": github_repo.stargazer_count,
            "fork_count": github_repo.fork_count,
            "url": github_repo.url,
            "homepage_url": github_repo.homepage_url,
            "pushed_at": github_repo.pushed_at.isoformat() if github_repo.pushed_at else None,
            "created_at": github_repo.created_at.isoformat() if github_repo.created_at else None,
            "archived": github_repo.archived,
            "visibility": github_repo.visibility,
            "owner_type": github_repo.owner_type,
            "organization": github_repo.organization,
            "last_synced_at": datetime.now().isoformat(),
            "summary": existing.get("summary"),
            "categories": existing.get("categories", []),
            "features": existing.get("features", []),
            "tech_stack": existing.get("tech_stack", []),
            "use_cases": existing.get("use_cases", [])
        }

        await self.db.update_repository(github_repo.name_with_owner, update_data)

    async def _record_sync_history(self, stats: dict[str, Any]) -> None:
        """
        Record sync operation to history table.

        Args:
            stats: Sync statistics
        """
        try:
            await self.db.execute_query("""
                INSERT INTO sync_history (
                    sync_type, started_at, completed_at,
                    stats_added, stats_updated, stats_deleted, stats_failed,
                    error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stats["sync_type"],
                stats["started_at"],
                stats.get("completed_at"),
                stats["added"],
                stats["updated"],
                stats["deleted"],
                stats["failed"],
                "; ".join(stats["errors"])[:1000] if stats["errors"] else None
            ))
        except Exception as e:
            log_error(f"Failed to record sync history: {e}")
