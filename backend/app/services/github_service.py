"""
GitHub Repository and Commit Intelligence Service for DebugGraph AI.
Interacts with the GitHub REST API using httpx to inspect repositories,
retrieve commit histories, analyze code diffs, and correlate changes with incident errors.
"""
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GitHubAPIError(Exception):
    """Raised when GitHub REST API returns an unexpected error."""
    pass


class GitHubRateLimitError(GitHubAPIError):
    """Raised when GitHub REST API rate limit is exceeded."""
    pass


class GitHubResourceNotFoundError(GitHubAPIError):
    """Raised when a repository or commit is not found on GitHub."""
    pass


def parse_github_url(url: str) -> Tuple[str, str]:
    """
    Parses a GitHub repository URL or slug into (owner, repo).
    Supports:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - git@github.com:owner/repo.git
    - owner/repo
    """
    cleaned = url.strip()
    if not cleaned:
        raise ValueError("GitHub URL or repository identifier cannot be empty.")

    # Match git@github.com:owner/repo.git
    ssh_match = re.match(r"^git@github\.com:([\w.-]+)/([\w.-]+?)(\.git)?$", cleaned)
    if ssh_match:
        return ssh_match.group(1), ssh_match.group(2)

    # Match https://github.com/owner/repo or http://...
    https_match = re.match(r"^https?://(?:www\.)?github\.com/([\w.-]+)/([\w.-]+?)(\.git)?(?:/.*)?$", cleaned)
    if https_match:
        return https_match.group(1), https_match.group(2)

    # Match owner/repo
    slug_match = re.match(r"^([\w.-]+)/([\w.-]+?)(\.git)?$", cleaned)
    if slug_match:
        return slug_match.group(1), slug_match.group(2)

    raise ValueError(
        f"Invalid GitHub repository URL or format: '{url}'. Expected 'https://github.com/owner/repo' or 'owner/repo'."
    )


class GitHubService:
    """
    Asynchronous GitHub API client for repository and commit intelligence.
    Supports public access without tokens and private access with GITHUB_TOKEN.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 15.0,
    ) -> None:
        self.token = token if token is not None else settings.GITHUB_TOKEN
        self.base_url = (base_url or settings.GITHUB_API_BASE_URL).rstrip("/")
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        """Constructs headers for GitHub REST API v3."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"DebugGraph-AI/{settings.APP_VERSION}",
        }
        if self.token and self.token.strip() and self.token != "your_github_token_here_optional":
            headers["Authorization"] = f"Bearer {self.token.strip()}"
        return headers

    def _handle_response_errors(self, response: httpx.Response, context: str) -> None:
        """Translates HTTP error status codes into domain-specific exceptions."""
        if response.status_code == 404:
            raise GitHubResourceNotFoundError(f"Resource not found on GitHub ({context}): {response.text}")
        if response.status_code in (403, 429):
            remaining = response.headers.get("x-ratelimit-remaining", "0")
            reset_ts = response.headers.get("x-ratelimit-reset", "")
            if remaining == "0" or "rate limit" in response.text.lower():
                raise GitHubRateLimitError(
                    f"GitHub API rate limit exceeded ({context}). Reset at timestamp: {reset_ts}."
                )
        if response.status_code >= 400:
            raise GitHubAPIError(f"GitHub API error [{response.status_code}] during {context}: {response.text}")

    async def get_repository_metadata(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Retrieves repository details from GitHub REST API.
        GET /repos/{owner}/{repo}
        """
        url = f"{self.base_url}/repos/{owner}/{repo}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                self._handle_response_errors(response, f"get_repository_metadata({owner}/{repo})")
                data = response.json()
                return {
                    "owner": data.get("owner", {}).get("login", owner),
                    "repo": data.get("name", repo),
                    "url": data.get("html_url", f"https://github.com/{owner}/{repo}"),
                    "default_branch": data.get("default_branch", "main"),
                    "description": data.get("description"),
                    "language": data.get("language"),
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "is_private": data.get("private", False),
                }
            except httpx.RequestError as exc:
                logger.error("Network error communicating with GitHub API: %s", exc)
                raise GitHubAPIError(f"Network error communicating with GitHub: {exc}") from exc

    async def get_recent_commits(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves recent commit list for a repository.
        GET /repos/{owner}/{repo}/commits
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params: Dict[str, Any] = {"per_page": min(max(1, limit), 100)}
        if branch:
            params["sha"] = branch
        if since:
            params["since"] = since

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self._get_headers(), params=params)
                self._handle_response_errors(response, f"get_recent_commits({owner}/{repo})")
                commits_raw = response.json()
                results = []
                for c in commits_raw:
                    sha = c.get("sha", "")
                    commit_obj = c.get("commit", {})
                    author_obj = commit_obj.get("author", {})
                    results.append({
                        "sha": sha,
                        "short_sha": sha[:7] if sha else "",
                        "message": commit_obj.get("message", "").split("\n")[0],
                        "author": author_obj.get("name", "Unknown"),
                        "date": author_obj.get("date", ""),
                        "url": c.get("html_url", f"https://github.com/{owner}/{repo}/commit/{sha}"),
                    })
                return results
            except httpx.RequestError as exc:
                logger.error("Network error fetching commits for %s/%s: %s", owner, repo, exc)
                raise GitHubAPIError(f"Network error fetching commits: {exc}") from exc

    async def get_commit_details(self, owner: str, repo: str, sha: str) -> Dict[str, Any]:
        """
        Retrieves commit metadata, stat summary, and file diff patches.
        GET /repos/{owner}/{repo}/commits/{ref}
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/commits/{sha}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                self._handle_response_errors(response, f"get_commit_details({owner}/{repo}@{sha})")
                data = response.json()

                commit_obj = data.get("commit", {})
                author_obj = commit_obj.get("author", {})
                files_raw = data.get("files", [])

                files = []
                for f in files_raw:
                    files.append({
                        "filename": f.get("filename", ""),
                        "status": f.get("status", "modified"),
                        "additions": f.get("additions", 0),
                        "deletions": f.get("deletions", 0),
                        "changes": f.get("changes", 0),
                        "patch": f.get("patch"),
                    })

                return {
                    "sha": sha,
                    "short_sha": sha[:7],
                    "message": commit_obj.get("message", ""),
                    "author": author_obj.get("name", "Unknown"),
                    "date": author_obj.get("date", ""),
                    "url": data.get("html_url", f"https://github.com/{owner}/{repo}/commit/{sha}"),
                    "stats": data.get("stats", {}),
                    "files": files,
                }
            except httpx.RequestError as exc:
                logger.error("Network error fetching commit details for %s/%s@%s: %s", owner, repo, sha, exc)
                raise GitHubAPIError(f"Network error fetching commit details: {exc}") from exc

    async def get_commit_diff(self, owner: str, repo: str, sha: str) -> str:
        """
        Retrieves raw unified diff patch for a commit.
        Headers: Accept: application/vnd.github.v3.diff
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/commits/{sha}"
        headers = self._get_headers()
        headers["Accept"] = "application/vnd.github.v3.diff"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                self._handle_response_errors(response, f"get_commit_diff({owner}/{repo}@{sha})")
                return response.text
            except httpx.RequestError as exc:
                logger.error("Network error fetching diff for %s/%s@%s: %s", owner, repo, sha, exc)
                raise GitHubAPIError(f"Network error fetching diff: {exc}") from exc

    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None,
    ) -> Optional[str]:
        """
        Retrieves raw file contents at a specific path and commit ref.
        GET /repos/{owner}/{repo}/contents/{path}
        Headers: Accept: application/vnd.github.v3.raw
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path.lstrip('/')}"
        headers = self._get_headers()
        headers["Accept"] = "application/vnd.github.v3.raw"
        params = {"ref": ref} if ref else {}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                if response.status_code == 404:
                    return None
                self._handle_response_errors(response, f"get_file_content({owner}/{repo}:{path})")
                return response.text
            except Exception as exc:
                logger.warning("Failed to fetch file content for %s/%s:%s: %s", owner, repo, path, exc)
                return None

    async def correlate_commits_with_incident(
        self,
        owner: str,
        repo: str,
        error_signatures: List[str],
        affected_files: Optional[List[str]] = None,
        since: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Analyzes recent commits and diffs against reported error signatures.
        Identifies suspect commits that modified relevant files or logic.
        Strictly enforces evidence grounding:
        - Cites Repository, Commit SHA, File path, and Diff excerpt.
        - Avoids claiming unverified causality without explicit log/code match.
        """
        try:
            commits = await self.get_recent_commits(owner=owner, repo=repo, since=since, limit=limit)
        except Exception as exc:
            logger.warning("Could not fetch commits for correlation on %s/%s: %s", owner, repo, exc)
            return {
                "repository": f"{owner}/{repo}",
                "commits_inspected_count": 0,
                "has_candidate_commits": False,
                "candidate_commits": [],
                "analysis_summary": f"Could not retrieve GitHub commits for correlation: {exc}",
            }

        candidate_commits = []
        error_tokens = set()
        for sig in error_signatures:
            for token in re.findall(r"[A-Za-z0-9_]{4,}", sig):
                error_tokens.add(token.lower())

        for c_summary in commits[:5]:  # Deeply inspect top 5 candidate commits
            sha = c_summary["sha"]
            try:
                details = await self.get_commit_details(owner=owner, repo=repo, sha=sha)
            except Exception:
                continue

            matching_files: List[str] = []
            matching_diff_snippets: List[str] = []
            score = 0.0

            for f in details.get("files", []):
                fname = f.get("filename", "")
                patch = f.get("patch", "") or ""

                # Check if file matches affected files or error tokens
                file_matched = False
                if affected_files and any(af.lower() in fname.lower() for af in affected_files):
                    file_matched = True
                    score += 0.4

                # Check diff patch against error tokens
                patch_lower = patch.lower()
                matched_tokens = [tok for tok in error_tokens if tok in patch_lower]
                if matched_tokens:
                    file_matched = True
                    score += min(0.5, len(matched_tokens) * 0.15)
                    # Extract up to 5 lines of relevant diff
                    lines = patch.split("\n")
                    matched_lines = [l for l in lines if any(tok in l.lower() for tok in matched_tokens)][:3]
                    if matched_lines:
                        matching_diff_snippets.append(f"{fname}:\n" + "\n".join(matched_lines))

                if file_matched:
                    matching_files.append(fname)

            # Check commit message
            msg_lower = details.get("message", "").lower()
            if any(tok in msg_lower for tok in error_tokens):
                score += 0.2

            score = min(1.0, round(score, 2))
            if score >= 0.2:
                candidate_commits.append({
                    "sha": sha,
                    "short_sha": sha[:7],
                    "repository": f"{owner}/{repo}",
                    "author": details.get("author", "Unknown"),
                    "date": details.get("date", ""),
                    "relevance_score": score,
                    "suspect_files": matching_files,
                    "diff_excerpt": "\n---\n".join(matching_diff_snippets) if matching_diff_snippets else None,
                    "correlation_reasoning": (
                        f"Commit {sha[:7]} by {details.get('author')} modified {len(matching_files)} "
                        f"relevant file(s) [{', '.join(matching_files[:3])}] with code changes matching "
                        f"incident error tokens."
                    ),
                })

        # Sort candidate commits by relevance score descending
        candidate_commits.sort(key=lambda x: x["relevance_score"], reverse=True)

        has_candidates = len(candidate_commits) > 0
        if has_candidates:
            top = candidate_commits[0]
            summary = (
                f"Identified {len(candidate_commits)} commit(s) in {owner}/{repo} with potential relevance "
                f"to the incident. Top candidate {top['short_sha']} modified {', '.join(top['suspect_files'][:2])}."
            )
        else:
            summary = f"Inspected {len(commits)} recent commit(s) in {owner}/{repo}. No direct code diff matches found for the reported error signatures."

        return {
            "repository": f"{owner}/{repo}",
            "commits_inspected_count": len(commits),
            "has_candidate_commits": has_candidates,
            "candidate_commits": candidate_commits,
            "analysis_summary": summary,
        }

