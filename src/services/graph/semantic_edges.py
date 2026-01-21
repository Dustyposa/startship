"""Semantic edge discovery service for knowledge graph."""
import json
from typing import List, Dict, Any

from loguru import logger


class SemanticEdgeDiscovery:
    """Discover and store semantic similarity edges between repositories."""

    DEFAULT_TOP_K = 10
    DEFAULT_MIN_SIMILARITY = 0.6

    def __init__(self, semantic_search, db):
        """Initialize semantic edge discovery service.

        Args:
            semantic_search: SemanticSearch instance for vector similarity
            db: Database instance for storing edges
        """
        self.semantic_search = semantic_search
        self.db = db

    async def discover_and_store_edges(
        self,
        top_k: int = DEFAULT_TOP_K,
        min_similarity: float = DEFAULT_MIN_SIMILARITY
    ) -> Dict[str, int]:
        """Discover and store semantic edges for all repositories.

        Performs a full rebuild of all semantic edges.

        Args:
            top_k: Number of similar repos to find for each repo
            min_similarity: Minimum similarity score to create an edge

        Returns:
            Dict with stats: {"repos_processed": int, "edges_created": int}
        """
        await self.db.execute_query(
            "DELETE FROM graph_edges WHERE edge_type = 'semantic'"
        )

        repos = await self.db.get_all_repositories()
        edges_created = 0
        repos_processed = 0

        for repo in repos:
            repo_name = repo.get("name_with_owner")
            if not repo_name:
                continue

            try:
                edges = await self._find_edges(repo_name, top_k, min_similarity)
                if edges:
                    await self.db.batch_insert_graph_edges(edges)
                    edges_created += len(edges)
                repos_processed += 1
            except Exception as e:
                logger.warning(f"Failed to process {repo_name}: {e}")

        logger.info(f"Semantic edge discovery complete: {repos_processed} repos, {edges_created} edges")

        return {
            "repos_processed": repos_processed,
            "edges_created": edges_created
        }

    async def update_edges_for_repo(
        self,
        repo_name: str,
        top_k: int = DEFAULT_TOP_K,
        min_similarity: float = DEFAULT_MIN_SIMILARITY
    ) -> None:
        """Update semantic edges for a single repository.

        Deletes old edges and creates new ones. Used for incremental updates.

        Args:
            repo_name: Repository identifier (e.g., "anthropic/claude-docs")
            top_k: Number of similar repos to find
            min_similarity: Minimum similarity score
        """
        try:
            await self.db.execute_query(
                "DELETE FROM graph_edges WHERE edge_type = 'semantic' AND (source_repo = ? OR target_repo = ?)",
                (repo_name, repo_name)
            )

            edges = await self._find_edges(repo_name, top_k, min_similarity)
            if edges:
                await self.db.batch_insert_graph_edges(edges)
                logger.info(f"Updated semantic edges for {repo_name}: {len(edges)} edges created")

        except Exception as e:
            logger.warning(f"Failed to update semantic edges for {repo_name}: {e}")

    async def _find_edges(
        self,
        repo_name: str,
        top_k: int,
        min_similarity: float
    ) -> List[Dict[str, Any]]:
        """Find similar repos and prepare edge documents.

        Args:
            repo_name: Source repository
            top_k: Number of similar repos to find
            min_similarity: Minimum similarity threshold

        Returns:
            List of edge dictionaries ready for database insertion
        """
        similar_repos = await self.semantic_search.get_similar_repos(
            repo_name, top_k=top_k
        )

        edges = []
        for similar_repo in similar_repos:
            score = similar_repo.get("score", 0)
            if score >= min_similarity:
                edges.append({
                    "source_repo": repo_name,
                    "target_repo": similar_repo["name_with_owner"],
                    "edge_type": "semantic",
                    "weight": score,
                    "metadata": json.dumps({"similarity": score}, ensure_ascii=False)
                })

        return edges
