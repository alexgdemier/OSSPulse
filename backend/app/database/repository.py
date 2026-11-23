from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.analyzers.scoring import DIMENSION_WEIGHTS
from app.core.config import settings
from app.database.analysis_protection import trim_repository_history
from app.database.models import AnalysisReport, DimensionScore, Finding, Insight, Repository


def save_report(session: Session, data: dict) -> None:
    try:
        repository_id = _save_report(session, data)
        trim_repository_history(session, repository_id=repository_id)
        session.commit()
    except Exception:
        session.rollback()
        raise


def _save_report(session: Session, data: dict) -> int:
    repository_data = data["repository"]
    repository = session.scalar(
        select(Repository).where(Repository.github_id == repository_data["id"])
    )
    if repository is None:
        repository = Repository(
            github_id=repository_data["id"],
            owner=repository_data["owner"],
            name=repository_data["name"],
            full_name=repository_data["full_name"],
            url=repository_data["url"],
            github_created_at=datetime.fromisoformat(repository_data["created_at"]),
        )
        session.add(repository)
        session.flush()
    else:
        repository.owner = repository_data["owner"]
        repository.name = repository_data["name"]
        repository.full_name = repository_data["full_name"]
        repository.url = repository_data["url"]

    report = AnalysisReport(
        id=data["report_id"],
        repository_id=repository.id,
        analyzed_at=datetime.fromisoformat(data["analyzed_at"]),
        health_score=data["health_score"],
        coverage=data["coverage"],
        classification=data["classification"],
        engine_version=data["engine_version"],
        status=data["status"],
        dimensions=data["dimensions"],
        data_completeness=data["data_completeness"],
        report_data=data,
    )
    session.add(report)
    for name, score in data["dimensions"].items():
        session.add(
            DimensionScore(
                report_id=report.id,
                dimension=name,
                score=score,
                weight=DIMENSION_WEIGHTS[name],
            )
        )

    finding_rows = []
    for item in data["findings"]:
        finding = Finding(
            report_id=report.id,
            code=item["code"],
            category=item["category"],
            title=item["title"],
            description=item["description"],
            severity=item["severity"],
            evidence=item["evidence"],
            recommendation=item["recommendation"],
            source_url=item["source_url"],
            detected_at=datetime.fromisoformat(item["detected_at"]),
        )
        report.findings.append(finding)
        finding_rows.append((finding, item))

    session.flush()
    for finding, item in finding_rows:
        insight = next(
            (
                candidate
                for candidate in data["insights"]
                if candidate["code"] == item["code"]
                and candidate["source_url"] == item["source_url"]
                and candidate["title"] == item["title"]
            ),
            None,
        )
        if insight:
            session.add(Insight(finding_id=finding.id, priority_score=insight["priority_score"]))

    return repository.id


def get_report(session: Session, report_id: str) -> dict | None:
    cutoff = datetime.now(UTC) - timedelta(days=settings.report_retention_days)
    statement = select(AnalysisReport.report_data).where(
        AnalysisReport.id == report_id,
        AnalysisReport.analyzed_at >= cutoff,
    )
    return session.scalar(statement)


def get_repository_reports(
    session: Session, owner: str, name: str, *, limit: int = 20
) -> list[dict]:
    cutoff = datetime.now(UTC) - timedelta(days=settings.report_retention_days)
    statement = (
        select(AnalysisReport.report_data)
        .join(Repository)
        .where(
            Repository.owner.ilike(owner),
            Repository.name.ilike(name),
            AnalysisReport.analyzed_at >= cutoff,
        )
        .order_by(desc(AnalysisReport.analyzed_at))
        .limit(limit)
    )
    return list(session.scalars(statement))


def list_recent_reports(session: Session, *, limit: int = 20) -> list[dict]:
    statement = (
        select(AnalysisReport.report_data)
        .where(
            AnalysisReport.analyzed_at
            >= datetime.now(UTC) - timedelta(days=settings.report_retention_days)
        )
        .order_by(desc(AnalysisReport.analyzed_at))
        .limit(limit)
    )
    return list(session.scalars(statement))
