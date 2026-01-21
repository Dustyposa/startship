"""Hybrid search combining FTS and semantic search."""
import asyncio
import json
import math
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
        """Initialize hybrid search.

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
        """Hybrid search with query expansion.

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

        seen_repos = {}
        all_results = []

        for expanded_query in expanded_queries:
            search_term = keywords or expanded_query

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

            if not isinstance(fts_results, Exception) and fts_results:
                self._merge_scores(all_results, seen_repos, fts_results, "fts")

            if not isinstance(semantic_results, Exception) and semantic_results:
                self._merge_scores(all_results, seen_repos, semantic_results, "semantic")

        results = self._get_top_k(seen_repos, top_k)

        if results:
            results = await self._enrich_results(results)

        return results

    def _merge_scores(
        self,
        all_results: list[dict],
        seen_repos: dict,
        new_results: list[dict],
        match_type: str
    ) -> None:
        """Merge new results into seen_repos with weighted score fusion.

        Scoring:
        - FTS5: BM25 score (negative, lower is better). Normalize to 0-1 using sigmoid.
        - Semantic: similarity_score (0-1, higher is better).
        - Fusion: final_score = fts_weight * fts_score + semantic_weight * semantic_score
        """
        for repo in new_results:
            name = repo.get("name_with_owner")
            if not name:
                continue

            if match_type == "fts":
                raw_score = repo.get("fts_score", 0)
                normalized_score = 1 / (1 + math.exp(-raw_score / 10))
            else:  # semantic
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

            if match_type == "fts":
                seen_repos[name]["fts_score"] = normalized_score
            else:
                seen_repos[name]["semantic_score"] = normalized_score

            seen_repos[name]["final_score"] = (
                self.fts_weight * seen_repos[name]["fts_score"] +
                self.semantic_weight * seen_repos[name]["semantic_score"]
            )

            if seen_repos[name]["match_type"] != match_type:
                seen_repos[name]["match_type"] = "hybrid"

    def _get_top_k(self, seen_repos: dict, top_k: int) -> list[dict]:
        """Extract top-k results from scored repos."""
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

    async def _fetch_complete_repos(self, repo_names: list[str]) -> dict:
        """Fetch complete repo data from database for enrichment."""
        if not repo_names:
            return {}

        placeholders = ",".join(["?"] * len(repo_names))
        query = f"""
            SELECT name_with_owner, stargazer_count, fork_count, starred_at,
                   created_at, languages, topics
            FROM repositories
            WHERE name_with_owner IN ({placeholders})
            AND is_deleted = 0
        """

        results = await self.db.execute_query(query, repo_names)
        return {r["name_with_owner"]: r for r in results}

    async def _enrich_results(self, results: list[dict]) -> list[dict]:
        """Enrich search results with complete repository data."""
        if not results:
            return results

        repo_names = [r.get("name_with_owner") for r in results
                      if not r.get("stargazer_count")]

        if not repo_names:
            return results

        complete_data = await self._fetch_complete_repos(repo_names)

        for result in results:
            repo_name = result.get("name_with_owner")
            if repo_name in complete_data:
                result.update(complete_data[repo_name])

            if "owner" not in result and "name_with_owner" in result:
                owner_full = result["name_with_owner"]
                result["owner"] = owner_full.split("/")[0] if "/" in owner_full else owner_full

            if "categories" not in result:
                result["categories"] = []

            for json_field in ("languages", "topics"):
                if json_field in result and isinstance(result[json_field], str):
                    try:
                        result[json_field] = json.loads(result[json_field])
                    except (json.JSONDecodeError, TypeError):
                        result[json_field] = []

        return results

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

    # Semantic search management methods (delegated to internal SemanticSearch)
    async def add_repositories(self, repos: list[dict]) -> None:
        """Add repositories to vector store."""
        if self.semantic:
            await self.semantic.add_repositories(repos)

    async def update_repository(self, repo: dict) -> None:
        """Update a single repository in vector store."""
        if self.semantic:
            await self.semantic.update_repository(repo)

    async def delete_repository(self, name_with_owner: str) -> None:
        """Delete a repository from vector store."""
        if self.semantic:
            await self.semantic.delete_repository(name_with_owner)

    async def get_similar_repos(self, repo_name: str, top_k: int = 10) -> list[dict]:
        """Find repositories similar to a given repository."""
        if self.semantic:
            return await self.semantic.get_similar_repos(repo_name, top_k)
        return []
