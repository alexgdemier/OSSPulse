# API v1

Base path: `/api/v1`. Analysis, report retrieval, repository history, findings, and insights are available.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Service health check |
| POST | `/analyze` | Analyze a GitHub repository URL |
| GET | `/reports/{report_id}` | Retrieve a stored report |
| GET | `/reports?limit=20` | List recent reports |
| GET | `/repositories/{owner}/{repo}` | Retrieve the latest repository report |
| GET | `/repositories/{owner}/{repo}/reports` | List repository report history |
| GET | `/repositories/{owner}/{repo}/findings` | Findings from the latest report |
| GET | `/repositories/{owner}/{repo}/insights` | Recommendations from the latest report |

`POST /analyze` accepts `{ "repository_url": "https://github.com/owner/repo" }` and returns the complete JSON report. It does not require authentication for public repositories. Reports are persisted in PostgreSQL and can be retrieved by ID after service restarts. If coverage is below 50%, classification is `Insufficient Data`.

Reports include an ID, status, repository, score, coverage, classification, UTC timestamp, dimension scores, findings, recommendations, and scoring methodology version. The `limit` query parameter accepts values from 1 to 100. The API contract is available through OpenAPI at `/docs`.

Expected errors: `400` invalid URL, `404` missing or inaccessible repository/report, `422` unsupported repository, `429` GitHub rate limit, `502` GitHub API failure, and `503` temporary service outage. Raw GitHub response bodies are not exposed to clients.
