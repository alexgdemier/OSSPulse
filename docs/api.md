# API v1

Base path: `/api/v1`. Analysis, report retrieval, repository history, findings, and insights are available.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/ready` | Database readiness check |
| POST | `/analyze` | Analyze a GitHub repository URL |
| GET | `/reports/{report_id}` | Retrieve a stored report |
| GET | `/reports?limit=20` | List recent reports |
| GET | `/repositories/{owner}/{repo}` | Retrieve the latest repository report |
| GET | `/repositories/{owner}/{repo}/reports` | List repository report history |
| GET | `/repositories/{owner}/{repo}/findings` | Findings from the latest report |
| GET | `/repositories/{owner}/{repo}/insights` | Recommendations from the latest report |

`POST /analyze` accepts `{ "repository_url": "https://github.com/owner/repo" }` and returns the complete JSON report. It does not require authentication for public repositories. Reports are persisted in PostgreSQL and can be retrieved by ID after service restarts. If coverage is below 50%, classification is `Insufficient Data`.

`health_score` remains the weighted value of evaluable dimensions for API consumers, even below 50% coverage. In that case it is diagnostic only: the web report and report history hide the total and show `Insufficient Data` so a partial score is not mistaken for a reliable rating.

Repeated analyses of the same repository and engine version reuse a report for six hours by default and return `X-OSS-Pulse-Cache: HIT`; a fresh analysis returns `MISS`. Hosted requests are limited to two per minute and ten per hour per visitor. A shared limit defaults to five analyses per hour without a GitHub token and 100 with one. These limits are configurable. A rejected request returns `429` with a `Retry-After` header. Caching is checked before the request limit, so cache hits do not consume analysis quota.

Reports older than 90 days are deleted in bounded batches during analysis requests. Each repository retains at most ten recent report snapshots by default. Both retention settings are configurable. The web app transfers the visitor IP to the API with a signed server-to-server header; only an HMAC of the address is stored in rate-limit buckets.

Reports include an experimental `activity` sample for repository-associated replies to open issues. OSS Pulse checks up to five of the oldest retrieved open issues by default, using one public GitHub issue-comments request for each sampled issue with comments. `repository_associated_response_sample_size` counts sampled issues whose response evidence could be classified; `repository_associated_responses` counts those with an associated reply; `median_days_to_repository_associated_response` is null when no associated reply was observed; `repository_associated_response_sampled` is the attempted sample size; and `repository_associated_response_evidence_complete` indicates whether the fetched open-issue set was covered. A comment author labeled `OWNER`, `MEMBER`, or `COLLABORATOR` is treated as repository-associated evidence, not a verified maintainer identity. Sample completeness is also reported under `data_completeness.issue_response_sample`. These fields do not affect the Health Score. Set `GITHUB_ISSUE_RESPONSE_SAMPLE_SIZE` from 0 to 20 to change the request cap.

`GET /health` checks that the API process responds. `GET /ready` also runs a database query and returns `503` if report storage is unavailable; use readiness for traffic routing.

Reports include an ID, status, repository, score, coverage, classification, UTC timestamp, dimension scores, findings, recommendations, and scoring methodology version. Activity context includes open issue and pull request counts, stale pull request counts, open issues with no comments, and commit counts for the last 30 days, the last 90 days, and the preceding 90-day period. Complete commit histories also include twelve `commit_activity_last_180_days` periods of 15 days each for charting; this field is `null` when commit pagination is incomplete. The report also includes the percentage change between complete 90-day windows and the number of distinct GitHub-attributed commit authors in the latest 90-day window. Other commit-derived activity values are `null` when commit pagination is incomplete; issue and pull request counts are `null` when issue pagination is incomplete. Attributed author counts do not represent verified community membership. The `limit` query parameter accepts values from 1 to 100. The API contract is available through OpenAPI at `/docs`.

Expected errors: `400` invalid URL, `404` missing or inaccessible repository/report, `422` unsupported repository, `429` analysis or GitHub rate limit, `502` GitHub API failure, and `503` temporary service outage. Analysis-limit responses include a `Retry-After` header. Raw GitHub response bodies are not exposed to clients.
