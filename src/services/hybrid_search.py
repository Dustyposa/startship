"""Hybrid search combining FTS and semantic search."""
import asyncio
from src.db import Database
from src.vector.semantic import SemanticSearch


class HybridSearch:
    """Hybrid search merging FTS and semantic results."""

    def __init__(
        self,
        db: Database,
        semantic: SemanticSearch | None = None,
        fts_weight: float = 0.3,
        semantic_weight: float = 0.7
    ):
        """
        Initialize hybrid search.

        Args:
            db: Database instance
            semantic: SemanticSearch instance (optional)
            fts_weight: Weight for FTS scores
            semantic_weight: Weight for semantic scores
        """
        self.db = db
        self.semantic = semantic
        self.fts_weight = fts_weight
        self.semantic_weight = semantic_weight

    async def search(
        self,
        query: str,
        keywords: str | None = None,
        top_k: int = 10
    ) -> list[dict]:
        """
        Perform hybrid search.

        Args:
            query: Original query for semantic search
            keywords: Extracted keywords for FTS (optional)
            top_k: Number of results to return

        Returns:
            List of merged and reranked repositories
        """
        search_term = keywords or query

        # Parallel search
        fts_task = self._fts_search(search_term, top_k * 2)
        semantic_task = self._semantic_search(query, top_k * 2) if self.semantic else asyncio.sleep(0)

        fts_results, semantic_results = await asyncio.gather(
            fts_task,
            semantic_task,
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(fts_results, Exception):
            fts_results = []
        if isinstance(semantic_results, Exception):
            semantic_results = []

        # Merge and rerank
        return self._merge_and_rerank(
            fts_results if isinstance(fts_results, list) else [],
            semantic_results if isinstance(semantic_results, list) else [],
            top_k
        )

    async def _fts_search(self, query: str, limit: int) -> list[dict]:
        """Perform FTS search."""
        try:
            results = await self.db.search_repositories(query, limit=limit)
            return results
        except Exception:
            return []

    async def _semantic_search(self, query: str, top_k: int) -> list[dict]:
        """Perform semantic search."""
        if self.semantic:
            return await self.semantic.search(query, top_k=top_k)
        return []

    def _merge_and_rerank(
        self,
        fts_results: list[dict],
        semantic_results: list[dict],
        top_k: int
    ) -> list[dict]:
        """
        Merge and rerank results from both searches.

        Args:
            fts_results: Results from FTS search
            semantic_results: Results from semantic search
            top_k: Number of final results

        Returns:
            Merged and reranked results
        """
        scores = {}

        # Score FTS results
        for i, repo in enumerate(fts_results):
            name = repo["name_with_owner"]
            fts_score = (1 - i / len(fts_results)) if fts_results else 0
            scores[name] = {
                "repo": repo,
                "score": self.fts_weight * fts_score,
                "match_type": "fts"
            }

        # Add semantic scores
        for i, repo in enumerate(semantic_results):
            name = repo["name_with_owner"]
            semantic_score = (1 - i / len(semantic_results)) if semantic_results else 0

            if name in scores:
                scores[name]["score"] += self.semantic_weight * semantic_score
                scores[name]["match_type"] = "hybrid"
            else:
                scores[name] = {
                    "repo": repo,
                    "score": self.semantic_weight * semantic_score,
                    "match_type": "semantic"
                }

        # Sort by score and return top-k
        sorted_items = sorted(
            scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )[:top_k]

        return [
            {**item["repo"], "match_type": item["match_type"]}
            for _, item in sorted_items
        ]
