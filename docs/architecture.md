# Architecture

## Analysis flow

```text
GitHub URL → validator → GitHub client → normalized data → analyzers
           → scoring + findings → recommendations → JSON report / API → web app
                                                              ↘ PostgreSQL
```

The CLI and API share the same application core. PostgreSQL stores repositories, reports, dimension scores, findings, and insights. The web app calls the API server-side and renders stored reports by ID.

## Module boundaries

- `integrations/github`: GitHub requests, pagination, timeouts, and normalized provider errors.
- `schemas`: normalized models independent of raw GitHub responses.
- `analyzers`: per-dimension metrics with no direct HTTP calls.
- `scoring`: combines evaluable dimensions and computes coverage, without API, storage, or UI dependencies.
- `detection` and `insights`: deterministic rules with evidence and source links.
- `services`: orchestration and report construction.
- `database`: SQLAlchemy models, sessions, and persistence.
- `api/v1` and `cli`: adapters from the analysis core to HTTP and the terminal.
- `apps/web`: report presentation; scoring rules are not duplicated in the frontend.

## Decisions

The monorepo contains a Python package shared by the CLI and FastAPI. PostgreSQL runs locally through Docker Compose and schema changes use Alembic. Timestamps use UTC; each report records the scoring engine version. Unknown signals are not scored as zero. GitHub REST API is the first provider; a server-side token is optional, and visitor personal tokens are never requested. Repository content is never executed.

## Security and operations

Validate GitHub hosts and repository paths; reject arbitrary URLs and redirects to private networks. Centralize timeouts, pagination, caching, and rate-limit handling. Bound API responses, keep secrets out of logs, and escape repository content before rendering it as HTML.
