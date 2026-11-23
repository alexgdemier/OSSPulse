from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class GitHubRepository(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    full_name: str
    name: str
    html_url: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime | None = None
    stargazers_count: int
    forks_count: int
    watchers_count: int
    open_issues_count: int
    language: str | None = None
    default_branch: str
    archived: bool = False
    fork: bool = False
    topics: list[str] = []
    owner: dict[str, Any]


class GitHubIssue(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: int
    html_url: str
    title: str
    state: str
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None
    comments: int = 0
    draft: bool = False
    pull_request: dict[str, Any] | None = None
    user: dict[str, Any] | None = None
    labels: list[dict[str, Any]] = []

    @property
    def is_pull_request(self) -> bool:
        return self.pull_request is not None


class GitHubCommit(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sha: str
    html_url: str
    commit: dict[str, Any]
    author: dict[str, Any] | None = None

    @property
    def committed_at(self) -> datetime | None:
        committer = self.commit.get("committer") or {}
        author = self.commit.get("author") or {}
        value = committer.get("date") or author.get("date")
        return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None

    @property
    def author_login(self) -> str | None:
        return self.author.get("login") if self.author else None


class GitHubRelease(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tag_name: str
    html_url: str
    published_at: datetime | None = None
    draft: bool = False
    prerelease: bool = False


class RepositoryFiles(BaseModel):
    readme: bool
    license: bool
    contributing: bool
    docs: bool
    tests: bool
    workflows: bool
    development_config: bool


class RepositorySnapshot(BaseModel):
    repository: GitHubRepository
    issues: list[GitHubIssue]
    commits: list[GitHubCommit]
    releases: list[GitHubRelease]
    files: RepositoryFiles
    fetched_at: datetime
    completeness: dict[str, bool]
