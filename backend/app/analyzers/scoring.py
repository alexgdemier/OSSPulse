from datetime import timedelta
from statistics import median
from typing import Any
from uuid import uuid4

from app.schemas.github import RepositorySnapshot

DIMENSION_WEIGHTS = {
    "maintenance": 30,
    "community": 25,
    "development": 20,
    "documentation": 15,
    "sustainability": 10,
}
ENGINE_VERSION = "0.1.0-alpha"


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


def build_report(snapshot: RepositorySnapshot) -> dict[str, Any]:
    now = snapshot.fetched_at
    issues = [item for item in snapshot.issues if not item.is_pull_request]
    prs = [item for item in snapshot.issues if item.is_pull_request]
    open_issues = [item for item in issues if item.state == "open"]
    open_prs = [item for item in prs if item.state == "open" and not item.draft]
    stale_prs = [item for item in open_prs if (now - item.updated_at).days >= 30]
    very_stale_prs = [item for item in open_prs if (now - item.updated_at).days >= 60]
    unanswered = [item for item in open_issues if item.comments == 0]
    unanswered_14 = [item for item in unanswered if (now - item.created_at).days >= 14]
    unanswered_30 = [item for item in unanswered if (now - item.created_at).days >= 30]

    maintainers = {
        snapshot.repository.owner.get("login", "").casefold(),
        *(snapshot.repository.owner.get("collaborators", []) or []),
    }
    external_prs = [
        item for item in prs if (item.user or {}).get("login", "").casefold() not in maintainers
    ]
    timestamps = [item.authored_at for item in snapshot.commits if item.authored_at]
    timestamps += [item.updated_at for item in snapshot.issues]
    recent_90 = [stamp for stamp in timestamps if now - timedelta(days=90) <= stamp <= now]
    previous_90 = [
        stamp
        for stamp in timestamps
        if now - timedelta(days=180) <= stamp < now - timedelta(days=90)
    ]

    dimensions: dict[str, float | None] = {
        "maintenance": None,
        "community": None,
        "development": None,
        "documentation": None,
        "sustainability": None,
    }
    median_pr_age = (
        median([(now - pr.updated_at).total_seconds() / 86400 for pr in open_prs])
        if open_prs
        else 0
    )
    push_age = (
        (now - snapshot.repository.pushed_at).total_seconds() / 86400
        if snapshot.repository.pushed_at
        else 181
    )
    maintenance_score = (
        0.45 * _score_age(median_pr_age, 7, 60)
        + 0.25 * (100 * (1 - len(unanswered_30) / max(1, len(open_issues))))
        + 0.30 * _score_age(push_age, 14, 180)
    )
    dimensions["maintenance"] = (
        round(maintenance_score, 1) if snapshot.completeness["issues"] else None
    )
    dimensions["community"] = (
        round(
            0.5 * min(100, len({p.user.get("login") for p in external_prs if p.user}) * 20)
            + 0.5 * (100 * len(external_prs) / len(prs)),
            1,
        )
        if snapshot.completeness["issues"] and prs
        else None
    )

    dev_checks = [snapshot.files.workflows, snapshot.files.tests, snapshot.files.development_config]
    dimensions["development"] = round(100 * sum(dev_checks) / len(dev_checks), 1)
    doc_checks = [
        snapshot.files.readme,
        snapshot.files.license,
        snapshot.files.contributing,
        snapshot.files.docs,
    ]
    doc_weights = [30, 25, 25, 20]
    dimensions["documentation"] = round(
        sum(weight for present, weight in zip(doc_checks, doc_weights) if present), 1
    )
    if snapshot.completeness["commits"]:
        activity = (
            100
            if recent_90 and not previous_90
            else (
                max(0.0, min(100.0, 100 * len(recent_90) / len(previous_90)))
                if previous_90
                else None
            )
        )
        release_score = (
            _score_age(
                (now - snapshot.releases[0].published_at).total_seconds() / 86400,
                180,
                730,
            )
            if snapshot.releases and snapshot.releases[0].published_at
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
    for issue in unanswered_30:
        add(
            "IS002",
            "maintenance",
            "Long unanswered issue",
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
    for issue in unanswered_14:
        if issue not in unanswered_30:
            add(
                "IS001",
                "maintenance",
                "Unanswered issue",
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
    if not snapshot.files.workflows:
        add(
            "DV001",
            "development",
            "No CI workflow detected",
            "No GitHub Actions workflow was found in the default branch.",
            "medium",
            {"checked": ".github/workflows/"},
            "Add a CI workflow for the project's supported environments.",
        )
    if not snapshot.files.tests:
        add(
            "DV002",
            "development",
            "No tests detected",
            "No common test directory or test workflow was found.",
            "medium",
            {"checked": ["tests/", "test/", "spec/", ".github/workflows/"]},
            "Add automated tests for key behavior and run them in CI.",
        )
    if not snapshot.files.contributing:
        add(
            "DC001",
            "documentation",
            "Contributor guide missing",
            "No CONTRIBUTING guide was found at the repository root.",
            "low",
            {"checked": "CONTRIBUTING*"},
            "Document how contributors can set up, test, and submit changes.",
        )
    if not snapshot.files.license:
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
        snapshot.releases
        and snapshot.releases[0].published_at
        and (now - snapshot.releases[0].published_at).days >= 365
    ):
        release_age = (now - snapshot.releases[0].published_at).days
        add(
            "SU002",
            "sustainability",
            "No recent release",
            f"The latest published release is {release_age} days old.",
            "informational",
            {
                "tag": snapshot.releases[0].tag_name,
                "published_at": snapshot.releases[0].published_at.isoformat(),
            },
            "Review release cadence in the context of the project's scope and stability.",
            snapshot.releases[0].html_url,
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
            "open_issues": len(open_issues),
            "open_pull_requests": len(open_prs),
            "stale_pull_requests": len(stale_prs),
            "unanswered_issues": len(unanswered),
        },
        "repository_files": snapshot.files.model_dump(),
        "findings": findings,
        "insights": insights,
    }
