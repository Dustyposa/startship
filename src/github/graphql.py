"""
GitHub GraphQL API client with async support.

Provides efficient access to GitHub data using GraphQL queries.
"""
from typing import List, Optional, Dict, Any
import asyncio
import httpx
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
            timeout=180.0,
            extra_headers={"Content-Type": "application/json"}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close async client"""
        await self.close()

    async def _query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Execute GraphQL query with retry logic."""
        self._check_client()

        payload = {
            "query": query,
            "variables": variables or {}
        }

        for attempt in range(max_retries):
            try:
                response = await self._client.post("/graphql", json=payload)
                response.raise_for_status()
                data = response.json()

                if "errors" in data:
                    raise Exception(f"GraphQL error: {data['errors']}")

                return data.get("data", {})

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (502, 503, 504) and attempt < max_retries - 1:
                    # Exponential backoff: 2s, 4s, 8s
                    wait_time = 2 ** (attempt + 1)
                    print(f"GraphQL timeout (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    print(f"GraphQL error (attempt {attempt + 1}/{max_retries}): {e}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                raise

        raise Exception("Max retries exceeded")

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
                id
                name
                nameWithOwner
                owner {
                  login
                }
                description
                url
                createdAt
                updatedAt
                primaryLanguage {
                  name
                }
                languages(first: 5) {
                  edges {
                    size
                    node {
                      name
                    }
                  }
                  totalSize
                }
                stargazerCount
                forkCount
                repositoryTopics(first: 10) {
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
              }
            }
          }
        }
        """

        repos = []
        cursor = None
        page_size = 30  # Reduced from 100 to avoid timeouts

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

            for repo_data in nodes:
                # repo_data is now the Repository directly, not nested
                topics_nodes = repo_data.get("repositoryTopics", {}).get("nodes", [])
                topics = [t["topic"]["name"] for t in topics_nodes] if topics_nodes else []

                # Extract README content
                readme_data = repo_data.get("readme", {})
                readme_content = readme_data.get("text") if readme_data else None

                # Extract languages with percentages
                languages_data = repo_data.get("languages", {})
                languages = []
                if languages_data:
                    lang_edges = languages_data.get("edges", [])
                    total_size = languages_data.get("totalSize", 0)
                    for lang_edge in lang_edges:
                        lang_name = lang_edge.get("node", {}).get("name")
                        size = lang_edge.get("size", 0)
                        if lang_name and total_size > 0:
                            percent = round(size / total_size * 100, 2)
                            languages.append({
                                "name": lang_name,
                                "size": size,
                                "percent": percent
                            })

                repo = GitHubRepository(
                    id=0,
                    name=repo_data["name"],
                    name_with_owner=repo_data["nameWithOwner"],
                    owner=repo_data.get("owner", {}).get("login", ""),
                    description=repo_data.get("description"),
                    url=repo_data["url"],
                    homepage_url=None,
                    primary_language=(repo_data.get("primaryLanguage") or {}).get("name"),
                    stargazer_count=repo_data["stargazerCount"],
                    fork_count=repo_data["forkCount"],
                    topics=topics,
                    starred_at=None,
                    languages=languages,
                    created_at=repo_data.get("createdAt"),
                    updated_at=repo_data.get("updatedAt"),
                    readme_content=readme_content
                )

                repos.append(repo)

            page_info = page_data.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break

            cursor = page_info.get("endCursor")

            if max_results and len(repos) >= max_results:
                repos = repos[:max_results]
                break

        return repos

    async def get_authenticated_user(self) -> Any:
        """
        Get the authenticated user using GraphQL.

        Returns:
            User object with login field
        """
        query = """
        query {
          viewer {
            login
          }
        }
        """

        data = await self._query(query)
        return data.get("viewer", {})

    async def get_readme_content(
        self,
        owner: str,
        repo: str
    ) -> Optional[str]:
        """
        Get README content using GraphQL.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            README text or None
        """
        query = """
        query ($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            readme: object(expression: "HEAD:README.md") {
              ... on Blob {
                text
              }
            }
          }
        }
        """

        try:
            data = await self._query(
                query,
                variables={"owner": owner, "repo": repo}
            )
            readme_data = data.get("repository", {}).get("readme")
            return readme_data.get("text") if readme_data else None
        except Exception:
            # Try common README filenames
            for filename in ["README.md", "README.rst", "README.txt", "README"]:
                query = f"""
                query ($owner: String!, $repo: String!) {{
                  repository(owner: $owner, name: $repo) {{
                    readme: object(expression: "HEAD:{filename}") {{
                      ... on Blob {{
                        text
                      }}
                    }}
                  }}
                }}
                """
                try:
                    data = await self._query(
                        query,
                        variables={"owner": owner, "repo": repo}
                    )
                    readme_data = data.get("repository", {}).get("readme")
                    if readme_data and readme_data.get("text"):
                        return readme_data.get("text")
                except Exception:
                    continue
            return None

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
