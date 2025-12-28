"""
GitHub API client with async support.
"""
import httpx
import base64
from typing import List, Optional, Dict, Any
from src.config import settings
from src.github.models import GitHubRepository, GitHubUser, GitHubReadme


class GitHubClient:
    """
    Async GitHub API client.

    Handles authentication, rate limiting, and pagination.
    """

    API_BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token
        """
        self.token = token or settings.github_token
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Initialize async client"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"GitHubStarHelper/1.0"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        self._client = httpx.AsyncClient(
            base_url=self.API_BASE,
            headers=headers,
            timeout=30.0
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close async client"""
        if self._client:
            await self._client.aclose()

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to GitHub API"""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context.")

        response = await self._client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    # ==================== User Operations ====================

    async def get_user(self, username: str) -> GitHubUser:
        """
        Get user profile.

        Args:
            username: GitHub username

        Returns:
            User data
        """
        data = await self._get(f"/users/{username}")
        return GitHubUser(**data)

    async def get_authenticated_user(self) -> GitHubUser:
        """Get the authenticated user's profile"""
        data = await self._get("/user")
        return GitHubUser(**data)

    # ==================== Repository Operations ====================

    async def get_repository(self, owner: str, repo: str) -> GitHubRepository:
        """
        Get a single repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository data
        """
        data = await self._get(f"/repos/{owner}/{repo}")
        # Handle owner as dict or string - the model handles this
        return GitHubRepository(**data)

    async def get_starred_repositories(
        self,
        username: Optional[str] = None,
        sort: str = "created",
        direction: str = "desc",
        per_page: int = 100,
        page: int = 1
    ) -> List[GitHubRepository]:
        """
        Get repositories starred by a user.

        Args:
            username: Username (None for authenticated user)
            sort: created or updated
            direction: asc or desc
            per_page: Results per page (max 100)
            page: Page number

        Returns:
            List of repositories
        """
        if username:
            endpoint = f"/users/{username}/starred"
        else:
            endpoint = "/user/starred"

        params = {
            "sort": sort,
            "direction": direction,
            "per_page": per_page,
            "page": page
        }

        data = await self._get(endpoint, params=params)

        repos = []
        for item in data:
            # Extract repo from starred response
            repo_data = item.get("repo", item)
            repos.append(GitHubRepository(**repo_data))

        return repos

    async def get_all_starred(
        self,
        username: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> List[GitHubRepository]:
        """
        Get all starred repositories with auto-pagination.

        Args:
            username: Username (None for authenticated user)
            max_results: Maximum number of results to fetch

        Returns:
            List of all starred repositories
        """
        all_repos = []
        page = 1
        per_page = 100

        while True:
            repos = await self.get_starred_repositories(
                username=username,
                per_page=per_page,
                page=page
            )

            if not repos:
                break

            all_repos.extend(repos)

            if max_results and len(all_repos) >= max_results:
                all_repos = all_repos[:max_results]
                break

            if len(repos) < per_page:
                break

            page += 1

        return all_repos

    # ==================== Content Operations ====================

    async def get_readme(self, owner: str, repo: str, branch: str = "main") -> GitHubReadme:
        """
        Get repository README.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (main or master)

        Returns:
            README content
        """
        try:
            data = await self._get(f"/repos/{owner}/{repo}/readme", params={"ref": branch})
            return GitHubReadme(**data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Try master branch
                data = await self._get(f"/repos/{owner}/{repo}/readme", params={"ref": "master"})
                return GitHubReadme(**data)
            raise

    async def get_readme_content(self, owner: str, repo: str) -> Optional[str]:
        """
        Get decoded README content.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            README text or None
        """
        try:
            readme = await self.get_readme(owner, repo)
            content = base64.b64decode(readme.content).decode("utf-8")
            return content
        except Exception:
            return None
