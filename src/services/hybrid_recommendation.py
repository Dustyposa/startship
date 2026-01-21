"""Hybrid recommendation service combining graph and semantic similarity."""
from typing import List, Dict, Any, Set, Optional

from loguru import logger


class HybridRecommendationService:
    """Hybrid recommendation service fusing graph edges and semantic similarity."""

    # Weight configuration
    WEIGHT_GRAPH = 0.65
    WEIGHT_SEMANTIC = 0.35
    MAX_GRAPH_SCORE = 2.0
    MAX_REPOS_PER_AUTHOR = 2

    # Edge type weights for normalization
    EDGE_TYPE_WEIGHTS = {
        "author": 1.0,
        "ecosystem": 0.5,
        "collection": 0.5,
    }

    def __init__(self, db, semantic_search=None):
        """Initialize hybrid recommendation service.

        Args:
            db: Database instance
            semantic_search: Optional SemanticSearch instance
        """
        self.db = db
        self.semantic_search = semantic_search

    @staticmethod
    def _parse_repo_name(repo_name: str) -> tuple[str, str]:
        """Parse repository name into owner and name.

        Args:
            repo_name: Repository identifier (e.g., "owner/repo" or just "repo")

        Returns:
            Tuple of (owner, name)
        """
        if "/" in repo_name:
            return repo_name.split("/", 1)
        return repo_name, repo_name

    async def get_recommendations(
        self,
        repo_name: str,
        limit: int = 10,
        include_semantic: bool = True,
        exclude_repos: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get hybrid recommendations for a repository.

        Args:
            repo_name: Repository identifier (e.g., "anthropic/claude-docs")
            limit: Maximum number of recommendations to return
            include_semantic: Whether to include semantic similarity
            exclude_repos: Set of repo names to exclude from results

        Returns:
            List of recommendation dicts with keys:
                - name_with_owner: str
                - name: str
                - owner: str
                - final_score: float
                - sources: List[str]
                - graph_score: Optional[float]
                - semantic_score: Optional[float]
        """
        exclude_repos = exclude_repos or set()

        graph_candidates = await self._recall_from_graph(repo_name)
        semantic_candidates = await self._recall_from_semantic(
            repo_name if include_semantic else None
        )

        fused = self._fuse_scores(graph_candidates, semantic_candidates)
        return self._optimize_diversity(fused, exclude_repos, limit)

    async def _recall_from_graph(self, repo_name: str) -> Dict[str, Dict]:
        """Recall candidates from graph edges.

        Returns:
            Dict mapping repo_name to {score, sources}
        """
        edges = await self.db.get_graph_edges(
            repo=repo_name,
            edge_types=["author", "ecosystem", "collection"]
        )

        candidates = {}
        for edge in edges:
            target = edge["target_repo"]
            edge_type = edge["edge_type"]
            type_weight = self.EDGE_TYPE_WEIGHTS.get(edge_type, 0.5)

            if target not in candidates:
                candidates[target] = {"score": 0.0, "sources": []}

            candidates[target]["score"] += edge["weight"] * type_weight
            candidates[target]["sources"].append(edge_type)

        return candidates

    async def _recall_from_semantic(self, repo_name: Optional[str]) -> Dict[str, Dict]:
        """Recall candidates from semantic similarity.

        Returns:
            Dict mapping repo_name to {score, sources}
        """
        if not repo_name or not self.semantic_search:
            return {}

        try:
            similar = await self.semantic_search.get_similar_repos(repo_name, top_k=20)
            return {
                s["name_with_owner"]: {"score": s["score"], "sources": ["semantic"]}
                for s in similar
            }
        except Exception as e:
            logger.warning(f"Semantic recall failed for {repo_name}: {e}")
            return {}

    def _fuse_scores(
        self,
        graph: Dict[str, Dict],
        semantic: Dict[str, Dict]
    ) -> List[Dict]:
        """Fuse graph and semantic scores with weighted combination.

        Returns:
            List of candidate dicts with fused scores
        """
        fused = []
        all_repos = set(graph.keys()) | set(semantic.keys())

        for repo_name in all_repos:
            graph_data = graph.get(repo_name, {"score": 0.0, "sources": []})
            semantic_data = semantic.get(repo_name, {"score": 0.0, "sources": []})

            graph_score = graph_data["score"]
            semantic_score = semantic_data["score"]

            normalized_graph = min(graph_score / self.MAX_GRAPH_SCORE, 1.0)
            final_score = (
                self.WEIGHT_GRAPH * normalized_graph +
                self.WEIGHT_SEMANTIC * semantic_score
            )

            owner, name = self._parse_repo_name(repo_name)

            fused.append({
                "name_with_owner": repo_name,
                "name": name,
                "owner": owner,
                "graph_score": graph_score if graph_score > 0 else None,
                "semantic_score": semantic_score if semantic_score > 0 else None,
                "final_score": final_score,
                "sources": graph_data["sources"] + semantic_data["sources"]
            })

        return fused

    def _optimize_diversity(
        self,
        candidates: List[Dict],
        exclude_repos: Set[str],
        limit: int
    ) -> List[Dict]:
        """Optimize diversity: deduplicate, exclude, limit per author.

        Args:
            candidates: List of candidate dicts
            exclude_repos: Repos to exclude
            limit: Max results to return

        Returns:
            Optimized and sorted list of recommendations
        """
        filtered = [
            c for c in candidates
            if c["name_with_owner"] not in exclude_repos
        ]

        filtered.sort(key=lambda x: x["final_score"], reverse=True)

        seen_authors: Dict[str, int] = {}
        diverse = []

        for candidate in filtered:
            owner = candidate["owner"]
            count = seen_authors.get(owner, 0)

            if count < self.MAX_REPOS_PER_AUTHOR:
                diverse.append(candidate)
                seen_authors[owner] = count + 1

            if len(diverse) >= limit:
                break

        return diverse
