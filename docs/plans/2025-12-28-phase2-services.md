# Phase 2: Core Services - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the core services layer including GitHub API client, LLM abstraction, initialization service, search service, and chat service.

**Architecture:** Service-oriented architecture with clean separation of concerns. Services depend on the database layer from Phase 1.

**Tech Stack:** httpx for async HTTP, OpenAI SDK (or compatible), Pydantic for data validation

---

## Task 1: Create Pydantic Models for GitHub Data

**Files:**
- Create: `src/github/models.py`

**Step 1: Write GitHub data models**

Create `src/github/models.py`:

```python
"""
Pydantic models for GitHub API data.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GitHubRepository(BaseModel):
    """Repository model from GitHub API"""

    # Basic fields
    id: int
    name_with_owner: str = Field(..., alias="full_name")
    name: str
    owner: str

    # Description and metadata
    description: Optional[str] = None
    primary_language: Optional[str] = Field(None, alias="language")
    topics: List[str] = Field(default_factory=list)

    # Stats
    stargazer_count: int = Field(..., alias="stargazers_count")
    fork_count: int = Field(..., alias="forks_count")
    open_issues_count: int = Field(default=0, alias="open_issues_count")

    # URLs
    url: str = Field(..., alias="html_url")
    homepage_url: Optional[str] = Field(None, alias="homepage")

    # Dates
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[datetime] = None

    # License
    license_key: Optional[str] = Field(None, alias="license")

    # Computed field for owner extraction
    @property
    def owner_login(self) -> str:
        """Extract owner login from full_name"""
        return self.name_with_owner.split("/")[0]

    class Config:
        populate_by_name = True


class GitHubUser(BaseModel):
    """GitHub user model"""

    id: int
    login: str
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: str = Field(..., alias="avatar_url")
    followers: int = Field(default=0, alias="followers")
    following: int = Field(default=0, alias="following")
    public_repos: int = Field(default=0, alias="public_repos")

    class Config:
        populate_by_name = True


class GitHubReadme(BaseModel):
    """README content model"""

    content: str
    encoding: str = "utf-8"


class RepositoryAnalysis(BaseModel):
    """Repository analysis result from LLM"""

    name_with_owner: str
    summary: str = Field(..., description="One-line summary of the repository")
    categories: List[str] = Field(default_factory=list, description="Category tags like '工具', '前端'")
    features: List[str] = Field(default_factory=list, description="Key features identified")
    tech_stack: List[str] = Field(default_factory=list, description="Technologies used")
    use_cases: List[str] = Field(default_factory=list, description="Common use cases")
    readme_summary: Optional[str] = None

    class Config:
        populate_by_name = True


class StargazerInfo(BaseModel):
    """Information about a user who starred a repo"""

    login: str
    starred_at: datetime


class StarBatch(BaseModel):
    """Batch of stargazers for pagination"""

    stargazers: List[StargazerInfo]
    total_count: int
    page: int
    per_page: int
```

**Step 2: Write tests for models**

Create `tests/unit/test_github_models.py`:

```python
import pytest
from datetime import datetime
from src.github.models import GitHubRepository, GitHubUser, RepositoryAnalysis


def test_repository_model_from_github_api():
    """Test parsing repository data from GitHub API format"""
    data = {
        "id": 123456,
        "full_name": "owner/repo",
        "name": "repo",
        "owner": {"login": "owner"},
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
        "license": {"key": "MIT"}
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
        full_name="test/repo",
        name="repo",
        owner="test",
        stargazers_count=0,
        forks_count=0,
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
        tech_stack=["Python", "FastAPI"],
        use_cases=["Testing", "Development"]
    )
    assert analysis.name_with_owner == "owner/repo"
    assert len(analysis.categories) == 2
```

**Step 3: Run tests**

```bash
pytest tests/unit/test_github_models.py -v
```

Expected: All tests PASS

**Step 4: Commit**

```bash
git add src/github/models.py tests/unit/test_github_models.py
git commit -m "feat: add Pydantic models for GitHub data"
```

---

## Task 2: Create GitHub API Client

**Files:**
- Create: `src/github/client.py`
- Create: `src/github/__init__.py`

**Step 1: Write GitHub API client**

Create `src/github/client.py`:

```python
"""
GitHub API client with async support.
"""
import httpx
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
        # Handle owner as dict or string
        if isinstance(data.get("owner"), dict):
            data["owner"] = data["owner"]["login"]
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
            if isinstance(repo_data.get("owner"), dict):
                repo_data["owner"] = repo_data["owner"]["login"]
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
            import base64
            content = base64.b64decode(readme.content).decode("utf-8")
            return content
        except Exception:
            return None
```

**Step 2: Write tests for GitHub client**

Create `tests/unit/test_github_client.py`:

```python
import pytest
from pytest_mock import Mocker
from src.github.client import GitHubClient


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initializes correctly"""
    async with GitHubClient(token="test_token") as client:
        assert client.token == "test_token"
        assert client._client is not None


@pytest.mark.asyncio
async def test_client_without_token():
    """Test client can work without token (for public data)"""
    async with GitHubClient(token=None) as client:
        assert client.token is None


@pytest.mark.asyncio
async def test_get_user(mocker: Mocker):
    """Test getting user data"""
    mock_response = {
        "id": 1,
        "login": "testuser",
        "name": "Test User",
        "avatar_url": "https://example.com/avatar.png",
        "followers": 10,
        "following": 5,
        "public_repos": 20
    }

    async def mock_get(*args, **kwargs):
        class Response:
            def raise_for_status(self):
                pass
        response = Response()
        response.json = lambda: mock_response
        return response

    mocker.patch("httpx.AsyncClient.get", mock_get)

    async with GitHubClient() as client:
        user = await client.get_user("testuser")
        assert user.login == "testuser"
        assert user.name == "Test User"


@pytest.mark.asyncio
async def test_context_manager():
    """Test client works as context manager"""
    async with GitHubClient() as client:
        assert client._client is not None
    # Client should be closed after context
```

**Step 3: Run tests**

```bash
pytest tests/unit/test_github_client.py -v
```

Expected: All tests PASS

**Step 4: Install pytest-mock**

```bash
uv add --dev pytest-mock
```

**Step 5: Commit**

```bash
git add src/github/client.py src/github/__init__.py tests/unit/test_github_client.py
git commit -m "feat: add GitHub API client"
```

---

## Task 3: Create LLM Abstraction Layer

**Files:**
- Create: `src/llm/base.py`
- Create: `src/llm/openai.py`
- Create: `src/llm/__init__.py`

**Step 1: Write LLM base class**

Create `src/llm/base.py`:

```python
"""
LLM abstraction layer.
Supports multiple LLM providers through a common interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Message(BaseModel):
    """Chat message"""
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    """LLM response"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None


class LLM(ABC):
    """
    Abstract LLM interface.

    All LLM operations must be async.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize LLM client"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close LLM client"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Send chat completion request.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLM response
        """
        pass

    @abstractmethod
    async def analyze_repository(
        self,
        repo_name: str,
        description: str,
        readme: Optional[str] = None,
        language: Optional[str] = None,
        topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a repository and extract structured information.

        Args:
            repo_name: Repository name
            description: Repository description
            readme: README content
            language: Primary language
            topics: Repository topics

        Returns:
            Analysis result with categories, features, tech_stack, etc.
        """
        pass
```

**Step 2: Write OpenAI implementation**

Create `src/llm/openai.py`:

```python
"""
OpenAI LLM implementation.
"""
import json
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
from src.config import settings
from src.llm.base import LLM, Message, LLMResponse


class OpenAILLM(LLM):
    """OpenAI LLM implementation"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Model name
            base_url: API base URL (for compatible APIs)
        """
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.llm_model
        self.base_url = base_url or settings.llm_base_url
        self._client: Optional[AsyncOpenAI] = None

    async def initialize(self) -> None:
        """Initialize OpenAI client"""
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self._client = AsyncOpenAI(**client_kwargs)

    async def close(self) -> None:
        """Close OpenAI client"""
        if self._client:
            await self._client.close()
            self._client = None

    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Send chat completion request"""
        if not self._client:
            raise RuntimeError("Client not initialized")

        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None
        )

    async def analyze_repository(
        self,
        repo_name: str,
        description: str,
        readme: Optional[str] = None,
        language: Optional[str] = None,
        topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze a repository using LLM"""
        # Build analysis prompt
        topics_str = ", ".join(topics) if topics else "None"

        system_prompt = """You are an expert software analyst. Analyze GitHub repositories and provide structured information.

Your response must be valid JSON with this exact structure:
{
    "summary": "One-line summary",
    "categories": ["category1", "category2"],
    "features": ["feature1", "feature2"],
    "tech_stack": ["tech1", "tech2"],
    "use_cases": ["use case1"]
}

Categories should be in Chinese and concise, such as: 工具, 前端, 后端, AI/ML, 数据库, DevOps, etc."""

        user_prompt = f"""Analyze this GitHub repository:

Name: {repo_name}
Language: {language or "Unknown"}
Description: {description or "No description"}
Topics: {topics_str}

README:
{readme[:4000] if readme else "No README available"}

Provide analysis in JSON format as specified."""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt)
        ]

        response = await self.chat(messages, temperature=0.3)

        # Parse JSON response
        try:
            # Extract JSON from response
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            result["name_with_owner"] = repo_name
            result["readme_summary"] = readme[:500] if readme else None
            return result
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            return {
                "name_with_owner": repo_name,
                "summary": description or f"{repo_name}",
                "categories": [],
                "features": [],
                "tech_stack": [language] if language else [],
                "use_cases": [],
                "readme_summary": readme[:500] if readme else None,
                "error": f"JSON parsing failed: {e}"
            }
```

**Step 3: Write LLM factory**

Create `src/llm/__init__.py`:

```python
"""LLM package with factory function."""
from .base import LLM, Message, LLMResponse
from .openai import OpenAILLM

__all__ = ["LLM", "Message", "LLMResponse", "OpenAILLM", "create_llm"]


def create_llm(provider: str = "openai", **config) -> LLM:
    """
    Factory function to create LLM instance.

    Args:
        provider: LLM provider ("openai")
        **config: Configuration parameters

    Returns:
        LLM instance

    Raises:
        ValueError: If provider is not supported
    """
    if provider == "openai":
        return OpenAILLM(**config)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
```

**Step 4: Write tests**

Create `tests/unit/test_llm.py`:

```python
import pytest
from src.llm import create_llm, OpenAILLM, Message


def test_create_openai_llm():
    """Test creating OpenAI LLM"""
    llm = create_llm("openai", api_key="test_key", model="gpt-4")
    assert isinstance(llm, OpenAI_llm)


def test_create_unsupported_llm():
    """Test creating unsupported LLM raises error"""
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_llm("unknown")


@pytest.mark.asyncio
async def test_openai_initialize(mocker):
    """Test OpenAI client initialization"""
    llm = OpenAILLM(api_key="test_key")
    await llm.initialize()
    assert llm._client is not None
    await llm.close()
```

**Step 5: Install openai dependency**

```bash
uv add openai
```

**Step 6: Run tests**

```bash
pytest tests/unit/test_llm.py -v
```

**Step 7: Commit**

```bash
git add src/llm/ tests/unit/test_llm.py
git commit -m "feat: add LLM abstraction layer with OpenAI support"
```

---

## Task 4: Create Initialization Service

**Files:**
- Create: `src/services/init.py`
- Create: `src/services/__init__.py`

**Step 1: Write initialization service**

Create `src/services/init.py`:

```python
"""
Service for initializing and updating repository data.
"""
from typing import List, Optional, Dict, Any
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

    def __init__(self, db: Database, llm: Optional[LLM] = None):
        """
        Initialize service.

        Args:
            db: Database instance
            llm: LLM instance (optional)
        """
        self.db = db
        self.llm = llm

    async def initialize_from_stars(
        self,
        username: Optional[str] = None,
        max_repos: Optional[int] = None,
        skip_llm: bool = False
    ) -> Dict[str, Any]:
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

            # Process each repository
            with Bar("Processing", max=len(repos)) as bar:
                for repo in repos:
                    try:
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

        return stats

    async def analyze_existing_repos(
        self,
        limit: Optional[int] = None,
        force: bool = False
    ) -> Dict[str, Any]:
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
```

**Step 2: Add progress bar dependency**

```bash
uv add progress
```

**Step 3: Write tests**

Create `tests/unit/test_init_service.py`:

```python
import pytest
from src.services.init import InitializationService


@pytest.mark.asyncio
async def test_initialization_service_creation(db):
    """Test creating initialization service"""
    service = InitializationService(db, llm=None)
    assert service.db is not None
    assert service.llm is None


@pytest.mark.asyncio
async def test_initialize_requires_llm(db):
    """Test initialization requires LLM unless skip_llm=True"""
    service = InitializationService(db, llm=None)

    with pytest.raises(ValueError, match="LLM is required"):
        await service.initialize_from_stars(skip_llm=False)


@pytest.mark.asyncio
async def test_initialize_skip_llm_no_error(db, mocker):
    """Test skip_llm=True bypasses LLM requirement"""
    service = InitializationService(db, llm=None)

    # Mock GitHub client
    async def mock_get_all_starred(*args, **kwargs):
        return []

    mocker.patch("src.services.init.GitHubClient")

    async def mock_enter(*args, **kwargs):
        class MockClient:
            async def get_all_starred(self, *args, **kwargs):
                return []
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args, **kwargs):
                pass
        return MockClient()

    mocker.patch("src.services.init.GitHubClient", mock_enter)

    result = await service.initialize_from_stars(skip_llm=True)
    assert "fetched" in result
```

**Step 4: Update pyproject.toml**

Add progress to dependencies.

**Step 5: Run tests**

```bash
pytest tests/unit/test_init_service.py -v
```

**Step 6: Commit**

```bash
git add src/services/init.py src/services/__init__.py tests/unit/test_init_service.py
git commit -m "feat: add initialization service"
```

---

## Task 5: Create Search Service

**Files:**
- Create: `src/services/search.py`

**Step 1: Write search service**

Create `src/services/search.py`:

```python
"""
Service for searching repositories.
"""
from typing import List, Dict, Any, Optional
from src.db import Database


class SearchService:
    """Service for searching and filtering repositories"""

    def __init__(self, db: Database):
        """
        Initialize search service.

        Args:
            db: Database instance
        """
        self.db = db

    async def search(
        self,
        query: Optional[str] = None,
        categories: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search repositories with filters.

        Args:
            query: Full-text search query (optional, for future)
            categories: Filter by categories
            languages: Filter by programming languages
            min_stars: Minimum star count
            max_stars: Maximum star count
            limit: Maximum number of results

        Returns:
            List of matching repositories
        """
        # Use database search
        results = await self.db.search_repositories(
            categories=categories,
            languages=languages,
            min_stars=min_stars,
            max_stars=max_stars,
            limit=limit
        )

        return results

    async def get_categories(self) -> Dict[str, int]:
        """
        Get all available categories with counts.

        Returns:
            Dictionary mapping category to count
        """
        stats = await self.db.get_statistics()
        return stats.get("categories", {})

    async def get_languages(self) -> List[str]:
        """
        Get all available programming languages.

        Returns:
            List of languages
        """
        # This would require a new DB method
        # For now, return empty list
        return []

    async def get_repository(self, name_with_owner: str) -> Optional[Dict[str, Any]]:
        """
        Get a single repository by name.

        Args:
            name_with_owner: Repository name (owner/repo)

        Returns:
            Repository data or None
        """
        return await self.db.get_repository(name_with_owner)

    async def get_similar_repositories(
        self,
        name_with_owner: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find repositories similar to the given one.

        Args:
            name_with_owner: Repository name
            limit: Maximum number of results

        Returns:
            List of similar repositories
        """
        # Get the target repository
        repo = await self.db.get_repository(name_with_owner)
        if not repo:
            return []

        # Find repos with same categories or language
        results = await self.db.search_repositories(
            categories=repo.get("categories", [])[:2],  # Use first 2 categories
            languages=[repo.get("primary_language")] if repo.get("primary_language") else None,
            limit=limit + 1  # +1 to exclude the repo itself
        )

        # Exclude the original repository
        return [r for r in results if r["name_with_owner"] != name_with_owner][:limit]
```

**Step 2: Write tests**

Create `tests/unit/test_search_service.py`:

```python
import pytest
from src.services.search import SearchService


@pytest.mark.asyncio
async def test_search_service_creation(db):
    """Test creating search service"""
    service = SearchService(db)
    assert service.db is not None


@pytest.mark.asyncio
async def test_search_empty_database(db):
    """Test searching empty database"""
    service = SearchService(db)
    results = await service.search()
    assert results == []


@pytest.mark.asyncio
async def test_search_with_data(db):
    """Test searching with data"""
    service = SearchService(db)

    # Add test data
    await db.add_repository({
        "name_with_owner": "owner/repo1",
        "name": "repo1",
        "owner": "owner",
        "primary_language": "Python",
        "stargazer_count": 100,
        "categories": ["工具"],
        "tech_stack": ["Python"]
    })

    results = await service.search(categories=["工具"])
    assert len(results) == 1
    assert results[0]["name_with_owner"] == "owner/repo1"
```

**Step 3: Run tests**

```bash
pytest tests/unit/test_search_service.py -v
```

**Step 4: Commit**

```bash
git add src/services/search.py tests/unit/test_search_service.py
git commit -m "feat: add search service"
```

---

## Task 6: Create Chat Service

**Files:**
- Create: `src/services/chat.py`
- Create: `src/api/routes/chat.py`

**Step 1: Write chat service**

Create `src/services/chat.py`:

```python
"""
Service for handling chat conversations.
"""
from typing import List, Dict, Any, Optional
from src.db import Database
from src.llm import LLM, Message


class ChatService:
    """Service for managing conversations and chat with LLM"""

    def __init__(self, db: Database, llm: LLM, search_service):
        """
        Initialize chat service.

        Args:
            db: Database instance
            llm: LLM instance
            search_service: Search service for RAG
        """
        self.db = db
        self.llm = llm
        self.search_service = search_service

    async def create_conversation(self, session_id: str) -> int:
        """Create a new conversation"""
        return await self.db.create_conversation(session_id)

    async def get_conversation_history(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return await self.db.get_conversation(session_id)

    async def chat(
        self,
        session_id: str,
        user_message: str,
        context_limit: int = 10
    ) -> str:
        """
        Send a chat message and get response.

        Args:
            session_id: Session identifier
            user_message: User's message
            context_limit: Number of previous messages to include

        Returns:
            Assistant's response
        """
        # Save user message
        await self.db.save_message(session_id, "user", user_message)

        # Get conversation history
        history = await self.db.get_conversation(session_id)

        # Build messages for LLM
        messages = [
            Message(
                role="system",
                content="You are GitHub Star Helper, an AI assistant that helps users analyze and discover their starred GitHub repositories. Be helpful, concise, and respond in Chinese."
            )
        ]

        # Add recent conversation (excluding the one we just saved)
        for msg in history[-context_limit:-1]:
            messages.append(Message(role=msg["role"], content=msg["content"]))

        # Add current user message
        messages.append(Message(role="user", content=user_message))

        # Get LLM response
        response = await self.llm.chat(messages, temperature=0.7)

        # Save assistant response
        await self.db.save_message(session_id, "assistant", response.content)

        return response.content

    async def chat_with_rag(
        self,
        session_id: str,
        user_message: str,
        search_results: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Chat with RAG (Retrieval Augmented Generation).

        Args:
            session_id: Session identifier
            user_message: User's message
            search_results: Pre-fetched search results

        Returns:
            Assistant's response
        """
        # Save user message
        await self.db.save_message(session_id, "user", user_message)

        # Build context from search results
        context = ""
        if search_results:
            context = "\n\nRelevant repositories:\n"
            for repo in search_results[:5]:
                context += f"- {repo['name_with_owner']}: {repo.get('summary', repo.get('description', ''))}\n"

        # Build messages
        messages = [
            Message(
                role="system",
                content=f"""You are GitHub Star Helper, an AI assistant that helps users analyze and discover their starred GitHub repositories.

{context}

Be helpful, concise, and respond in Chinese. Use the repository information above when relevant to the user's question."""
            )
        ]

        # Get recent history
        history = await self.db.get_conversation(session_id)
        for msg in history[-10:-1]:
            messages.append(Message(role=msg["role"], content=msg["content"]))

        # Add current message
        messages.append(Message(role="user", content=user_message))

        # Get response
        response = await self.llm.chat(messages, temperature=0.7)

        # Save and return
        await self.db.save_message(session_id, "assistant", response.content)
        return response.content

    async def delete_conversation(self, session_id: str) -> bool:
        """Delete a conversation"""
        return await self.db.delete_conversation(session_id)
```

**Step 2: Create chat API routes**

Create `src/api/routes/chat.py`:

```python
"""
Chat API endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model"""
    session_id: str
    message: str
    use_rag: bool = False


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str


class ConversationHistoryResponse(BaseModel):
    """Conversation history response"""
    session_id: str
    messages: List[dict]


# Dependency to get services
async def get_chat_service():
    """Get chat service instance"""
    from src.api.app import db, search_service
    from src.llm import create_llm

    llm = create_llm("openai")
    await llm.initialize()

    from src.services.chat import ChatService
    service = ChatService(db, llm, search_service)

    # We'd normally use a proper dependency injection pattern
    # For now, we'll handle this in the route
    return service


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a chat message and get response.

    - **session_id**: Unique session identifier
    - **message**: User's message
    - **use_rag**: Whether to use RAG (search repositories)
    """
    from src.api.app import db
    from src.llm import create_llm
    from src.services.chat import ChatService
    from src.services.search import SearchService

    # Create services
    llm = create_llm("openai")
    await llm.initialize()
    search_service = SearchService(db)
    chat_service = ChatService(db, llm, search_service)

    try:
        if request.use_rag:
            response = await chat_service.chat_with_rag(
                session_id=request.session_id,
                user_message=request.message
            )
        else:
            response = await chat_service.chat(
                session_id=request.session_id,
                user_message=request.message
            )

        return ChatResponse(response=response)

    finally:
        await llm.close()


@router.get("/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation(session_id: str):
    """
    Get conversation history.

    - **session_id**: Session identifier
    """
    from src.api.app import db

    messages = await db.get_conversation(session_id)

    return ConversationHistoryResponse(
        session_id=session_id,
        messages=messages
    )


@router.delete("/{session_id}")
async def delete_conversation(session_id: str):
    """
    Delete a conversation.

    - **session_id**: Session identifier
    """
    from src.api.app import db

    result = await db.delete_conversation(session_id)

    return {"success": result}
```

**Step 3: Integrate chat routes into main app**

Update `src/api/app.py`:

```python
# Add to imports
from src.api.routes import chat

# Include router
app.include_router(chat.router)
```

**Step 4: Write tests**

Create `tests/unit/test_chat_service.py`:

```python
import pytest
from src.services.chat import ChatService


@pytest.mark.asyncio
async def test_chat_service_creation(db):
    """Test creating chat service"""
    llm = None
    from src.services.search import SearchService
    search = SearchService(db)

    service = ChatService(db, llm, search)
    assert service.db is not None
```

**Step 5: Run tests**

```bash
pytest tests/unit/test_chat_service.py -v
```

**Step 6: Commit**

```bash
git add src/services/chat.py src/api/routes/ tests/unit/test_chat_service.py
git commit -m "feat: add chat service and API routes"
```

---

## Task 7: Update Main App with All Services

**Files:**
- Modify: `src/api/app.py`

**Step 1: Update main app**

Update `src/api/app.py` to include all new services and routes.

**Step 2: Test full integration**

Run all tests:

```bash
pytest tests/ -v --asyncio-mode=auto
```

**Step 3: Commit**

```bash
git add src/api/app.py
git commit -m "feat: integrate all services into main app"
```

---

## Task 8: Create API Documentation

**Files:**
- Modify: `docs/plans/README.phase2.md`

**Step 1: Create Phase 2 documentation**

Create comprehensive documentation for Phase 2.

**Step 2: Update main README**

Update README.md with Phase 2 status.

**Step 3: Commit**

```bash
git add docs/plans/README.phase2.md README.md
git commit -m "docs: add Phase 2 completion documentation"
```

---

## Phase 2 Completion Checklist

- [x] GitHub API client
- [x] LLM abstraction layer
- [x] Initialization service
- [x] Search service
- [x] Chat service
- [x] API routes for chat
- [x] Integration tests
- [x] Documentation

---

## Summary

Phase 2 adds the core services layer:

✅ **GitHub Client**: Async HTTP client for GitHub API
✅ **LLM Abstraction**: OpenAI integration with extensibility
✅ **Init Service**: Fetch and analyze starred repositories
✅ **Search Service**: Filter and search repositories
✅ **Chat Service**: Conversational AI with RAG support

**Estimated time to complete Phase 2**: 5-7 days

**Ready for Phase 3**: Yes - proceed to implementing web UI and advanced features
