"""
Service for initializing and updating repository data.
"""
from typing import Any
from progress.bar import Bar

from src.config import settings
from src.github.client import GitHubClient
from src.github.models import GitHubRepository
from src.llm import create_llm, LLM, Message
from src.db import Database


class InitializationService:
    """
    Service for initializing the database with GitHub star data.

    Fetches repositories, analyzes with LLM, and stores in database.
    """

    def __init__(
        self,
        db: Database,
        llm: LLM | None = None,
        semantic: object | None = None
    ):
        """
        Initialize service.

        Args:
            db: Database instance
            llm: LLM instance (optional)
            semantic: SemanticSearch instance (optional)
        """
        self.db = db
        self.llm = llm
        self.semantic = semantic

    async def initialize_from_stars(
        self,
        username: str | None = None,
        max_repos: int | None = None,
        skip_llm: bool = False
    ) -> dict[str, any]:
        """
        Initialize database from user's starred repositories.

        Args:
            username: GitHub username (None for authenticated user)
            max_repos: Maximum number of repositories to fetch
            skip_llm: Skip LLM analysis (faster)

        Returns:
            Statistics about initialization
        """
        if not self.llm and not skip_llm:
            raise ValueError("LLM is required for analysis. Set skip_llm=True or provide an LLM.")

        stats = {
            "fetched": 0,
            "added": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }

        async with GitHubClient() as github:
            # Fetch starred repositories
            print(f"Fetching starred repositories for {username or 'authenticated user'}...")
            repos = await github.get_all_starred(username=username, max_results=max_repos)
            stats["fetched"] = len(repos)
            print(f"Fetched {len(repos)} repositories")

            if not repos:
                return stats

            # Process each repository
            with Bar("Processing", max=len(repos)) as bar:
                for repo in repos:
                    try:
                        # Get starred_at time from GitHub API response
                        starred_at = getattr(repo, 'starred_at', None)

                        # Check if already exists
                        existing = await self.db.get_repository(repo.name_with_owner)

                        # Get README content
                        readme = await github.get_readme_content(
                            repo.owner_login,
                            repo.name
                        )

                        # Analyze with LLM
                        if not skip_llm and self.llm:
                            print(f"\nAnalyzing {repo.name_with_owner}...")
                            analysis = await self.llm.analyze_repository(
                                repo_name=repo.name_with_owner,
                                description=repo.description or "",
                                readme=readme,
                                language=repo.primary_language,
                                topics=repo.topics
                            )
                        else:
                            analysis = {
                                "name_with_owner": repo.name_with_owner,
                                "summary": repo.description or f"{repo.name_with_owner}",
                                "categories": [],
                                "features": [],
                                "tech_stack": [repo.primary_language] if repo.primary_language else [],
                                "use_cases": []
                            }

                        # Prepare repo data
                        repo_data = {
                            "name_with_owner": repo.name_with_owner,
                            "name": repo.name,
                            "owner": repo.owner_login,
                            "description": repo.description,
                            "primary_language": repo.primary_language,
                            "topics": repo.topics,
                            "stargazer_count": repo.stargazer_count,
                            "fork_count": repo.fork_count,
                            "url": repo.url,
                            "homepage_url": repo.homepage_url,
                            "readme_path": f"{settings.readme_storage_path}/{repo.name_with_owner.replace('/', '_')}.md",
                            "readme_content": readme[:10000] if readme else None,  # Cache first 10k chars
                            "starred_at": starred_at,
                            **analysis
                        }

                        # Add or update
                        if existing:
                            await self.db.update_repository(repo.name_with_owner, repo_data)
                            stats["updated"] += 1
                        else:
                            await self.db.add_repository(repo_data)
                            stats["added"] += 1

                    except Exception as e:
                        stats["failed"] += 1
                        stats["errors"].append(f"{repo.name_with_owner}: {str(e)}")
                        print(f"Error processing {repo.name_with_owner}: {e}")

                    bar.next()

        # Generate vector embeddings if semantic search enabled
        if self.semantic and repos:
            print("Generating vector embeddings...")
            await self.semantic.add_repositories([
                {
                    "name_with_owner": repo.name_with_owner,
                    "name": repo.name,
                    "description": repo.description or "",
                    "primary_language": repo.primary_language or "",
                    "url": repo.url,
                    "topics": repo.topics or []
                }
                for repo in repos
            ])
            print("Vector embeddings generated")

        return stats

    async def analyze_existing_repos(
        self,
        limit: int | None = None,
        force: bool = False
    ) -> dict[str, any]:
        """
        Analyze existing repositories in database without LLM data.

        Args:
            limit: Maximum number of repositories to analyze
            force: Re-analyze even if already analyzed

        Returns:
            Statistics about analysis
        """
        if not self.llm:
            raise ValueError("LLM is required for analysis")

        # For now, this is a placeholder - we'd need to add a method
        # to search for repos without analysis in the database
        return {
            "analyzed": 0,
            "failed": 0,
            "message": "Not yet implemented"
        }
