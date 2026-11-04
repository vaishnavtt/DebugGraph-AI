"""
Pydantic schemas for GitHub repository intelligence, commits, diffs,
and code-to-incident correlation.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RepositoryRegisterRequest(BaseModel):
    """Payload to register a GitHub repository and link it to a microservice."""

    url: str = Field(
        ...,
        min_length=1,
        description="GitHub repository URL (e.g. 'https://github.com/org/repo' or 'org/repo')",
    )
    service_name: Optional[str] = Field(
        default=None,
        description="Optional microservice name to associate with this repository in Neo4j",
    )
    default_branch: Optional[str] = Field(
        default="main",
        description="Default repository branch (e.g. 'main', 'master')",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://github.com/my-org/payment-service",
                "service_name": "payment-service",
                "default_branch": "main",
            }
        }
    )


class RepositoryResponse(BaseModel):
    """Structured details of a registered GitHub repository."""

    owner: str
    repo: str
    url: str
    service_name: Optional[str] = None
    default_branch: str = "main"
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    is_private: bool = False
    registered_at: str


class CommitSummary(BaseModel):
    """Summary metadata of an individual Git commit."""

    sha: str
    short_sha: str
    message: str
    author: str
    date: str
    url: str
    files_changed_count: Optional[int] = None


class CommitFileDiff(BaseModel):
    """File-level diff details within a Git commit."""

    filename: str
    status: str = Field(..., description="'modified', 'added', 'removed', or 'renamed'")
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: Optional[str] = Field(default=None, description="Unified git diff hunk")


class CommitDetails(BaseModel):
    """Detailed Git commit metadata including changed files and diff patches."""

    sha: str
    short_sha: str
    message: str
    author: str
    date: str
    url: str
    stats: Dict[str, int] = Field(default_factory=dict)
    files: List[CommitFileDiff] = Field(default_factory=list)


class CommitCorrelationFinding(BaseModel):
    """Individual commit correlation finding tied to incident evidence."""

    sha: str
    short_sha: str
    repository: str
    author: str
    date: str
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in commit relevance")
    suspect_files: List[str] = Field(default_factory=list, description="Files with changes matching error patterns")
    diff_excerpt: Optional[str] = Field(default=None, description="Key diff excerpt relevant to the incident")
    correlation_reasoning: str = Field(
        ...,
        description="Explanation linking commit diff changes to specific log errors or exceptions",
    )


class GitHubCorrelationResult(BaseModel):
    """Aggregated GitHub commit analysis for an incident."""

    repository: str
    commits_inspected_count: int
    has_candidate_commits: bool
    candidate_commits: List[CommitCorrelationFinding] = Field(default_factory=list)
    analysis_summary: str = Field(
        default="",
        description="Synthesis of how recent commits relate to the incident without unverified claims of causality",
    )

