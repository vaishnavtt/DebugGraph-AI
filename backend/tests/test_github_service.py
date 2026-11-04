"""
Unit and integration tests for GitHub Repository and Commit Intelligence Service and endpoints.
Uses mock HTTP responses to verify functionality without external network calls or credentials.
"""
from unittest.mock import AsyncMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.github_service import (
    GitHubAPIError,
    GitHubRateLimitError,
    GitHubResourceNotFoundError,
    GitHubService,
    parse_github_url,
)

client = TestClient(app)


# =============================================================================
# 1. parse_github_url Tests
# =============================================================================

def test_parse_github_url_variants():
    """Verify parsing of various GitHub URL formats."""
    # HTTPS full URL
    owner, repo = parse_github_url("https://github.com/my-org/payment-service")
    assert owner == "my-org"
    assert repo == "payment-service"

    # HTTPS with .git
    owner, repo = parse_github_url("https://github.com/my-org/payment-service.git")
    assert owner == "my-org"
    assert repo == "payment-service"

    # SSH format
    owner, repo = parse_github_url("git@github.com:octocat/Hello-World.git")
    assert owner == "octocat"
    assert repo == "Hello-World"

    # Slug format
    owner, repo = parse_github_url("kubernetes/kubernetes")
    assert owner == "kubernetes"
    assert repo == "kubernetes"


def test_parse_github_url_invalid():
    """Verify invalid repository URLs raise ValueError."""
    with pytest.raises(ValueError, match="Invalid GitHub repository URL"):
        parse_github_url("https://gitlab.com/owner/repo")

    with pytest.raises(ValueError, match="cannot be empty"):
        parse_github_url("")


# =============================================================================
# 2. GitHubService Tests
# =============================================================================

@pytest.mark.asyncio
async def test_get_repository_metadata():
    """Verify retrieving repository metadata from GitHub API."""
    mock_response = httpx.Response(
        200,
        json={
            "owner": {"login": "my-org"},
            "name": "payment-service",
            "html_url": "https://github.com/my-org/payment-service",
            "default_branch": "main",
            "description": "Core payment processing service",
            "language": "Python",
            "stargazers_count": 42,
            "forks_count": 5,
            "private": False,
        },
        request=httpx.Request("GET", "https://api.github.com/repos/my-org/payment-service"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        svc = GitHubService()
        meta = await svc.get_repository_metadata("my-org", "payment-service")
        assert meta["owner"] == "my-org"
        assert meta["repo"] == "payment-service"
        assert meta["default_branch"] == "main"
        assert meta["stars"] == 42


@pytest.mark.asyncio
async def test_get_repository_not_found():
    """Verify 404 response raises GitHubResourceNotFoundError."""
    mock_response = httpx.Response(
        404,
        json={"message": "Not Found"},
        request=httpx.Request("GET", "https://api.github.com/repos/my-org/nonexistent"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        svc = GitHubService()
        with pytest.raises(GitHubResourceNotFoundError):
            await svc.get_repository_metadata("my-org", "nonexistent")


@pytest.mark.asyncio
async def test_get_repository_rate_limited():
    """Verify 403 rate limit response raises GitHubRateLimitError."""
    mock_response = httpx.Response(
        403,
        json={"message": "API rate limit exceeded"},
        headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1730000000"},
        request=httpx.Request("GET", "https://api.github.com/repos/my-org/payment-service"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        svc = GitHubService()
        with pytest.raises(GitHubRateLimitError):
            await svc.get_repository_metadata("my-org", "payment-service")


@pytest.mark.asyncio
async def test_get_recent_commits():
    """Verify fetching commit list returns structured summaries."""
    mock_response = httpx.Response(
        200,
        json=[
            {
                "sha": "a1b2c3d4e5f67890123456789abcdef012345678",
                "commit": {
                    "message": "fix: resolve PostgreSQL connection pool timeout",
                    "author": {"name": "Alice Dev", "date": "2026-11-04T10:00:00Z"},
                },
                "html_url": "https://github.com/my-org/payment-service/commit/a1b2c3d",
            }
        ],
        request=httpx.Request("GET", "https://api.github.com/repos/my-org/payment-service/commits"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        svc = GitHubService()
        commits = await svc.get_recent_commits("my-org", "payment-service", limit=5)
        assert len(commits) == 1
        assert commits[0]["short_sha"] == "a1b2c3d"
        assert commits[0]["author"] == "Alice Dev"
        assert "PostgreSQL" in commits[0]["message"]


@pytest.mark.asyncio
async def test_correlate_commits_with_incident():
    """Verify commit correlation against error signatures with strict citations."""
    mock_commits_resp = httpx.Response(
        200,
        json=[
            {
                "sha": "f1e2d3c4b5a6",
                "commit": {
                    "message": "chore: adjust pool size configuration",
                    "author": {"name": "Bob Architect", "date": "2026-11-04T11:00:00Z"},
                },
                "html_url": "https://github.com/my-org/payment-service/commit/f1e2d3c",
            }
        ],
        request=httpx.Request("GET", "https://api.github.com/repos/my-org/payment-service/commits"),
    )

    mock_commit_detail_resp = httpx.Response(
        200,
        json={
            "sha": "f1e2d3c4b5a6",
            "commit": {
                "message": "chore: adjust pool size configuration",
                "author": {"name": "Bob Architect", "date": "2026-11-04T11:00:00Z"},
            },
            "html_url": "https://github.com/my-org/payment-service/commit/f1e2d3c",
            "stats": {"total": 4, "additions": 2, "deletions": 2},
            "files": [
                {
                    "filename": "backend/app/database/pool.py",
                    "status": "modified",
                    "additions": 1,
                    "deletions": 1,
                    "patch": "- pool_size = 20\n+ pool_size = 2\n# timeout error",
                }
            ],
        },
        request=httpx.Request("GET", "https://api.github.com/repos/my-org/payment-service/commits/f1e2d3c4b5a6"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = [mock_commits_resp, mock_commit_detail_resp]

        svc = GitHubService()
        result = await svc.correlate_commits_with_incident(
            owner="my-org",
            repo="payment-service",
            error_signatures=["timeout error in database pool", "ConnectionRefusedError"],
        )

        assert result["has_candidate_commits"] is True
        assert len(result["candidate_commits"]) == 1
        cand = result["candidate_commits"][0]
        assert cand["short_sha"] == "f1e2d3c"
        assert "backend/app/database/pool.py" in cand["suspect_files"]
        assert cand["diff_excerpt"] is not None
        assert "pool_size" in cand["diff_excerpt"]


# =============================================================================
# 3. GitHub API Endpoints Tests
# =============================================================================

def test_api_register_repository():
    """Verify POST /api/v1/github/repositories registers repo and connects to service."""
    with patch("app.services.github_service.GitHubService.get_repository_metadata", new_callable=AsyncMock) as mock_meta:
        mock_meta.return_value = {
            "owner": "test-org",
            "repo": "auth-service",
            "url": "https://github.com/test-org/auth-service",
            "default_branch": "main",
            "description": "Auth service repository",
            "language": "Python",
            "stars": 10,
            "forks": 1,
            "is_private": False,
        }

        with patch("app.graph.manager.KnowledgeGraphManager.is_available") as mock_avail:
            mock_avail.return_value = False

            response = client.post(
                "/api/v1/github/repositories",
                json={
                    "url": "https://github.com/test-org/auth-service",
                    "service_name": "auth-service",
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["owner"] == "test-org"
            assert data["repo"] == "auth-service"
            assert data["service_name"] == "auth-service"


def test_api_get_repository_commits():
    """Verify GET /api/v1/github/repositories/{owner}/{repo}/commits endpoint."""
    with patch("app.services.github_service.GitHubService.get_recent_commits", new_callable=AsyncMock) as mock_commits:
        mock_commits.return_value = [
            {
                "sha": "1234567890abcdef",
                "short_sha": "1234567",
                "message": "fix: handle connection timeout",
                "author": "Dev",
                "date": "2026-11-04T12:00:00Z",
                "url": "https://github.com/test-org/repo/commit/1234567",
            }
        ]

        response = client.get("/api/v1/github/repositories/test-org/repo/commits")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["short_sha"] == "1234567"

