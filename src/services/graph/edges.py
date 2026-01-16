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

    async def discover_ecosystem_edges(
        self,
        repos: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Discover edges based on common primary language or topics.

        Uses Jaccard similarity for topics to find related repositories.

        Args:
            repos: List of repository dictionaries containing at minimum
                   'name_with_owner' field, and optionally 'primary_language'
                   and 'topics' fields

        Returns:
            List of edge dictionaries with format:
            {
                "source": "owner/repo1",
                "target": "owner/repo2",
                "type": "ecosystem",
                "weight": 0.6,
                "metadata": {"language": "Python"}
            }

        Raises:
            ValueError: If repos is not a list

        Example:
            >>> repos = [
            ...     {"name_with_owner": "owner/repo1", "primary_language": "Python", "topics": ["web", "api"]},
            ...     {"name_with_owner": "owner/repo2", "primary_language": "Python", "topics": ["web", "http"]},
            ... ]
            >>> edges = await service.discover_ecosystem_edges(repos)
            >>> len(edges) > 0
            True
        """
        if not isinstance(repos, list):
            raise ValueError("repos must be a list")

        # Handle empty input
        if not repos:
            logger.info("Empty repo list, no ecosystem edges to discover")
            return []

        # Validate repos and extract valid ones
        valid_repos = []
        skipped_count = 0

        for repo in repos:
            if not isinstance(repo, dict):
                logger.warning(f"Skipping non-dict repo item: {repo}")
                skipped_count += 1
                continue

            # Safely get and validate name_with_owner field
            name_with_owner = repo.get('name_with_owner')

            if not name_with_owner or not isinstance(name_with_owner, str) or not name_with_owner.strip():
                logger.warning("Skipping repo with invalid name_with_owner")
                skipped_count += 1
                continue

            name_with_owner = name_with_owner.strip()

            # Validate format (should contain "/")
            if '/' not in name_with_owner:
                logger.warning(f"Skipping repo with invalid name_with_owner format: {name_with_owner}")
                skipped_count += 1
                continue

            # Ensure topics is a list
            topics = repo.get('topics', [])
            if not isinstance(topics, list):
                logger.warning(f"Repo {name_with_owner} has non-list topics, converting to empty list")
                topics = []

            # Create a validated repo dict
            valid_repo = {
                'name_with_owner': name_with_owner,
                'primary_language': repo.get('primary_language'),
                'topics': topics
            }

            valid_repos.append(valid_repo)

        if skipped_count > 0:
            logger.warning(f"Skipped {skipped_count} repos due to missing or invalid fields")

        edges = []

        # Group by primary language
        lang_repos: Dict[str, List[str]] = {}
        for repo in valid_repos:
            lang = repo.get('primary_language')
            if lang and isinstance(lang, str) and lang.strip():
                lang = lang.strip()
                if lang not in lang_repos:
                    lang_repos[lang] = []
                lang_repos[lang].append(repo['name_with_owner'])

        # Create edges for repos with same language (limit to avoid too many)
        for lang, repo_list in lang_repos.items():
            # Only if there are multiple repos with this language
            if len(repo_list) > 1 and len(repo_list) < 50:  # Avoid popular languages
                for i, repo1 in enumerate(repo_list[:20]):  # Limit per language
                    for repo2 in repo_list[i+1:20]:
                        edges.append({
                            "source": repo1,
                            "target": repo2,
                            "type": "ecosystem",
                            "weight": 0.6,
                            "metadata": {"language": lang}
                        })

        # Group by topics (Jaccard similarity)
        for i, repo1 in enumerate(valid_repos):
            topics1 = set(repo1.get('topics', []))
            if not topics1:
                continue

            for repo2 in valid_repos[i+1:]:
                topics2 = set(repo2.get('topics', []))
                if not topics2:
                    continue

                # Calculate Jaccard similarity
                intersection = len(topics1 & topics2)
                union = len(topics1 | topics2)

                if intersection >= 2:  # At least 2 common topics
                    jaccard = intersection / union if union > 0 else 0
                    if jaccard > 0.3:  # Threshold for similarity
                        edges.append({
                            "source": repo1['name_with_owner'],
                            "target": repo2['name_with_owner'],
                            "type": "ecosystem",
                            "weight": round(jaccard, 2),
                            "metadata": {"common_topics": intersection}
                        })

        logger.info(f"Discovered {len(edges)} ecosystem edges from {len(repos)} repositories")
        return edges

    async def discover_collection_edges(
        self,
        db: Any
    ) -> List[Dict[str, Any]]:
        """
        Discover edges based on repos in the same collection.

        Groups repositories by collection and creates edges between repositories
        that are in the same collection. Only creates edges when a collection has
        multiple repositories.

        Args:
            db: Database connection with fetch_all method for executing queries

        Returns:
            List of edge dictionaries with format:
            {
                "source": "repo_id_1",
                "target": "repo_id_2",
                "type": "collection",
                "weight": 0.5,
                "metadata": {"collection": "collection_name"}
            }

        Raises:
            Exception: If database query fails

        Example:
            >>> edges = await service.discover_collection_edges(db)
            >>> len(edges) > 0
            True
        """
        try:
            query = """
                SELECT c1.repo_id as source_repo, c2.repo_id as target_repo, col.name as collection_name
                FROM repo_collections c1
                JOIN repo_collections c2 ON c1.collection_id = c2.collection_id
                JOIN collections col ON col.id = c1.collection_id
                WHERE c1.repo_id < c2.repo_id
            """

            rows = await db.fetch_all(query)

        except Exception as e:
            logger.error(f"Failed to query collection edges: {e}")
            raise

        edges = []
        for row in rows:
            # Validate row has required fields
            if not row.get('source_repo') or not row.get('target_repo'):
                logger.warning(f"Skipping row with missing repo IDs: {row}")
                continue

            edges.append({
                "source": row['source_repo'],
                "target": row['target_repo'],
                "type": "collection",
                "weight": 0.5,
                "metadata": {"collection": row["collection_name"]}
            })

        logger.info(f"Discovered {len(edges)} collection edges")
        return edges
