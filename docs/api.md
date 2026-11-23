# API v1

Base path: `/api/v1`. Analysis and report retrieval are available; repository-level history endpoints are planned for a later release.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Service health check |
| POST | `/analyze` | Analyze a GitHub repository URL |
| GET | `/reports/{report_id}` | Retrieve a stored report |
| GET | `/repositories/{owner}/{repo}` | Latest report (planned) |
| GET | `/repositories/{owner}/{repo}/findings` | Findings (planned) |
| GET | `/repositories/{owner}/{repo}/insights` | Recommendations (planned) |

`POST /analyze` accepts `{ "repository_url": "https://github.com/owner/repo" }` and returns the complete JSON report. It does not require authentication for public repositories. Reports are persisted in PostgreSQL and can be retrieved by ID after service restarts. If coverage is below 50%, classification is `Insufficient Data`.

Reports include an ID, status, repository, score, coverage, classification, UTC timestamp, dimension scores, findings, recommendations, and scoring methodology version. The API contract is available through OpenAPI at `/docs`.

Expected errors: `400` invalid URL, `404` missing or inaccessible repository/report, `422` unsupported repository, `429` GitHub rate limit, `502` GitHub API failure, and `503` temporary service outage. Raw GitHub response bodies are not exposed to clients.
