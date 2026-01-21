"""
Data synchronization service for GitHub starred repositories.

Handles sync, change detection, and deletion of repositories.
"""
import asyncio
from datetime import datetime
from typing import Any

from src.github.models import GitHubRepository
from src.db import Database
from src.utils import log_info, log_error, log_debug


class SyncService:
    """Service for synchronizing GitHub starred repositories with local database."""

    def __init__(self, db: Database, semantic_search=None, semantic_edge_discovery=None):
        """Initialize sync service.

        Args:
            db: Database instance
            semantic_search: Optional SemanticSearch instance for vector updates
            semantic_edge_discovery: Optional SemanticEdgeDiscovery instance for graph updates
        """
        self.db = db
        self.semantic_search = semantic_search
        self.semantic_edge_discovery = semantic_edge_discovery

    async def sync(
        self,
        skip_llm: bool = True,
        force_update: bool = False
    ) -> dict[str, Any]:
        """Synchronize all starred repositories from GitHub.

        This will:
        1. Fetch all starred repositories from GitHub
        2. Compare with local database
        3. Add new repositories
        4. Update existing repositories with changes
        5. Delete repositories that are no longer starred
        6. Rebuild semantic edges if full_sync

        Args:
            skip_llm: Skip LLM analysis (faster)
            force_update: Force update all repos even if no changes detected

        Returns:
            Statistics about the sync operation
        """
        stats = self._init_stats("full")

        try:
            from src.github.graphql import GitHubGraphQLClient
            import os

            async with GitHubGraphQLClient() as github:
                log_info("Starting sync")

                username = os.getenv("GITHUB_USER")
                if not username:
                    user = await github.get_authenticated_user()
                    username = user.get("login")
                    if not username:
                        raise ValueError("Could not get authenticated user. Please set GITHUB_USER environment variable.")

                github_repos = await github.get_starred_repositories(username)
                github_repo_map = {repo.name_with_owner: repo for repo in github_repos}

                local_repos = await self.db.search_repositories(is_deleted=False, limit=1000)
                local_repo_map = {repo['name_with_owner']: repo for repo in local_repos}

                github_names = set(github_repo_map.keys())
                local_names = set(local_repo_map.keys())

                new_names = github_names - local_names
                deleted_names = local_names - github_names
                common_names = github_names & local_names

                await self._process_new_repos(github_repo_map, new_names, stats, skip_llm)
                await self._process_updates(github_repo_map, local_repo_map, common_names, stats, skip_llm, force_update)
                await self._process_deletions(deleted_names, stats)

            # Full sync: rebuild semantic edges
            if force_update and self.semantic_edge_discovery:
                log_info("Full sync: rebuilding semantic edges...")
                await self.semantic_edge_discovery.discover_and_store_edges(top_k=10, min_similarity=0.6)

            stats["completed_at"] = datetime.now().isoformat()
            log_info(f"Sync completed: +{stats['added']} ~{stats['updated']} -{stats['deleted']}")

            await self._record_sync_history(stats)
            return stats

        except Exception as e:
            return await self._handle_sync_error(stats, e, "Sync")

    def _init_stats(self, sync_type: str) -> dict[str, Any]:
        """Initialize statistics dictionary for sync operation."""
        return {
            "sync_type": sync_type,
            "started_at": datetime.now().isoformat(),
            "added": 0,
            "updated": 0,
            "deleted": 0,
            "failed": 0,
            "errors": [],
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
        skip_llm: bool,
        force_update: bool = False
    ) -> None:
        """Process and update existing repositories."""
        for name in common_names:
            if await self._should_update_repo(name, github_repo_map, local_repo_map, stats, skip_llm, force_update):
                stats["updated"] += 1
                log_debug(f"Updated repo: {name}")

    async def _should_update_repo(
        self,
        name: str,
        github_repo_map: dict[str, GitHubRepository],
        local_repo_map: dict[str, dict],
        stats: dict,
        skip_llm: bool,
        force_update: bool = False
    ) -> bool:
        """Check if a repository should be updated and perform the update."""
        try:
            github_repo = github_repo_map[name]
            local_repo = local_repo_map[name]

            if force_update:
                change_type = "heavy"
                changed_fields = {}
                needs_llm = not skip_llm
            else:
                change_type, changed_fields, needs_llm = self._detect_changes(local_repo, github_repo)
                if change_type == "none":
                    return False

            await self._update_repository(
                name_with_owner=github_repo.name_with_owner,
                github_repo=github_repo,
                change_type=change_type,
                changed_fields=changed_fields,
                needs_llm=needs_llm or not skip_llm,
                skip_llm=skip_llm
            )
            return True
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
        """Process and delete removed repositories."""
        for name in deleted_names:
            try:
                await self.db.delete_repository(name)
                stats["deleted"] += 1
                log_debug(f"Deleted repo: {name}")

                if self.semantic_search:
                    try:
                        await self.semantic_search.delete_repository(name)
                        log_debug(f"Deleted from vector index: {name}")
                    except Exception as e:
                        log_error(f"Failed to delete {name} from vector index: {e}")
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"{name}: {str(e)}")
                log_error(f"Failed to delete {name}: {e}")

    def _detect_changes(
        self,
        local_repo: dict[str, Any],
        github_repo: GitHubRepository
    ) -> tuple[str, dict[str, Any], bool]:
        """Detect what changed between local and GitHub repository.

        Returns:
            Tuple of (change_type, changed_fields, needs_llm):
            - change_type: "none", "light", "heavy"
            - changed_fields: Dict of field names to new values
            - needs_llm: Whether LLM re-analysis is needed
        """
        if local_repo.get("pushed_at") != (github_repo.pushed_at.isoformat() if github_repo.pushed_at else None):
            return "heavy", {}, True

        if not local_repo.get("languages"):
            return "heavy", {}, True

        field_map = {
            "stargazer_count": github_repo.stargazer_count,
            "fork_count": github_repo.fork_count,
            "description": github_repo.description,
            "primary_language": github_repo.primary_language,
            "archived": 1 if github_repo.archived else 0,
            "visibility": github_repo.visibility,
            "owner_type": github_repo.owner_type,
        }

        changed_fields = {
            field: value
            for field, value in field_map.items()
            if local_repo.get(field) != value
        }

        if not changed_fields:
            return "none", {}, False

        needs_llm = any(field in changed_fields for field in ("description", "primary_language"))

        return "light", changed_fields, needs_llm

    def _needs_vector_update(self, changed_fields: dict[str, Any]) -> bool:
        """Check if vector index should be updated based on changed fields."""
        return any(field in changed_fields for field in ("description", "primary_language", "topics"))

    def _build_repo_data(self, github_repo: GitHubRepository, existing: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build repository data dict from GitHub repo."""
        base_data = {
            "description": github_repo.description,
            "primary_language": github_repo.primary_language,
            "languages": [lang.model_dump() for lang in github_repo.languages] if github_repo.languages else [],
            "topics": github_repo.topics or [],
            "stargazer_count": github_repo.stargazer_count,
            "fork_count": github_repo.fork_count,
            "url": github_repo.url,
            "homepage_url": github_repo.homepage_url,
            "readme_content": github_repo.readme_content,
            "pushed_at": github_repo.pushed_at.isoformat() if github_repo.pushed_at else None,
            "created_at": github_repo.created_at.isoformat() if github_repo.created_at else None,
            "archived": github_repo.archived,
            "visibility": github_repo.visibility,
            "owner_type": github_repo.owner_type,
            "organization": github_repo.organization,
            "last_synced_at": datetime.now().isoformat(),
            "starred_at": github_repo.starred_at.isoformat() if github_repo.starred_at else None,
        }

        if existing:
            base_data.update({
                "summary": existing.get("summary"),
                "categories": existing.get("categories", []),
                "features": existing.get("features", []),
                "use_cases": existing.get("use_cases", [])
            })
        else:
            base_data.update({
                "name_with_owner": github_repo.name_with_owner,
                "name": github_repo.name,
                "owner": github_repo.owner_login,
                "starred_at": github_repo.starred_at.isoformat() if github_repo.starred_at else None,
                "summary": github_repo.description or github_repo.name_with_owner,
                "categories": [],
                "features": [],
                "use_cases": []
            })

        return base_data

    async def _trigger_semantic_edge_update(self, name_with_owner: str) -> None:
        """Trigger semantic edge update asynchronously."""
        if self.semantic_edge_discovery:
            asyncio.create_task(
                self.semantic_edge_discovery.update_edges_for_repo(name_with_owner)
            )

    async def _update_vector_index(self, name_with_owner: str) -> bool:
        """Update vector index for a repository."""
        if not self.semantic_search:
            return False

        try:
            updated_repo = await self.db.get_repository(name_with_owner)
            if updated_repo:
                await self.semantic_search.update_repository(updated_repo)
                log_debug(f"Updated vector index: {name_with_owner}")
                return True
        except Exception as e:
            log_error(f"Failed to update vector index for {name_with_owner}: {e}")

        return False

    async def _add_repository(
        self,
        github_repo: GitHubRepository,
        skip_llm: bool = True
    ) -> None:
        """Add a new repository to the database."""
        repo_data = self._build_repo_data(github_repo)
        await self.db.add_repository(repo_data)

        if self.semantic_search:
            try:
                await self.semantic_search.add_repositories([repo_data])
            except Exception as e:
                log_error(f"Failed to add {github_repo.name_with_owner} to vector index: {e}")

    async def _update_repository(
        self,
        name_with_owner: str,
        github_repo: GitHubRepository,
        change_type: str,
        changed_fields: dict[str, Any],
        needs_llm: bool,
        skip_llm: bool = True
    ) -> None:
        """Update an existing repository in the database."""
        existing = await self.db.get_repository(name_with_owner)
        if not existing:
            await self._add_repository(github_repo, skip_llm)
            return

        if change_type == "light":
            if needs_llm and not skip_llm:
                update_data = self._build_repo_data(github_repo, existing)
                await self.db.update_repository(name_with_owner, update_data)
                log_debug(f"Light update with LLM: {name_with_owner} (fields: {list(changed_fields.keys())})")
            else:
                update_data = changed_fields.copy()
                update_data.update({
                    "summary": existing.get("summary"),
                    "categories": existing.get("categories", []),
                    "features": existing.get("features", []),
                    "use_cases": existing.get("use_cases", [])
                })
                await self.db.update_repository(name_with_owner, update_data)
                log_debug(f"Light update without LLM: {name_with_owner} (fields: {list(changed_fields.keys())})")

            if self.semantic_search and self._needs_vector_update(changed_fields):
                await self._update_vector_index(name_with_owner)
                await self._trigger_semantic_edge_update(name_with_owner)
        else:  # heavy
            update_data = self._build_repo_data(github_repo, existing)
            await self.db.update_repository(name_with_owner, update_data)
            log_debug(f"Heavy update: {name_with_owner}")

            if self.semantic_search:
                await self._update_vector_index(name_with_owner)
                await self._trigger_semantic_edge_update(name_with_owner)

    async def _record_sync_history(self, stats: dict[str, Any]) -> None:
        """Record sync operation to history table."""
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
