"""
Pydantic models for GitHub API data.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Union, Any, Dict
from datetime import datetime


class LanguageInfo(BaseModel):
    """Language information with percentage"""
    name: str
    size: int
    percent: float


class GitHubRepository(BaseModel):
    """Repository model from GitHub API"""

    # Basic fields
    id: int
    name_with_owner: str
    name: str
    owner: str

    # Description and metadata
    description: Optional[str] = None
    primary_language: Optional[str] = None
    languages: List[LanguageInfo] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)

    # Stats
    stargazer_count: int
    fork_count: int
    open_issues_count: int = 0

    # URLs
    url: str
    homepage_url: Optional[str] = None

    # Dates
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[datetime] = None
    starred_at: Optional[datetime] = None  # When this repo was starred by the user

    # Status and visibility
    archived: bool = False
    visibility: str = "public"
    owner_type: Optional[str] = None  # "Organization" or "User" - extracted from owner dict
    organization: Optional[str] = None  # Organization name if owned by org

    # License
    license_key: Optional[str] = None

    # README content
    readme_content: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def extract_owner_fields(cls, data: Any) -> Any:
        """Extract owner_type and organization from owner dict before field validation"""
        if isinstance(data, dict):
            owner_data = data.get('owner')
            if isinstance(owner_data, dict):
                # Store owner_type from the owner dict
                if 'owner_type' not in data and 'type' in owner_data:
                    data['owner_type'] = owner_data['type']
                # Store organization if owner type is Organization
                if 'organization' not in data and owner_data.get('type') == 'Organization':
                    data['organization'] = owner_data.get('login')
        return data

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
