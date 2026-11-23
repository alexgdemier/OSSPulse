import argparse
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from app.analyzers.scoring import build_report
from app.cli import parse_repository_url
from app.database.models import AnalysisReport, DimensionScore, Finding, Insight, Repository
from app.database.repository import (
    get_report,
    get_repository_reports,
    list_recent_reports,
    save_report,
)
from app.database.session import database_connect_args
from app.integrations.github import GitHubAPIError, GitHubClient
from app.schemas.github import (
    GitHubCommit,
    GitHubIssue,
    GitHubRelease,
    GitHubRepository,
    RepositoryFiles,
    RepositorySnapshot,
)


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


def test_api_health_and_invalid_repository_url(api_client):
    assert api_client.get("/api/v1/health").json() == {"status": "ok"}
    assert api_client.get("/api/v1/ready").json() == {"status": "ready"}
    response = api_client.post(
        "/api/v1/analyze", json={"repository_url": "https://example.com/owner/repo"}
    )
    assert response.status_code == 400


def test_readiness_returns_service_unavailable_when_database_fails(api_client, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session

    def fail_query(self, statement, *args, **kwargs):
        raise SQLAlchemyError("simulated database outage")

    monkeypatch.setattr(Session, "execute", fail_query)
    response = api_client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database is unavailable"


def test_database_ssl_uses_certificate_and_hostname_verification(monkeypatch):
    monkeypatch.setattr("app.database.session.settings.database_ssl", True)
    ssl_context = database_connect_args()["ssl_context"]
    assert ssl_context.check_hostname is True
    assert ssl_context.verify_mode.name == "CERT_REQUIRED"


def test_analysis_api_rejects_invalid_urls_without_requesting_github(api_client):
    response = api_client.post(
        "/api/v1/analyze", json={"repository_url": "https://github.com.evil.test/owner/repo"}
    )
    assert response.status_code == 400


def test_unknown_report_returns_not_found(api_client):
    response = api_client.get("/api/v1/reports/missing")
    assert response.status_code == 404


def test_report_is_persisted_in_normalized_tables(sqlite_sessions, api_client):
    timestamp = "2026-11-23T12:00:00+00:00"
    report = {
        "report_id": "report-123",
        "status": "completed",
        "analyzed_at": timestamp,
        "engine_version": "0.2.0-alpha",
        "health_score": 82,
        "coverage": 100,
        "classification": "Healthy",
        "repository": {
            "id": 123,
            "owner": "owner",
            "name": "project",
            "full_name": "owner/project",
            "url": "https://github.com/owner/project",
            "created_at": timestamp,
        },
        "dimensions": {"maintenance": 80.0, "community": None},
        "data_completeness": {"issues": True},
        "findings": [
            {
                "code": "DC001",
                "category": "documentation",
                "title": "Contributor guide missing",
                "description": "No contributor guide was found.",
                "severity": "low",
                "evidence": {"checked": "CONTRIBUTING*"},
                "recommendation": "Add a contributor guide.",
                "source_url": None,
                "detected_at": timestamp,
            }
        ],
        "insights": [
            {
                "code": "DC001",
                "title": "Contributor guide missing",
                "source_url": None,
                "priority_score": 50,
            }
        ],
    }
    with sqlite_sessions() as session:
        save_report(session, report)
        assert get_report(session, "report-123") == report
        assert session.query(Repository).count() == 1
        assert session.query(AnalysisReport).count() == 1
        assert session.query(DimensionScore).count() == 2
        assert session.query(Finding).count() == 1
        assert session.query(Insight).count() == 1
        assert len(get_repository_reports(session, "owner", "project")) == 1
        assert len(list_recent_reports(session)) == 1

    assert api_client.get("/api/v1/reports?limit=5").json()[0]["report_id"] == "report-123"
    assert api_client.get("/api/v1/repositories/owner/project").json()["report_id"] == "report-123"
    assert api_client.get("/api/v1/repositories/owner/project/reports").status_code == 200
    assert (
        api_client.get("/api/v1/repositories/owner/project/findings").json()[0]["code"] == "DC001"
    )
    assert (
        api_client.get("/api/v1/repositories/owner/project/insights").json()[0]["priority_score"]
        == 50
    )


def test_save_report_rolls_back_all_rows_on_database_failure(sqlite_sessions, monkeypatch):
    from sqlalchemy.orm import Session

    original_commit = Session.commit

    def failing_commit(self):
        raise RuntimeError("simulated commit failure")

    monkeypatch.setattr(Session, "commit", failing_commit)
    report = {
        "report_id": "failed-report",
        "status": "completed",
        "analyzed_at": "2026-11-23T12:00:00+00:00",
        "engine_version": "0.2.0-alpha",
        "health_score": 70,
        "coverage": 65,
        "classification": "Healthy",
        "repository": {
            "id": 456,
            "owner": "owner",
            "name": "project",
            "full_name": "owner/project",
            "url": "https://github.com/owner/project",
            "created_at": "2025-01-01T00:00:00+00:00",
        },
        "dimensions": {"maintenance": 70.0},
        "data_completeness": {"issues": True},
        "findings": [],
        "insights": [],
    }
    with sqlite_sessions() as session, pytest.raises(RuntimeError):
        save_report(session, report)

    monkeypatch.setattr(Session, "commit", original_commit)
    with sqlite_sessions() as session:
        assert session.query(Repository).count() == 0
        assert session.query(AnalysisReport).count() == 0


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
    issue_request = next(request for request in calls if request.url.path.endswith("/issues"))
    commit_request = next(request for request in calls if request.url.path.endswith("/commits"))
    assert issue_request.url.params["state"] == "open"
    assert "since" in commit_request.url.params
    assert "until" in commit_request.url.params


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


def test_open_issue_without_comments_produces_careful_finding():
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
    assert finding["title"] == "Open issue with no comments"
    assert finding["source_url"] == issue.html_url


def test_complete_commit_windows_report_activity_decline():
    now = datetime.now(UTC)
    repository = GitHubRepository(
        id=2,
        full_name="owner/project",
        name="project",
        html_url="https://github.com/owner/project",
        created_at=now - timedelta(days=500),
        updated_at=now,
        pushed_at=now - timedelta(days=10),
        stargazers_count=0,
        forks_count=0,
        watchers_count=0,
        open_issues_count=0,
        default_branch="main",
        owner={"login": "owner"},
    )
    commit_days = [10, 110, 120, 140, 170]
    commits = [
        GitHubCommit(
            sha=f"commit-{days}",
            html_url=f"https://github.com/owner/project/commit/{days}",
            commit={
                "author": {"date": (now - timedelta(days=days)).isoformat()},
                "committer": {"date": (now - timedelta(days=days)).isoformat()},
            },
            author={"login": "maintainer" if days != 110 else "contributor"},
        )
        for days in commit_days
    ]
    snapshot = RepositorySnapshot(
        repository=repository,
        issues=[],
        commits=commits,
        releases=[
            GitHubRelease(
                tag_name="v1",
                html_url="https://github.com/owner/project/releases/tag/v1",
                published_at=now - timedelta(days=30),
            )
        ],
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
    decline = next(item for item in report["findings"] if item["code"] == "SU001")
    assert report["activity"]["commits_last_30_days"] == 1
    assert report["activity"]["commits_last_90_days"] == 1
    assert report["activity"]["commits_previous_90_days"] == 4
    assert report["activity"]["commit_activity_change_percent"] == -75.0
    assert report["activity"]["active_commit_authors_last_90_days"] == 1
    assert decline["evidence"]["latest_90_days"] == 1


def test_stale_pull_request_detection_skips_drafts_and_waiting_labels():
    now = datetime.now(UTC)
    repository = GitHubRepository(
        id=3,
        full_name="owner/repo",
        name="repo",
        html_url="https://github.com/owner/repo",
        created_at=now - timedelta(days=100),
        updated_at=now,
        pushed_at=now,
        stargazers_count=0,
        forks_count=0,
        watchers_count=0,
        open_issues_count=0,
        default_branch="main",
        owner={"login": "owner"},
    )
    pull_requests = [
        GitHubIssue(
            number=number,
            html_url=f"https://github.com/owner/repo/pull/{number}",
            title="Old pull request",
            state="open",
            created_at=now - timedelta(days=90),
            updated_at=now - timedelta(days=80),
            pull_request={"url": "https://api.github.com/repos/owner/repo/pulls"},
            draft=draft,
            labels=[{"name": label}] if label else [],
        )
        for number, draft, label in [
            (1, True, None),
            (2, False, "blocked"),
            (3, False, "waiting-for-author"),
            (4, False, None),
        ]
    ]
    snapshot = RepositorySnapshot(
        repository=repository,
        issues=pull_requests,
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
    stale_findings = [item for item in report["findings"] if item["code"] == "PR002"]
    assert len(stale_findings) == 1
    assert stale_findings[0]["source_url"] == "https://github.com/owner/repo/pull/4"


def test_incomplete_repository_tree_does_not_score_or_emit_missing_file_findings():
    now = datetime.now(UTC)
    repository = GitHubRepository(
        id=4,
        full_name="owner/truncated",
        name="truncated",
        html_url="https://github.com/owner/truncated",
        created_at=now - timedelta(days=100),
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
        commits=[],
        releases=[],
        files=RepositoryFiles(
            readme=False,
            license=False,
            contributing=False,
            docs=False,
            tests=False,
            workflows=False,
            development_config=False,
        ),
        fetched_at=now,
        completeness={"issues": False, "commits": True, "releases": True, "repository_tree": False},
    )

    report = build_report(snapshot)

    assert report["dimensions"]["development"] is None
    assert report["dimensions"]["documentation"] is None
    assert report["activity"]["open_issues"] is None
    assert report["activity"]["open_pull_requests"] is None
    assert not {"DV001", "DV002", "DC001", "DC002"} & {
        finding["code"] for finding in report["findings"]
    }


def test_release_checks_use_latest_published_date_and_require_complete_pagination():
    now = datetime.now(UTC)
    repository = GitHubRepository(
        id=5,
        full_name="owner/releases",
        name="releases",
        html_url="https://github.com/owner/releases",
        created_at=now - timedelta(days=500),
        updated_at=now,
        pushed_at=now,
        stargazers_count=0,
        forks_count=0,
        watchers_count=0,
        open_issues_count=0,
        default_branch="main",
        owner={"login": "owner"},
    )
    releases = [
        GitHubRelease(
            tag_name="old",
            html_url="https://github.com/owner/releases/releases/tag/old",
            published_at=now - timedelta(days=400),
        ),
        GitHubRelease(
            tag_name="recent",
            html_url="https://github.com/owner/releases/releases/tag/recent",
            published_at=now - timedelta(days=20),
        ),
    ]
    snapshot = RepositorySnapshot(
        repository=repository,
        issues=[],
        commits=[],
        releases=releases,
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
    assert not any(finding["code"] == "SU002" for finding in report["findings"])

    snapshot.completeness["releases"] = False
    snapshot.releases = [releases[0]]
    incomplete_report = build_report(snapshot)
    assert not any(finding["code"] == "SU002" for finding in incomplete_report["findings"])
