"""GitHub package for GraphQL API client and models."""
from .graphql import GitHubGraphQLClient
from .models import (
    GitHubRepository,
    GitHubUser,
    GitHubReadme,
    RepositoryAnalysis,
    StargazerInfo,
    StarBatch
)

__all__ = [
    "GitHubGraphQLClient",
    "GitHubRepository",
    "GitHubUser",
    "GitHubReadme",
    "RepositoryAnalysis",
    "StargazerInfo",
    "StarBatch"
]
