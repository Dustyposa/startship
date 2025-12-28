"""GitHub package for API client and models."""
from .client import GitHubClient
from .models import (
    GitHubRepository,
    GitHubUser,
    GitHubReadme,
    RepositoryAnalysis,
    StargazerInfo,
    StarBatch
)

__all__ = [
    "GitHubClient",
    "GitHubRepository",
    "GitHubUser",
    "GitHubReadme",
    "RepositoryAnalysis",
    "StargazerInfo",
    "StarBatch"
]
