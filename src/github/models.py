"""
Pydantic models for GitHub API data.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union, Any
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
    license_key: Optional[str] = None

    @field_validator("owner", mode="before")
    @classmethod
    def extract_owner_login(cls, v: Any) -> str:
        """Extract owner login from dict or return string"""
        if isinstance(v, dict):
            return v.get("login", "")
        return str(v) if v else ""

    @field_validator("license_key", mode="before")
    @classmethod
    def extract_license_key(cls, v: Any) -> Optional[str]:
        """Extract license key from dict or return string"""
        if isinstance(v, dict):
            return v.get("key")
        return v

    @property
    def owner_login(self) -> str:
        """Extract owner login from full_name"""
        return self.name_with_owner.split("/")[0]


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
