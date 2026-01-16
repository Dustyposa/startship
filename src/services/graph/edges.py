# src/services/graph/edges.py
from typing import List, Dict, Any, Optional
from loguru import logger


class EdgeDiscoveryService:
    """Service for discovering relationships between repositories."""

    async def discover_author_edges(self, repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Discover edges based on common author/organization.

        Returns list of edges with format:
        {
            "source": "owner/repo1",
            "target": "owner/repo2",
            "type": "author",
            "weight": 1.0,
            "metadata": {"author": "owner"}
        }
        """
        # Group by owner
        owner_repos: Dict[str, List[str]] = {}
        for repo in repos:
            owner = repo.get('owner', '')
            if owner:
                if owner not in owner_repos:
                    owner_repos[owner] = []
                owner_repos[owner].append(repo['name_with_owner'])

        # Create edges between repos of same owner
        edges = []
        for owner, repo_list in owner_repos.items():
            if len(repo_list) > 1:
                for i, repo1 in enumerate(repo_list):
                    for repo2 in repo_list[i+1:]:
                        edges.append({
                            "source": repo1,
                            "target": repo2,
                            "type": "author",
                            "weight": 1.0,
                            "metadata": f'{{"author": "{owner}"}}'
                        })

        logger.info(f"Discovered {len(edges)} author edges")
        return edges
