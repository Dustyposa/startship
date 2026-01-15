"""
GitHub REST API client with async support.
"""
import httpx
import base64
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.github.base import GitHubBaseClient
from src.github.models import GitHubRepository, GitHubUser, GitHubReadme


class GitHubClient(GitHubBaseClient):
    """
    Async GitHub REST API client.

    Handles authentication, rate limiting, and pagination.
    """

    async def __aenter__(self):
        """Initialize async client"""
        self._client = await self._init_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close async client"""
        await self.close()

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to GitHub API"""
        self._check_client()
        response = await self._client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    # ==================== User Operations ====================

    async def get_user(self, username: str) -> GitHubUser:
        """Get user profile."""
        data = await self._get(f"/users/{username}")
        return GitHubUser(**data)

    async def get_authenticated_user(self) -> GitHubUser:
        """Get the authenticated user's profile"""
        data = await self._get("/user")
        return GitHubUser(**data)

    # ==================== Repository Operations ====================

    async def get_repository(self, owner: str, repo: str) -> GitHubRepository:
        """Get a single repository."""
        data = await self._get(f"/repos/{owner}/{repo}")
        return GitHubRepository(**data)

    async def get_starred_repositories(
        self,
        sort: str = "created",
        direction: str = "desc",
        per_page: int = 100,
        page: int = 1
    ) -> List[GitHubRepository]:
        """
        Get repositories starred by the authenticated user.

        Note:
            Requires GitHub Token to be configured.
        """
        endpoint = "/user/starred"
        params = {
            "sort": sort,
            "direction": direction,
            "per_page": per_page,
            "page": page
        }

        headers = self._default_headers.copy()
        headers["Accept"] = "application/vnd.github.v3.star+json"

        response = await self._client.get(endpoint, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        repos = []
        for item in data:
            starred_at = item.get("starred_at")
            repo_data = item.get("repo", item)
            repo = GitHubRepository(**repo_data)

            if starred_at and isinstance(starred_at, str):
                try:
                    repo.starred_at = datetime.fromisoformat(starred_at.replace('Z', '+00:00'))
                except:
                    repo.starred_at = starred_at
            else:
                repo.starred_at = starred_at
            repos.append(repo)

        return repos

    async def get_all_starred(
        self,
        max_results: Optional[int] = None
    ) -> List[GitHubRepository]:
        """
        Get all starred repositories with auto-pagination.

        Note:
            Requires GitHub Token to be configured.
        """
        all_repos = []
        page = 1
        per_page = 100

        while True:
            repos = await self.get_starred_repositories(
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

        all_repos.sort(
            key=lambda r: r.starred_at if r.starred_at else datetime.min,
            reverse=True
        )

        return all_repos

    # ==================== Content Operations ====================

    async def get_readme(self, owner: str, repo: str, branch: str = "main") -> GitHubReadme:
        """Get repository README."""
        try:
            data = await self._get(f"/repos/{owner}/{repo}/readme", params={"ref": branch})
            return GitHubReadme(**data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                data = await self._get(f"/repos/{owner}/{repo}/readme", params={"ref": "master"})
                return GitHubReadme(**data)
            raise

    async def get_readme_content(self, owner: str, repo: str) -> Optional[str]:
        """Get decoded README content."""
        try:
            readme = await self.get_readme(owner, repo)
            content = base64.b64decode(readme.content).decode("utf-8")
            return content
        except Exception:
            return None
