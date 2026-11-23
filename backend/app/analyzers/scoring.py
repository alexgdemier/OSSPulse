from datetime import timedelta
from statistics import median
from typing import Any
from uuid import uuid4

from app.schemas.github import GitHubIssue, RepositorySnapshot

DIMENSION_WEIGHTS = {
    "maintenance": 30,
    "community": 25,
    "development": 20,
    "documentation": 15,
    "sustainability": 10,
}
ENGINE_VERSION = "0.2.0-alpha"

WAITING_OR_BLOCKED_LABELS = {
    "blocked",
    "waiting for author",
    "waiting on author",
    "awaiting author",
    "needs author",
    "waiting for maintainer",
    "waiting on maintainer",
    "awaiting maintainer",
    "needs maintainer",
}


def _score_age(days: float, good: float, bad: float) -> float:
    return max(0.0, min(100.0, 100 * (bad - days) / (bad - good)))


def _classify(score: int) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Healthy"
    if score >= 50:
        return "Needs Attention"
    if score >= 30:
        return "At Risk"
    return "Critical"


def _is_waiting_or_blocked(pr: GitHubIssue) -> bool:
    labels = {
        str(label.get("name", "")).casefold().replace("-", " ").replace("_", " ").strip()
        for label in pr.labels
    }
    return bool(labels & WAITING_OR_BLOCKED_LABELS) or any(
        label.startswith(("waiting for ", "waiting on ", "awaiting ", "needs ")) for label in labels
    )


def build_report(snapshot: RepositorySnapshot) -> dict[str, Any]:
    now = snapshot.fetched_at
    issues = [item for item in snapshot.issues if not item.is_pull_request]
    prs = [item for item in snapshot.issues if item.is_pull_request]
    open_issues = [item for item in issues if item.state == "open"]
    open_prs = [item for item in prs if item.state == "open" and not item.draft]
    reviewable_prs = [item for item in open_prs if not _is_waiting_or_blocked(item)]
    stale_prs = [item for item in reviewable_prs if (now - item.updated_at).days >= 30]
    very_stale_prs = [item for item in reviewable_prs if (now - item.updated_at).days >= 60]
    issues_without_comments = [item for item in open_issues if item.comments == 0]
    issues_without_comments_14 = [
        item for item in issues_without_comments if (now - item.created_at).days >= 14
    ]
    issues_without_comments_30 = [
        item for item in issues_without_comments if (now - item.created_at).days >= 30
    ]

    commit_dates = [item.committed_at for item in snapshot.commits if item.committed_at]
    recent_30 = [stamp for stamp in commit_dates if now - timedelta(days=30) <= stamp <= now]
    recent_90 = [stamp for stamp in commit_dates if now - timedelta(days=90) <= stamp <= now]
    activity_periods = None
    if snapshot.completeness["commits"]:
        activity_window_start = now - timedelta(days=180)
        period_days = 15
        period_counts = [0] * 12
        for stamp in commit_dates:
            if activity_window_start <= stamp <= now:
                period_index = min(
                    int((stamp - activity_window_start).total_seconds() // (period_days * 86400)),
                    len(period_counts) - 1,
                )
                period_counts[period_index] += 1
        activity_periods = [
            {
                "period_start": (
                    activity_window_start + timedelta(days=period_days * index)
                ).isoformat(),
                "commits": count,
            }
            for index, count in enumerate(period_counts)
        ]
    previous_90 = [
        stamp
        for stamp in commit_dates
        if now - timedelta(days=180) <= stamp < now - timedelta(days=90)
    ]
    active_authors_90 = {
        item.author_login.casefold()
        for item in snapshot.commits
        if item.author_login
        and item.committed_at
        and now - timedelta(days=90) <= item.committed_at <= now
    }

    dimensions: dict[str, float | None] = {
        "maintenance": None,
        "community": None,
        "development": None,
        "documentation": None,
        "sustainability": None,
    }
    median_pr_age = (
        median([(now - pr.updated_at).total_seconds() / 86400 for pr in reviewable_prs])
        if reviewable_prs
        else 0
    )
    push_age = (
        (now - snapshot.repository.pushed_at).total_seconds() / 86400
        if snapshot.repository.pushed_at
        else 181
    )
    maintenance_score = (
        0.45 * _score_age(median_pr_age, 7, 60)
        + 0.25 * (100 * (1 - len(issues_without_comments_30) / max(1, len(open_issues))))
        + 0.30 * _score_age(push_age, 14, 180)
    )
    dimensions["maintenance"] = (
        round(maintenance_score, 1) if snapshot.completeness["issues"] else None
    )
    # Public PR and commit data cannot reliably distinguish maintainers from external contributors.
    dimensions["community"] = None

    dev_checks = [snapshot.files.workflows, snapshot.files.tests, snapshot.files.development_config]
    dimensions["development"] = (
        round(100 * sum(dev_checks) / len(dev_checks), 1)
        if snapshot.completeness["repository_tree"]
        else None
    )
    doc_checks = [
        snapshot.files.readme,
        snapshot.files.license,
        snapshot.files.contributing,
        snapshot.files.docs,
    ]
    doc_weights = [30, 25, 25, 20]
    dimensions["documentation"] = (
        round(sum(weight for present, weight in zip(doc_checks, doc_weights) if present), 1)
        if snapshot.completeness["repository_tree"]
        else None
    )
    dated_releases = [
        release
        for release in snapshot.releases
        if not release.draft and release.published_at is not None
    ]
    latest_release = max(dated_releases, key=lambda release: release.published_at, default=None)
    activity_trend = None
    if snapshot.completeness["commits"]:
        activity = (
            100.0
            if recent_90 and not previous_90
            else (
                max(0.0, min(100.0, 100 * len(recent_90) / len(previous_90)))
                if previous_90
                else None
            )
        )
        if previous_90:
            activity_trend = round(100 * (len(recent_90) - len(previous_90)) / len(previous_90), 1)
        release_score = (
            _score_age(
                (now - latest_release.published_at).total_seconds() / 86400,
                180,
                730,
            )
            if latest_release
            else None
        )
        dimensions["sustainability"] = (
            round(0.65 * activity + 0.35 * release_score, 1)
            if activity is not None
            and release_score is not None
            and snapshot.completeness["releases"]
            else None
        )

    evaluable = {
        name: score
        for name, score in dimensions.items()
        if score is not None
        and (name not in {"maintenance", "community"} or snapshot.completeness["issues"])
        and (
            name not in {"development", "documentation"} or snapshot.completeness["repository_tree"]
        )
    }
    total_weight = sum(DIMENSION_WEIGHTS[name] for name in evaluable)
    health_score = (
        round(
            sum(score * DIMENSION_WEIGHTS[name] for name, score in evaluable.items()) / total_weight
        )
        if total_weight
        else None
    )
    coverage = sum(DIMENSION_WEIGHTS[name] for name in evaluable)
    findings: list[dict[str, Any]] = []

    def add(
        code: str,
        category: str,
        title: str,
        description: str,
        severity: str,
        evidence: dict,
        recommendation: str,
        source_url: str | None = None,
    ) -> None:
        findings.append(
            {
                "code": code,
                "category": category,
                "title": title,
                "description": description,
                "severity": severity,
                "evidence": evidence,
                "recommendation": recommendation,
                "source_url": source_url,
                "detected_at": now.isoformat(),
            }
        )

    for pr in very_stale_prs:
        add(
            "PR002",
            "maintenance",
            "Very stale pull request",
            f"This pull request has had no activity for {(now - pr.updated_at).days} days.",
            "critical",
            {
                "number": pr.number,
                "updated_at": pr.updated_at.isoformat(),
                "days_inactive": (now - pr.updated_at).days,
            },
            "Review whether the pull request is still relevant and update its author.",
            pr.html_url,
        )
    for pr in stale_prs:
        if pr not in very_stale_prs:
            add(
                "PR001",
                "maintenance",
                "Stale pull request",
                f"This pull request has had no activity for {(now - pr.updated_at).days} days.",
                "high",
                {
                    "number": pr.number,
                    "updated_at": pr.updated_at.isoformat(),
                    "days_inactive": (now - pr.updated_at).days,
                },
                "Review the change and ask the author whether it is ready to proceed.",
                pr.html_url,
            )
    for issue in issues_without_comments_30:
        add(
            "IS002",
            "maintenance",
            "Open issue with no comments",
            f"No comments have been recorded for {(now - issue.created_at).days} days.",
            "high",
            {
                "number": issue.number,
                "created_at": issue.created_at.isoformat(),
                "days_open": (now - issue.created_at).days,
            },
            "Acknowledge the report or request the details needed to triage it.",
            issue.html_url,
        )
    for issue in issues_without_comments_14:
        if issue not in issues_without_comments_30:
            add(
                "IS001",
                "maintenance",
                "Open issue with no comments",
                f"No comments have been recorded for {(now - issue.created_at).days} days.",
                "medium",
                {
                    "number": issue.number,
                    "created_at": issue.created_at.isoformat(),
                    "days_open": (now - issue.created_at).days,
                },
                "Acknowledge the issue and clarify next steps.",
                issue.html_url,
            )
    if snapshot.completeness["repository_tree"] and not snapshot.files.workflows:
        add(
            "DV001",
            "development",
            "No CI workflow detected",
            "No GitHub Actions workflow was found in the default branch.",
            "medium",
            {"checked": ".github/workflows/"},
            "Add a CI workflow for the project's supported environments.",
        )
    if snapshot.completeness["repository_tree"] and not snapshot.files.tests:
        add(
            "DV002",
            "development",
            "No tests detected",
            "No common test directory or test workflow was found.",
            "medium",
            {"checked": ["tests/", "test/", "spec/", ".github/workflows/"]},
            "Add automated tests for key behavior and run them in CI.",
        )
    if snapshot.completeness["repository_tree"] and not snapshot.files.contributing:
        add(
            "DC001",
            "documentation",
            "Contributor guide missing",
            "No CONTRIBUTING guide was found at the repository root.",
            "low",
            {"checked": "CONTRIBUTING*"},
            "Document how contributors can set up, test, and submit changes.",
        )
    if snapshot.completeness["repository_tree"] and not snapshot.files.license:
        add(
            "DC002",
            "documentation",
            "License file missing",
            "No recognizable LICENSE or COPYING file was found at the repository root.",
            "high",
            {"checked": ["LICENSE*", "COPYING*"]},
            "Choose and publish a license so people can understand how they may use the project.",
        )
    if snapshot.repository.archived:
        add(
            "ST001",
            "sustainability",
            "Repository is archived",
            "GitHub marks this repository as archived.",
            "informational",
            {"archived": True},
            "If the project is still maintained, unarchive it and clarify its status.",
            snapshot.repository.html_url,
        )
    if (
        snapshot.completeness["commits"]
        and len(previous_90) >= 4
        and len(recent_90) * 2 <= len(previous_90)
    ):
        add(
            "SU001",
            "sustainability",
            "Commit activity has declined",
            "Fewer than half as many commits were observed in the latest 90-day window.",
            "medium",
            {
                "previous_90_days": len(previous_90),
                "latest_90_days": len(recent_90),
                "change_percent": activity_trend,
            },
            "Review recent project activity and consider communicating the maintenance plan.",
            snapshot.repository.html_url,
        )
    if (
        snapshot.completeness["releases"]
        and latest_release
        and (now - latest_release.published_at).days >= 365
    ):
        release_age = (now - latest_release.published_at).days
        add(
            "SU002",
            "sustainability",
            "No recent release",
            f"The latest published release is {release_age} days old.",
            "informational",
            {
                "tag": latest_release.tag_name,
                "published_at": latest_release.published_at.isoformat(),
            },
            "Review release cadence in the context of the project's scope and stability.",
            latest_release.html_url,
        )

    priorities = {"critical": 100, "high": 75, "medium": 50, "low": 25, "informational": 10}
    insights = [
        {
            **finding,
            "priority_score": round(0.5 * priorities[finding["severity"]] + 0.3 * 75 + 0.2 * 90),
        }
        for finding in findings
    ]
    insights.sort(key=lambda item: item["priority_score"], reverse=True)
    return {
        "report_id": str(uuid4()),
        "status": "completed",
        "repository": {
            "id": snapshot.repository.id,
            "full_name": snapshot.repository.full_name,
            "owner": snapshot.repository.owner.get("login"),
            "name": snapshot.repository.name,
            "url": snapshot.repository.html_url,
            "description": snapshot.repository.description,
            "created_at": snapshot.repository.created_at.isoformat(),
            "language": snapshot.repository.language,
            "stars": snapshot.repository.stargazers_count,
            "forks": snapshot.repository.forks_count,
            "watchers": snapshot.repository.watchers_count,
            "open_issues_count": snapshot.repository.open_issues_count,
            "archived": snapshot.repository.archived,
            "fork": snapshot.repository.fork,
        },
        "analyzed_at": now.isoformat(),
        "engine_version": ENGINE_VERSION,
        "health_score": health_score,
        "coverage": coverage,
        "classification": (
            _classify(health_score)
            if health_score is not None and coverage >= 50
            else "Insufficient Data"
        ),
        "dimensions": dimensions,
        "data_completeness": snapshot.completeness,
        "activity": {
            "commit_activity_last_180_days": activity_periods,
            "commits_last_30_days": len(recent_30) if snapshot.completeness["commits"] else None,
            "commits_last_90_days": len(recent_90) if snapshot.completeness["commits"] else None,
            "commits_previous_90_days": len(previous_90)
            if snapshot.completeness["commits"]
            else None,
            "commit_activity_change_percent": activity_trend,
            "active_commit_authors_last_90_days": (
                len(active_authors_90) if snapshot.completeness["commits"] else None
            ),
            "open_issues": len(open_issues) if snapshot.completeness["issues"] else None,
            "open_pull_requests": len(open_prs) if snapshot.completeness["issues"] else None,
            "stale_pull_requests": len(stale_prs) if snapshot.completeness["issues"] else None,
            "open_issues_with_no_comments": (
                len(issues_without_comments) if snapshot.completeness["issues"] else None
            ),
        },
        "repository_files": snapshot.files.model_dump(),
        "findings": findings,
        "insights": insights,
    }
