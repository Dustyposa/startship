"""Semantic search using ChromaDB."""
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from src.vector.embeddings import OllamaEmbedder


class SemanticSearch:
    """Semantic search using vector embeddings."""

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        persist_path: str = "data/chromadb"
    ):
        """
        Initialize semantic search.

        Args:
            ollama_base_url: Ollama API URL
            model: Embedding model name
            persist_path: ChromaDB persistence path

        Raises:
            ImportError: If chromadb is not installed
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "chromadb is not installed. Semantic search is not available. "
                "Install it with: pip install chromadb"
            )

        self.embedder = OllamaEmbedder(ollama_base_url, model)
        self.client = chromadb.PersistentClient(
            path=persist_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="github_repos",
            metadata={"hnsw:space": "cosine"}
        )

    async def add_repositories(self, repos: list[dict]) -> None:
        """
        Add repositories to vector store.

        Args:
            repos: List of repository data dicts
        """
        if not repos:
            return

        # Generate texts for embedding
        texts = [self._repo_to_text(repo) for repo in repos]
        embeddings = await self.embedder.embed_batch(texts)

        # Prepare data
        ids = [repo["name_with_owner"] for repo in repos]
        metadatas = []
        for repo in repos:
            metadata = {
                "name": repo.get("name", ""),
                "description": repo.get("description", "") or "",
                "primary_language": repo.get("primary_language", "") or "",
                "url": repo.get("url", "")
            }
            metadatas.append(metadata)

        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )

    async def search(self, query: str, top_k: int = 10) -> list[dict]:
        """
        Search for similar repositories.

        Args:
            query: Search query text
            top_k: Number of results to return

        Returns:
            List of repository dicts with similarity scores
        """
        query_embedding = await self.embedder.embed(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # Format results
        repos = []
        if results["ids"] and results["ids"][0]:
            for i, repo_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i] if "distances" in results else 0
                repos.append({
                    "name_with_owner": repo_id,
                    "name": metadata.get("name", ""),
                    "description": metadata.get("description", ""),
                    "primary_language": metadata.get("primary_language", ""),
                    "url": metadata.get("url", ""),
                    "similarity_score": 1 - distance  # Convert to similarity
                })

        return repos

    async def update_repository(self, repo: dict) -> None:
        """
        Update a single repository in vector store.

        Deletes existing embedding and adds new one.

        Args:
            repo: Repository dict with required fields including name_with_owner
        """
        if not repo or not repo.get("name_with_owner"):
            return

        # Delete existing embedding
        try:
            self.collection.delete(ids=[repo["name_with_owner"]])
        except Exception:
            # Ignore if not found
            pass

        # Add new embedding
        await self.add_repositories([repo])

    async def delete_repository(self, name_with_owner: str) -> None:
        """
        Delete a repository from vector store.

        Args:
            name_with_owner: Repository identifier (owner/repo)
        """
        if not name_with_owner:
            return

        try:
            self.collection.delete(ids=[name_with_owner])
        except Exception:
            # Ignore if not found
            pass

    def _repo_to_text(self, repo: dict) -> str:
        """Convert repository dict to text for embedding."""
        parts = [
            repo.get("name", ""),
            repo.get("description", "") or "",
            " ".join(repo.get("topics", []))
        ]
        return " ".join(p for p in parts if p)
