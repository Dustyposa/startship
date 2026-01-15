"""
GitHub GraphQL API client with async support.

Provides efficient access to GitHub data using GraphQL queries.
"""
from typing import List, Optional, Dict, Any
from src.github.base import GitHubBaseClient
from src.github.models import GitHubRepository


class GitHubGraphQLClient(GitHubBaseClient):
    """
    Async GitHub GraphQL API client.

    Uses GraphQL for efficient data fetching with fewer requests.
    """

    async def __aenter__(self):
        """Initialize async client"""
        self._client = await self._init_client(
            timeout=60.0,
            extra_headers={"Content-Type": "application/json"}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close async client"""
        await self.close()

    async def _query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute GraphQL query."""
        self._check_client()

        payload = {
            "query": query,
            "variables": variables or {}
        }

        response = await self._client.post("/graphql", json=payload)
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            raise Exception(f"GraphQL error: {data['errors']}")

        return data.get("data", {})

    async def get_starred_repositories(
        self,
        username: str,
        max_results: Optional[int] = None
    ) -> List[GitHubRepository]:
        """
        Get all starred repositories using GraphQL.

        Args:
            username: GitHub username
            max_results: Maximum number of repositories to fetch

        Returns:
            List of repositories
        """
        query = """
        query ($login: String!, $cursor: String, $first: Int!) {
          user(login: $login) {
            starredRepositories(first: $first, after: $cursor, orderBy: {field: STARRED_AT, direction: DESC}) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                starredAt
                repository {
                  id
                  name
                  nameWithOwner
                  description
                  url
                  homepageUrl
                  primaryLanguage {
                    name
                  }
                  stargazerCount
                  forkCount
                  repositoryTopics(first: 20) {
                    nodes {
                      topic {
                        name
                      }
                    }
                  }
                  readme: object(expression: "HEAD:README.md") {
                    ... on Blob {
                      text
                    }
                  }
                  defaultBranchRef {
                    name
                  }
                }
              }
            }
          }
        }
        """

        repos = []
        cursor = None
        page_size = 100

        while True:
            variables = {
                "login": username,
                "cursor": cursor,
                "first": page_size
            }

            data = await self._query(query, variables)
            page_data = data.get("user", {}).get("starredRepositories", {})

            nodes = page_data.get("nodes", [])
            if not nodes:
                break

            for node in nodes:
                repo_data = node["repository"]
                starred_at = node.get("starredAt")

                topics_nodes = repo_data.get("repositoryTopics", {}).get("nodes", [])
                topics = [t["topic"]["name"] for t in topics_nodes] if topics_nodes else []

                readme_text = None
                readme_obj = repo_data.get("readme")
                if readme_obj and readme_obj.get("text"):
                    readme_text = readme_obj["text"]
                    if len(readme_text) > 10000:
                        readme_text = readme_text[:10000]

                repo = GitHubRepository(
                    id=repo_data["id"],
                    name=repo_data["name"],
                    name_with_owner=repo_data["nameWithOwner"],
                    description=repo_data.get("description"),
                    url=repo_data["url"],
                    homepage_url=repo_data.get("homepageUrl"),
                    primary_language=repo_data.get("primaryLanguage", {}).get("name"),
                    stargazer_count=repo_data["stargazerCount"],
                    fork_count=repo_data["forkCount"],
                    topics=topics,
                    starred_at=starred_at
                )

                if readme_text:
                    repo._readme_content = readme_text

                repos.append(repo)

            page_info = page_data.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break

            cursor = page_info.get("endCursor")

            if max_results and len(repos) >= max_results:
                repos = repos[:max_results]
                break

        return repos

    def get_repository_readme(
        self,
        repo: GitHubRepository
    ) -> Optional[str]:
        """
        Get README content from repository (cached during fetch).

        Args:
            repo: Repository object

        Returns:
            README text or None
        """
        return getattr(repo, "_readme_content", None)
