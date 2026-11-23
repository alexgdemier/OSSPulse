"""Persistent abuse controls, report caching, and bounded data retention."""

import hashlib
import hmac
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.analyzers.scoring import ENGINE_VERSION
from app.core.config import settings
from app.database.models import AnalysisRateLimit, AnalysisReport, Repository


def get_cached_report(
    session: Session, owner: str, repository: str, *, now: datetime
) -> dict | None:
    if settings.analysis_cache_ttl_seconds == 0:
        return None

    statement = (
        select(AnalysisReport.report_data)
        .join(Repository)
        .where(
            func.lower(Repository.owner) == owner.casefold(),
            func.lower(Repository.name) == repository.casefold(),
            AnalysisReport.engine_version == ENGINE_VERSION,
            AnalysisReport.analyzed_at
            >= now - timedelta(seconds=settings.analysis_cache_ttl_seconds),
        )
        .order_by(AnalysisReport.analyzed_at.desc())
        .limit(1)
    )
    return session.scalar(statement)


def _window_start(now: datetime, seconds: int) -> datetime:
    timestamp = int(now.timestamp())
    return datetime.fromtimestamp(timestamp - timestamp % seconds, UTC)


def _consume_bucket(session: Session, *, key: str, now: datetime, seconds: int, limit: int) -> bool:
    table = AnalysisRateLimit.__table__
    dialect = session.get_bind().dialect.name
    insert = postgresql_insert if dialect == "postgresql" else sqlite_insert
    statement = insert(table).values(
        bucket_key=key,
        window_start=_window_start(now, seconds),
        request_count=1,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[table.c.bucket_key, table.c.window_start],
        set_={"request_count": table.c.request_count + 1},
        where=table.c.request_count < limit,
    ).returning(table.c.request_count)
    return session.execute(statement).scalar_one_or_none() is not None


def consume_analysis_quota(session: Session, *, client_ip: str, now: datetime) -> int | None:
    """Consume per-client and global fixed-window quotas; return retry seconds when blocked."""
    hmac_key = (settings.analysis_proxy_secret or settings.database_url).encode()
    client_key = hmac.new(hmac_key, client_ip.encode(), hashlib.sha256).hexdigest()
    global_limit = settings.analysis_rate_limit_global_per_hour
    if global_limit is None:
        global_limit = 100 if settings.github_token else 5

    buckets = [
        (f"client:{client_key}:minute", 60, settings.analysis_rate_limit_per_minute),
        (f"client:{client_key}:hour", 3600, settings.analysis_rate_limit_per_hour),
        ("global:hour", 3600, global_limit),
    ]
    for key, seconds, limit in buckets:
        window_start = _window_start(now, seconds)
        if not _consume_bucket(session, key=key, now=now, seconds=seconds, limit=limit):
            session.rollback()
            return max(1, int((window_start + timedelta(seconds=seconds) - now).total_seconds()))

    session.commit()
    return None


def purge_expired_data(session: Session, *, now: datetime) -> tuple[int, int]:
    """Prune old report trees and unused repository rows in bounded batches."""
    report_cutoff = now - timedelta(days=settings.report_retention_days)
    expired_reports = session.scalars(
        select(AnalysisReport)
        .where(AnalysisReport.analyzed_at < report_cutoff)
        .order_by(AnalysisReport.analyzed_at)
        .limit(50)
    ).all()
    for report in expired_reports:
        session.delete(report)

    session.flush()
    reports_exist = (
        select(AnalysisReport.id).where(AnalysisReport.repository_id == Repository.id).exists()
    )
    orphan_repositories = session.scalars(select(Repository).where(~reports_exist).limit(50)).all()
    for repository in orphan_repositories:
        session.delete(repository)

    session.execute(
        delete(AnalysisRateLimit).where(AnalysisRateLimit.window_start < now - timedelta(days=2))
    )
    return len(expired_reports), len(orphan_repositories)


def trim_repository_history(session: Session, *, repository_id: int) -> int:
    reports_to_remove = session.scalars(
        select(AnalysisReport)
        .where(AnalysisReport.repository_id == repository_id)
        .order_by(AnalysisReport.analyzed_at.desc())
        .offset(settings.report_max_history_per_repository)
        .limit(50)
    ).all()
    for report in reports_to_remove:
        session.delete(report)
    return len(reports_to_remove)
