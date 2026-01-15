"""
Service for initializing and updating repository data.
"""
from typing import Any
from progress.bar import Bar

from src.config import settings
from src.github.client import GitHubClient
from src.github.graphql import GitHubGraphQLClient
from src.github.models import GitHubRepository
from src.llm import create_llm, LLM
from src.db import Database


# Default analysis when LLM is skipped
def _default_analysis(repo: GitHubRepository) -> dict[str, Any]:
    """Create default analysis without LLM."""
    return {
        "name_with_owner": repo.name_with_owner,
        "summary": repo.description or repo.name_with_owner,
        "categories": [],
        "features": [],
        "tech_stack": [repo.primary_language] if repo.primary_language else [],
        "use_cases": []
    }


def _build_repo_data(repo: GitHubRepository, starred_at, analysis: dict[str, Any]) -> dict[str, Any]:
    """Build repository data dict from GitHub repo and LLM analysis."""
    return {
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
        "readme_content": None,  # Set separately if needed
        "starred_at": starred_at,
        "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
        "created_at": repo.created_at.isoformat() if repo.created_at else None,
        "archived": repo.archived,
        "visibility": repo.visibility,
        "owner_type": repo.owner_type,
        "organization": repo.organization,
        **analysis
    }


async def _analyze_repo(llm: LLM, repo: GitHubRepository, readme: str | None) -> dict[str, Any]:
    """Analyze repository with LLM."""
    print(f"\nAnalyzing {repo.name_with_owner}...")
    return await llm.analyze_repository(
        repo_name=repo.name_with_owner,
        description=repo.description or "",
        readme=readme,
        language=repo.primary_language,
        topics=repo.topics
    )


async def _process_repos(
    repos: list[GitHubRepository],
    db: Database,
    llm: LLM | None,
    skip_llm: bool,
    readme_getter
) -> dict[str, int]:
    """Process repository list and save to database."""
    stats = {"added": 0, "updated": 0, "failed": 0, "errors": []}

    with Bar("Processing", max=len(repos)) as bar:
        for repo in repos:
            try:
                starred_at = getattr(repo, 'starred_at', None)
                existing = await db.get_repository(repo.name_with_owner)
                readme = await readme_getter(repo)

                analysis = (
                    _default_analysis(repo)
                    if skip_llm or not llm
                    else await _analyze_repo(llm, repo, readme)
                )

                repo_data = _build_repo_data(repo, starred_at, analysis)
                if readme:
                    repo_data["readme_content"] = readme[:10000]

                if existing:
                    await db.update_repository(repo.name_with_owner, repo_data)
                    stats["updated"] += 1
                else:
                    await db.add_repository(repo_data)
                    stats["added"] += 1
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"{repo.name_with_owner}: {str(e)}")
                print(f"Error processing {repo.name_with_owner}: {e}")
            bar.next()

    return stats


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
        skip_llm: bool = False,
        force_graphql: bool = False,
        force_rest: bool = False
    ) -> dict[str, any]:
        """
        Initialize database from user's starred repositories.

        Args:
            username: GitHub username (None for authenticated user)
            max_repos: Maximum number of repositories to fetch
            skip_llm: Skip LLM analysis (faster)
            force_graphql: Force use of GraphQL API (requires token)
            force_rest: Force use of REST API

        Returns:
            Statistics about initialization
        """
        if not self.llm and not skip_llm:
            raise ValueError("LLM is required for analysis. Set skip_llm=True or provide an LLM.")

        has_token = bool(settings.github_token and settings.github_token.strip())
        use_graphql = force_graphql or (has_token and not force_rest)

        if use_graphql:
            repos, stats = await self._fetch_with_graphql(username, max_repos)
        else:
            repos, stats = await self._fetch_with_rest(username, max_repos)

        if not repos:
            return stats

        # Process repositories
        processing_stats = await _process_repos(
            repos,
            self.db,
            self.llm,
            skip_llm,
            self._get_readme_for_graphql if use_graphql else self._get_readme_for_rest
        )
        stats.update(processing_stats)

        # Generate vector embeddings if enabled
        await self._generate_embeddings(repos)

        # Build network graph
        await self._build_network_graph()

        return stats

    async def _fetch_with_rest(
        self,
        username: str | None,
        max_repos: int | None
    ) -> tuple[list[GitHubRepository], dict[str, any]]:
        """Fetch repositories using REST API."""
        async with GitHubClient() as github:
            print(f"Fetching starred repositories for {username or 'authenticated user'} using REST API...")
            repos = await github.get_all_starred(username=username, max_results=max_repos)
            print(f"Fetched {len(repos)} repositories using REST API")
            return repos, {"fetched": len(repos), "api_used": "REST"}

    async def _fetch_with_graphql(
        self,
        username: str | None,
        max_repos: int | None
    ) -> tuple[list[GitHubRepository], dict[str, any]]:
        """Fetch repositories using GraphQL API."""
        async with GitHubGraphQLClient() as github:
            print(f"Fetching starred repositories for {username or 'authenticated user'} using GraphQL API...")
            repos = await github.get_starred_repositories(username=username, max_results=max_repos)
            print(f"Fetched {len(repos)} repositories using GraphQL API")
            return repos, {"fetched": len(repos), "api_used": "GraphQL"}

    async def _get_readme_for_rest(self, repo: GitHubRepository) -> str | None:
        """Get README content using REST API (separate call needed)."""
        async with GitHubClient() as github:
            return await github.get_readme_content(repo.owner_login, repo.name)

    async def _get_readme_for_graphql(self, repo: GitHubRepository) -> str | None:
        """Get README content from GraphQL client (cached during fetch)."""
        return getattr(repo, "_readme_content", None)

    async def _generate_embeddings(self, repos: list[GitHubRepository]) -> None:
        """Generate vector embeddings for semantic search."""
        if not self.semantic or not repos:
            return

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

    async def _build_network_graph(self) -> None:
        """Build repository network graph."""
        print("Building repository network graph...")
        from src.services.network import NetworkService

        network_service = NetworkService(self.db, semantic=self.semantic)
        network = await network_service.build_network(top_n=100, k=5)
        await network_service.save_network(network, top_n=100, k=5)
        print(f"Network graph built with {len(network['nodes'])} nodes and {len(network['edges'])} edges")

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

        return {
            "analyzed": 0,
            "failed": 0,
            "message": "Not yet implemented"
        }
