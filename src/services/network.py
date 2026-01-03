from typing import Any
import json
from datetime import datetime
from src.db import Database
from src.vector.semantic import SemanticSearch


class NetworkService:
    """Service for building and managing repository relationship networks."""

    def __init__(self, db: Database, semantic: SemanticSearch | None = None) -> None:
        self.db = db
        self.semantic = semantic

    async def calculate_category_similarity(
        self,
        repo_a: dict[str, Any],
        repo_b: dict[str, Any]
    ) -> float:
        """
        Calculate Jaccard similarity between two repositories based on categories.

        J(A,B) = |A ∩ B| / |A ∪ B|
        """
        cats_a = set(repo_a.get("categories", []))
        cats_b = set(repo_b.get("categories", []))

        if not cats_a or not cats_b:
            return 0.0

        intersection = cats_a & cats_b
        union = cats_a | cats_b

        if not union:
            return 0.0

        return len(intersection) / len(union)

    async def calculate_semantic_similarity(
        self,
        repo_a: dict[str, Any],
        repo_b: dict[str, Any]
    ) -> float:
        """
        Calculate semantic similarity using ChromaDB vector search.

        Returns 0.0 if semantic search is not available.
        """
        if not self.semantic:
            return 0.0

        try:
            name_a = repo_a.get("name_with_owner", "")
            name_b = repo_b.get("name_with_owner", "")

            # Use semantic search to find similarity
            # Query for repo_b, check if repo_a appears in results with score
            results = await self.semantic.search(name_b, top_k=10)

            for result in results:
                if result.get("name_with_owner") == name_a:
                    # Return normalized score (0-1)
                    return result.get("similarity_score", 0.0)

            return 0.0
        except Exception as e:
            # Silently fall back to category-only similarity
            return 0.0

    async def calculate_similarity(
        self,
        repo_a: dict[str, Any],
        repo_b: dict[str, Any]
    ) -> float:
        """
        Calculate combined similarity score.

        Combines category and semantic similarity with equal weight.
        Falls back to category-only if semantic search unavailable.
        """
        category_sim = await self.calculate_category_similarity(repo_a, repo_b)
        semantic_sim = await self.calculate_semantic_similarity(repo_a, repo_b)

        # Weighted combination: 50% category + 50% semantic
        # If semantic is unavailable, effectively 100% category
        if semantic_sim == 0.0:
            return category_sim

        return 0.5 * category_sim + 0.5 * semantic_sim

    async def build_network(
        self,
        top_n: int = 100,
        k: int = 5
    ) -> dict[str, Any]:
        """
        Build network graph with nodes and edges.

        Args:
            top_n: Number of top repositories to include (by star count)
            k: Number of edges per node (top-k most similar)

        Returns:
            Dictionary with 'nodes' and 'edges' lists
        """
        if top_n <= 0 or k <= 0:
            raise ValueError("top_n and k must be positive integers")
        if top_n > 500:
            raise ValueError("top_n is limited to 500 for performance reasons")

        # Get top N repositories by star count
        cursor = await self.db._connection.execute(
            """
            SELECT name_with_owner, description, stargazer_count, categories, primary_language
            FROM repositories
            WHERE stargazer_count IS NOT NULL
            ORDER BY stargazer_count DESC
            LIMIT ?
            """,
            (top_n,)
        )
        rows = await cursor.fetchall()

        if not rows:
            return {"nodes": [], "edges": []}

        repos = []
        for name_with_owner, description, stars, categories, primary_language in rows:
            # Parse categories from JSON string if needed
            if isinstance(categories, str):
                try:
                    categories = json.loads(categories)
                except json.JSONDecodeError:
                    categories = []

            repos.append({
                "name_with_owner": name_with_owner,
                "description": description,
                "stargazer_count": stars,
                "categories": categories or [],
                "primary_language": primary_language
            })

        # Build nodes
        nodes = []
        for repo in repos:
            # Size = number of categories
            size = len(repo.get("categories", []))

            # Color = heatmap based on stars (green -> yellow -> red)
            color = self._get_color_by_stars(repo["stargazer_count"])

            nodes.append({
                "id": repo["name_with_owner"],
                "name": repo["name_with_owner"].split("/")[-1],
                "size": size,
                "color": color,
                "starCount": repo["stargazer_count"],
                "categories": repo.get("categories", []),
                "language": repo.get("primary_language", "Unknown")
            })

        # Build edges (top-k for each node)
        edges = []
        seen_edges = set()
        for i, repo_a in enumerate(repos):
            similarities = []

            for j, repo_b in enumerate(repos):
                if i == j:
                    continue

                sim = await self.calculate_similarity(repo_a, repo_b)
                similarities.append({
                    "target": repo_b["name_with_owner"],
                    "strength": sim
                })

            # Sort by similarity and take top-k
            similarities.sort(key=lambda x: x["strength"], reverse=True)
            top_k = similarities[:k]

            for edge in top_k:
                edge_key = (repo_a["name_with_owner"], edge["target"])
                if edge["strength"] > 0 and edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges.append({
                        "source": repo_a["name_with_owner"],
                        "target": edge["target"],
                        "strength": edge["strength"]
                    })

        return {"nodes": nodes, "edges": edges}

    def _get_color_by_stars(self, stars: int) -> str:
        """
        Generate heatmap color based on star count.

        Green (low) -> Yellow (medium) -> Red (high)
        """
        # Normalize: 0 to 10000+ stars
        normalized = min(stars / 10000, 1.0)

        # HSL: 120 (green) -> 0 (red)
        hue = 120 - (normalized * 120)

        return f"hsl({hue}, 70%, 50%)"

    async def save_network(
        self,
        network: dict[str, Any],
        top_n: int,
        k: int
    ) -> None:
        """Save network data to cache."""
        # Serialize with error handling
        try:
            nodes_json = json.dumps(network["nodes"])
            edges_json = json.dumps(network["edges"])
        except (TypeError, ValueError) as e:
            raise ValueError(f"Network data is not JSON-serializable: {e}")

        # Atomic INSERT OR REPLACE to avoid race condition
        await self.db._connection.execute(
            """
            INSERT OR REPLACE INTO network_cache
            (id, nodes, edges, top_n, k, updated_at)
            VALUES (1, ?, ?, ?, ?, ?)
            """,
            (nodes_json, edges_json, top_n, k, datetime.now())
        )

        await self.db._connection.commit()

    async def get_cached_network(self) -> dict[str, Any] | None:
        """Get cached network data."""
        cursor = await self.db._connection.execute(
            "SELECT nodes, edges FROM network_cache ORDER BY updated_at DESC LIMIT 1"
        )
        row = await cursor.fetchone()

        if not row:
            return None

        nodes_json, edges_json = row

        # Deserialize with error handling
        try:
            nodes = json.loads(nodes_json)
            edges = json.loads(edges_json)
        except json.JSONDecodeError:
            # Cache is corrupted, delete it and return None
            await self.db._connection.execute("DELETE FROM network_cache")
            await self.db._connection.commit()
            return None

        return {
            "nodes": nodes,
            "edges": edges
        }
