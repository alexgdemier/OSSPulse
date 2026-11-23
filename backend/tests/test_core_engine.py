import argparse
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from app.analyzers.scoring import build_report
from app.api.v1 import router as api_router
from app.cli import parse_repository_url
from app.integrations.github import GitHubAPIError, GitHubClient
from app.main import app
from app.schemas.github import (
    GitHubCommit,
    GitHubIssue,
    GitHubRelease,
    GitHubRepository,
    RepositoryFiles,
    RepositorySnapshot,
)
from fastapi.testclient import TestClient


def test_repository_url_validation():
    assert parse_repository_url("https://github.com/tiangolo/fastapi.git") == (
        "tiangolo",
        "fastapi",
    )
    for invalid in (
        "http://github.com/owner/repo",
        "https://github.com.evil.test/owner/repo",
        "https://example.com/owner/repo",
        "https://github.com/owner/repo/extra",
    ):
        with pytest.raises(argparse.ArgumentTypeError):
            parse_repository_url(invalid)


def test_api_health_and_invalid_repository_url():
    client = TestClient(app)
    assert client.get("/api/v1/health").json() == {"status": "ok"}
    response = client.post(
        "/api/v1/analyze", json={"repository_url": "https://example.com/owner/repo"}
    )
    assert response.status_code == 400


def test_unknown_report_returns_not_found():
    api_router._REPORTS.clear()
    response = TestClient(app).get("/api/v1/reports/missing")
    assert response.status_code == 404


def test_github_client_normalizes_snapshot_and_calls_central_api():
    calls = []
    now = datetime.now(UTC)
    repo = {
        "id": 1,
        "full_name": "owner/repo",
        "name": "repo",
        "html_url": "https://github.com/owner/repo",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "pushed_at": now.isoformat(),
        "stargazers_count": 3,
        "forks_count": 1,
        "watchers_count": 3,
        "open_issues_count": 1,
        "default_branch": "main",
        "owner": {"login": "owner"},
    }

    def handler(request):
        calls.append(request)
        path = request.url.path
        if path.endswith("/repos/owner/repo"):
            return httpx.Response(200, json=repo)
        if path.endswith("/issues"):
            return httpx.Response(200, json=[])
        if path.endswith("/commits"):
            return httpx.Response(200, json=[])
        if path.endswith("/releases"):
            return httpx.Response(200, json=[])
        if path.endswith("/git/trees/main"):
            return httpx.Response(
                200,
                json={"truncated": False, "tree": [{"path": "README.md", "type": "blob"}]},
            )
        return httpx.Response(404, json={"message": "Not found"})

    snapshot = GitHubClient(transport=httpx.MockTransport(handler)).analyze("owner", "repo")
    assert snapshot.repository.full_name == "owner/repo"
    assert snapshot.files.readme is True
    assert snapshot.completeness["issues"] is True
    assert all(request.url.host == "api.github.com" for request in calls)


def test_github_client_marks_bounded_pagination_incomplete(monkeypatch):
    monkeypatch.setattr("app.integrations.github.client.settings.github_max_pages", 2)
    calls = []

    def handler(request):
        calls.append(request)
        page = request.url.params.get("page")
        if request.url.path.endswith("/issues"):
            return httpx.Response(
                200,
                json=[
                    {
                        "number": int(page),
                        "html_url": f"https://github.com/owner/repo/issues/{page}",
                        "title": "Example issue",
                        "state": "open",
                        "created_at": "2025-01-01T00:00:00Z",
                        "updated_at": "2025-01-01T00:00:00Z",
                        "comments": 0,
                    }
                ],
                headers={
                    "Link": (
                        '<https://api.github.com/repos/owner/repo/issues?page=2>; rel="next", '
                        '<https://api.github.com/repos/owner/repo/issues?page=3>; rel="last"'
                        if page == "1"
                        else ""
                    )
                },
            )
        if request.url.path.endswith("/repos/owner/repo"):
            return httpx.Response(
                200,
                json={
                    "id": 1,
                    "full_name": "owner/repo",
                    "name": "repo",
                    "html_url": "https://github.com/owner/repo",
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z",
                    "pushed_at": "2025-01-01T00:00:00Z",
                    "stargazers_count": 0,
                    "forks_count": 0,
                    "watchers_count": 0,
                    "open_issues_count": 1,
                    "default_branch": "main",
                    "owner": {"login": "owner"},
                },
            )
        if request.url.path.endswith("/git/trees/main"):
            return httpx.Response(200, json={"truncated": False, "tree": []})
        return httpx.Response(200, json=[])

    snapshot = GitHubClient(transport=httpx.MockTransport(handler)).analyze("owner", "repo")
    issue_pages = [call for call in calls if call.url.path.endswith("/issues")]
    assert [call.url.params["page"] for call in issue_pages] == ["1"]
    assert snapshot.completeness["issues"] is False


def test_404_is_normalized():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(404, json={"message": "Not Found"})
    )
    with pytest.raises(GitHubAPIError) as caught:
        GitHubClient(transport=transport).analyze("owner", "missing")
    assert caught.value.status_code == 404


def test_scoring_does_not_turn_missing_data_into_zero():
    now = datetime.now(UTC)
    repository = GitHubRepository(
        id=1,
        full_name="owner/repo",
        name="repo",
        html_url="https://github.com/owner/repo",
        created_at=now - timedelta(days=60),
        updated_at=now,
        pushed_at=now,
        stargazers_count=0,
        forks_count=0,
        watchers_count=0,
        open_issues_count=0,
        default_branch="main",
        owner={"login": "owner"},
    )
    snapshot = RepositorySnapshot(
        repository=repository,
        issues=[],
        commits=[
            GitHubCommit(
                sha="abc",
                html_url="https://github.com/owner/repo/commit/abc",
                commit={"author": {"date": now.isoformat()}},
            )
        ],
        releases=[
            GitHubRelease(
                tag_name="v1",
                html_url="https://github.com/owner/repo/releases/tag/v1",
                published_at=now - timedelta(days=30),
            )
        ],
        files=RepositoryFiles(
            readme=True,
            license=True,
            contributing=False,
            docs=False,
            tests=True,
            workflows=True,
            development_config=True,
        ),
        fetched_at=now,
        completeness={"issues": False, "commits": False, "releases": True, "repository_tree": True},
    )
    report = build_report(snapshot)
    assert report["health_score"] is not None
    assert report["dimensions"]["maintenance"] is None
    assert report["dimensions"]["community"] is None
    assert report["dimensions"]["sustainability"] is None
    assert report["coverage"] == 35
    assert report["classification"] == "Insufficient Data"


def test_open_unanswered_issue_produces_evidence():
    now = datetime.now(UTC)
    repository = GitHubRepository(
        id=1,
        full_name="owner/repo",
        name="repo",
        html_url="https://github.com/owner/repo",
        created_at=now - timedelta(days=100),
        updated_at=now,
        pushed_at=now,
        stargazers_count=0,
        forks_count=0,
        watchers_count=0,
        open_issues_count=1,
        default_branch="main",
        owner={"login": "owner"},
    )
    issue = GitHubIssue(
        number=42,
        html_url="https://github.com/owner/repo/issues/42",
        title="Example",
        state="open",
        created_at=now - timedelta(days=20),
        updated_at=now - timedelta(days=20),
        comments=0,
    )
    snapshot = RepositorySnapshot(
        repository=repository,
        issues=[issue],
        commits=[],
        releases=[],
        files=RepositoryFiles(
            readme=True,
            license=True,
            contributing=True,
            docs=True,
            tests=True,
            workflows=True,
            development_config=True,
        ),
        fetched_at=now,
        completeness={"issues": True, "commits": True, "releases": True, "repository_tree": True},
    )
    report = build_report(snapshot)
    finding = next(item for item in report["findings"] if item["code"] == "IS001")
    assert finding["evidence"]["number"] == 42
    assert finding["source_url"] == issue.html_url
