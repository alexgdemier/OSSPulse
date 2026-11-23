from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, quote, urlparse

import httpx

from app.core.config import settings
from app.schemas.github import (
    GitHubCommit,
    GitHubIssue,
    GitHubRelease,
    GitHubRepository,
    RepositoryFiles,
    RepositorySnapshot,
)


class GitHubAPIError(Exception):
    def __init__(self, status_code: int, message: str, *, reset_at: str | None = None):
        self.status_code = status_code
        self.reset_at = reset_at
        super().__init__(message)


class GitHubClient:
    def __init__(self, *, token: str | None = None, transport: httpx.BaseTransport | None = None):
        self._token = token if token is not None else settings.github_token
        self._transport = transport

    def _request(self, client: httpx.Client, path: str, params: dict | None = None):
        response = client.get(path, params=params)
        if response.status_code >= 400:
            message = "GitHub API request failed"
            try:
                message = response.json().get("message", message)
            except ValueError:
                pass
            raise GitHubAPIError(
                response.status_code, message, reset_at=response.headers.get("x-ratelimit-reset")
            )
        return response

    def _list(
        self, client: httpx.Client, path: str, params: dict | None = None
    ) -> tuple[list[dict], bool]:
        results: list[dict] = []
        base = {"per_page": 100, **(params or {})}
        complete = True
        page = 1
        page_limit = max(1, settings.github_max_pages)
        while page <= page_limit:
            response = self._request(client, path, {**base, "page": page})
            results.extend(response.json())
            links = response.headers.get("link", "").split(",")
            next_link = next(
                (part.split(";", 1)[0].strip()[1:-1] for part in links if 'rel="next"' in part),
                None,
            )
            if not next_link:
                break
            next_page = parse_qs(urlparse(next_link).query).get("page", [None])[0]
            if not next_page or not next_page.isdigit():
                complete = False
                break
            page = int(next_page)
            if page > page_limit:
                complete = False
                break
            if page >= page_limit:
                last_link = next(
                    (part.split(";", 1)[0].strip()[1:-1] for part in links if 'rel="last"' in part),
                    None,
                )
                last_page = (
                    parse_qs(urlparse(last_link).query).get("page", [None])[0]
                    if last_link
                    else None
                )
                if last_page and last_page.isdigit() and int(last_page) > page:
                    complete = False
                    break
        return results, complete

    def analyze(self, owner: str, repository: str) -> RepositorySnapshot:
        fetched_at = datetime.now(UTC)
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "OSS-Pulse/0.2.0-alpha",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        safe_owner, safe_repo = quote(owner, safe=""), quote(repository, safe="")
        base_url = settings.github_api_url.rstrip("/") + "/"
        with httpx.Client(
            base_url=base_url,
            headers=headers,
            timeout=settings.github_timeout_seconds,
            follow_redirects=False,
            transport=self._transport,
        ) as client:
            repo = GitHubRepository.model_validate(
                self._request(client, f"repos/{safe_owner}/{safe_repo}").json()
            )
            raw_issues, issues_complete = self._list(
                client,
                f"repos/{safe_owner}/{safe_repo}/issues",
                {"state": "open", "sort": "updated", "direction": "desc"},
            )
            raw_commits, commits_complete = self._list(
                client,
                f"repos/{safe_owner}/{safe_repo}/commits",
                {
                    "sha": repo.default_branch,
                    "since": (fetched_at - timedelta(days=180)).isoformat().replace("+00:00", "Z"),
                    "until": fetched_at.isoformat().replace("+00:00", "Z"),
                },
            )
            raw_releases, releases_complete = self._list(
                client, f"repos/{safe_owner}/{safe_repo}/releases"
            )
            raw_tree = self._request(
                client,
                f"repos/{safe_owner}/{safe_repo}/git/trees/{quote(repo.default_branch, safe='')}",
                {"recursive": "1"},
            ).json()

        names = {
            item.get("path", "").lower()
            for item in raw_tree.get("tree", [])
            if item.get("type") == "blob"
        }
        root_names = {name for name in names if "/" not in name}
        directory_names = {part for name in names for part in name.split("/")[:-1]}
        documentation_directories = {"docs", "documentation"}
        test_directories = {"test", "tests", "spec", "specs", "__tests__"}
        files = RepositoryFiles(
            readme=any(name == "readme" or name.startswith("readme.") for name in root_names),
            license=any(
                name.startswith("license") or name.startswith("copying") for name in root_names
            ),
            contributing=any(name.startswith("contributing") for name in root_names),
            docs=bool(directory_names & documentation_directories),
            tests=bool(directory_names & test_directories)
            or any(
                name.startswith(".github/workflows/") and "test" in name for name in names
            ),
            workflows=any(name.startswith(".github/workflows/") for name in names),
            development_config=any(
                name in root_names
                for name in (
                    "makefile",
                    "justfile",
                    "pyproject.toml",
                    "package.json",
                    "cargo.toml",
                    "go.mod",
                )
            ),
        )
        return RepositorySnapshot(
            repository=repo,
            issues=[GitHubIssue.model_validate(item) for item in raw_issues],
            commits=[GitHubCommit.model_validate(item) for item in raw_commits],
            releases=[GitHubRelease.model_validate(item) for item in raw_releases],
            files=files,
            fetched_at=fetched_at,
            completeness={
                "issues": issues_complete,
                "commits": commits_complete,
                "releases": releases_complete,
                "repository_tree": not raw_tree.get("truncated", False),
            },
        )
