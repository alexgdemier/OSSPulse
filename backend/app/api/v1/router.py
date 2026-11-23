from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from httpx import HTTPError
from pydantic import BaseModel, HttpUrl

from app.analyzers.scoring import build_report
from app.integrations.github import GitHubAPIError, GitHubClient

router = APIRouter()
_REPORTS: dict[str, dict] = {}


class AnalyzeRequest(BaseModel):
    repository_url: HttpUrl


@router.get("/health", tags=["service"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze", tags=["analysis"])
def analyze(request: AnalyzeRequest) -> dict:
    parsed = urlparse(str(request.repository_url))
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.scheme != "https" or parsed.netloc != "github.com" or len(parts) != 2:
        raise HTTPException(status_code=400, detail="Expected a GitHub repository URL")
    owner, repository = parts
    if repository.endswith(".git"):
        repository = repository[:-4]
    try:
        report = build_report(GitHubClient().analyze(owner, repository))
        _REPORTS[report["report_id"]] = report
        return report
    except GitHubAPIError as exc:
        if exc.status_code == 404:
            raise HTTPException(
                status_code=404, detail="Repository not found or inaccessible"
            ) from exc
        if exc.status_code in (403, 429):
            raise HTTPException(status_code=429, detail="GitHub API rate limit reached") from exc
        if exc.status_code >= 500:
            raise HTTPException(
                status_code=502, detail="GitHub is temporarily unavailable"
            ) from exc
        raise HTTPException(status_code=502, detail="GitHub API request failed") from exc
    except HTTPError as exc:
        raise HTTPException(status_code=502, detail="Could not connect to GitHub") from exc


@router.get("/reports/{report_id}", tags=["reports"])
def get_report(report_id: str) -> dict:
    report = _REPORTS.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found or expired")
    return report
