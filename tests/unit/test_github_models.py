import pytest
from datetime import datetime
from src.github.models import GitHubRepository, GitHubUser, RepositoryAnalysis


def test_repository_model_from_github_api():
    """Test parsing repository data from GitHub API format"""
    data = {
        "id": 123456,
        "full_name": "owner/repo",
        "name": "repo",
        "owner": {"login": "owner", "type": "User"},
        "description": "Test repo",
        "language": "Python",
        "topics": ["web", "api"],
        "stargazers_count": 100,
        "forks_count": 10,
        "open_issues_count": 5,
        "html_url": "https://github.com/owner/repo",
        "homepage": "https://example.com",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "pushed_at": "2024-01-03T00:00:00Z",
        "license_key": {"key": "MIT"}
    }

    repo = GitHubRepository(**data)
    assert repo.id == 123456
    assert repo.name_with_owner == "owner/repo"
    assert repo.primary_language == "Python"
    assert repo.stargazer_count == 100
    assert repo.topics == ["web", "api"]


def test_repository_owner_login_extraction():
    """Test owner login extraction from full_name"""
    repo = GitHubRepository(
        id=1,
        name_with_owner="test/repo",
        name="repo",
        owner="test",
        stargazer_count=0,
        fork_count=0,
        url="https://github.com/test/repo",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z"
    )
    assert repo.owner_login == "test"


def test_repository_analysis_model():
    """Test repository analysis model"""
    analysis = RepositoryAnalysis(
        name_with_owner="owner/repo",
        summary="A test repository",
        categories=["工具", "测试"],
        features=["Feature 1", "Feature 2"],
        use_cases=["Testing", "Development"]
    )
    assert analysis.name_with_owner == "owner/repo"
    assert len(analysis.categories) == 2
