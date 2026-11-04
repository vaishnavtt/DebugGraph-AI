"""
FastAPI endpoints for GitHub repository registration, commit inspection,
and diff analysis.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.logging import get_logger
from app.graph.manager import KnowledgeGraphManager
from app.schemas.github import (
    CommitDetails,
    CommitSummary,
    RepositoryRegisterRequest,
    RepositoryResponse,
)
from app.services.github_service import (
    GitHubAPIError,
    GitHubRateLimitError,
    GitHubResourceNotFoundError,
    GitHubService,
    parse_github_url,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/github", tags=["GitHub Intelligence"])


def get_github_service() -> GitHubService:
    """Dependency provider for GitHubService."""
    return GitHubService()


def get_graph_manager() -> KnowledgeGraphManager:
    """Dependency provider for KnowledgeGraphManager."""
    return KnowledgeGraphManager()


@router.post(
    "/repositories",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a GitHub repository and link to microservice",
)
async def register_repository(
    payload: RepositoryRegisterRequest,
    github_service: GitHubService = Depends(get_github_service),
    graph_manager: KnowledgeGraphManager = Depends(get_graph_manager),
) -> RepositoryResponse:
    """
    Validates a repository URL via GitHub REST API, creates the Repository node
    in Neo4j, and connects it to a microservice if service_name is provided.
    """
    try:
        owner, repo = parse_github_url(payload.url)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )

    try:
        # Fetch metadata from GitHub REST API
        meta = await github_service.get_repository_metadata(owner=owner, repo=repo)
    except GitHubResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GitHub repository '{owner}/{repo}' does not exist or is inaccessible.",
        )
    except GitHubRateLimitError as rate_err:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(rate_err),
        )
    except Exception as exc:
        logger.warning("Could not reach GitHub API for metadata, falling back to URL registration: %s", exc)
        meta = {
            "owner": owner,
            "repo": repo,
            "url": payload.url,
            "default_branch": payload.default_branch or "main",
            "description": None,
            "language": None,
            "stars": 0,
            "forks": 0,
            "is_private": False,
        }

    # Register in Neo4j if available
    try:
        if graph_manager.is_available():
            graph_manager.register_repository(
                url=meta["url"],
                name=repo,
                default_branch=meta["default_branch"],
                owner=owner,
                metadata={
                    "language": meta.get("language"),
                    "stars": meta.get("stars", 0),
                    "forks": meta.get("forks", 0),
                },
            )
            if payload.service_name:
                # Ensure service exists in graph first
                graph_manager.register_service(name=payload.service_name)
                graph_manager.connect_service_to_repo(
                    service_name=payload.service_name,
                    repo_url=meta["url"],
                )
    except Exception as graph_err:
        logger.warning("Failed to persist repository in Neo4j: %s", graph_err)

    return RepositoryResponse(
        owner=owner,
        repo=repo,
        url=meta["url"],
        service_name=payload.service_name,
        default_branch=meta.get("default_branch", "main"),
        description=meta.get("description"),
        language=meta.get("language"),
        stars=meta.get("stars", 0),
        forks=meta.get("forks", 0),
        is_private=meta.get("is_private", False),
        registered_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/repositories/{owner}/{repo}",
    response_model=RepositoryResponse,
    summary="Get repository metadata from GitHub",
)
async def get_repository(
    owner: str,
    repo: str,
    github_service: GitHubService = Depends(get_github_service),
) -> RepositoryResponse:
    """Retrieves repository metadata from GitHub API."""
    try:
        meta = await github_service.get_repository_metadata(owner=owner, repo=repo)
        return RepositoryResponse(
            owner=meta["owner"],
            repo=meta["repo"],
            url=meta["url"],
            default_branch=meta["default_branch"],
            description=meta["description"],
            language=meta["language"],
            stars=meta["stars"],
            forks=meta["forks"],
            is_private=meta["is_private"],
            registered_at=datetime.now(timezone.utc).isoformat(),
        )
    except GitHubResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{owner}/{repo}' not found on GitHub.",
        )
    except GitHubRateLimitError as rate_err:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(rate_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitHub API error: {str(exc)}",
        )


@router.get(
    "/repositories/{owner}/{repo}/commits",
    response_model=List[CommitSummary],
    summary="Get recent commits for a repository",
)
async def get_repository_commits(
    owner: str,
    repo: str,
    branch: Optional[str] = Query(default=None),
    since: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    github_service: GitHubService = Depends(get_github_service),
) -> List[CommitSummary]:
    """Retrieves recent commits from the specified repository."""
    try:
        commits = await github_service.get_recent_commits(
            owner=owner,
            repo=repo,
            branch=branch,
            since=since,
            limit=limit,
        )
        return [CommitSummary(**c) for c in commits]
    except GitHubResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{owner}/{repo}' not found on GitHub.",
        )
    except GitHubRateLimitError as rate_err:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(rate_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitHub API error: {str(exc)}",
        )


@router.get(
    "/repositories/{owner}/{repo}/commits/{sha}",
    response_model=CommitDetails,
    summary="Get commit details and file diff patches",
)
async def get_commit_details(
    owner: str,
    repo: str,
    sha: str,
    github_service: GitHubService = Depends(get_github_service),
) -> CommitDetails:
    """Retrieves commit metadata, changed files, and unified diff patches."""
    try:
        details = await github_service.get_commit_details(owner=owner, repo=repo, sha=sha)
        return CommitDetails(**details)
    except GitHubResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commit '{sha}' not found in repository '{owner}/{repo}'.",
        )
    except GitHubRateLimitError as rate_err:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(rate_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitHub API error: {str(exc)}",
        )

