import hmac
import ipaddress
import logging
from datetime import UTC, datetime
from hashlib import sha256
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from httpx import HTTPError
from pydantic import BaseModel, HttpUrl
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.analyzers.scoring import build_report
from app.core.config import settings
from app.database import get_db
from app.database.analysis_protection import (
    consume_analysis_quota,
    get_cached_report,
    purge_expired_data,
)
from app.database.repository import (
    get_report as load_report,
)
from app.database.repository import (
    get_repository_reports,
    list_recent_reports,
    save_report,
)
from app.integrations.github import GitHubAPIError, GitHubClient

router = APIRouter()
logger = logging.getLogger(__name__)


class AnalyzeRequest(BaseModel):
    repository_url: HttpUrl


def _client_address(request: Request) -> str:
    proxy_ip = request.headers.get("x-oss-pulse-client-ip")
    proxy_signature = request.headers.get("x-oss-pulse-client-signature")
    if proxy_ip and proxy_signature and settings.analysis_proxy_secret:
        expected = hmac.new(
            settings.analysis_proxy_secret.encode(), proxy_ip.encode(), sha256
        ).hexdigest()
        if hmac.compare_digest(proxy_signature, expected):
            try:
                return ipaddress.ip_address(proxy_ip).compressed
            except ValueError:
                pass

    if settings.analysis_trust_forwarded_for:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            candidate = forwarded_for.split(",", 1)[0].strip()
            try:
                return ipaddress.ip_address(candidate).compressed
            except ValueError:
                pass

    return request.client.host if request.client else "unknown"


def _load_repository_history(
    session: Session, owner: str, repository: str, *, limit: int = 20
) -> list[dict]:
    try:
        return get_repository_reports(session, owner, repository, limit=limit)
    except SQLAlchemyError as exc:
        logger.warning("Repository history lookup failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=503, detail="Report storage is temporarily unavailable"
        ) from exc


@router.get("/health", tags=["service"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", tags=["service"])
def ready(session: Session = Depends(get_db)) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("Database readiness check failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    return {"status": "ready"}


@router.post("/analyze", tags=["analysis"])
def analyze(
    request: AnalyzeRequest,
    http_request: Request,
    response: Response,
    session: Session = Depends(get_db),
) -> dict:
    parsed = urlparse(str(request.repository_url))
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.scheme != "https" or parsed.netloc != "github.com" or len(parts) != 2:
        raise HTTPException(status_code=400, detail="Expected a GitHub repository URL")
    owner, repository = parts
    if repository.endswith(".git"):
        repository = repository[:-4]
    now = datetime.now(UTC)
    try:
        cached_report = get_cached_report(session, owner, repository, now=now)
        if cached_report is not None:
            response.headers["X-OSS-Pulse-Cache"] = "HIT"
            return cached_report

        if settings.analysis_rate_limit_enabled:
            retry_after = consume_analysis_quota(
                session, client_ip=_client_address(http_request), now=now
            )
            if retry_after is not None:
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "Analysis limit reached. Please wait before analyzing another repository."
                    ),
                    headers={"Retry-After": str(retry_after)},
                )

        purge_expired_data(session, now=now)
        session.commit()

        report = build_report(GitHubClient().analyze(owner, repository))
        save_report(session, report)
        response.headers["X-OSS-Pulse-Cache"] = "MISS"
        return report
    except HTTPException:
        raise
    except GitHubAPIError as exc:
        if exc.status_code == 404:
            raise HTTPException(
                status_code=404, detail="Repository not found or inaccessible"
            ) from exc
        if exc.is_rate_limit:
            raise HTTPException(
                status_code=429,
                detail="GitHub API rate limit reached",
                headers={"Retry-After": str(exc.retry_after_seconds or 60)},
            ) from exc
        if exc.status_code >= 500:
            raise HTTPException(
                status_code=502, detail="GitHub is temporarily unavailable"
            ) from exc
        raise HTTPException(status_code=502, detail="GitHub API request failed") from exc
    except HTTPError as exc:
        raise HTTPException(status_code=502, detail="Could not connect to GitHub") from exc
    except SQLAlchemyError as exc:
        logger.warning("Report analysis storage failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=503, detail="Report storage is temporarily unavailable"
        ) from exc


@router.get("/reports", tags=["reports"])
def list_reports(
    limit: int = Query(default=20, ge=1, le=100), session: Session = Depends(get_db)
) -> list[dict]:
    try:
        return list_recent_reports(session, limit=limit)
    except SQLAlchemyError as exc:
        logger.warning("Recent report lookup failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=503, detail="Report storage is temporarily unavailable"
        ) from exc


@router.get("/repositories/{owner}/{repository}", tags=["repositories"])
def latest_repository_report(
    owner: str, repository: str, session: Session = Depends(get_db)
) -> dict:
    reports = _load_repository_history(session, owner, repository)
    if not reports:
        raise HTTPException(status_code=404, detail="No report exists for this repository")
    return reports[0]


@router.get("/repositories/{owner}/{repository}/reports", tags=["reports"])
def repository_report_history(
    owner: str,
    repository: str,
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db),
) -> list[dict]:
    return _load_repository_history(session, owner, repository, limit=limit)


@router.get("/repositories/{owner}/{repository}/findings", tags=["findings"])
def repository_findings(
    owner: str, repository: str, session: Session = Depends(get_db)
) -> list[dict]:
    reports = _load_repository_history(session, owner, repository)
    if not reports:
        raise HTTPException(status_code=404, detail="No report exists for this repository")
    return reports[0]["findings"]


@router.get("/repositories/{owner}/{repository}/insights", tags=["insights"])
def repository_insights(
    owner: str, repository: str, session: Session = Depends(get_db)
) -> list[dict]:
    reports = _load_repository_history(session, owner, repository)
    if not reports:
        raise HTTPException(status_code=404, detail="No report exists for this repository")
    return reports[0]["insights"]


@router.get("/reports/{report_id}", tags=["reports"])
def get_report(report_id: str, session: Session = Depends(get_db)) -> dict:
    try:
        report = load_report(session, report_id)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503, detail="Report storage is temporarily unavailable"
        ) from exc
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
