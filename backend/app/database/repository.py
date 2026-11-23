from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.analyzers.scoring import DIMENSION_WEIGHTS
from app.database.models import AnalysisReport, DimensionScore, Finding, Insight, Repository


def save_report(session: Session, data: dict) -> None:
    try:
        _save_report(session, data)
        session.commit()
    except Exception:
        session.rollback()
        raise


def _save_report(session: Session, data: dict) -> None:
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


def get_report(session: Session, report_id: str) -> dict | None:
    report = session.get(AnalysisReport, report_id)
    return report.report_data if report else None


def get_repository_reports(
    session: Session, owner: str, name: str, *, limit: int = 20
) -> list[dict]:
    statement = (
        select(AnalysisReport.report_data)
        .join(Repository)
        .where(Repository.owner.ilike(owner), Repository.name.ilike(name))
        .order_by(desc(AnalysisReport.analyzed_at))
        .limit(limit)
    )
    return list(session.scalars(statement))


def list_recent_reports(session: Session, *, limit: int = 20) -> list[dict]:
    statement = (
        select(AnalysisReport.report_data).order_by(desc(AnalysisReport.analyzed_at)).limit(limit)
    )
    return list(session.scalars(statement))
