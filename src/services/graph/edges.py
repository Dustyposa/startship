from typing import List, Dict, Any
from loguru import logger


class EdgeDiscoveryService:
    """Service for discovering relationships between repositories."""

    async def discover_author_edges(self, repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Discover edges based on common author/organization.

        Groups repositories by owner and creates edges between repositories
        that share the same owner. Only creates edges when an owner has
        multiple repositories.

        Args:
            repos: List of repository dictionaries containing at minimum
                   'owner' and 'name_with_owner' fields

        Returns:
            List of edge dictionaries with format:
            {
                "source": "owner/repo1",
                "target": "owner/repo2",
                "type": "author",
                "weight": 1.0,
                "metadata": {"author": "owner"}
            }

        Raises:
            ValueError: If repos is not a list

        Example:
            >>> repos = [
            ...     {"owner": "tiangolo", "name_with_owner": "tiangolo/fastapi"},
            ...     {"owner": "tiangolo", "name_with_owner": "tiangolo/typer"},
            ... ]
            >>> edges = await service.discover_author_edges(repos)
            >>> len(edges)
            1
        """
        if not isinstance(repos, list):
            raise ValueError("repos must be a list")

        # Handle empty input
        if not repos:
            logger.info("Empty repo list, no author edges to discover")
            return []

        # Group by owner with validation
        owner_repos: Dict[str, List[str]] = {}
        skipped_count = 0

        for repo in repos:
            if not isinstance(repo, dict):
                logger.warning(f"Skipping non-dict repo item: {repo}")
                skipped_count += 1
                continue

            # Safely get and validate owner field
            owner = repo.get('owner', '')

            # Skip empty or whitespace-only owners
            if not owner or not isinstance(owner, str) or not owner.strip():
                skipped_count += 1
                continue

            owner = owner.strip()

            # Safely get and validate name_with_owner field
            name_with_owner = repo.get('name_with_owner')

            if not name_with_owner or not isinstance(name_with_owner, str) or not name_with_owner.strip():
                logger.warning(f"Skipping repo with invalid name_with_owner for owner '{owner}'")
                skipped_count += 1
                continue

            name_with_owner = name_with_owner.strip()

            # Validate format (should contain "/")
            if '/' not in name_with_owner:
                logger.warning(f"Skipping repo with invalid name_with_owner format: {name_with_owner}")
                skipped_count += 1
                continue

            # Initialize list for new owner
            if owner not in owner_repos:
                owner_repos[owner] = []

            owner_repos[owner].append(name_with_owner)

        if skipped_count > 0:
            logger.warning(f"Skipped {skipped_count} repos due to missing or invalid fields")

        # Create edges between repos of same owner
        edges = []
        for owner, repo_list in owner_repos.items():
            # Only create edges if owner has multiple repos
            if len(repo_list) > 1:
                # Create all pairwise combinations
                for i, repo1 in enumerate(repo_list):
                    for repo2 in repo_list[i+1:]:
                        edges.append({
                            "source": repo1,
                            "target": repo2,
                            "type": "author",
                            "weight": 1.0,
                            "metadata": {"author": owner}
                        })

        logger.info(f"Discovered {len(edges)} author edges from {len(repos)} repositories")
        return edges
