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
        Hybrid search with query expansion.

        Args:
            query: Search query
            keywords: Optional keywords for FTS
            top_k: Number of results to return

        Returns:
            List of search results
        """
        from src.services.query_expander import QueryExpander

        expander = QueryExpander()
        expanded_queries = await expander.expand(query)

        all_results = []
        seen_repos = {}

        for expanded_query in expanded_queries:
            search_term = keywords or expanded_query

            # Parallel FTS and semantic search
            fts_task = self._fts_search(search_term, top_k * 2)
            semantic_task = (
                self._semantic_search(expanded_query, top_k * 2)
                if self.semantic
                else asyncio.sleep(0)
            )

            fts_results, semantic_results = await asyncio.gather(
                fts_task,
                semantic_task,
                return_exceptions=True
            )

            # Merge results tracking best scores
            if not isinstance(fts_results, Exception) and fts_results:
                self._merge_scores(all_results, seen_repos, fts_results, "fts")

            if not isinstance(semantic_results, Exception) and semantic_results:
                self._merge_scores(all_results, seen_repos, semantic_results, "semantic")

        # Return top-k results
        return self._get_top_k(seen_repos, top_k)

    def _merge_scores(
        self,
        all_results: list[dict],
        seen_repos: dict,
        new_results: list[dict],
        match_type: str
    ) -> None:
        """
        Merge new results into seen_repos with weighted score fusion.

        Scoring:
        - FTS5: BM25 score (negative, lower is better). Normalize to 0-1 using sigmoid.
        - Semantic: similarity_score (0-1, higher is better).
        - Fusion: final_score = fts_weight * fts_score + semantic_weight * semantic_score
        """
        import math

        for repo in new_results:
            name = repo.get("name_with_owner")
            if not name:
                continue

            # Extract raw score based on match type
            if match_type == "fts":
                raw_score = repo.get("fts_score", 0)
                # BM25 score is negative (lower is better). Convert to 0-1 using sigmoid.
                # BM25 typically ranges from -50 to 0. Using -raw_score to flip it.
                normalized_score = 1 / (1 + math.exp(-raw_score / 10))
            else:  # semantic
                # Semantic score is already 0-1
                normalized_score = repo.get("similarity_score", 0)

            if name not in seen_repos:
                seen_repos[name] = {
                    "repo": repo,
                    "fts_score": 0.0,
                    "semantic_score": 0.0,
                    "final_score": 0.0,
                    "match_type": match_type
                }
                all_results.append(repo)

            # Update component scores
            if match_type == "fts":
                seen_repos[name]["fts_score"] = normalized_score
            else:
                seen_repos[name]["semantic_score"] = normalized_score

            # Calculate weighted fusion score
            seen_repos[name]["final_score"] = (
                self.fts_weight * seen_repos[name]["fts_score"] +
                self.semantic_weight * seen_repos[name]["semantic_score"]
            )

            # Update match type if both FTS and semantic found this repo
            if seen_repos[name]["match_type"] != match_type:
                seen_repos[name]["match_type"] = "hybrid"

    def _get_top_k(self, seen_repos: dict, top_k: int) -> list[dict]:
        """
        Extract top-k results from scored repos.

        Returns results sorted by final_score (descending), with score details.
        """
        sorted_items = sorted(
            seen_repos.items(),
            key=lambda x: x[1]["final_score"],
            reverse=True
        )[:top_k]

        return [
            {
                **item["repo"],
                "match_type": item["match_type"],
                "fts_score": round(item["fts_score"], 3),
                "semantic_score": round(item["semantic_score"], 3),
                "final_score": round(item["final_score"], 3)
            }
            for _, item in sorted_items
        ]

    async def _fts_search(self, query: str, limit: int) -> list[dict]:
        """Perform FTS search."""
        try:
            results = await self.db.search_repositories(query, limit=limit)
            for result in results:
                if "match_type" not in result:
                    result["match_type"] = "fts"
            return results
        except Exception:
            return []

    async def _semantic_search(self, query: str, top_k: int) -> list[dict]:
        """Perform semantic search."""
        if self.semantic:
            results = await self.semantic.search(query, top_k=top_k)
            for result in results:
                if "match_type" not in result:
                    result["match_type"] = "semantic"
            return results
        return []
