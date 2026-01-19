"""ChromaDB vector store for repository embeddings."""

import logging
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class ChromaDBStore:
    """ChromaDB vector storage management."""

    def __init__(
        self,
        persist_path: str = "data/chromadb",
        collection_name: str = "github_repos"
    ):
        """
        Initialize ChromaDB store.

        Args:
            persist_path: Persistent storage path
            collection_name: Collection name
        """
        self.persist_path = persist_path
        self.collection_name = collection_name

        # Initialize client
        self.client = chromadb.PersistentClient(
            path=persist_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Cosine similarity
        )

        logger.info(f"ChromaDB initialized at {persist_path}")

    def add(
        self,
        repo_id: str,
        text: str,
        embedding: List[float],
        metadata: Dict[str, any]
    ) -> None:
        """
        Add repository vector.

        Args:
            repo_id: Repository unique identifier (name_with_owner)
            text: Original text
            embedding: Embedding vector
            metadata: Metadata dictionary
        """
        try:
            self.collection.add(
                ids=[repo_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
            logger.debug(f"Added embedding for {repo_id}")
        except Exception as e:
            logger.error(f"Failed to add {repo_id}: {e}")

    def add_batch(
        self,
        repo_ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadata_list: List[Dict[str, any]]
    ) -> int:
        """
        Batch add repository vectors.

        Args:
            repo_ids: Repository ID list
            texts: Text list
            embeddings: Embedding vector list
            metadata_list: Metadata list

        Returns:
            Number of successfully added items
        """
        if not repo_ids:
            return 0

        try:
            self.collection.add(
                ids=repo_ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadata_list
            )
            logger.info(f"Added {len(repo_ids)} embeddings")
            return len(repo_ids)
        except Exception as e:
            logger.error(f"Batch add failed: {e}")
            return 0

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        where: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Vector search.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            where: Metadata filter conditions

        Returns:
            List of search results
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where
            )

            # Format results
            formatted = []
            if results and results['ids'] and results['ids'][0]:
                for i, repo_id in enumerate(results['ids'][0]):
                    formatted.append({
                        "id": repo_id,
                        "score": 1 - results['distances'][0][i],  # Convert to similarity
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                    })

            return formatted

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def delete(self, repo_id: str) -> None:
        """
        Delete repository vector.

        Args:
            repo_id: Repository ID
        """
        try:
            self.collection.delete(ids=[repo_id])
            logger.debug(f"Deleted {repo_id}")
        except Exception as e:
            logger.error(f"Failed to delete {repo_id}: {e}")

    def get_count(self) -> int:
        """
        Get total vector count.

        Returns:
            Number of vectors
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get count: {e}")
            return 0

    def clear(self) -> None:
        """Clear all data."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.warning("Cleared all embeddings")
        except Exception as e:
            logger.error(f"Failed to clear: {e}")
