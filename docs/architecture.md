# Architecture

## Analysis flow

```text
GitHub URL → validator → GitHub client → normalized data → analyzers
           → scoring + findings → recommendations → JSON report / API → web app
                                                              ↘ PostgreSQL
```

The CLI and API share the same application core. The GitHub integration fetches a bounded snapshot; the scoring module builds the report and findings without network or storage access. The API persists the completed report and its normalized rows in PostgreSQL. The web app submits analysis through a POST route and renders stored reports by ID.

The API applies shared PostgreSQL-backed analysis quotas, caches recent reports by repository and scoring-engine version, and prunes expired reports in bounded batches. Client addresses are HMAC-hashed before rate-limit storage. The web service signs the client address when proxying a form submission to the API; direct Vercel API requests use Vercel's forwarded client-IP header. GitHub-associated issue reply evidence is collected for a small configurable sample. When that sample covers all open issues, its associated-reply share and response speed contribute to Community; otherwise that dimension is unevaluated. Association labels are only a proxy for project involvement, not a verified maintainer roster. Comment text and commenter identities are used only transiently; reports retain only aggregate response counts and median timing.

## Module boundaries

- `integrations/github`: GitHub requests, pagination, timeouts, and normalized provider errors.
- `schemas`: normalized models independent of raw GitHub responses.
- `analyzers/scoring.py`: deterministic findings, dimension scores, coverage, and report construction without API, storage, or UI dependencies.
- `database`: SQLAlchemy models, sessions, and persistence.
- `api/v1` and `cli`: adapters from the analysis core to HTTP and the terminal.
- `apps/web`: report presentation; scoring rules are not duplicated in the frontend.

## Decisions

The monorepo contains a Python package shared by the CLI and FastAPI. PostgreSQL runs locally through Docker Compose and schema changes use Alembic. Timestamps use UTC; each report records the scoring engine version. Unknown signals are not scored as zero. GitHub REST API is the first provider; a server-side token is optional, and visitor personal tokens are never requested. Repository content is never executed.

## Security and operations

Validate GitHub hosts and repository paths; reject arbitrary URLs and redirects. Centralize timeouts, bounded pagination, and rate-limit handling. Keep secrets and raw client IP addresses out of logs and stored rate-limit buckets; render repository content as escaped text.
