"""
Base GitHub client with shared functionality.

Provides common utilities for both REST and GraphQL clients.
"""
import httpx
from typing import Optional, Dict, Any
from src.config import settings


class GitHubBaseClient:
    """Base client with shared HTTP functionality."""

    API_BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token
        """
        self.token = token or settings.github_token
        self._client: Optional[httpx.AsyncClient] = None
        self._default_headers: Dict[str, str] = {}

    def _build_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build HTTP headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHubStarHelper/1.0"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        if extra_headers:
            headers.update(extra_headers)

        return headers

    async def _init_client(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> httpx.AsyncClient:
        """Initialize async HTTP client."""
        headers = self._build_headers(extra_headers)
        self._default_headers = headers.copy()

        return httpx.AsyncClient(
            base_url=base_url or self.API_BASE,
            headers=headers,
            timeout=timeout
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _check_client(self) -> None:
        """Raise error if client not initialized."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context.")

    def _extract_owner_repo(self, name_with_owner: str) -> tuple[str, str]:
        """Extract owner and repo name from 'owner/repo' string."""
        parts = name_with_owner.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid repository name: {name_with_owner}")
        return parts[0], parts[1]
